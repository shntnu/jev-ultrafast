"""Piximi observations, typed decisions, single-use execution, and outcome evidence."""

import time
from copy import deepcopy

from browser_harness.helpers import cdp

from .browser import Browser, StalePage
from .model import action_space, choose, field_context, field_text
from .piximi import URL, require_piximi, verify_training
from .questions import DEFAULT_GOAL, MAX_STEPS

TERMINAL = {"done", "needs_review", "blocked", "uncertain", "error"}


class Agent:
    def __init__(self, goal=DEFAULT_GOAL, *, target_id=None, screenshots=False):
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 6000:
            raise ValueError("Supply one Piximi goal of 1-6,000 characters")
        self.pending_text = None
        self.screenshots = screenshots
        if target_id:
            require_piximi(cdp("Target.getTargetInfo", targetId=target_id)["targetInfo"]["url"])
        self.browser = Browser(URL, target_id=target_id)
        page = self.browser.observe(screenshot=screenshots)
        require_piximi(page["url"])
        self.state = dict(
            browser=self.browser, target_id=self.browser.target, goal=goal.strip(), page=page,
            decision=None, history=[], status="ready", decisions=[], text_calls=[],
            elapsed_ms=0, started_at=None, verification=None, evidence={}, error=None,
            wait_count=0, busy_since=None, expected_epochs=3 if goal.strip() == DEFAULT_GOAL else None,
        )
        self.remember(page)

    def remember(self, page):
        """Keep observed training history when its dialog is subsequently closed."""
        facts = page.get("piximi", {})
        evidence = self.state.setdefault("evidence", {})
        if facts.get("project") and evidence.get("project") not in (None, facts["project"]):
            evidence.clear()
        for key in ("project", "epochs", "completed_epochs"):
            if facts.get(key) not in (None, ""):
                evidence[key] = facts[key]

    def observe(self):
        page = self.state["browser"].observe(screenshot=self.screenshots)
        require_piximi(page["url"])
        self.state["page"] = page
        self.remember(page)
        return page

    def snapshot(self):
        return {
            **{k: v for k, v in self.state.items() if k != "browser"},
            "elements": action_space(self.state["page"]["actions"])[0],
        }

    def command(self, name, body=None):
        try:
            return self._command(name, body or {})
        except StalePage:
            raise
        except (RuntimeError, TimeoutError, ValueError) as error:
            if self.state["status"] != "uncertain":
                self.state["status"] = "error"
            self.state["error"] = str(error)
            self.state["decision"] = None
            raise

    def _command(self, name, body):
        state = self.state
        if name == "observe":
            self.observe()
            state["decision"] = None
            return self.snapshot()
        if name == "resume":
            # Explicit user operation: observe first, never replay the interrupted action.
            if body.get("goal"):
                goal = body["goal"].strip()
                if not goal or len(goal) > 6000:
                    raise ValueError("Supply one Piximi goal of 1-6,000 characters")
                state["goal"] = goal
                state["expected_epochs"] = 3 if goal == DEFAULT_GOAL else None
                self.pending_text = None
            self.observe()
            state.update(status="ready", decision=None, error=None, busy_since=None, verification=None)
            return self.snapshot()
        if state["status"] in TERMINAL:
            raise ValueError("Run stopped. Inspect the page, then explicitly resume or start a new task.")
        if state["started_at"] is None:
            state["started_at"] = time.perf_counter()
        if name == "tick":
            try:
                self.command("predict")
                if state["decision"]:
                    self.command("act", {"fingerprint": state["page"]["fingerprint"]})
            except StalePage:
                state.update(decision=None, status="ready")
                self.observe()
            return self.snapshot()
        if name == "predict":
            self.observe()
            facts = state["page"].get("piximi", {})
            if facts.get("busy"):
                state["busy_since"] = state.get("busy_since") or time.monotonic()
                if time.monotonic() - state["busy_since"] > 180:
                    state.update(status="blocked", error="Piximi remained busy for 3 minutes. Inspect and resume.")
                else:
                    state.update(status="waiting", decision=None)
                    state["wait_count"] = state.get("wait_count", 0) + 1
                    time.sleep(1)
                self.elapsed()
                return self.snapshot()
            state["busy_since"] = None
            if len(state["decisions"]) >= MAX_STEPS * 2:
                raise ValueError("Reached the 120-decision budget. Inspect the trace before resuming.")
            policy_page = deepcopy(state["page"])
            expected = state.get("expected_epochs")
            if expected is not None and (facts.get("epochs") != str(expected) or facts.get("editing_epochs")):
                policy_page["actions"] = [a for a in policy_page["actions"]
                                          if a["label"].lower() != "fit classifier"]
                policy_page.setdefault("piximi", {})["training_guard"] = (
                    f"Set Epochs to {expected} and blur the field before starting training."
                )
            state["decision"] = choose(policy_page, state["goal"], state["history"])
            state["decisions"].append({**state["decision"], "fingerprint": state["page"]["fingerprint"]})
            state["status"] = "predicted"
        elif name == "act":
            decision, page = state["decision"], state["page"]
            if not decision or body.get("fingerprint") != page["fingerprint"]:
                raise ValueError("Observe and choose before acting")
            state["decision"] = None
            selected = decision["choice"]
            if selected in {"DONE", "BLOCKED"}:
                if not state["browser"].fresh(page):
                    raise StalePage("Page changed since the decision")
                fresh = self.observe()
                facts = fresh.get("piximi", {})
                evidence = {**state.get("evidence", {}), **facts}
                for key in ("epochs", "completed_epochs"):
                    if evidence.get(key) is None:
                        evidence[key] = state.get("evidence", {}).get(key)
                if selected == "BLOCKED":
                    state["status"] = "blocked"
                elif state.get("expected_epochs") is not None:
                    state["verification"] = verify_training(evidence, state["expected_epochs"])
                    state["status"] = "done" if state["verification"]["passed"] else "needs_review"
                else:
                    state["verification"] = {"passed": False, "evidence": evidence,
                                             "reason": "No automatic outcome check for this custom goal."}
                    state["status"] = "needs_review"
                self.elapsed()
                return self.snapshot()
            action = next(a for a in page["actions"] if a["id"] == selected)
            if len(state["history"]) >= MAX_STEPS:
                raise ValueError("Reached the 60-action budget")
            text, helper = None, None
            if action["kind"] == "fill":
                if not state["browser"].fresh(page):
                    raise StalePage("Page changed before text generation")
                context = field_context(state["goal"], action, page, state["history"])
                if self.pending_text and self.pending_text[0] == context:
                    _, text, helper = self.pending_text
                else:
                    text, helper = field_text(context)
                    self.pending_text = (context, text, helper)
                    state["text_calls"].append({**helper, "field": action["label"], "value": text})
            require_piximi(page["url"])
            entry = dict(
                step=len(state["history"]) + 1, action=action["label"], kind=action["kind"],
                choice=selected, probability=decision["probabilities"][selected],
                confidence=decision["confidence"], latency_ms=decision["latency_ms"], text=text,
                text_helper=helper["model"] if helper else None,
                operation=decision["operation"], target=decision["target"], page_changed=None,
                url=page["url"], usage=decision["usage"], outcome="attempted",
            )
            state["history"].append(entry)
            try:
                state["browser"].act(action, page, text=text)
            except StalePage:
                state["history"].pop()  # Rejected before browser input.
                raise
            except (RuntimeError, TimeoutError):
                entry["outcome"] = "uncertain"
                state["status"] = "uncertain"
                self.pending_text = None
                self.elapsed()
                raise
            entry["outcome"] = "executed"
            self.pending_text = None
            self.elapsed()
            entry["executed_ms"] = state["elapsed_ms"]
            self.observe()
            self.elapsed()
            entry.update(page_changed=state["page"]["fingerprint"] != page["fingerprint"],
                         url=state["page"]["url"], elapsed_ms=state["elapsed_ms"])
            repeated = state["history"][-3:]
            state["status"] = "blocked" if len(repeated) == 3 and all(
                h["page_changed"] is False and h["kind"] != "wait" for h in repeated
            ) else "ready"
        else:
            raise ValueError("Unknown command")
        self.elapsed()
        return self.snapshot()

    def elapsed(self):
        if self.state.get("started_at") is not None:
            self.state["elapsed_ms"] = round((time.perf_counter() - self.state["started_at"]) * 1000)

    def run(self):
        while self.state["status"] not in TERMINAL:
            yield self.command("tick")

    def close(self):
        self.browser.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

"""Run a Piximi goal. Leaves the tab open and writes a local trace, including failures."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from jev_ultrafast import Agent
from jev_ultrafast.questions import DEFAULT_GOAL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal", default=DEFAULT_GOAL)
    parser.add_argument("--target", help="Attach to an existing Piximi target ID without navigating")
    parser.add_argument("--trace", type=Path)
    args = parser.parse_args()
    trace = args.trace or Path("artifacts") / (datetime.now(timezone.utc).strftime("piximi-%Y%m%dT%H%M%S") + ".json")
    agent = Agent(args.goal, target_id=args.target)
    print(f"Piximi tab: {agent.browser.target}", flush=True)
    try:
        for state in agent.run():
            last = state["history"][-1] if state["history"] else {}
            print(f"{state['elapsed_ms']:>6} ms  {len(state['history'])} actions  "
                  f"{state['status']}  {last.get('action', '')}", flush=True)
    finally:
        state = agent.snapshot()
        try:
            state["final_observation"] = agent.browser.observe(screenshot=False)
        except (RuntimeError, TimeoutError) as error:
            state["observation_error"] = str(error)
        trace.parent.mkdir(parents=True, exist_ok=True)
        trace.write_text(json.dumps(state, indent=2, ensure_ascii=True))
        print(f"Trace: {trace}\nTab left open. {len(state['decisions'])} Jev calls; "
              f"{len(state['text_calls'])} text calls.", flush=True)
    if state["status"] != "done":
        raise SystemExit(f"Outcome not verified: {state['status']}")


if __name__ == "__main__":
    main()

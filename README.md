# Jev for Piximi

> [!NOTE] > **An experimental AI assistant for Piximi.** > > Give it a request like "load the U2OS example, train for three epochs, and show the evaluation," and it operates [Piximi](https://piximi.app/) in your existing Chrome browser. > Jev is an AI model from TypeSafe that chooses which controls to use; a separate language model fills in text fields. > It reads page controls, not microscopy images, and its dashboard shows screenshots and an action history so you can follow its work. > One [verified test](docs/performance.md) completed that workflow in about 10 seconds; broader Piximi workflows still need testing.

## Run

```bash
uv sync
cp .env.example .env
# Set TYPESAFE_API_KEY and TEXT_MODEL_API_KEY in .env.
uv run jev
```

Open http://127.0.0.1:8766, choose a new or existing Piximi workspace, and click **Open Piximi**.
Use **Run analysis** or inspect and execute individual choices.
The default goal loads the U2OS example, trains a classifier for three epochs, and opens evaluation results.
Tabs stay open so you can inspect or save work in Piximi.

Chrome connects through Browser Harness.
Enable **Allow remote debugging for this browser instance** at `chrome://inspect/#remote-debugging`, then approve Chrome's connection prompt.
`uv run browser-harness --doctor` provides connection diagnostics.

The command-line runner saves a trace even if the run fails and leaves its tab open:

```bash
uv run --env-file .env python examples/run.py
uv run --env-file .env python examples/run.py \
  --goal 'Load the human U2OS cells example and open its classifier hyperparameters without training.'
```

To continue an existing workspace, choose it in the inspector or pass `--target TARGET_ID` to the runner.
Attaching never reloads the tab.
**Refresh view** is read-only; **Resume with goal** takes a fresh observation before making a new decision.
It never replays an interrupted browser action.

```python
from jev_ultrafast import Agent

agent = Agent("Load the human U2OS cells example and open its classifier hyperparameters without training.")
for state in agent.run():
    print(state["status"])
# Inspect the still-open tab. Call agent.close() only when ready to close an owned tab.
```

## What changed

This repository now targets Piximi exclusively.
The previous Flights/Wikipedia demonstrations and their performance claims have been removed; their history remains in Git.
The Python package and `jev` command keep their existing names.

The reader exposes Piximi tooltip labels, nearby numeric-field labels, modal tabs, and nested scroll regions.
Loading and training indicators trigger bounded read-only waits without repeated model calls.
The default task withholds **Fit Classifier** until the epoch field reads `3` and is no longer focused.
Those are observed state checks; the executor never injects a prepared field value or runs a scripted click sequence.

Every decision contains an operation and operation-specific target heads in one TypeSafe request.
Only the selected head is consumed.
Targets resolve to observed DOM nodes, with freshness and occlusion checks before input.
Models cannot emit selectors or executable code.
Screenshots are for the inspector; Jev receives structured state, not image pixels.

## Outcomes and limits

`done` means the default U2OS training contract passed independent DOM checks.
Checks include the project name, configured epochs, plotted training points, idle state, and visible numeric accuracy/loss with reported class metrics (which may be `N/A`).
A model's `DONE` choice by itself yields `needs_review` for custom goals.
`blocked`, `error`, and `uncertain` preserve the page and trace for inspection.
A timed-out mutation is recorded as uncertain and is never automatically retried.

This is experimental browser automation.
Classification is the first verification target; segmentation and measurements have workflow guidance but no automatic success contract.
Canvas drawing, image interpretation, uploads, and pop-up tabs remain manual.
An evaluation on a tiny example dataset demonstrates interaction, not scientific model quality.
The checks depend on Piximi's current DOM and Nivo chart rendering; missing evidence fails closed.
See [validation notes](docs/performance.md) for what was actually exercised.

Credentials stay server-side in ignored `.env` files.
Live runs make paid API calls; tests do not.
Raw traces stay under ignored `artifacts/`.

## Development

```bash
uv run ruff check .
uv run pytest
node --check jev_ultrafast/static/app.js
node --check jev_ultrafast/snapshot.js
uv build
uv run python scripts/check_guards.py
```

The last command uses Chrome with a local HTML fixture, without model calls.
The core loop is in [agent.py](jev_ultrafast/agent.py), Piximi guidance in [questions.py](jev_ultrafast/questions.py), and outcome checks in [piximi.py](jev_ultrafast/piximi.py).

Install the project-local TypeSafe skill for Codex and Claude Code:

```bash
npx skills@1.5.20 add typesafe-ai/skills --skill typesafe-ai -a codex -a claude-code -y
```

`skills-lock.json` records the installed source and hash.
The installer-owned skill directory and Claude link are ignored.
Use the installed skill and current [TypeSafe docs](https://docs.typesafe.ai/) when changing the integration.
Piximi workflow references: [classification tutorial](https://documentation.piximi.app/pages/tutorial/classify-example-eukaryotic-image.html) and [source](https://github.com/piximi/piximi).

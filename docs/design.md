# Piximi agent design

The public input is one natural-language Piximi goal.
The entry points always open Piximi or attach to an existing Piximi tab.
The low-level browser adapter also supports local HTML for offline browser checks.

The loop is observation, indexed candidates, a TypeSafe operation/target decision, freshness validation, one execution, and a fresh observation.
Piximi workflow knowledge is supplied to every relevant question.
The text helper sees the goal, observed field, page context, and recent actions.
Generated text is reused after a stale rejection only if that entire input is unchanged.

The DOM adapter reads rendered controls, tooltip-wrapper labels, field labels, and scrollable regions.
It filters covered controls, hidden tabs, and external links.
Each scroll direction is an operation-specific target associated with a real observed region.
Code resolves coordinates at execution time.

Piximi's loading and training indicators bypass model calls while busy, with a three-minute bound.
The default U2OS contract excludes training until its requested epoch value has been observed and the field has lost focus.
The model still discovers and selects controls; code does not navigate a fixed sequence.

Execution is logged before its resulting observation.
A stale rejection happens before input and may be reobserved.
Other mutation failures stop as uncertain, preserving the attempted action.
Explicit resume observes the current page and clears the old choice; it never replays that action.
Tabs are retained by the inspector and command-line runner for manual inspection and saving.

The default U2OS verification checks fresh evaluation evidence plus previously observed training evidence from the same run.
Nivo's rendered circles supply the training epoch count; chart labels alone do not prove completed training.
Missing or incompatible evidence yields needs_review.
Custom tasks always require outcome review.

The local inspector binds to loopback, validates Host and Origin, and requires a per-process token for mutation requests.
API keys never reach the browser UI.

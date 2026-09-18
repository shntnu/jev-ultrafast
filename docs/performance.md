# Piximi validation

The first verified Piximi workflow was exercised on September 18, 2026.
This is one successful browser run, not a reliability benchmark.

The default natural-language goal loaded the human U2OS example, trained an image classifier for three epochs with existing labels, and opened evaluation results.
The verified run took **9,950 ms**, with **9 executed actions, 14 Jev requests, and 1 text-helper request**.
Timing starts at the first decision cycle after opening Piximi and includes loading waits, model calls, training, and evaluation.
It excludes initial browser connection and page load.
The unmodified text helper supplied the epoch value `3`.
No model-generated selectors, scripted click sequence, or manually entered training value was used.

[Recorded outcome and action sequence](piximi-validation.json) contains the actual models, call counts, metrics, and verification checks.
The full local trace is `artifacts/piximi-verified.json` (ignored).
A prior rewrite trial reached the same requested training/evaluation outcome but failed verification because the metric parser did not handle trailing colons or `N/A` values.
Its local trace is `artifacts/piximi-first.json`; it used 11 Jev requests and 1 text request over 8 actions.
The parser was corrected, and the successful run started in a new tab.

Verification checks the U2OS project name, epoch setting, number of rendered training points, visible evaluation view, reported metrics, and idle state.
The three-epoch evidence comes from the training plot, not a model's completion choice.
Undefined class metrics stay `N/A`; they are never converted to numeric scores.
The example is too small to establish classifier quality.

The final checks include 38 offline tests, 23 local-browser guard checks, Ruff, both JavaScript syntax checks, and a package build.
The browser checks include tooltip-wrapper labels, selected tabs, clipped fields, nested scrolling, freshness, and occlusion.
The inspector was checked at 1120px and 390px widths, including attachment to an existing Piximi evaluation tab.
No model APIs are called by the offline or local-browser checks.

The generic-agent trials before the rewrite failed on Piximi loading/navigation and default epoch handling.
Their temporary traces remain local; they are not included in the successful rewrite count.
Historical Flights and Wikipedia timings do not describe this implementation.

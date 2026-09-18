"""Piximi-only routing and conservative, DOM-based outcome checks."""

import math
from urllib.parse import urlparse

URL = "https://piximi.app/"


def require_piximi(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "piximi.app" or parsed.port not in (None, 443):
        raise ValueError("This agent operates only https://piximi.app/.")


def verify_training(evidence, epochs):
    """Check a fresh evaluation view plus previously observed, rendered training data.

    This contract is deliberately specific to the U2OS example, not arbitrary goals.
    Missing evidence never becomes a pass, and model DONE is not used here.
    """
    checks = {
        "piximi": evidence.get("url", "").startswith(URL),
        "u2os_project": "u2os" in evidence.get("project", "").lower(),
        "requested_epochs": evidence.get("epochs") == str(epochs),
        "completed_epochs": evidence.get("completed_epochs") == epochs,
        "evaluation_visible": evidence.get("evaluation", False),
        "numeric_metrics": all(
            type(evidence.get("metrics", {}).get(key)) in (int, float)
            and math.isfinite(evidence["metrics"][key])
            for key in ("Accuracy", "Cross entropy")
        ),
        "class_metrics_present": all(
            evidence.get("metrics", {}).get(key) == "N/A" or (
                type(evidence.get("metrics", {}).get(key)) in (int, float)
                and math.isfinite(evidence["metrics"][key])
            ) for key in ("Precision", "Recall", "F1-score")
        ),
        "idle": not evidence.get("busy", True),
    }
    return {"passed": all(checks.values()), "checks": checks, "evidence": evidence}

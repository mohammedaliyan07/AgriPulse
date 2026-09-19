# -*- coding: utf-8 -*-
"""
AgriPulse — Streamlit Community Cloud entry point
=================================================
Streamlit Community Cloud looks for `streamlit_app.py` by default when you
deploy a GitHub repo, so this zero-config shim simply executes `app.py`
(the full dashboard). Both entry points work:

    streamlit run app.py            # local use — the real dashboard
    streamlit run streamlit_app.py  # identical (this file, used by the Cloud)

No other configuration is required: the committed `outputs/` artefacts mean
the dashboard renders immediately after deployment.
"""
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_TARGET = _HERE / "app.py"

if not _TARGET.exists():
    raise FileNotFoundError(
        f"app.py not found next to streamlit_app.py (expected at {_TARGET}). "
        "Make sure the full repository was uploaded."
    )

# Execute app.py with its own __file__ so relative paths (outputs/, etc.)
# resolve correctly regardless of the working directory.
exec(_TARGET.read_text(encoding="utf-8"), {"__name__": "__main__", "__file__": str(_TARGET)})

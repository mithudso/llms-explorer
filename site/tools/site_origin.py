"""One canonical-domain migration shared by static exports and their indexes."""
import json
import os
from pathlib import Path

CONFIG = json.loads((Path(__file__).resolve().parents[1] / "site-origin.json").read_text())
DEFAULT_SITE_URL = CONFIG["canonical"]


def default_site_url() -> str:
    requested = os.environ.get("SITE_URL", "").strip().rstrip("/") or DEFAULT_SITE_URL
    return DEFAULT_SITE_URL if requested in CONFIG["legacy"] else requested

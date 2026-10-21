"""Verify new public tracker citations without credentials or source publication."""
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path


def resolve(repo: Path, hub: Path, changes: dict) -> tuple[dict, list[str]]:
    allow_path = repo / ".privacy-allowlist"
    allow_text = allow_path.read_text() if allow_path.is_file() else ""
    existing = set(allow_text.splitlines())
    cache_path = hub / "research/.site-public-references.json"
    cache = json.loads(cache_path.read_text()) if cache_path.is_file() else {}
    keys = set()
    candidates = {path: path.read_text() for path in (repo / "site/src/data/concepts").glob("*.json")}
    candidates.update(changes)
    for path, value in candidates.items():
        if isinstance(value, str) and any(path.is_relative_to(root) for root in
                                         (repo / "site/src/data/concepts", repo / "outputs/llms-concepts")):
            keys.update(re.findall(r"\bSERVER-\d+\b", value))
    keys -= existing
    def stale(value):
        try:
            return datetime.now(UTC) - datetime.fromisoformat(value["checked"]) > timedelta(days=1)
        except (KeyError, ValueError):
            return True
    keys.update(key for key, value in cache.items() if not value["public"] and stale(value))
    if len(keys) > 200:
        raise ValueError("More than 200 new public tracker references need verification; split this refresh")

    def check(key):
        if key in cache and (cache[key]["public"] or not stale(cache[key])):
            return key, cache[key]
        url = "https://jira.mongodb.org/rest/api/2/issue/" + key + "?fields=summary"
        try:
            response = subprocess.run(["curl", "--silent", "--show-error", "--connect-timeout", "3",
                                       "--max-time", "8", "-A", "Mozilla/5.0", url],
                                      capture_output=True, text=True, timeout=12, check=False)
            data = json.loads(response.stdout)
            public = response.returncode == 0 and data.get("key") == key and bool(data.get("fields", {}).get("summary"))
        except (ValueError, OSError, subprocess.TimeoutExpired):
            public = False
        return key, {"public": public, "checked": datetime.now(UTC).isoformat()}

    with ThreadPoolExecutor(max_workers=8) as pool:
        cache.update(pool.map(check, sorted(keys)))
    accepted = sorted(key for key in keys if cache[key]["public"])
    blocked = sorted(key for key, value in cache.items() if not value["public"])
    writes = {}
    if accepted:
        writes[allow_path] = allow_text.rstrip() + "\n\n# Anonymous public MongoDB issue metadata verified by research completion.\n" + "\n".join(accepted) + "\n"
    if keys:
        writes[cache_path] = json.dumps(cache, indent=2) + "\n"
    return writes, blocked

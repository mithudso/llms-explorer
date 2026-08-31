"""settings.py — persisted hub-manager options (~/.global-ai-hub/hub-manager.json).

Precedence at use time: explicit env vars (HUB_OLLAMA_URLS, HUB_EMBED_MODEL)
win over saved settings; saved settings win over defaults. The TUI's Settings
tab edits this file only — it never mutates config.yaml or the environment.
"""

from __future__ import annotations

import json
import os

from . import core

SETTINGS_PATH = core.HUB_DIR / "hub-manager.json"

DEFAULTS = {
    "max_pages": 2000,      # crawl page cap per docset (300 missed most docs)
    "crawlers": 3,          # concurrent crawls
    "refresh_secs": 3,      # queue/health auto-refresh interval
    "log_lines": 200,       # log viewer tail depth
    "query_top": 5,         # docset query result count
    "mirror_clone": 0,      # 1 = also write a browsable offline site clone
    # 1 = pipeline_manager --local-only: keep the mirror stage on this box.
    # Remote boxes have no ~/.global-ai-hub/scripts/llms_acquire.py, so a
    # crawl placed there falls back to trafilatura and loses the code blocks.
    "local_only": 1,
    "ollama_urls": "",      # blank = embed_core default / env
    "embed_model": "",      # blank = embed_core default / env
    "disabled_checks": "",  # comma-separated health check_ids to mute
    # host=user@host pairs enabling ssh process control on Remotes (blank user
    # disables that host), e.g. "192.168.4.1=mitch@192.168.4.1"
    "ssh_targets": ("192.168.4.1=mitch@192.168.4.1,"
                    "192.168.4.75=mithudso@192.168.4.75,"
                    "192.168.4.113=mitch.hudson@192.168.4.113"),
}


def load() -> dict:
    data = dict(DEFAULTS)
    if SETTINGS_PATH.exists():
        try:
            saved = json.loads(SETTINGS_PATH.read_text())
            data.update({k: v for k, v in saved.items() if k in DEFAULTS})
        except (OSError, json.JSONDecodeError):
            pass
    return data


def save(values: dict) -> dict:
    data = load()
    for key, value in values.items():
        if key not in DEFAULTS:
            continue
        if isinstance(DEFAULTS[key], int):
            try:
                # floor of 1: a 0/negative interval would busy-spin the UI
                # timers and Semaphore(0) would deadlock the manager
                value = max(1, int(value))
            except (TypeError, ValueError):
                continue
        data[key] = value
    tmp = SETTINGS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, SETTINGS_PATH)
    return data


def stage_env(settings: dict | None = None) -> dict:
    """Env overrides to pass to spawned hub scripts, honoring precedence."""
    settings = settings or load()
    env = {}
    if settings.get("ollama_urls") and "HUB_OLLAMA_URLS" not in os.environ:
        env["HUB_OLLAMA_URLS"] = settings["ollama_urls"]
    if settings.get("embed_model") and "HUB_EMBED_MODEL" not in os.environ:
        env["HUB_EMBED_MODEL"] = settings["embed_model"]
    if settings.get("mirror_clone") and "HUB_MIRROR_CLONE" not in os.environ:
        env["HUB_MIRROR_CLONE"] = "1"
    return env

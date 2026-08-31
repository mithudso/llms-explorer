#!/usr/bin/env python3
"""
hub_lib.py — Shared library for all Global AI Hub scripts.
Single source of truth for config loading, embedding, hashing, and file I/O with locking.
"""

import os
import sys
import json
import fcntl
import hashlib
import urllib.request
import urllib.error
import time
import logging

HUB_DIR = os.path.expanduser("~/.global-ai-hub")
CONFIG_FILE = os.path.join(HUB_DIR, "config.yaml")
INDEX_JSON = os.path.join(HUB_DIR, "UNIVERSAL-INDEX.json")
EMBEDDINGS_JSON = os.path.join(HUB_DIR, "UNIVERSAL-EMBEDDINGS.json")
CONCEPT_FILE = os.path.join(HUB_DIR, "docs", "CONCEPT_TREE.json")
LOCK_FILE = os.path.join(HUB_DIR, ".hub.lock")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _parse_yaml_lite(text):
    """Minimal stdlib YAML parser for flat key-value and list configs."""
    result = {}
    current_key = None
    current_list = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current_key and current_list is not None:
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if ":" in stripped:
            if current_key and current_list is not None:
                result[current_key] = current_list
                current_list = None
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val:
                # Try to coerce types
                if val.lower() in ("true", "false"):
                    result[key] = val.lower() == "true"
                else:
                    try:
                        result[key] = float(val) if "." in val else int(val)
                    except ValueError:
                        result[key] = val
                current_key = None
            else:
                current_key = key
                current_list = []
    if current_key and current_list is not None:
        result[current_key] = current_list
    return result


_config_cache = None

def load_config():
    """Load config.yaml. Cached after first call."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    defaults = {
        "ollama_url": "http://localhost:11434",
        "embed_model": "nomic-embed-text",
        "concept_model": "qwen2.5-coder:7b",
        "idle_threshold": 2.0,
        "sleep_between_files": 2.0,
        "sleep_idle_check": 60.0,
        "max_content_chars": 4000,
        "allowed_extensions": [".md", ".txt", ".json", ".yaml", ".yml", ".py", ".sh", ".js", ".ts", ".go", ".rs"],
        "excluded_dirs": [".git", ".github", "__pycache__", "node_modules", ".claude", ".next", "build", "dist", ".venv", "venv", ".system_generated"],
    }
    try:
        with open(CONFIG_FILE, "r") as f:
            parsed = _parse_yaml_lite(f.read())
        defaults.update(parsed)
    except Exception:
        pass
    _config_cache = defaults
    return defaults


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def get_logger(name, log_file=None):
    """Create a logger with optional file output and timestamps."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if log_file:
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=3)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


# ---------------------------------------------------------------------------
# File I/O with locking
# ---------------------------------------------------------------------------



def read_json(filepath):
    """Read a JSON file safely, returning empty dict on failure."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def write_json_atomic(filepath, data):
    """Write JSON atomically via tmp file + rename."""
    tmp = filepath + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.rename(tmp, filepath)


# ---------------------------------------------------------------------------
# Content helpers
# ---------------------------------------------------------------------------

def get_text_content(filepath, max_chars=None):
    """Read text from a file, up to max_chars."""
    if max_chars is None:
        max_chars = load_config().get("max_content_chars", 4000)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read(max_chars)
    except (UnicodeDecodeError, PermissionError, FileNotFoundError):
        return None

def compute_hash(text, model=None):
    """SHA256 hash of model+text, truncated to 16 hex chars."""
    if model is None:
        model = load_config()["embed_model"]
    return hashlib.sha256((model + "\n" + text).encode("utf-8")).hexdigest()[:16]

def is_allowed_file(filepath, cfg=None):
    """Check if a file has an allowed extension."""
    if cfg is None:
        cfg = load_config()
    return any(filepath.endswith(ext) for ext in cfg["allowed_extensions"])

def is_excluded_dir(dirname, cfg=None):
    """Check if a directory should be excluded."""
    if cfg is None:
        cfg = load_config()
    return dirname in cfg["excluded_dirs"]


# ---------------------------------------------------------------------------
# Ollama embedding
# ---------------------------------------------------------------------------

_embed_fail_log = {"when": 0.0, "reason": ""}
EMBED_FAIL_LOG_INTERVAL = 60  # seconds between repeats of the same reason


def _log_embed_failure(model, url, reason):
    """Say WHY an embedding failed, at most once a minute per distinct reason.

    This used to be a bare `except Exception: return None`. The caller treats
    None as "skip this file", so when the configured embed_model was not pulled
    on a box, idle-indexer logged `Indexing: <path>` for every file forever
    while writing nothing at all — hub.db sat at 0 rows for days on one box and
    stalled at 39% on another, with no error anywhere. Rate-limited because the
    indexer calls this once per file.
    """
    import time as _time
    now = _time.monotonic()
    same = reason == _embed_fail_log["reason"]
    if same and now - _embed_fail_log["when"] < EMBED_FAIL_LOG_INTERVAL:
        return
    _embed_fail_log.update(when=now, reason=reason)
    get_logger("hub_lib", os.path.join(HUB_DIR, "idle-indexer.log")).warning(
        "embedding failed (model=%s url=%s): %s", model, url, reason)


def fetch_embedding(text, model=None):
    """Fetch an embedding vector from Ollama's /api/embed endpoint.

    Returns None on failure, but never silently: see _log_embed_failure.
    """
    cfg = load_config()
    if model is None:
        model = cfg["embed_model"]
    url = cfg["ollama_url"] + "/api/embed"
    payload = json.dumps({"model": model, "input": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "embeddings" in data and isinstance(data["embeddings"], list):
                return data["embeddings"][0]
            if "embedding" in data:
                return data["embedding"]
    except Exception as exc:
        # a missing model comes back as HTTP 404 with the pull hint in the body
        detail = getattr(exc, "read", None)
        body = ""
        if detail is not None:
            try:
                body = detail().decode("utf-8", "replace")[:200]
            except Exception:
                body = ""
        _log_embed_failure(model, url, f"{type(exc).__name__}: {exc} {body}".strip())
        return None
    _log_embed_failure(model, url, "response had no embedding field")
    return None


# ---------------------------------------------------------------------------
# Index operations (SQLite backend)
# ---------------------------------------------------------------------------

import hub_sqlite

def load_index():
    return hub_sqlite.load_index()

def load_embeddings():
    return hub_sqlite.load_embeddings()

def upsert_file(abs_path, content_hash, size, embedding):
    hub_sqlite.upsert_file(abs_path, content_hash, size, embedding, load_config()["embed_model"])

def gc_stale_entries():
    return hub_sqlite.gc_stale_entries()

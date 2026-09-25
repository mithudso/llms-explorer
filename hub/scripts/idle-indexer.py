#!/usr/bin/env python3
"""
idle-indexer.py — Background daemon that indexes files during idle time.
Crawls watch_dirs.txt, embeds unindexed files via Ollama, and runs GC.
Uses hub_lib for all operations.

Usage:
  idle-indexer.py          # no arguments; runs until SIGTERM
Only embeds while load average < idle_threshold. Watch list:
~/.global-ai-hub/watch_dirs.txt (one directory per line — the Index tab
appends to it). Start from the hub-manager Health tab (t on its row);
logs to ~/.global-ai-hub/idle-indexer.log.

Env: HUB_IDLE_THRESHOLD overrides config.yaml's idle_threshold — needed on
any box whose baseline load routinely exceeds the shared config's value
(e.g. a multi-core Ollama inference host that's never "idle" by a
single-user-laptop threshold; watch_dirs.txt is shared across boxes but
idle_threshold in config.yaml is one flat number, so per-box tuning has to
go through env, same pattern as HUB_OLLAMA_URLS/HUB_EMBED_MODEL).
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import hub_lib

WATCH_DIRS_FILE = os.path.join(hub_lib.HUB_DIR, "watch_dirs.txt")
log = hub_lib.get_logger("idle-indexer", os.path.join(hub_lib.HUB_DIR, "idle-indexer.log"))

def is_system_idle(cfg):
    try:
        load1, _, _ = os.getloadavg()
        threshold = float(os.environ.get("HUB_IDLE_THRESHOLD", cfg.get("idle_threshold", 2.0)))
        return load1 < threshold
    except Exception:
        return True

def get_watch_dirs():
    if not os.path.exists(WATCH_DIRS_FILE):
        return [os.path.expanduser("~/dev")]
    with open(WATCH_DIRS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip() and os.path.isdir(line.strip())]

def main_loop():
    log.info("Idle indexer daemon started.")
    cfg = hub_lib.load_config()
    sleep_between = cfg.get("sleep_between_files", 2.0)
    sleep_idle = cfg.get("sleep_idle_check", 60.0)
    gc_interval = 10  # Run GC every 10 full passes
    pass_count = 0

    while True:
        if not is_system_idle(cfg):
            log.info("System busy, sleeping...")
            time.sleep(sleep_idle)
            continue

        log.info("System idle, starting indexing pass...")
        indexed_map = hub_lib.load_index()
        fts_map = hub_lib.hub_sqlite.load_fts_index()
        watch_dirs = get_watch_dirs()

        for wdir in watch_dirs:
            for root, dirs, files in os.walk(wdir):
                dirs[:] = [d for d in dirs if not hub_lib.is_excluded_dir(d, cfg)]
                for f in files:
                    if not hub_lib.is_allowed_file(f, cfg):
                        continue
                    filepath = os.path.join(root, f)
                    abs_path = os.path.abspath(filepath)
                    if abs_path in {hub_lib.INDEX_JSON, hub_lib.EMBEDDINGS_JSON}:
                        continue
                    try:
                        current_size = os.path.getsize(abs_path)
                        current_mtime = os.path.getmtime(abs_path)
                    except OSError:
                        continue
                    if current_size == 0:
                        continue
                    existing = indexed_map.get(abs_path)
                    # Embedding current: still refresh the keyword row when it
                    # is missing or stale (the tail of a file can change
                    # without touching the embedded head). No Ollama call.
                    kw_fresh = hub_lib.hub_sqlite.fts_is_fresh(
                        fts_map.get(abs_path), current_size, current_mtime)
                    if existing and existing.get("size") == current_size:
                        if not kw_fresh:
                            hub_lib.index_keywords(abs_path)
                        continue

                    text = hub_lib.get_text_content(abs_path)
                    if not text or not text.strip():
                        continue
                    content_hash = hub_lib.compute_hash(text)
                    if existing and existing.get("hash") == content_hash:
                        if not kw_fresh:
                            hub_lib.index_keywords(abs_path)
                        continue

                    if not is_system_idle(cfg):
                        log.info("System became busy. Breaking to outer loop.")
                        break  # Break to outer idle check, not continue

                    log.info(f"Indexing: {abs_path}")
                    emb = hub_lib.fetch_embedding(text)
                    if emb:
                        hub_lib.upsert_file(abs_path, content_hash, current_size, emb)
                        indexed_map[abs_path] = {"hash": content_hash, "size": current_size}
                        # upsert_file wrote the keyword row too
                        fts_map[abs_path] = (current_size, current_mtime)
                    time.sleep(sleep_between)
                else:
                    continue
                break  # Propagate inner break

        pass_count += 1
        if pass_count % gc_interval == 0:
            removed = hub_lib.gc_stale_entries()
            if removed:
                log.info(f"GC removed {removed} stale entries.")

        log.info("Completed full pass. Sleeping 5 min.")
        time.sleep(sleep_idle * 5)

if __name__ == "__main__":
    os.makedirs(hub_lib.HUB_DIR, exist_ok=True)
    main_loop()

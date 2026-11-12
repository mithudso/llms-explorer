"""Explicit environment loading without interpolation, shell evaluation or discovery."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values


def load_environment(path: str | Path | None = None) -> None:
    chosen = path or os.environ.get("RESEARCH_LIBRARY_ENV_FILE")
    if not chosen:
        return
    source = Path(chosen).expanduser()
    if not source.is_file() or source.stat().st_size > 1024 * 1024:
        raise ValueError("The selected research library environment file is unavailable")
    for key, value in dotenv_values(source, interpolate=False).items():
        if value is not None:
            os.environ.setdefault(key, value)

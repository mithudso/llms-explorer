"""Explicit local environment loading without shell evaluation or secret output."""

from __future__ import annotations

import os
from pathlib import Path


def load_environment(path: str | Path | None = None) -> None:
    """Load only an explicitly selected file; existing process settings win.

    No search of the current directory occurs. dotenv does not execute shell
    syntax and interpolation is disabled so literal credential bytes survive.
    """
    chosen = path or os.environ.get("SKILL_REGISTRY_ENV_FILE")
    if not chosen:
        return
    source = Path(chosen).expanduser()
    if not source.is_file() or source.stat().st_size > 1024 * 1024:
        raise ValueError("The selected skill registry environment file is unavailable")
    try:
        from dotenv import dotenv_values
    except ImportError as exc:
        raise ValueError("Install skill-registry[mongo] to load an environment file") from exc
    for key, value in dotenv_values(source, interpolate=False).items():
        if value is not None:
            os.environ.setdefault(key, value)

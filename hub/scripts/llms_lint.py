#!/usr/bin/env python3
"""llms_lint — the deterministic passes of the llms-deep-optimizer (`/ldo`).

The implementation lives in the shared `llms-txt` library (`llms_txt.lint`), whose output is
byte-identical to the script that used to be here. This file keeps the entry point and the
import name working.

Usage:
    llms_lint.py detect FILE
    llms_lint.py check  FILE|DIR... [--kind K] [--check-links] [--fix] [--json]
                        [--mirror M] [--third-party]
    llms_lint.py hygiene FILE [--fix]

    import llms_lint; llms_lint.check(path)      # same module object as llms_txt.lint

`import llms_lint` returns the `llms_txt.lint` module itself, so every public and private name
(`check`, `detect_kind`, `_steer_hit`, `_mirror_headings`, ...) and any monkeypatch lands on the
code that actually runs. Install the library: `pip install -e ~/dev/libraries/llms-txt`.
"""
from __future__ import annotations

import sys

try:
    import llms_txt.lint as _impl
except ImportError as exc:  # pragma: no cover - environment problem, say how to fix it
    raise SystemExit(
        "llms_lint: the llms-txt library is not installed "
        f"({exc}); pip install 'llms-txt @ git+https://github.com/mithudso/llms-txt'"
    ) from exc

if __name__ == "__main__":
    raise SystemExit(_impl.main())

# A file-loaded copy of this module (importlib.util.spec_from_file_location) sees every name too.
globals().update(
    {k: v for k, v in vars(_impl).items() if not (k.startswith("__") and k.endswith("__"))}
)
# `import llms_lint` returns the library module itself, so monkeypatches reach the running code.
sys.modules[__name__] = _impl

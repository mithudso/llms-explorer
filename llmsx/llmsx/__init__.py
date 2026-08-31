"""llmsx — a read-only CLI and TUI over the llms-explorer concept tree.

The tree it reads is the build-time JSON the site generates
(`site/src/data/tree.json`, from `site/tools/gen_tree.py`), so this package
never touches the hub and works from a plain checkout. Step 3 swaps the same
shape in from an API without changing any caller.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("llmsx")
except PackageNotFoundError:      # a source tree that was never installed
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]

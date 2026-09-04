"""llmsx — a read-only CLI/TUI over the llms-explorer concept tree and the
llms-concept-abstractor concept packs, plus a thin invocation layer over the
skills SDK.

Three genuinely different surfaces share this distribution:

- `llmsx.tree` walks the generated SEO research tree (`site/src/data/
  tree.json`) — always read-only, no network, no third-party dependency.
- `llmsx.concepts` walks a directory of `<slug>.llms/` concept packs (default
  `~/.global-ai-hub/llms-concepts`) — read-only for `list`/`show`/`serve`;
  the concept-pack TUI's "edit" action opens `$EDITOR` on a pack file, which
  is a write.
- `llmsx.skills` loads a `SKILL.md` and runs it against a model — this one
  makes an outbound network call and needs the `skills` extra
  (`pip install 'llmsx[skills]'`).

So "read-only" and "never touches the hub" hold for `tree`/`concepts`'
default surface but not for the package as a whole; see each module's own
docstring for its exact boundary.
"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("llmsx")
except PackageNotFoundError:      # a source tree that was never installed
    __version__ = "0.0.0+dev"

from . import concepts, skills, tree  # after __version__, by design (E402 is repo-wide ignored)

__all__ = ["__version__", "concepts", "skills", "tree"]

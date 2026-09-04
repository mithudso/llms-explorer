"""tui — the Textual concept-tree browser.

A read-only `Tree` widget over `llmsx.tree`'s data: a filter `Input` that
shows only matching branches, a detail `RichLog` fed by node selection, and
frontier concepts rendered dim italic with a `(frontier)` label so the
researched/unresearched split is visible. There is no write path here — no
button mutates the tree — because this package has nowhere to write it to;
queuing a concept or launching research belongs to the hub itself, which
this standalone read-only package cannot reach.

This is a distinct screen from `llmsx.concepts_tui.ConceptPackBrowser`, which
browses a different data model entirely (a directory of concept packs, not
this SEO research tree) — see `llmsx.concepts`'s module docstring for why
the two are not interchangeable, and *that* module's TUI is the one that
actually ports the hub-manager's `TabPane("Concepts")`.

Textual is an optional extra; importing this module without it raises
`ImportError` with an install hint rather than terminating the process —
`SystemExit` at import time would kill whatever host process imported this
module (a docs build, a plugin scanner, an IDE indexer), which is not this
library's call to make. `__main__._cmd_tui` is the layer that turns that
`ImportError` into a CLI exit code.
"""
from __future__ import annotations

import logging

from . import tree as treemod

logger = logging.getLogger(__name__)

try:
    from rich.text import Text
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.widgets import Footer, Header, Input, RichLog, Static, Tree
except ImportError as exc:
    raise ImportError(
        "llmsx tui needs Textual — install it with:  pip install 'llmsx[tui]'"
    ) from exc

#: A resource bound on `ConceptBrowser._render()`'s widget-building recursion
#: — see that method's docstring. Much smaller than `tree.MAX_WALK_NODES`:
#: building a `Tree` widget node is far more expensive than yielding a tuple.
_MAX_TREE_WIDGET_NODES = 5_000


def _matching_slugs(data: dict, needle: str) -> set[str] | None:
    """Slugs that match ``needle`` plus every ancestor of a match, so a filter
    never hides the path to a hit — the hub-manager Concepts rule, widened to
    aliases. ``None`` means no filter is active.

    Computed once per render over a parent map rather than by re-walking each
    branch: the tree links by name and names can cycle.
    """
    if not needle:
        return None
    nodes = data.get("nodes") or {}
    parent_of: dict[str, str] = {}
    candidates: list[tuple[str, str, list[str]]] = []
    for slug, node in nodes.items():
        if not isinstance(node, dict):
            continue
        candidates.append((slug, node.get("concept", ""), node.get("aliases") or []))
        for child in node.get("children") or []:
            if not isinstance(child, dict) or not child.get("concept"):
                continue
            cslug = treemod.child_slug(child)
            parent_of.setdefault(cslug, slug)
            if child.get("state") == treemod.FRONTIER:
                candidates.append((cslug, child["concept"], []))
    for entry in data.get("frontier") or []:
        if isinstance(entry, dict) and entry.get("concept"):
            candidates.append((treemod.slugify(entry["concept"]), entry["concept"], []))

    keep: set[str] = set()
    for slug, concept, aliases in candidates:
        if needle not in concept.lower() and not any(needle in a.lower() for a in aliases):
            continue
        cur: str | None = slug
        while cur and cur not in keep:
            keep.add(cur)
            cur = parent_of.get(cur)
    return keep


class ConceptBrowser(App):
    """Read-only concept tree: filter on the left of the detail pane."""

    CSS = """
    #concept-tree { height: 1fr; border: round $primary; }
    #concept-detail { height: 12; border: round $secondary; }
    .row-inputs { height: auto; }
    .hint { color: $text-muted; padding: 0 1; }
    #concept-status { padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_tree", "Refresh"),
        Binding("slash", "focus_filter", "Filter", key_display="/"),
    ]

    def __init__(self, data_path=None):
        super().__init__()
        self._data_path = data_path
        self._data: dict = {}
        self._load_failed = False

    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header()
        yield Tree("concept tree", id="concept-tree")
        with Horizontal(classes="row-inputs"):
            yield Input(placeholder="filter concepts… (only matching branches "
                                    "are shown)", id="concept-filter")
        yield Static("", id="concept-status")
        yield Static("click a node for its skill, research and neighbours · "
                     "[dim]dim = frontier: known to the tree, never "
                     "researched[/dim] · read-only — this package has no write "
                     "path to the hub", classes="hint")
        yield RichLog(id="concept-detail", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx"
        self._load_data()
        self._render()

    # ------------------------------------------------------------------ #

    def action_focus_filter(self) -> None:
        self.query_one("#concept-filter", Input).focus()

    def action_refresh_tree(self) -> None:
        self._load_data()
        self._render()

    def _load_data(self) -> None:
        """Read the tree from disk. Separate from `_render()` deliberately:
        the generator rewrites the file and no event tells this app about
        it, so a reload belongs on mount and on explicit refresh (`r`) — not
        on every keystroke in the filter box, which used to re-read and
        re-parse the whole file just to re-render the already-loaded data."""
        try:
            self._data = treemod.load(self._data_path)
            self._load_failed = False
        except (FileNotFoundError, ValueError, OSError) as exc:
            self._load_failed = True
            self._data = {}
            logger.warning("could not load concept tree: %s", exc)
            self.query_one("#concept-detail", RichLog).write(
                Text(f"could not load the concept tree: {exc}"))

    def _render(self) -> None:
        """Rebuild the tree widget from `self._data` and the current filter —
        no disk I/O. Does not touch `#concept-detail`: it used to `clear()`
        that log on every call, which meant typing one character into the
        filter destroyed whatever node detail the user was reading.

        Ancestors are tracked per-branch (a fresh set per recursive path),
        the same rule `tree.walk()` uses and for the same reason: a concept
        reachable from two different parents is a DAG, not a cycle, and must
        render under both rather than silently vanishing from every parent
        but the first one reached. That correctness has a cost — a deep,
        widely-shared subtree re-expands once per path to it — so, exactly
        like `tree.walk()`, this stops (with a logged warning) past a node
        budget rather than growing without bound. The budget here is far
        smaller than `tree.MAX_WALK_NODES`: building a real Textual widget
        per node is much more expensive than yielding a tuple, and nobody
        can usefully browse a tree with hundreds of thousands of rows
        anyway.
        """
        data = self._data
        nodes = data.get("nodes") or {}
        widget = self.query_one("#concept-tree", Tree)
        widget.clear()
        needle = self.query_one("#concept-filter", Input).value.strip().lower()

        keep = _matching_slugs(data, needle)

        def wanted(slug: str) -> bool:
            return keep is None or slug in keep

        budget = [_MAX_TREE_WIDGET_NODES]

        def add(parent, slug: str, concept: str, state: str, ancestors: frozenset[str]) -> None:
            if slug in ancestors:      # true cycle — a slug reachable from itself
                return
            if budget[0] <= 0:
                return
            budget[0] -= 1
            if budget[0] == 0:
                logger.warning("tui render: stopped after %d nodes — tree.json may "
                               "have pathological multi-parent fan-in",
                               _MAX_TREE_WIDGET_NODES)
                return
            style = "dim italic" if state == treemod.FRONTIER else ""
            label = Text(concept, style=style)
            if state == treemod.FRONTIER:
                label.append("  (frontier)", style="dim")
            kids = [c for c in (nodes.get(slug) or {}).get("children") or []
                    if isinstance(c, dict) and c.get("concept")
                    and wanted(treemod.child_slug(c))]
            node = (parent.add(label, data=(slug, concept), expand=bool(needle))
                    if kids else parent.add_leaf(label, data=(slug, concept)))
            next_ancestors = ancestors | {slug}
            for child in kids:
                add(node, treemod.child_slug(child), child["concept"],
                    child.get("state", treemod.RESEARCHED), next_ancestors)

        for slug in data.get("roots") or []:
            if budget[0] <= 0:
                break
            node = nodes.get(slug)
            if node and wanted(slug):
                add(widget.root, slug, node.get("concept", slug),
                    node.get("state", treemod.RESEARCHED), frozenset())

        orphans = [f for f in data.get("frontier") or []
                   if isinstance(f, dict) and f.get("concept")
                   and f.get("parent_slug") not in nodes
                   and wanted(treemod.slugify(f["concept"]))]
        if orphans:
            # Frontier concepts with no researched parent would otherwise
            # render nowhere at all — invisible rather than absent.
            bucket = widget.root.add(Text("(unparented frontier)", style="dim"),
                                     data=None, expand=True)
            for entry in orphans:
                bucket.add_leaf(Text(entry["concept"], style="dim italic"),
                                data=(treemod.slugify(entry["concept"]), entry["concept"]))
        widget.root.expand()

        self.query_one("#concept-status", Static).update(
            f"[b]concept tree[/b] — {len(nodes)} researched · "
            f"{len(data.get('frontier') or [])} frontier · generated "
            f"{data.get('generated', '?')}")

    # ------------------------------------------------------------------ #

    @on(Input.Changed, "#concept-filter")
    def _filter_changed(self, event: Input.Changed) -> None:
        self._render()

    @on(Tree.NodeSelected, "#concept-tree")
    def _node_selected(self, event: Tree.NodeSelected) -> None:
        node_data = event.node.data
        if not node_data:
            return
        slug, concept = node_data
        log = self.query_one("#concept-detail", RichLog)
        log.clear()
        try:
            d = treemod.detail(self._data, slug)
        except KeyError:
            log.write(f"[b]{concept}[/b]  [dim](frontier)[/dim]")
            log.write("  [dim]named by the tree, never researched — no node of "
                      "its own[/dim]")
            return
        log.write(f"[b]{d['concept']}[/b]  [dim]({d.get('state', 'researched')})[/dim]")
        log.write(f"  skill      {d.get('skillId') or '-'}")
        log.write(f"  researched {d.get('researchedAt') or '-'}  "
                  f"sources {d.get('sourcesCount', '-')}  "
                  f"concepts {d.get('conceptsCount', '-')}")
        if d.get("aliases"):
            log.write(f"  aliases    {', '.join(d['aliases'])}")
        if d.get("skillSummary"):
            log.write("")
            log.write(Text(d["skillSummary"]))
        log.write("")
        log.write(f"  parent     {d.get('parent') or '-'}")
        log.write("  children   " +
                  (", ".join(c.get("concept", "?") for c in d.get("children") or []
                             if isinstance(c, dict)) or "-"))
        log.write(f"  siblings   {', '.join(d.get('siblings') or []) or '-'}")
        log.write(f"  frontier   {', '.join(d.get('frontierChildren') or []) or '-'}")


def run(data_path=None) -> int:
    app = ConceptBrowser(data_path)
    app.run()
    return 1 if app._load_failed else 0


__all__ = ["ConceptBrowser", "run"]

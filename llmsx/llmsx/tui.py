"""tui — the Textual concept browser.

Parity with the hub-manager Concepts tab (`~/.global-ai-hub/scripts/hub_manager/
app.py`): a `Tree` widget, a filter `Input` that shows only matching branches,
a detail `RichLog` fed by node selection, and frontier concepts rendered dim
italic with a `(frontier)` label so the researched/unresearched split is
visible. The write actions of that tab — queue a concept, launch research —
are deliberately absent: they mutate the hub, which this read-only package
cannot reach. They arrive in step 3, over the API.

Textual is an optional extra; importing this module without it fails with an
install hint rather than a traceback.
"""
from __future__ import annotations

from . import tree as treemod

try:
    from rich.text import Text
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal
    from textual.widgets import Footer, Header, Input, RichLog, Static, Tree
except ModuleNotFoundError as exc:  # pragma: no cover - depends on the install
    raise SystemExit(
        "llmsx tui needs Textual — install it with:  pip install 'llmsx[tui]'"
    ) from exc


def _matching_slugs(data: dict, needle: str) -> set[str] | None:
    """Slugs that match ``needle`` plus every ancestor of a match, so a filter
    never hides the path to a hit — the hub-manager Concepts rule, widened to
    aliases. ``None`` means no filter is active.

    Computed once per refresh over a parent map rather than by re-walking each
    branch: the tree links by name and names can cycle.
    """
    if not needle:
        return None
    nodes = data.get("nodes") or {}
    parent_of: dict[str, str] = {}
    candidates: list[tuple[str, str, list[str]]] = []
    for slug, node in nodes.items():
        candidates.append((slug, node.get("concept", ""), node.get("aliases") or []))
        for child in node.get("children") or []:
            child_slug = child.get("slug") or treemod.slugify(child["concept"])
            parent_of.setdefault(child_slug, slug)
            if child.get("state") == treemod.FRONTIER:
                candidates.append((child_slug, child["concept"], []))
    for entry in data.get("frontier") or []:
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

    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header()
        yield Tree("concept tree", id="concept-tree")
        with Horizontal(classes="row-inputs"):
            yield Input(placeholder="filter concepts… (only matching branches "
                                    "are shown)", id="concept-filter")
        yield Static("click a node for its skill, research and neighbours · "
                     "[dim]dim = frontier: known to the tree, never "
                     "researched[/dim] · read-only: queue and launch land in "
                     "step 3", classes="hint")
        yield RichLog(id="concept-detail", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx"
        self.refresh_tree()

    # ------------------------------------------------------------------ #

    def action_focus_filter(self) -> None:
        self.query_one("#concept-filter", Input).focus()

    def action_refresh_tree(self) -> None:
        self.refresh_tree()

    def refresh_tree(self) -> None:
        """Reload from disk every time: the generator rewrites the file and no
        event would tell this app about it."""
        log = self.query_one("#concept-detail", RichLog)
        try:
            self._data = treemod.load(self._data_path)
        except (FileNotFoundError, ValueError) as exc:
            log.write(Text(f"could not load the concept tree: {exc}"))
            return
        data = self._data
        nodes = data.get("nodes") or {}
        widget = self.query_one("#concept-tree", Tree)
        widget.clear()
        needle = self.query_one("#concept-filter", Input).value.strip().lower()

        keep = _matching_slugs(data, needle)

        def wanted(slug: str) -> bool:
            return keep is None or slug in keep

        def add(parent, slug: str, concept: str, state: str, seen: set) -> None:
            if slug in seen:          # name links can cycle
                return
            seen.add(slug)
            style = "dim italic" if state == treemod.FRONTIER else ""
            label = Text(concept, style=style)
            if state == treemod.FRONTIER:
                label.append("  (frontier)", style="dim")
            kids = [c for c in (nodes.get(slug) or {}).get("children") or []
                    if wanted(c.get("slug") or treemod.slugify(c["concept"]))]
            node = (parent.add(label, data=slug, expand=bool(needle))
                    if kids else parent.add_leaf(label, data=slug))
            for child in kids:
                add(node, child.get("slug") or treemod.slugify(child["concept"]),
                    child["concept"], child.get("state", treemod.RESEARCHED), seen)

        seen: set = set()
        for slug in data.get("roots") or []:
            node = nodes.get(slug)
            if node and wanted(slug):
                add(widget.root, slug, node["concept"],
                    node.get("state", treemod.RESEARCHED), seen)

        orphans = [f for f in data.get("frontier") or []
                   if f.get("parent_slug") not in nodes
                   and wanted(treemod.slugify(f["concept"]))]
        if orphans:
            # Frontier concepts with no researched parent would otherwise
            # render nowhere at all — invisible rather than absent.
            bucket = widget.root.add(Text("(unparented frontier)", style="dim"),
                                     data=None, expand=True)
            for entry in orphans:
                bucket.add_leaf(Text(entry["concept"], style="dim italic"),
                                data=treemod.slugify(entry["concept"]))
        widget.root.expand()

        log.clear()
        log.write(f"[b]concept tree[/b] — {len(nodes)} researched · "
                  f"{len(data.get('frontier') or [])} frontier · generated "
                  f"{data.get('generated', '?')}")

    # ------------------------------------------------------------------ #

    @on(Input.Changed, "#concept-filter")
    def _filter_changed(self, event: Input.Changed) -> None:
        self.refresh_tree()

    @on(Tree.NodeSelected, "#concept-tree")
    def _node_selected(self, event: Tree.NodeSelected) -> None:
        slug = event.node.data
        if not slug:
            return
        log = self.query_one("#concept-detail", RichLog)
        log.clear()
        try:
            d = treemod.detail(self._data, slug)
        except KeyError:
            concept = str(event.node.label).split("  (")[0]
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
                  (", ".join(c["concept"] for c in d.get("children") or []) or "-"))
        log.write(f"  siblings   {', '.join(d.get('siblings') or []) or '-'}")
        log.write(f"  frontier   {', '.join(d.get('frontierChildren') or []) or '-'}")


def run(data_path=None) -> int:
    ConceptBrowser(data_path).run()
    return 0

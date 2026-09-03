"""concepts_tui — the Textual concept-pack browser.

Ports the hub-manager Concepts tab (`~/.global-ai-hub/scripts/hub_manager/
app.py`, `TabPane("Concepts"`) to `llmsx.concepts`: a `DataTable` listing
packs, a filter `Input` that live-filters by slug/name/summary, and a
detail `Tree` that expands the selected pack into its summary plus two
branches — "Related concepts" and "Files" — the same fields
`_build_concept_report` shows there, but each concept and file is now its
own clickable node instead of flat text. Selecting a related-concept leaf
that matches another pack's slug/name jumps the tree to that pack (a cheap
form of pack-to-pack navigation, since `concept-graph.json` nodes are plain
term strings, not pack pointers — see `concepts.related_terms()`).
Selecting a file leaf opens a read-only preview in a modal.

Editing (open the pack's `llms.txt` in `$EDITOR`) is included: it only
touches a local file, no different from any other editor invocation.
Indexing is not: the hub's version shells out to `docset_indexer.py`, which
depends on ChromaDB and an Ollama embedding pool — hub-specific heavy
dependencies this package deliberately does not carry (see the package's
"zero required dependencies" rule in `pyproject.toml`). The Index button
here says so plainly instead of failing silently or vendoring those deps.

This is a distinct screen from `llmsx.tui.ConceptBrowser`, which browses a
different data model entirely (the SEO research tree, `tree.json`) — see
`llmsx.concepts`'s module docstring for why the two are not interchangeable.

Textual is an optional extra, like `llmsx.tui`; importing this module
without it raises `ImportError` with the same install hint (see that
module's docstring for why `ImportError`, not `SystemExit`).
"""
from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path

from . import concepts as conceptsmod

logger = logging.getLogger(__name__)

try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, VerticalScroll
    from textual.screen import ModalScreen
    from textual.widgets import Button, DataTable, Footer, Header, Input, Static, Tree
except ImportError as exc:
    raise ImportError(
        "llmsx concepts tui needs Textual — install it with:  pip install 'llmsx[tui]'"
    ) from exc

# Preview bodies are capped so a stray multi-megabyte llms-full.txt can't
# stall the modal or blow past Textual's render budget.
_PREVIEW_MAX_CHARS = 20_000


class FilePreviewScreen(ModalScreen[None]):
    """Read-only preview of one concept-pack file, opened from the tree."""

    DEFAULT_CSS = """
    FilePreviewScreen { align: center middle; }
    #preview-box { width: 90%; height: 80%; border: round $primary; background: $panel; }
    #preview-title { padding: 0 1; }
    #preview-body { padding: 0 2 1 2; }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "close", "Close"),
        Binding("q", "close", "Close"),
    ]

    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self._preview_title = title
        self._text = text

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-box"):
            yield Static(f"[b]{self._preview_title}[/b]  [dim](esc to close)[/dim]",
                         id="preview-title", markup=True)
            yield Static(self._text, id="preview-body")

    def action_close(self) -> None:
        self.dismiss(None)


class ConceptPackBrowser(App):
    """List/filter/detail/edit over the concept packs under one directory."""

    CSS = """
    #packs-table { height: 1fr; border: round $primary; }
    #packs-tree { height: 16; border: round $secondary; }
    #packs-status { height: auto; }
    .row-inputs { height: auto; }
    .hint { color: $text-muted; padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_packs", "Refresh"),
        Binding("slash", "focus_filter", "Filter", key_display="/"),
        Binding("e", "edit_pack", "Edit"),
    ]

    def __init__(self, data_path=None):
        super().__init__()
        self._data_path = data_path
        self._cache: list[dict] = []
        self._load_failed = False
        self._current_entry: dict | None = None

    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="packs-table", cursor_type="row", zebra_stripes=True)
        with Horizontal(classes="row-inputs"):
            yield Input(placeholder="filter by slug/name/summary…", id="packs-filter")
        with Horizontal(classes="row-inputs"):
            yield Button("Edit llms.txt ($EDITOR)", id="packs-edit")
            yield Button("Index (needs the hub)", id="packs-index")
        yield Static("select a row to expand its concept tree · click a related concept to "
                     "jump to its pack · click a file to preview it · [b]e[/b] edit llms.txt",
                     classes="hint")
        yield Tree("(select a pack)", id="packs-tree")
        yield Static("", id="packs-status", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx concepts"
        table = self.query_one("#packs-table", DataTable)
        table.add_columns("slug", "concept", "kind", "useful for", "files")
        self.refresh_packs()

    # ------------------------------------------------------------------ #

    def action_focus_filter(self) -> None:
        self.query_one("#packs-filter", Input).focus()

    def action_refresh_packs(self) -> None:
        self.refresh_packs()

    def action_edit_pack(self) -> None:
        self._edit_selected()

    def refresh_packs(self) -> None:
        """Reload the catalog from disk, then re-render through the filter."""
        status = self.query_one("#packs-status", Static)
        try:
            self._cache = conceptsmod.library("", self._data_path)
            self._load_failed = False
            status.update("")
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            status.update(f"could not load concept packs: {exc}")
            logger.warning("could not load concept packs: %s", exc)
            self._cache = []
            self._load_failed = True
        self._render_cached()

    def _render_cached(self) -> None:
        """Re-filter the last-loaded catalog without re-reading disk, so
        typing in the filter box stays instant."""
        table = self.query_one("#packs-table", DataTable)
        table.clear()
        needle = self.query_one("#packs-filter", Input).value.strip().lower()
        for e in self._cache:
            if needle and needle not in e["slug"].lower() \
                    and needle not in e["concept"].lower() \
                    and needle not in e["summary"].lower():
                continue
            table.add_row(e["slug"], e["concept"], e["kind"],
                          e["useful_for"][:40], str(len(e["files"])), key=e["slug"])

    # ------------------------------------------------------------------ #

    @on(Input.Changed, "#packs-filter")
    def _filter_changed(self, event: Input.Changed) -> None:
        self._render_cached()

    def _selected_key(self) -> str | None:
        """Row key of the cursor row in the packs table."""
        table = self.query_one("#packs-table", DataTable)
        if not table.row_count:
            return None
        try:
            return str(table.coordinate_to_cell_key((table.cursor_row, 0)).row_key.value)
        except (KeyError, IndexError) as exc:
            logger.debug("row-key lookup failed: %s", exc)
            return None

    def _entry(self, slug: str | None) -> dict | None:
        """The cached catalog entry for `slug`, or `None` — the one place
        that scans `self._cache` by slug, used by both selection and edit."""
        if not slug:
            return None
        return next((e for e in self._cache if e["slug"] == slug), None)

    def _selected_entry(self) -> dict | None:
        return self._entry(self._selected_key())

    @on(DataTable.RowSelected, "#packs-table")
    def _row_selected(self, event: DataTable.RowSelected) -> None:
        entry = self._entry(str(event.row_key.value) if event.row_key else None)
        if entry is None:
            return
        self._populate_tree(entry)

    def _populate_tree(self, entry: dict) -> None:
        """Expand `entry` into the detail tree: a root node carrying the
        summary/useful-for lines, plus two branches of clickable leaves —
        one per related concept, one per file."""
        self._current_entry = entry
        tree = self.query_one("#packs-tree", Tree)
        tree.clear()
        root = tree.root
        root.label = f"{entry['concept']}  ({entry['kind']})  [{entry['slug']}]"
        root.add_leaf(f"summary: {entry['summary'] or '(no summary)'}")
        root.add_leaf(f"useful for: {entry['useful_for']}")

        related = entry["related_terms"]
        concepts_branch = root.add(f"Related concepts ({len(related)})")
        for term in related:
            concepts_branch.add_leaf(term, data={"kind": "concept", "term": term})

        files = entry["files"]
        files_branch = root.add(f"Files ({len(files)})")
        for fname, tokens in sorted(files.items()):
            label = f"{fname}  ({tokens if tokens is not None else '?'} tokens)"
            files_branch.add_leaf(label, data={"kind": "file", "name": fname})

        root.expand()
        concepts_branch.expand()
        files_branch.expand()

    @on(Tree.NodeSelected, "#packs-tree")
    def _tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data
        if not data:
            return
        status = self.query_one("#packs-status", Static)
        if data["kind"] == "concept":
            self._jump_to_concept(data["term"], status)
        elif data["kind"] == "file":
            self._preview_file(data["name"], status)

    def _jump_to_concept(self, term: str, status: Static) -> None:
        """A related-concept leaf is just a term string (see module
        docstring) — try to resolve it to another pack by slug or display
        name and, if found, re-expand the tree onto it."""
        needle = term.strip().lower()
        match = next(
            (e for e in self._cache
             if e["slug"].lower() == needle or e["concept"].lower() == needle),
            None,
        )
        if match is None:
            status.update(f"no concept pack matches related term {term!r}")
            return
        self._populate_tree(match)
        status.update(f"jumped to pack: {match['slug']}")

    def _preview_file(self, filename: str, status: Static) -> None:
        entry = self._current_entry
        if entry is None:
            status.update("select a concept pack row first")
            return
        pack_dir = Path(entry["dir"]).resolve()
        target = pack_dir / filename
        try:
            resolved = target.resolve()
        except OSError as exc:
            status.update(f"could not resolve {target}: {exc}")
            return
        if not resolved.is_relative_to(pack_dir):
            # Same containment rule as concepts.serve()/_edit_selected(): a
            # file inside an otherwise-legitimate pack directory can still
            # be a symlink pointing outside it.
            status.update(f"refusing to preview {target}: it resolves outside the pack directory")
            return
        if not resolved.is_file():
            status.update(f"file not found: {target}")
            return
        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            status.update(f"could not read {target}: {exc}")
            return
        if len(text) > _PREVIEW_MAX_CHARS:
            text = (text[:_PREVIEW_MAX_CHARS]
                    + f"\n\n… truncated ({len(text)} chars total, showing first "
                      f"{_PREVIEW_MAX_CHARS})")
        self.push_screen(FilePreviewScreen(f"{entry['slug']} / {filename}", text))
        status.update(f"previewing {filename}")

    @on(Button.Pressed, "#packs-edit")
    def _edit_button(self, event: Button.Pressed) -> None:
        self._edit_selected()

    def _edit_selected(self) -> None:
        """Open the pack's llms.txt in $EDITOR, suspending the TUI the way
        Textual apps must — via app.suspend() — so the terminal is not left
        corrupted."""
        status = self.query_one("#packs-status", Static)
        entry = self._selected_entry()
        if entry is None:
            status.update("select a concept pack row first")
            return
        pack_dir = Path(entry["dir"])
        target = pack_dir / "llms.txt"
        if not target.is_file():
            status.update(f"no llms.txt in pack: {target}")
            return
        if not target.resolve().is_relative_to(pack_dir.resolve()):
            # Same containment rule as concepts.serve(): a file inside an
            # otherwise-legitimate pack directory can still be a symlink
            # pointing outside it.
            status.update(f"refusing to open {target}: it resolves outside the pack directory")
            return
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        try:
            argv = [*shlex.split(editor), str(target)]
        except ValueError as exc:      # unbalanced quotes etc. in $EDITOR
            status.update(f"could not parse $EDITOR/$VISUAL ({editor!r}): {exc}")
            return
        status.update(f">>> suspending TUI: {' '.join(argv)}")
        try:
            with self.suspend():
                rc = subprocess.call(argv)
        except OSError as exc:
            status.update(f"editor failed: {exc}")
            logger.warning("editor %r failed for %s", editor, target, exc_info=True)
            return
        if rc:
            status.update(f"editor exited with status {rc}: {target}")
        else:
            status.update(f"back from editor: {target}")
        self.refresh_packs()

    @on(Button.Pressed, "#packs-index")
    def _index_button(self, event: Button.Pressed) -> None:
        status = self.query_one("#packs-status", Static)
        status.update(
            "indexing is not available in the standalone llmsx package — it "
            "depends on docset_indexer.py, ChromaDB and an Ollama embedding "
            "pool, which are hub-specific heavy dependencies llmsx deliberately "
            "does not carry. Install the hub (~/.global-ai-hub) and use its "
            "Concepts tab or hub_index_docset to index a pack's units.jsonl.")


def run(data_path=None) -> int:
    app = ConceptPackBrowser(data_path)
    app.run()
    return 1 if app._load_failed else 0


__all__ = ["ConceptPackBrowser", "FilePreviewScreen", "run"]

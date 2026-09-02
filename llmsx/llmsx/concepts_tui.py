"""concepts_tui — the Textual concept-pack browser.

Ports the hub-manager Concepts tab (`~/.global-ai-hub/scripts/hub_manager/
app.py`, `TabPane("Concepts"`) to `llmsx.concepts`: a `DataTable` listing
packs, a filter `Input` that live-filters by slug/name/summary, and a
detail `RichLog` printing the selected pack's summary, facets, related
terms and files — the same fields `_build_concept_report` shows there.

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
    from textual.containers import Horizontal
    from textual.widgets import Button, DataTable, Footer, Header, Input, RichLog, Static
except ImportError as exc:
    raise ImportError(
        "llmsx concepts tui needs Textual — install it with:  pip install 'llmsx[tui]'"
    ) from exc


class ConceptPackBrowser(App):
    """List/filter/detail/edit over the concept packs under one directory."""

    CSS = """
    #packs-table { height: 1fr; border: round $primary; }
    #packs-detail { height: 16; border: round $secondary; }
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

    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="packs-table", cursor_type="row", zebra_stripes=True)
        with Horizontal(classes="row-inputs"):
            yield Input(placeholder="filter by slug/name/summary…", id="packs-filter")
        with Horizontal(classes="row-inputs"):
            yield Button("Edit llms.txt ($EDITOR)", id="packs-edit")
            yield Button("Index (needs the hub)", id="packs-index")
        yield Static("select a row for detail · [b]e[/b] edit llms.txt · "
                     "indexing needs the hub — see the button", classes="hint")
        yield RichLog(id="packs-detail", wrap=True, markup=True)
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
        log = self.query_one("#packs-detail", RichLog)
        try:
            self._cache = conceptsmod.library("", self._data_path)
            self._load_failed = False
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            log.clear()
            log.write(f"could not load concept packs: {exc}")
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
        log = self.query_one("#packs-detail", RichLog)
        log.clear()
        log.write(f"[b]{entry['concept']}[/b]  ({entry['kind']})  [dim]{entry['slug']}[/dim]")
        log.write("")
        log.write(entry["summary"] or "(no summary)")
        log.write("")
        log.write(f"useful for: {entry['useful_for']}")
        if entry["related_terms"]:
            log.write(f"related:    {', '.join(entry['related_terms'])}")
        if entry["files"]:
            log.write("files:")
            for fname, tokens in sorted(entry["files"].items()):
                log.write(f"  {fname}  ({tokens if tokens is not None else '?'} tokens)")

    @on(Button.Pressed, "#packs-edit")
    def _edit_button(self, event: Button.Pressed) -> None:
        self._edit_selected()

    def _edit_selected(self) -> None:
        """Open the pack's llms.txt in $EDITOR, suspending the TUI the way
        Textual apps must — via app.suspend() — so the terminal is not left
        corrupted."""
        log = self.query_one("#packs-detail", RichLog)
        entry = self._selected_entry()
        if entry is None:
            log.write("select a concept pack row first")
            return
        pack_dir = Path(entry["dir"])
        target = pack_dir / "llms.txt"
        if not target.is_file():
            log.write(f"no llms.txt in pack: {target}")
            return
        if not target.resolve().is_relative_to(pack_dir.resolve()):
            # Same containment rule as concepts.serve(): a file inside an
            # otherwise-legitimate pack directory can still be a symlink
            # pointing outside it.
            log.write(f"refusing to open {target}: it resolves outside the pack directory")
            return
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        try:
            argv = [*shlex.split(editor), str(target)]
        except ValueError as exc:      # unbalanced quotes etc. in $EDITOR
            log.write(f"could not parse $EDITOR/$VISUAL ({editor!r}): {exc}")
            return
        log.write(f">>> suspending TUI: {' '.join(argv)}")
        try:
            with self.suspend():
                rc = subprocess.call(argv)
        except OSError as exc:
            log.write(f"editor failed: {exc}")
            logger.warning("editor %r failed for %s", editor, target, exc_info=True)
            return
        if rc:
            log.write(f"editor exited with status {rc}: {target}")
        else:
            log.write(f"back from editor: {target}")
        self.refresh_packs()

    @on(Button.Pressed, "#packs-index")
    def _index_button(self, event: Button.Pressed) -> None:
        log = self.query_one("#packs-detail", RichLog)
        log.write(
            "indexing is not available in the standalone llmsx package — it "
            "depends on docset_indexer.py, ChromaDB and an Ollama embedding "
            "pool, which are hub-specific heavy dependencies llmsx deliberately "
            "does not carry. Install the hub (~/.global-ai-hub) and use its "
            "Concepts tab or hub_index_docset to index a pack's units.jsonl.")


def run(data_path=None) -> int:
    app = ConceptPackBrowser(data_path)
    app.run()
    return 1 if app._load_failed else 0


__all__ = ["ConceptPackBrowser", "run"]

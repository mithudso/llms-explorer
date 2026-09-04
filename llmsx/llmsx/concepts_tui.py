"""concepts_tui — the Textual concept-pack browser.

Ports the hub-manager Concepts tab (`~/.global-ai-hub/scripts/hub_manager/
app.py`, `TabPane("Concepts"`) to `llmsx.concepts`: a `DataTable` listing
packs, a filter `Input` that live-filters by slug/name/summary, and a
detail `Tree` that expands the selected pack into its summary plus two
branches — "Related concepts" and "Files".

The tree is genuinely hierarchical, not a flat dump: a related-concept leaf
that resolves to another pack (by slug/name match against the loaded
catalog — `concept-graph.json` nodes are plain term strings, not pack
pointers, see `concepts.related_terms()`) becomes its own expandable branch,
lazily populated with *that* pack's own summary/related-concepts/files on
first expand (`Tree.NodeExpanded`), so drilling down never loses the parent
you came from. Every branch starts collapsed. Textual's stock `Tree` binds
no left/right arrow at all (only up/down/enter/space) — this app adds its
own `right`/`left` bindings (`action_expand_node`/`action_collapse_node`) to
expand/roll-up the node under the cursor, scoped to when the tree itself has
focus so they don't fight `Input`'s own left/right (text-cursor movement). A
cycle guard (the chain of pack slugs from the root to the current node)
stops a pack that relates back to an ancestor from recursing forever.
Selecting (Enter/click) a file leaf opens a read-only preview modal showing
the owning pack's metadata above the raw file content, with an in-modal
handoff to $EDITOR ('e'); selecting a pack-ref node (a concept, or the root)
previews that pack's own primary file the same way, on top of the
expand/collapse toggle `Tree`'s `auto_expand` already does for Enter — so
picking an item shows its file and metadata together, not just a sub-tree.

Six buttons run the matching Claude Code skill/agent against whichever tree
node is currently highlighted (or the selected pack row, falling back), by
shelling out to `claude -p "<prompt>"` the same way `_edit_file` shells out
to $EDITOR — suspending the TUI so the terminal is handed over cleanly, and
refreshing the catalog afterward since a `/dr` or concept-family-explorer
run can create a brand new pack on disk. This is deliberately live, not a
queue: llmsx has no Claude session of its own, and `claude -p` is the only
way to actually run a skill from here. "Verify/Index All Docs" is the odd
one out — it isn't node-scoped, it delegates hub-wide to the
`llms-librarian` agent's index-coverage step (see `.claude/agents/llms-librarian.md`
at the repo root — every docset should have both a semantic and a keyword layer).

Editing (open a pack file in `$EDITOR`) is included: it only touches a
local file, no different from any other editor invocation. Indexing is not:
the hub's version shells out to `docset_indexer.py`, which depends on
ChromaDB and an Ollama embedding pool — hub-specific heavy dependencies
this package deliberately does not carry (see the package's "zero required
dependencies" rule in `pyproject.toml`). The Index button here says so
plainly instead of failing silently or vendoring those deps.

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
    """Read-only preview of one concept-pack file, opened from the tree —
    the owning pack's metadata (frontmatter) above a rule, the raw file
    content (the actual research) below it."""

    DEFAULT_CSS = """
    FilePreviewScreen { align: center middle; }
    #preview-box { width: 92%; height: 85%; border: round $primary; background: $panel; }
    #preview-meta { padding: 0 1; }
    #preview-rule { color: $text-muted; padding: 0 1; }
    #preview-body { padding: 0 2 1 2; }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("enter", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("e", "edit", "Edit file"),
    ]

    def __init__(self, meta: str, body: str) -> None:
        super().__init__()
        self._meta = meta
        self._body = body

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-box"):
            yield Static(self._meta, id="preview-meta", markup=True)
            yield Static("─" * 70, id="preview-rule")
            yield Static(self._body, id="preview-body")

    def action_close(self) -> None:
        self.dismiss(None)

    def action_edit(self) -> None:
        self.dismiss(None)
        self.app._edit_current_file()


class ConceptPackBrowser(App):
    """List/filter/detail/edit over the concept packs under one directory."""

    CSS = """
    #packs-table { height: 1fr; border: round $primary; }
    #packs-tree { height: 16; border: round $secondary; }
    #packs-status { height: auto; }
    .row-inputs { height: auto; }
    .row-actions { height: auto; overflow-x: auto; }
    .hint { color: $text-muted; padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_packs", "Refresh"),
        Binding("slash", "focus_filter", "Filter", key_display="/"),
        Binding("e", "edit_pack", "Edit"),
        Binding("right", "expand_node", "Expand", show=False),
        Binding("left", "collapse_node", "Collapse", show=False),
    ]

    def __init__(self, data_path=None):
        super().__init__()
        self._data_path = data_path
        self._cache: list[dict] = []
        self._load_failed = False
        self._current_entry: dict | None = None
        self._current_file: tuple[dict, str] | None = None
        self._current_node_data: dict | None = None

    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="packs-table", cursor_type="row", zebra_stripes=True)
        with Horizontal(classes="row-inputs"):
            yield Input(placeholder="filter by slug/name/summary…", id="packs-filter")
        with Horizontal(classes="row-inputs"):
            yield Button("Edit llms.txt ($EDITOR)", id="packs-edit")
            yield Button("Edit tree file", id="packs-edit-file")
            yield Button("Index (needs the hub)", id="packs-index")
        with Horizontal(classes="row-actions"):
            yield Button("Deep Research (/dr)", id="packs-dr")
            yield Button("Concept Family Explorer", id="packs-cfe")
            yield Button("Rabbithole", id="packs-rabbithole")
            yield Button("Rebalance Skill Tree", id="packs-skilltree")
            yield Button("Deep Optimize", id="packs-optimize")
            yield Button("Verify/Index All Docs", id="packs-index-all")
        yield Static("[b]→[/b] expand · [b]←[/b] roll up · enter a concept to drill in + "
                     "preview its file · enter a file to preview it · [b]e[/b] edit llms.txt",
                     classes="hint", markup=True)
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

    def action_expand_node(self) -> None:
        """Right arrow: expand the node under the tree cursor. Textual's
        `Tree` has no left/right bindings of its own (only up/down/enter/
        space) — Input already claims left/right for text-cursor movement,
        so this only ever fires while the tree itself has focus."""
        tree = self.query_one("#packs-tree", Tree)
        if self.focused is not tree:
            return
        node = tree.cursor_node
        if node is not None and node.allow_expand and not node.is_expanded:
            node.expand()

    def action_collapse_node(self) -> None:
        """Left arrow: collapse (roll up) the node under the tree cursor."""
        tree = self.query_one("#packs-tree", Tree)
        if self.focused is not tree:
            return
        node = tree.cursor_node
        if node is not None and node.is_expanded:
            node.collapse()

    def refresh_packs(self) -> None:
        """Reload the catalog from disk, then re-render through the filter.
        Only touches the status line to clear a stale load-failure banner —
        callers that just set their own status (edit/skill-run results)
        call this afterward and must not have that message clobbered."""
        status = self.query_one("#packs-status", Static)
        was_failed = self._load_failed
        try:
            self._cache = conceptsmod.library("", self._data_path)
            self._load_failed = False
            if was_failed:
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

    # -- tree building -------------------------------------------------- #

    def _populate_tree(self, entry: dict) -> None:
        """Reset the tree onto `entry` as its root pack, then expand it."""
        self._current_entry = entry
        self._current_file = None
        self._current_node_data = None
        tree = self.query_one("#packs-tree", Tree)
        tree.clear()
        root = tree.root
        ancestors = [entry["slug"]]
        root.data = {"kind": "pack-ref", "entry": entry, "ancestors": ancestors,
                     "_populated": True}
        self._expand_pack_into(root, entry, ancestors)
        root.label = f"{entry['concept']}  ({entry['kind']})  [{entry['slug']}]"
        root.expand()

    def _expand_pack_into(self, node, entry: dict, ancestors: list[str]) -> None:
        """Fill `node`'s children with `entry`'s frontmatter (summary,
        useful-for) plus its "Related concepts" and "Files" branches — the
        shape every pack-ref node gets, root or nested. `ancestors` is the
        chain of pack slugs from the tree root down to `node`, threaded
        through so a cycle (pack A relates to pack B relates back to A)
        renders as a plain leaf instead of recursing forever."""
        node.remove_children()
        node.add_leaf(f"summary: {entry['summary'] or '(no summary)'}")
        node.add_leaf(f"useful for: {entry['useful_for']}")

        related = entry["related_terms"]
        concepts_branch = node.add(f"Related concepts ({len(related)})")
        for term in related:
            self._add_concept_node(concepts_branch, term, ancestors)

        files = entry["files"]
        files_branch = node.add(f"Files ({len(files)})")
        for fname, tokens in sorted(files.items()):
            label = f"{fname}  ({tokens if tokens is not None else '?'} tokens)"
            files_branch.add_leaf(label, data={"kind": "file", "name": fname, "entry": entry})

    def _add_concept_node(self, parent_branch, term: str, ancestors: list[str]) -> None:
        needle = term.strip().lower()
        match = next(
            (e for e in self._cache
             if e["slug"].lower() == needle or e["concept"].lower() == needle),
            None,
        )
        if match is None:
            parent_branch.add_leaf(term, data={"kind": "concept-term", "term": term})
            return
        if match["slug"] in ancestors:
            parent_branch.add_leaf(f"{term}  (cycle — see above)",
                                    data={"kind": "concept-term", "term": term})
            return
        parent_branch.add(term, data={"kind": "pack-ref", "entry": match,
                                       "ancestors": [*ancestors, match["slug"]]})

    @on(Tree.NodeExpanded, "#packs-tree")
    def _tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Lazily populate a pack-ref branch's own frontmatter/concepts/
        files the first time it's expanded — right arrow, click, or enter —
        so drilling in never needs re-navigating from the table."""
        node = event.node
        data = node.data
        if not data or data.get("kind") != "pack-ref" or data.get("_populated"):
            return
        data["_populated"] = True
        self._expand_pack_into(node, data["entry"], data["ancestors"])

    @on(Tree.NodeHighlighted, "#packs-tree")
    def _tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Track whatever the tree cursor sits on, arrow keys included —
        the skill-runner buttons act on this, not just an Enter-pressed
        selection, so you can arrow to a node and just click a button."""
        self._current_node_data = event.node.data

    @on(Tree.NodeSelected, "#packs-tree")
    def _tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Enter/click on a file leaf previews that file; on a pack-ref node
        it previews the pack's own primary file too (on top of the
        expand/collapse toggle Tree's own `auto_expand` already does for
        us) — so selecting a concept shows its file and metadata together,
        not just a sub-tree you'd have to drill further into."""
        data = event.node.data
        if not data:
            return
        status = self.query_one("#packs-status", Static)
        if data["kind"] == "file":
            self._preview_file(data["entry"], data["name"], status)
        elif data["kind"] == "pack-ref":
            self._preview_pack_primary_file(data["entry"], status)

    def _preview_pack_primary_file(self, entry: dict, status: Static) -> None:
        """`llms.txt` if the pack has one, else whichever file sorts first —
        the same "primary file" `_edit_selected` assumes for its Edit
        button."""
        files = entry["files"]
        if not files:
            status.update(f"{entry['slug']}: no files to preview")
            return
        filename = "llms.txt" if "llms.txt" in files else sorted(files)[0]
        self._preview_file(entry, filename, status)

    # -- file preview ----------------------------------------------------- #

    def _preview_file(self, entry: dict, filename: str, status: Static) -> None:
        pack_dir = Path(entry["dir"]).resolve()
        target = pack_dir / filename
        try:
            resolved = target.resolve()
        except OSError as exc:
            status.update(f"could not resolve {target}: {exc}")
            return
        if not resolved.is_relative_to(pack_dir):
            # Same containment rule as concepts.serve()/_edit_file(): a
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
        meta_lines = [
            f"[b]{entry['concept']}[/b]  ({entry['kind']})  [dim]{entry['slug']}[/dim]",
            f"summary: {entry['summary'] or '(no summary)'}",
            f"useful for: {entry['useful_for']}",
        ]
        if entry["related_terms"]:
            meta_lines.append(f"related: {', '.join(entry['related_terms'])}")
        meta_lines.append(f"\nfile: {filename}  [dim](e to edit · esc to close)[/dim]")
        self._current_file = (entry, filename)
        self.push_screen(FilePreviewScreen("\n".join(meta_lines), text))
        status.update(f"previewing {filename}")

    # -- editing ------------------------------------------------------ #

    def _edit_file(self, pack_dir: Path, target: Path, status: Static) -> None:
        """Open `target` (known to live under `pack_dir`) in $EDITOR,
        suspending the TUI the way Textual apps must — via app.suspend() —
        so the terminal is not left corrupted. Shared by the row-level
        Edit button (llms.txt) and the tree-level Edit-file action."""
        if not target.is_file():
            status.update(f"file not found: {target}")
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

    @on(Button.Pressed, "#packs-edit")
    def _edit_button(self, event: Button.Pressed) -> None:
        self._edit_selected()

    def _edit_selected(self) -> None:
        status = self.query_one("#packs-status", Static)
        entry = self._selected_entry()
        if entry is None:
            status.update("select a concept pack row first")
            return
        pack_dir = Path(entry["dir"])
        self._edit_file(pack_dir, pack_dir / "llms.txt", status)

    @on(Button.Pressed, "#packs-edit-file")
    def _edit_file_button(self, event: Button.Pressed) -> None:
        self._edit_current_file()

    def _edit_current_file(self) -> None:
        """Edit whichever file was last opened in the preview modal —
        which may belong to a nested pack, not the top-level table row."""
        status = self.query_one("#packs-status", Static)
        if self._current_file is None:
            status.update("select a file in the tree first (press enter on a file leaf)")
            return
        entry, filename = self._current_file
        pack_dir = Path(entry["dir"])
        self._edit_file(pack_dir, pack_dir / filename, status)

    @on(Button.Pressed, "#packs-index")
    def _index_button(self, event: Button.Pressed) -> None:
        status = self.query_one("#packs-status", Static)
        status.update(
            "indexing is not available in the standalone llmsx package — it "
            "depends on docset_indexer.py, ChromaDB and an Ollama embedding "
            "pool, which are hub-specific heavy dependencies llmsx deliberately "
            "does not carry. Install the hub (~/.global-ai-hub) and use its "
            "Concepts tab or hub_index_docset to index a pack's units.jsonl.")

    # -- Claude Code skill triggers ------------------------------------ #

    def _run_claude_skill(self, prompt: str, status: Static) -> None:
        """Shell out to `claude -p <prompt>`, suspending the TUI the same
        way `_edit_file` suspends it for $EDITOR. llmsx has no Claude
        session of its own, so this is the only way to actually run a
        skill from here rather than just naming one."""
        status.update(f">>> suspending TUI: claude -p {prompt!r}")
        try:
            with self.suspend():
                rc = subprocess.call(["claude", "-p", prompt])
        except FileNotFoundError:
            status.update("claude CLI not found on PATH — install Claude Code to run "
                           "skills from here")
            return
        except OSError as exc:
            status.update(f"claude failed: {exc}")
            logger.warning("claude -p failed for %r: %s", prompt, exc, exc_info=True)
            return
        if rc:
            status.update(f"claude exited with status {rc}")
        else:
            status.update("back from claude — refreshing catalog")
        self.refresh_packs()

    def _current_node_term(self) -> str | None:
        """The concept/pack name behind whichever tree node is currently
        highlighted, falling back to the selected table row — the target
        for /dr, concept-family-explorer, and rabbithole."""
        data = self._current_node_data
        if data:
            kind = data.get("kind")
            if kind == "concept-term":
                return data["term"]
            if kind in ("pack-ref", "file"):
                return data["entry"]["concept"]
        if self._current_entry is not None:
            return self._current_entry["concept"]
        return None

    def _optimizer_target(self) -> Path | None:
        """The file path deep-optimize should run against: the highlighted
        file leaf, else the last-previewed file, else the highlighted or
        selected pack's own llms.txt."""
        data = self._current_node_data
        if data and data.get("kind") == "file":
            return Path(data["entry"]["dir"]) / data["name"]
        if self._current_file is not None:
            entry, filename = self._current_file
            return Path(entry["dir"]) / filename
        if data and data.get("kind") == "pack-ref":
            return Path(data["entry"]["dir"]) / "llms.txt"
        if self._current_entry is not None:
            return Path(self._current_entry["dir"]) / "llms.txt"
        return None

    @staticmethod
    def _optimizer_command_for(path: Path) -> str:
        """Dispatch to the matching deep-optimizer: llms-family files to
        /ldo, a SKILL.md to /sko, anything else to the general doc /ddo."""
        name = path.name.lower()
        if name.startswith("llms") and name.endswith(".txt"):
            return "/ldo"
        if name == "skill.md":
            return "/sko"
        return "/ddo"

    @on(Button.Pressed, "#packs-dr")
    def _dr_button(self, event: Button.Pressed) -> None:
        status = self.query_one("#packs-status", Static)
        term = self._current_node_term()
        if term is None:
            status.update("select a pack or concept node first")
            return
        self._run_claude_skill(f"/dr {term}", status)

    @on(Button.Pressed, "#packs-cfe")
    def _cfe_button(self, event: Button.Pressed) -> None:
        status = self.query_one("#packs-status", Static)
        term = self._current_node_term()
        if term is None:
            status.update("select a pack or concept node first")
            return
        self._run_claude_skill(f"map the concept family of {term}", status)

    @on(Button.Pressed, "#packs-rabbithole")
    def _rabbithole_button(self, event: Button.Pressed) -> None:
        status = self.query_one("#packs-status", Static)
        term = self._current_node_term()
        if term is None:
            status.update("select a pack or concept node first")
            return
        self._run_claude_skill(f"/rabbithole {term}", status)

    @on(Button.Pressed, "#packs-skilltree")
    def _skilltree_button(self, event: Button.Pressed) -> None:
        # Whole-tree rebalance is global, not scoped to a node.
        status = self.query_one("#packs-status", Static)
        self._run_claude_skill("rebalance the skill tree", status)

    @on(Button.Pressed, "#packs-optimize")
    def _optimize_button(self, event: Button.Pressed) -> None:
        status = self.query_one("#packs-status", Static)
        target = self._optimizer_target()
        if target is None:
            status.update("select a file or pack in the tree first")
            return
        cmd = self._optimizer_command_for(target)
        self._run_claude_skill(f"{cmd} {target}", status)

    @on(Button.Pressed, "#packs-index-all")
    def _index_all_button(self, event: Button.Pressed) -> None:
        # Hub-wide, not scoped to a node — delegates to the llms-librarian
        # agent's index-coverage step (semantic + keyword per docset).
        status = self.query_one("#packs-status", Static)
        self._run_claude_skill(
            "run the llms-librarian agent's index-coverage check: verify every file "
            "referenced across the hub has both a semantic and a keyword index, and "
            "fix whatever's missing", status)


def run(data_path=None) -> int:
    app = ConceptPackBrowser(data_path)
    app.run()
    return 1 if app._load_failed else 0


__all__ = ["ConceptPackBrowser", "FilePreviewScreen", "run"]

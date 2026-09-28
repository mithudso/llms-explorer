"""explorer — the concept-tree workbench: `llmsx explorer`.

One Textual screen over `llmsx.explorer_store`: a collapsible outline of the
raw concept tree on the left, and on the right a tabbed, Markdown-rendered
view of whatever the selected concept has — overview and local notes, the
pack's facts, the skill, each reference file, and each llms-family file when
the hub's `.llms` directory exists. Selecting a node never navigates; the
right pane updates in place, and a tab's file is read and rendered only
when that tab is first opened.

Every write to the *repo* goes through the store and a confirmation modal:

* marks (`m` needs-review, `f` further-research, `x` clear) → `marks.json`,
  and further-research also appends a research-queue row;
* node edits (`E`) → `tree.json`, preserving every other key;
* research (`R`) → one `claude -p` job for one concept, TUI suspended,
  tree snapshotted before and validated after — or a queue row when the
  `claude` binary is not installed;
* sync (`s`) → `git pull --ff-only`; commit (`c`) → stage only the
  allow-listed files, commit, push with the token through `GIT_ASKPASS`.

Local-only writes need no confirmation: notes (`n`) → `$LLMSX_HOME/notes/`,
the bundle (`b` toggle, `B` export) → `$LLMSX_HOME/bundles/`, settings (`,`)
→ `$LLMSX_HOME/config.json`. One carve-out: `e` hands the current tab's file
to `$EDITOR` directly, with no modal and no store in between — the editor
writes the file; nothing is committed until `c` shows the diff and asks.

Rendered files, concept names and notes are untrusted display text: the
Markdown widget only draws them, `<` is escaped before rendering, Rich
markup is escaped in every label, and only a name matching
`explorer_store.SAFE_NAME` may reach a research prompt.

Git and clipboard calls run in thread workers so the event loop, and the
first paint, are never blocked on the network.

Textual is an optional extra, as for `llmsx.tui`; importing this module
without it raises `ImportError` with the install hint.
"""
from __future__ import annotations

import functools
import logging
import os
import shlex
import subprocess
from collections.abc import Callable
from pathlib import Path

from . import explorer_store as store

try:
    from rich.markup import escape
    from rich.text import Text
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.screen import ModalScreen
    from textual.widgets import (
        Button,
        Footer,
        Header,
        Input,
        Label,
        Markdown,
        Select,
        Static,
        TabbedContent,
        TabPane,
        TextArea,
        Tree,
    )
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "llmsx explorer needs Textual — install it with:  pip install 'llmsx[tui]'"
    ) from exc

logger = logging.getLogger(__name__)

#: Largest file the Markdown widget is asked to render; llms-full.txt can be
#: hundreds of KB and the widget is not built for that.
_MAX_RENDER_BYTES = 200_000
#: Wall-clock cap on one headless research job while the TUI is suspended.
def _research_timeout() -> int:
    try:
        return max(1, int(os.environ.get("LLMSX_RESEARCH_TIMEOUT", "3600")))
    except ValueError:        # a typo in the shell rc must not break the import
        return 3600


_RESEARCH_TIMEOUT_S = _research_timeout()

_NOT_AVAILABLE = {
    "no-pack": "not available: no concept pack for this node "
               "(site/src/data/concepts/<slug>.json)",
    "no-skill": "not available: this node names no skill",
    "no-skill-dir": "not available: skill (or its reference file) not in this checkout",
    "no-llms": "not available: no .llms directory for this concept "
               "(hub-only; set $LLMSX_CONCEPTS_PATH)",
    "no-file": "not available: file missing in the .llms directory",
    "frontier": "not available: frontier concept, never researched",
}
_NO_FILE_TAB = "this tab has no file behind it — open Facts, Skill, a reference or an llms tab"


def _pane_id(name: str) -> str:
    return "pane-" + "".join(ch if ch.isalnum() else "-" for ch in name).strip("-").lower()


def _read_for_render(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        logger.warning("could not read %s: %s", path, exc)
        return f"_could not read {escape(path.name)}: {escape(str(exc))}_\n"
    note = ""
    if len(raw) > _MAX_RENDER_BYTES:
        raw = raw[:_MAX_RENDER_BYTES]
        note = (f"\n\n_…truncated for display at {_MAX_RENDER_BYTES:,} bytes; "
                f"the file on disk is complete_\n")
    return store.md_escape(raw.decode("utf-8", errors="replace")) + note


# --------------------------------------------------------------------------- #
# modals
# --------------------------------------------------------------------------- #

class _Modal(ModalScreen):
    """Shared scaffolding: centred box, escape cancels with None, buttons in a
    right-aligned row. Subclasses add widgets and override `_result`."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    DEFAULT_CSS = """
    _Modal { align: center middle; }
    _Modal > Vertical {
        width: 90; max-width: 95%; height: auto; max-height: 90%;
        border: round $primary; padding: 1 2; background: $surface;
    }
    _Modal .body { height: auto; max-height: 20; }
    _Modal .tall { height: 1fr; }
    _Modal Horizontal { height: auto; align: right middle; }
    _Modal .hint { color: $text-muted; }
    _Modal TextArea { height: 8; }
    """

    def action_cancel(self) -> None:
        self.dismiss(None)


class Confirm(_Modal):
    """Yes/no. `enter` on the focused Yes confirms; `escape` cancels."""

    def __init__(self, title: str, body: str, yes: str = "Yes") -> None:
        super().__init__()
        self._heading, self._body, self._yes = title, body, yes

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{escape(self._heading)}[/b]")
            with VerticalScroll(classes="body"):
                yield Static(Text(self._body))
            with Horizontal():
                yield Button(self._yes, id="yes", variant="primary")
                yield Button("Cancel", id="no")

    def on_mount(self) -> None:
        self.query_one("#yes", Button).focus()

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_cancel(self) -> None:
        self.dismiss(False)


class MarkFurther(_Modal):
    """Mode + optional note for a further-research mark. The mode goes into
    the queue row's `Mode:` field; `dr` is the default the queue consumers
    fall back to anyway."""

    def __init__(self, concept: str) -> None:
        super().__init__()
        self._concept = concept

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]Mark for further research:[/b] {escape(self._concept)}")
            yield Select([(m, m) for m in store.RESEARCH_MODES if m != "queue"], value="dr",
                         id="mode", allow_blank=False)
            yield Input(placeholder="note (optional) — stored in marks.json", id="note")
            with Horizontal():
                yield Button("Mark and queue", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#ok", Button).focus()

    def _ok(self) -> None:
        self.dismiss((str(self.query_one("#mode", Select).value),
                      self.query_one("#note", Input).value))

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self._ok() if event.button.id == "ok" else self.dismiss(None)

    @on(Input.Submitted, "#note")
    def _submitted(self) -> None:
        self._ok()


class EditNode(_Modal):
    """summary, aliases (comma-separated) and one new child concept."""

    def __init__(self, node: dict) -> None:
        super().__init__()
        self._target = node

    def compose(self) -> ComposeResult:
        node = self._target
        with Vertical():
            yield Label(f"[b]Edit node:[/b] {escape(node['concept'])}  "
                        f"[dim]({escape(node['slug'])})[/dim]")
            yield Label("summary")
            yield TextArea(node.get("summary") or "", id="summary")
            yield Label("aliases (comma-separated)")
            yield Input(", ".join(str(a) for a in (node.get("aliases") or [])), id="aliases")
            yield Label("add a child concept (a new frontier point; leave blank for none)")
            yield Input(placeholder="Child Concept Name", id="child")
            with Horizontal():
                yield Button("Save to tree.json", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "ok":
            self.dismiss(None)
            return
        aliases = [a.strip() for a in self.query_one("#aliases", Input).value.split(",")]
        self.dismiss({"summary": self.query_one("#summary", TextArea).text.strip(),
                      "aliases": [a for a in aliases if a],
                      "add_child": self.query_one("#child", Input).value.strip() or None})


class Notes(_Modal):
    BINDINGS = [Binding("escape", "cancel", "Cancel"), Binding("ctrl+s", "save", "Save")]
    DEFAULT_CSS = _Modal.DEFAULT_CSS + """
    Notes > Vertical { height: 80%; }
    Notes TextArea { height: 1fr; }
    """

    def __init__(self, concept: str, text: str, path: Path) -> None:
        super().__init__()
        self._concept, self._initial, self._note_path = concept, text, path

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]Notes (local only):[/b] {escape(self._concept)}  "
                        f"[dim]{escape(str(self._note_path))}[/dim]")
            yield TextArea(self._initial, id="text")
            with Horizontal():
                yield Button("Save (ctrl+s)", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#text", TextArea).focus()

    def action_save(self) -> None:
        self.dismiss(self.query_one("#text", TextArea).text)

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self.dismiss(self.query_one("#text", TextArea).text if event.button.id == "ok" else None)


class Research(_Modal):
    """Pick a mode; returns it, or None. Without the claude binary only
    `queue` is offered, and the screen says why."""

    def __init__(self, concept: str, parent: str | None, have_claude: bool) -> None:
        super().__init__()
        self._concept, self._parent_name, self._have_claude = concept, parent, have_claude

    def compose(self) -> ComposeResult:
        modes = list(store.RESEARCH_MODES) if self._have_claude else ["queue"]
        with Vertical():
            yield Label(f"[b]Research:[/b] {escape(self._concept)}"
                        + (f"  [dim]under {escape(self._parent_name)}[/dim]"
                           if self._parent_name else ""))
            if not self._have_claude:
                yield Static("claude CLI not found on PATH — only `queue` is available "
                             "(the row lands in RESEARCH_QUEUE.md for a box that has it).",
                             classes="hint")
            yield Static("dr = /dr skill · family = concept-family-explorer · deep = rabbithole"
                         " · crawl = crawl-to-llms-txt · full = full-suite (the whole stack) · "
                         "queue = append a queue row only", classes="hint")
            yield Select([(m, m) for m in modes], value=modes[0], id="mode", allow_blank=False)
            with Horizontal():
                yield Button("Run one job" if self._have_claude else "Queue", id="ok",
                             variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#ok", Button).focus()

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self.dismiss(str(self.query_one("#mode", Select).value)
                     if event.button.id == "ok" else None)


class Settings(_Modal):
    """repo_url, push target, token. The token field is masked and its value
    is never echoed back in any status line. "Test token" runs in a thread
    worker so the modal stays responsive."""

    def __init__(self, cfg: dict, env_token: bool, tester: Callable[[str, str], str]) -> None:
        super().__init__()
        self._cfg, self._env_token, self._tester = cfg, env_token, tester

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[b]Settings[/b]  [dim]stored 0600 at "
                        + escape(str(store.config_path())) + "[/dim]")
            yield Label("repo_url — https URL cloned on first run when no checkout is found")
            yield Input(self._cfg.get("repo_url") or store.DEFAULT_REPO_URL, id="repo_url")
            yield Label("push_url — a git remote name (origin) or an https URL, e.g. your fork")
            yield Input(self._cfg.get("push_url") or "origin", id="push_url")
            yield Label("GitHub token — blank keeps the current one; type `-` to remove it")
            if self._env_token:
                yield Static("$LLMSX_GITHUB_TOKEN is set and wins over the stored token.",
                             classes="hint")
            yield Input(placeholder="ghp_… (masked)", password=True, id="token")
            yield Static("", id="test-result", classes="hint")
            with Horizontal():
                yield Button("Test token", id="test")
                yield Button("Save", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def _values(self) -> dict:
        return {"repo_url": self.query_one("#repo_url", Input).value.strip(),
                "push_url": self.query_one("#push_url", Input).value.strip() or "origin",
                "token": self.query_one("#token", Input).value}

    def _show_test_result(self, text: str) -> None:
        try:
            self.query_one("#test-result", Static).update(Text(text))
        except Exception as exc:  # the modal was dismissed before the test finished
            logger.debug("token test result dropped: %s", exc)

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self._values())
        elif event.button.id == "test":
            v = self._values()
            self._show_test_result("testing…")
            tester, show = self._tester, self._show_test_result
            app = self.app

            def work() -> None:
                result = tester(v["push_url"], v["token"])
                try:
                    app.call_from_thread(show, result)
                except RuntimeError:   # app already exited
                    pass
            app.run_worker(work, thread=True, group="token-test", exclusive=True)
        else:
            self.dismiss(None)


class Bundle(_Modal):
    """What is marked; export under a name; or clear."""

    DEFAULT_CSS = _Modal.DEFAULT_CSS + """
    Bundle > Vertical { height: 80%; }
    """

    def __init__(self, items: list[store.BundleItem], default_name: str) -> None:
        super().__init__()
        self._bundle_items, self._default = items, default_name

    def compose(self) -> ComposeResult:
        items = self._bundle_items
        with Vertical():
            yield Label(f"[b]Bundle[/b]  {len(items)} file(s) marked with `b`")
            with VerticalScroll(classes="tall"):
                yield Markdown(store.bundle_markdown(self._default, items) if items
                               else "_nothing marked yet — press `b` on a file tab to add it_")
            yield Label("bundle name (directory under $LLMSX_HOME/bundles/)")
            yield Input(self._default, id="name")
            with Horizontal():
                yield Button("Export", id="ok", variant="primary", disabled=not items)
                yield Button("Clear bundle", id="clear", disabled=not items)
                yield Button("Close", id="cancel")

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one("#name", Input).value.strip() or self._default)
        elif event.button.id == "clear":
            self.dismiss("")
        else:
            self.dismiss(None)


# --------------------------------------------------------------------------- #
# the outline widget
# --------------------------------------------------------------------------- #

class OutlineTree(Tree):
    """The stock Tree plus right/left to expand/collapse the cursor node."""

    BINDINGS = [Binding("right", "expand_node", "Expand", show=False),
                Binding("left", "collapse_node", "Collapse", show=False)]

    def action_expand_node(self) -> None:
        node = self.cursor_node
        if node is not None and node.allow_expand:
            node.expand()

    def action_collapse_node(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.is_expanded:
            node.collapse()
        elif node.parent is not None and node.parent is not self.root:
            self.select_node(node.parent)
            self.scroll_to_node(node.parent)


# --------------------------------------------------------------------------- #
# the app
# --------------------------------------------------------------------------- #

class Explorer(App):
    CSS = """
    #left { width: 42%; min-width: 30; }
    #outline { height: 1fr; border: round $primary; }
    #right { width: 1fr; }
    #tabs { height: 1fr; }
    #status { height: auto; max-height: 4; padding: 0 1; color: $text-muted; }
    .hint { color: $text-muted; }
    TabPane { padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("slash", "focus_filter", "Filter", key_display="/"),
        Binding("r", "reload", "Reload"),
        Binding("m", "mark_review", "Needs review"),
        Binding("f", "mark_further", "Further research"),
        Binding("x", "clear_mark", "Clear mark", show=False),
        Binding("n", "notes", "Notes"),
        Binding("e", "edit_file", "$EDITOR", show=False),
        Binding("E", "edit_node", "Edit node"),
        Binding("b", "bundle_toggle", "Bundle ±", show=False),
        Binding("B", "bundle_screen", "Bundle"),
        Binding("R", "research", "Research"),
        Binding("s", "sync", "Sync"),
        Binding("c", "commit", "Commit+push"),
        Binding("comma", "settings", "Settings", key_display=","),
    ]

    def __init__(self, repo: str | Path, auto_sync: bool = True) -> None:
        super().__init__()
        self.repo = Path(repo).resolve()
        self._auto_sync = auto_sync
        self._tree_nodes: list[dict] = []
        self._outline: store.Outline | None = None
        self._marks: dict[str, dict] = {}
        self._queued: set[str] = set()
        self._available: set[str] = set()                    # slugs with a pack or .llms dir
        self._selected: str | None = None                    # concept name
        self._pane_files: dict[str, tuple[Path, str]] = {}   # pane id -> (path, kind)
        self._pane_source: dict[str, Path | str] = {}        # pane id -> file or literal text
        self._filled: set[str] = set()                       # pane ids already rendered
        self._bundle: dict[str, store.BundleItem] = {}       # resolved path -> item
        self._dynamic_panes: list[str] = []
        self._pending_removal: list[str] = []   # panes a cancelled render did not get to
        self._render_serial = 0     # pane ids are unique per render: removal is async
        self._git_busy = False      # one git subprocess at a time, whatever the workers do
        self._filter_timer = None

    # ------------------------------------------------------------------ #
    # layout

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left"):
                yield Input(placeholder="filter concepts and aliases…  (/)", id="filter")
                yield OutlineTree("concept tree", id="outline")
            with Vertical(id="right"), TabbedContent(id="tabs"):
                yield TabPane("Overview", Markdown("", id="md-overview"), id="pane-overview")
                yield TabPane("Facts", Markdown("", id="md-facts"), id="pane-facts")
                yield TabPane("Skill", Markdown("", id="md-skill"), id="pane-skill")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer"
        self.sub_title = str(self.repo)
        self._load()
        self._render_outline()
        if self._auto_sync:
            self.action_sync()

    # ------------------------------------------------------------------ #
    # data

    def _status(self, text: str) -> None:
        self.query_one("#status", Static).update(Text(text))

    def _load(self) -> None:
        try:
            self._tree_nodes = store.load_raw_tree(self.repo / store.TREE_REL)
        except (FileNotFoundError, ValueError) as exc:
            self._tree_nodes = []
            logger.warning("could not load the tree: %s", exc)
            self._status(f"could not load the tree: {exc}")
        self._outline = store.build_outline(self._tree_nodes)
        self._marks = store.load_marks(self.repo)
        try:
            self._queued = {e["concept"] for e in store.load_queue(self.repo) if not e["done"]}
            self._available = store.available_slugs(self.repo)
        except OSError as exc:
            logger.warning("could not read the queue or the packs: %s", exc)
            self._queued, self._available = set(), set()

    def _refresh(self, focus: str | None = None, *, reload: bool = True) -> None:
        """Reload from disk (unless `reload=False`), redraw the outline, and
        re-render the panes for `focus` or the current selection."""
        if reload:
            self._load()
        self._render_outline()
        name = focus or self._selected
        if name:
            self._selected = name
            self._render_later(name)

    def _node(self, name: str | None) -> dict | None:
        return self._outline.nodes.get(name) if (self._outline and name) else None

    def _slug(self, name: str) -> str:
        node = self._node(name)
        return node["slug"] if node else store.slugify(name)

    # ------------------------------------------------------------------ #
    # outline

    def _matching(self, needle: str) -> set[str] | None:
        if not needle or not self._outline:
            return None
        keep: set[str] = set()
        names = list(self._outline.nodes) + [
            c for kids in self._outline.children.values() for c in kids
            if self._outline.is_frontier(c)]
        for name in names:
            node = self._outline.nodes.get(name)
            aliases = (node.get("aliases") or []) if node else []
            if needle not in name.lower() and not any(needle in a.lower() for a in aliases):
                continue
            cur: str | None = name
            while cur and cur not in keep:
                keep.add(cur)
                cur = self._outline.parent_of(cur)
        return keep

    def _label(self, name: str) -> Text:
        o = self._outline
        node = o.nodes.get(name) if o else None
        if node is None:
            label = Text(name, style="dim italic")
            label.append("  (frontier)", style="dim")
            if name in self._queued:
                label.append("  queued", style="dim cyan")
            return label
        label = Text(name)
        if node["slug"] in self._available:
            label.append(" ●", style="cyan")
        mark = self._marks.get(node["slug"])
        if isinstance(mark, dict):
            label.append(f"  [{mark.get('state')}]", style="bold yellow")
        if name in self._queued:
            label.append("  queued", style="dim cyan")
        return label

    def _render_outline(self) -> None:
        tree = self.query_one("#outline", OutlineTree)
        tree.clear()
        o = self._outline
        if not o:
            return
        needle = self.query_one("#filter", Input).value.strip().lower()
        keep = self._matching(needle)

        def wanted(name: str) -> bool:
            return keep is None or name in keep

        def add(parent, name: str, ancestors: frozenset[str]) -> None:
            if name in ancestors:
                return
            kids = [k for k in o.children.get(name, []) if wanted(k)]
            if kids:
                node = parent.add(self._label(name), data=name, expand=bool(needle))
                for k in kids:
                    add(node, k, ancestors | {name})
            else:
                parent.add_leaf(self._label(name), data=name)

        for root in o.roots:
            if wanted(root):
                add(tree.root, root, frozenset())
        tree.root.expand()
        self._status(f"{len(o.nodes)} concepts · {len(o.roots)} roots · "
                     f"{len(self._marks)} marked · {len(self._queued)} queued · "
                     f"bundle {len(self._bundle)} file(s)")

    @on(Input.Changed, "#filter")
    def _filter_changed(self) -> None:
        # one rebuild per pause in typing, not one per keystroke over 4,500 rows
        if self._filter_timer is not None:
            self._filter_timer.stop()
        self._filter_timer = self.set_timer(0.15, self._render_outline)

    @on(Input.Submitted, "#filter")
    def _filter_submitted(self) -> None:
        self.query_one("#outline", OutlineTree).focus()

    def action_focus_filter(self) -> None:
        self.query_one("#filter", Input).focus()

    def action_reload(self) -> None:
        self._refresh()

    @on(Tree.NodeHighlighted, "#outline")
    def _highlighted(self, event: Tree.NodeHighlighted) -> None:
        if event.node.data:
            self._select(event.node.data)

    @on(Tree.NodeSelected, "#outline")
    def _selected_node(self, event: Tree.NodeSelected) -> None:
        if event.node.data:
            self._select(event.node.data)

    def _select(self, name: str) -> None:
        """Render `name`'s panes in an exclusive worker: a cursor sweeping
        through the outline cancels the previous, unfinished render instead
        of queueing one per row."""
        if name == self._selected:
            return
        self._selected = name
        self._render_later(name)

    def _render_later(self, name: str) -> None:
        # a partial, not a coroutine object: an exclusive worker that never
        # starts would otherwise leave a never-awaited coroutine behind
        self.run_worker(functools.partial(self._render_panes, name), exclusive=True,
                        group="panes")

    # ------------------------------------------------------------------ #
    # panes

    async def _render_panes(self, name: str) -> None:
        """Rebuild the tab set for `name`. Fixed tabs (Overview, Facts, Skill)
        get their source recorded; dynamic tabs (references, llms files) are
        created empty. Only the Overview and the currently active tab are
        rendered now; the rest render on first activation."""
        tabs = self.query_one("#tabs", TabbedContent)
        # Reset the bookkeeping BEFORE the first await: this worker is
        # exclusive, so a faster selection cancels it mid-await, and a
        # TabActivated fired by a removal must find empty state, not the
        # previous concept's sources.
        self._pending_removal.extend(self._dynamic_panes)
        self._dynamic_panes = []
        self._pane_files = {}
        self._pane_source = {}
        self._filled = set()
        self._render_serial += 1
        # sweep everything still pending, including what a cancelled render
        # left behind; each id leaves the list only once its pane is gone
        while self._pending_removal:
            pid = self._pending_removal[0]
            try:
                await tabs.remove_pane(pid)
            except Exception as exc:   # already gone: a cancelled render removed it
                logger.debug("pane %s already removed: %s", pid, exc)
            if self._pending_removal and self._pending_removal[0] == pid:
                self._pending_removal.pop(0)
        node = self._node(name)
        slug = self._slug(name)
        # each pane is set on its own: one I/O failure (a concurrent pull
        # swapping a file) marks that pane, never its siblings
        self._try_set("pane-overview", lambda: self._set_overview(name, node, slug), name)
        if node is None:
            self._pane_source["pane-facts"] = f"_{_NOT_AVAILABLE['frontier']}_"
            self._pane_source["pane-skill"] = f"_{_NOT_AVAILABLE['frontier']}_"
        else:
            self._try_set("pane-facts", lambda: self._set_facts(name, slug), name)
            self._try_set("pane-skill", lambda: self._set_skill(node), name)
            self._try_set(None, lambda: self._set_llms(slug), name)
        self._fill("pane-overview")
        self._fill(tabs.active)

    def _try_set(self, pid: str | None, fn: Callable[[], None], name: str) -> None:
        try:
            fn()
        except OSError as exc:
            logger.warning("render of %r hit an I/O error: %s", name, exc)
            msg = f"_could not read this concept: {escape(str(exc))}_"
            if pid:
                self._pane_source[pid] = msg
            else:
                self._add_pane("llms", text=msg)

    def _set_overview(self, name: str, node: dict | None, slug: str) -> None:
        note = store.read_note(slug) if node else ""
        self._pane_source["pane-overview"] = store.overview_markdown(
            node, name, self._outline, self._marks, note, name in self._queued)

    def _set_facts(self, name: str, slug: str) -> None:
        pack_file = store.pack_path(self.repo, slug)
        if pack_file:
            self._pane_source["pane-facts"] = store.facts_markdown(
                store.load_pack(self.repo, slug), name)
            self._pane_files["pane-facts"] = (pack_file, "pack")
        else:
            self._pane_source["pane-facts"] = f"_{_NOT_AVAILABLE['no-pack']}_"

    def _set_skill(self, node: dict) -> None:
        target = store.skill_target(self.repo, node.get("skillId"))
        if not node.get("skillId"):
            self._pane_source["pane-skill"] = f"_{_NOT_AVAILABLE['no-skill']}_"
        elif not target:
            self._pane_source["pane-skill"] = (f"_{_NOT_AVAILABLE['no-skill-dir']}: "
                                               f"`{store.md_escape(node['skillId'])}`_")
        else:
            skill, shown = target
            kind = "skill" if shown.name == "SKILL.md" else "reference"
            self._pane_source["pane-skill"] = shown
            self._pane_files["pane-skill"] = (shown, kind)
            if kind == "reference":
                self._add_pane("SKILL.md (hub)", path=skill / "SKILL.md", kind="skill")
            for ref in store.reference_files(skill):
                if ref != shown:
                    self._add_pane(f"ref: {ref.stem}", path=ref, kind="reference")

    def _set_llms(self, slug: str) -> None:
        ldir = store.llms_dir(slug)
        if not ldir:
            self._add_pane("llms", text=f"_{_NOT_AVAILABLE['no-llms']}_")
            return
        for fname in store.LLMS_FILES:
            f = store.llms_file(ldir, fname)
            if f:
                self._add_pane(fname, path=f, kind="llms")
            else:
                self._add_pane(fname, text=f"_{_NOT_AVAILABLE['no-file']}: {fname}_")

    def _add_pane(self, title: str, *, path: Path | None = None, text: str | None = None,
                  kind: str | None = None) -> None:
        pid = _pane_id(f"{kind or 'text'}-{title}-{self._render_serial}-{len(self._dynamic_panes)}")
        if path is not None and str(path.resolve()) in self._bundle:
            title += " ✓"
        self.query_one("#tabs", TabbedContent).add_pane(TabPane(title, Markdown(""), id=pid))
        self._dynamic_panes.append(pid)
        self._pane_source[pid] = path if path is not None else (text or "")
        if path is not None and kind:
            self._pane_files[pid] = (path, kind)

    def _fill(self, pid: str | None) -> None:
        """Render one pane's source into its Markdown widget, once."""
        if not pid or pid in self._filled or pid not in self._pane_source:
            return
        source = self._pane_source[pid]
        text = _read_for_render(source) if isinstance(source, Path) else source
        try:
            pane = self.query_one(f"#{pid}", TabPane)
            pane.query_one(Markdown).update(text)
        except Exception as exc:  # the pane may already be gone (re-render in flight)
            logger.debug("pane %s not filled: %s", pid, exc)
            return
        self._filled.add(pid)

    @on(TabbedContent.TabActivated, "#tabs")
    def _tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self._fill(event.pane.id)

    def _current_file(self) -> tuple[Path, str] | None:
        return self._pane_files.get(self.query_one("#tabs", TabbedContent).active)

    # ------------------------------------------------------------------ #
    # marks and notes

    def _require_node(self) -> dict | None:
        node = self._node(self._selected)
        if node is None:
            self._status("select a researched concept first "
                         "(frontier concepts have no node to mark)")
        return node

    def _guarded(self, what: str, fn: Callable[[], str]) -> None:
        """Run a store write, turning any failure into a status line."""
        try:
            self._status(fn())
        except (OSError, ValueError, KeyError, store.GitError) as exc:
            logger.warning("%s failed: %s", what, exc)
            self._status(f"{what} failed: {exc}")

    def action_mark_review(self) -> None:
        node = self._require_node()
        if not node:
            return

        def apply() -> str:
            self._marks = store.set_mark(self.repo, node["slug"], "needs-review")
            self._refresh(node["concept"], reload=False)
            return f"marked needs-review: {node['concept']} → {store.MARKS_REL}"

        def done(ok: bool) -> None:
            if ok:
                self._guarded("mark", apply)
        self.push_screen(Confirm("Mark as needs-review?",
                                 f"{node['concept']}\n\nwrites {self.repo / store.MARKS_REL}"),
                         done)

    def action_mark_further(self) -> None:
        node = self._require_node()
        if not node:
            return

        def done(result: tuple[str, str] | None) -> None:
            if not result:
                return
            mode, note = result

            def apply() -> str:
                self._marks = store.set_mark(self.repo, node["slug"], "further-research", note)
                added = store.queue_concept(self.repo, node["concept"],
                                            node.get("parentConcept"), mode)
                self._refresh(node["concept"])
                return (f"marked further-research: {node['concept']} "
                        + ("(queue row added)" if added else "(already queued)"))
            self._guarded("mark", apply)
        self.push_screen(MarkFurther(node["concept"]), done)

    def action_clear_mark(self) -> None:
        node = self._require_node()
        if not node or node["slug"] not in self._marks:
            return

        def apply() -> str:
            self._marks = store.set_mark(self.repo, node["slug"], None)
            self._refresh(node["concept"], reload=False)
            return f"cleared mark: {node['concept']}"
        self._guarded("clear mark", apply)

    def action_notes(self) -> None:
        node = self._require_node()
        if not node:
            return
        slug = node["slug"]

        def done(text: str | None) -> None:
            if text is None:
                return

            def apply() -> str:
                p = store.write_note(slug, text)
                self._refresh(node["concept"], reload=False)
                return f"notes saved (local only): {p}"
            self._guarded("notes", apply)
        try:
            path = store.note_path(slug)
        except ValueError as exc:
            self._status(f"notes unavailable: {exc}")
            return
        self.push_screen(Notes(node["concept"], store.read_note(slug), path), done)

    # ------------------------------------------------------------------ #
    # editing

    def action_edit_node(self) -> None:
        node = self._require_node()
        if not node:
            return

        def done(changes: dict | None) -> None:
            if not changes:
                return

            def apply() -> str:
                store.edit_node(self._tree_nodes, node["concept"], summary=changes["summary"],
                                aliases=changes["aliases"], add_child=changes["add_child"])
                store.save_raw_tree(self._tree_nodes, self.repo / store.TREE_REL)
                self._refresh(node["concept"])
                return f"saved {store.TREE_REL}: {node['concept']}"
            self._guarded("edit", apply)
        self.push_screen(EditNode(node), done)

    def action_edit_file(self) -> None:
        current = self._current_file()
        if not current:
            self._status(_NO_FILE_TAB)
            return
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if not editor:
            self._status("$EDITOR is not set — export EDITOR=vim (or similar) and try again")
            return
        try:
            argv = shlex.split(editor, posix=(os.name != "nt")) + [str(current[0])]
            with self.suspend():
                rc = subprocess.call(argv)
        except (OSError, ValueError) as exc:
            logger.warning("could not run editor %r: %s", editor, exc)
            self._status(f"could not run {editor!r}: {exc}")
            return
        self._refresh(reload=False)
        self._status(f"{editor} exited {rc}: {current[0]}")

    # ------------------------------------------------------------------ #
    # bundle

    def action_bundle_toggle(self) -> None:
        current = self._current_file()
        if not current:
            self._status(_NO_FILE_TAB)
            return
        path, kind = current
        key = str(path.resolve())
        if key in self._bundle:
            del self._bundle[key]
            msg = f"removed from bundle: {path}"
        else:
            self._bundle[key] = store.bundle_item(path, kind, self._selected or path.stem)
            msg = f"added to bundle ({len(self._bundle)}): {path}"
        self._refresh(reload=False)
        self._status(msg)

    def action_bundle_screen(self) -> None:
        items = list(self._bundle.values())
        default = store.default_bundle_name(self._slug(self._selected) if self._selected
                                            else "bundle")

        def done(name: str | None) -> None:
            if name is None:
                return
            if name == "":
                self._bundle.clear()
                self._refresh(reload=False)
                self._status("bundle cleared")
                return

            def apply() -> str:
                out = store.export_bundle(name, items)
                text = (out / "bundle.md").read_text(encoding="utf-8")
                self.run_worker(lambda: store.copy_to_clipboard(text), thread=True,
                                group="clipboard")
                return f"bundle exported: {out}/bundle.md + bundle.json"
            self._guarded("bundle export", apply)
        self.push_screen(Bundle(items, default), done)

    # ------------------------------------------------------------------ #
    # research

    def action_research(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return
        parent = self._outline.parent_of(name) if self._outline else None
        node = self._node(name)
        if node and node.get("parentConcept"):
            parent = node["parentConcept"]
        if parent and not store.safe_name(parent):
            parent = None
        have_claude = store.claude_binary() is not None

        def done(mode: str | None) -> None:
            if not mode:
                return
            if mode == "queue":
                def apply() -> str:
                    added = store.queue_concept(self.repo, name, parent, None)
                    self._refresh(name)
                    return f"queued {name}" if added else f"already queued: {name}"
                self._guarded("queue", apply)
                return
            why = store.unsafe_name_reason(name)
            if why:
                self._status(f"refusing to build a research prompt: the concept name {why}")
                return
            self._run_research(name, mode, parent)
        self.push_screen(Research(name, parent, have_claude), done)

    def _run_research(self, name: str, mode: str, parent: str | None) -> None:
        argv = store.research_argv(name, mode, parent)
        if not argv:
            self._status("claude CLI not found on PATH")
            return
        snapshot = store.snapshot_tree(self.repo)
        self._status(f"running one {mode} job for {name} (timeout {_RESEARCH_TIMEOUT_S}s)…")
        try:
            with self.suspend():
                subprocess.run(argv, cwd=str(self.repo), timeout=_RESEARCH_TIMEOUT_S,
                               check=False)
        except subprocess.TimeoutExpired:
            store.restore_tree_snapshot(self.repo, snapshot)
            logger.warning("research job for %r exceeded %ss", name, _RESEARCH_TIMEOUT_S)
            self._status(f"research job exceeded {_RESEARCH_TIMEOUT_S}s and was killed; "
                         "tree snapshot restored")
            return
        except OSError as exc:
            logger.warning("could not run claude: %s", exc)
            self._status(f"could not run claude: {exc}")
            return
        ok, msg = store.verify_tree_after_run(self.repo, snapshot)
        self._refresh()
        self._status(("done — " if ok else "FAILED — ") + msg)

    # ------------------------------------------------------------------ #
    # git (thread workers: never on the event loop, one subprocess at a time)

    def _post(self, fn: Callable, *args) -> None:
        """`call_from_thread` that tolerates the app having exited."""
        try:
            self.call_from_thread(fn, *args)
        except RuntimeError:
            pass

    def _git_start(self, what: str) -> bool:
        """Claim the git slot; exclusive workers cannot interrupt a running
        subprocess, so a flag serialises pull and commit for real."""
        if self._git_busy:
            self._status(f"a git operation is already running; {what} skipped")
            return False
        self._git_busy = True
        return True

    def _git_done(self) -> None:
        self._git_busy = False

    def action_sync(self) -> None:
        if not self._git_start("sync"):
            return
        repo = self.repo

        def work() -> None:
            try:
                msg = store.git_pull(repo)
            except store.GitError as exc:
                self._post(self._status,
                           f"sync (git pull --ff-only) failed, working offline: {exc}")
                return
            finally:
                self._post(self._git_done)
            self._post(self._after_pull, msg)
        self._status("sync: pulling…")
        self.run_worker(work, thread=True, group="git", exclusive=True)

    def _after_pull(self, msg: str) -> None:
        self._refresh()
        self._status(f"sync: {msg}")

    def action_commit(self) -> None:
        """Fetch the status and diff in a thread, then ask; git never runs on
        the event loop."""
        if not self._git_start("commit"):
            return
        repo = self.repo

        def work() -> None:
            try:
                changed = store.changed_allowlisted(repo)
                summary = store.diff_summary(repo, changed)
            except store.GitError as exc:
                self._post(self._status, f"git status failed: {exc}")
                return
            finally:
                self._post(self._git_done)
            self._post(self._ask_commit, changed[0], summary)
        self._status("checking the working tree…")
        self.run_worker(work, thread=True, group="git", exclusive=True)

    def _ask_commit(self, ok: list[str], summary: str) -> None:
        if not ok:
            self._status("nothing to commit: tree.json, marks.json and RESEARCH_QUEUE.md "
                         "are unchanged")
            return
        touched = sorted(self._marks_touched_names())
        message = "explorer: " + (", ".join(touched) if touched else "update concept tree")
        target = store.push_url()
        body = (f"stages ONLY: {', '.join(ok)}\n\n{summary}\n\n"
                f"message: {message}\npush to: {target}"
                + ("" if store.github_token() else
                   "\n\n(no token configured — the commit will be made but not pushed; "
                   "set one with `,`)"))

        def done(confirmed: bool) -> None:
            if confirmed:
                self._commit_and_push(message, target)
        self.push_screen(Confirm("Commit and push?", body, yes="Commit"), done)

    def _commit_and_push(self, message: str, target: str) -> None:
        if not self._git_start("commit"):
            return
        repo = self.repo

        def work() -> None:
            try:
                self._post(self._status, self._commit_then_push(repo, message, target))
            finally:
                self._post(self._git_done)
        self._status("committing…")
        self.run_worker(work, thread=True, group="git", exclusive=True)

    @staticmethod
    def _commit_then_push(repo: Path, message: str, target: str) -> str:
        """The blocking half of a commit: runs in the thread, returns the
        status line."""
        try:
            sha = store.commit_allowlisted(repo, message)
        except store.GitError as exc:
            return f"commit failed: {exc}"
        token = store.github_token()
        if not token:
            return f"committed {sha}; not pushed (no token — set one with `,`)"
        try:
            out = store.git_push(repo, target, token)
        except store.GitError as exc:
            return f"committed {sha}; push failed: {exc}"
        return f"committed {sha} and pushed to {target}: {out}"

    def _marks_touched_names(self) -> set[str]:
        """Concept names for the commit message: only names that pass
        SAFE_NAME, so a hostile name in a public tree cannot shape it."""
        out: set[str] = set()
        if not self._outline:
            return out
        for slug in self._marks:
            node = self._outline.by_slug.get(slug)
            if node and store.safe_name(node["concept"]):
                out.add(node["concept"])
        if self._selected and store.safe_name(self._selected):
            out.add(self._selected)
        return out

    def action_settings(self) -> None:
        cfg = store.load_config()

        def tester(target: str, token: str) -> str:
            tok = token.strip() if token and token != "-" else store.github_token()
            try:
                return store.test_token(self.repo, target, tok)
            except store.GitError as exc:
                logger.warning("token test failed: %s", exc)
                return f"failed: {exc}"

        def done(values: dict | None) -> None:
            if not values:
                return

            def apply() -> str:
                p = store.set_remotes(values["repo_url"] or store.DEFAULT_REPO_URL,
                                      values["push_url"])
                tok = values["token"]
                if tok == "-":
                    store.set_github_token("")
                elif tok.strip():
                    store.set_github_token(tok)
                return f"settings saved: {p} (mode 0600)"
            self._guarded("settings", apply)
        self.push_screen(Settings(cfg, bool(os.environ.get("LLMSX_GITHUB_TOKEN")), tester), done)


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def run(repo: str | None = None, no_sync: bool = False) -> int:
    """Resolve the checkout (or clone one on first run), then launch.
    Warnings go to `$LLMSX_HOME/explorer.log`: stdout and stderr belong to the
    alternate screen while the TUI runs."""
    try:
        log = store.home() / "explorer.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=str(log), level=logging.WARNING,
                            format="%(asctime)s %(name)s %(levelname)s %(message)s")
    except OSError:
        pass
    path = Path(repo).expanduser().resolve() if repo else store.find_repo()
    if repo and not (path / store.TREE_REL).is_file():
        print(f"llmsx: no concept tree at {path / store.TREE_REL}", flush=True)
        return 2
    if path is None:
        dest = store.home() / "llms-explorer"
        url = store.repo_url()
        print(f"llmsx: no llms-explorer checkout found from {Path.cwd()};\n"
              f"       cloning {url}\n       into    {dest}  (Ctrl-C to cancel)", flush=True)
        try:
            store.clone_repo(url, dest)
        except KeyboardInterrupt:
            print("llmsx: clone cancelled", flush=True)
            return 130
        except store.GitError as exc:
            print(f"llmsx: clone failed: {exc}", flush=True)
            return 2
        path = dest
    Explorer(path, auto_sync=not no_sync).run()
    return 0

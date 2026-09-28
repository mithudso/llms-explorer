"""explorer_screens — the secondary screens and modals of `llmsx explorer`.

Kept out of `explorer.py` so the main screen stays readable:

* `Library` — the site's directory of scored `llms-full.txt` files, its
  blog posts, its installable skills, and the files imported into
  `$LLMSX_HOME/imports/`, each list with a Markdown preview of the selected
  entry (the mirrored llms-full file when the hub has it);
* `Ledger` — `llms_ledger.py report` for the last N days, by file, kind,
  project or surface;
* `SkillRunner` — pick any skill the explorer can point `claude -p` at (the
  research stack, the crawl-to-llms family, every deep optimizer) and a
  target for it;
* `Braindump` and `Journal` — capture: a dump saved verbatim and parsed by
  the braindump skill; dated entries a skill can turn into an llms family;
* `Flashcards` and `Quiz` — learning over the selected branch, Leitner
  boxes in `$LLMSX_HOME/flashcards.json`;
* `TagEditor`, `LinkPicker`, `ImportDialog`, `PanelSettings`, `TextPrompt`,
  `Chooser`, and `_Modal` (the shared scaffold `explorer.py` imports too) —
  small modals over one store call each.

Everything rendered here is untrusted text: previews go through
`explorer_store.md_escape`, labels through `rich.markup.escape`.
"""
from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from rich.markup import escape
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Markdown,
    OptionList,
    RichLog,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
)
from textual.widgets.option_list import Option

from . import explorer_store as store

_MAX_PREVIEW = 200_000


def read_preview(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return f"_could not read {escape(path.name)}: {escape(str(exc))}_"
    note = "" if len(raw) <= _MAX_PREVIEW else "\n\n_…truncated for display_"
    return store.md_escape(raw[:_MAX_PREVIEW].decode("utf-8", errors="replace")) + note


class _Modal(ModalScreen):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    DEFAULT_CSS = """
    _Modal { align: center middle; }
    _Modal > Vertical {
        width: 90; max-width: 95%; height: auto; max-height: 90%;
        border: round $primary; padding: 1 2; background: $surface;
    }
    _Modal Horizontal { height: auto; align: right middle; }
    _Modal .hint { color: $text-muted; }
    _Modal OptionList { height: 12; }
    _Modal .body { height: auto; max-height: 20; }
    _Modal .tall { height: 1fr; }
    _Modal TextArea { height: 8; }
    """

    def action_cancel(self) -> None:
        self.dismiss(None)


# --------------------------------------------------------------------------- #
# tags, links, imports, panels

class TagEditor(_Modal):
    """Comma-separated tags for one concept; existing tags offered as hints."""

    def __init__(self, concept: str, current: list[str], known: list[str]) -> None:
        super().__init__()
        self._concept, self._current, self._known = concept, current, known

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]Tags:[/b] {escape(self._concept)}")
            yield Input(", ".join(self._current), placeholder="tag, another tag", id="tags")
            if self._known:
                yield Static("known: " + ", ".join(escape(t) for t in self._known[:40]),
                             classes="hint")
            with Horizontal():
                yield Button("Save", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#tags", Input).focus()

    def _ok(self) -> None:
        self.dismiss([t.strip() for t in self.query_one("#tags", Input).value.split(",")])

    @on(Input.Submitted, "#tags")
    def _submitted(self) -> None:
        self._ok()

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self._ok() if event.button.id == "ok" else self.dismiss(None)


class LinkPicker(_Modal):
    """Type to search concepts; pick one. Also used to pick a new parent
    (`title="Move under"`, local roots in `extra`, and `allow_clear` for
    "back under the repo parent", which dismisses with "")."""

    def __init__(self, concept: str, outline: store.Outline, title: str = "Link a concept to",
                 extra: set[str] | None = None, allow_clear: bool = False) -> None:
        super().__init__()
        self._concept, self._outline = concept, outline
        self._heading, self._extra, self._allow_clear = title, extra or set(), allow_clear

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{escape(self._heading)}:[/b] {escape(self._concept)}")
            yield Input(placeholder="type part of a concept name…", id="q")
            yield OptionList(id="hits")
            with Horizontal():
                if self._allow_clear:
                    yield Button("Repo parent", id="clear")
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#q", Input).focus()

    @on(Input.Changed, "#q")
    def _search(self, event: Input.Changed) -> None:
        hits = self.query_one("#hits", OptionList)
        hits.clear_options()
        q = event.value.strip().lower()
        if len(q) >= 2:
            for name in sorted(self._extra):
                if q in name.lower() and name != self._concept:
                    hits.add_option(Option(escape(name) + "  (local root)", id=name))
            for name in store.search_concepts(self._outline, event.value):
                if name != self._concept and name not in self._extra:
                    tag = "" if name in self._outline.nodes else "  (frontier)"
                    hits.add_option(Option(escape(name) + tag, id=name))
            if hits.option_count:
                hits.highlighted = 0

    def _chosen(self) -> str | None:
        hits = self.query_one("#hits", OptionList)
        if hits.highlighted is None:
            return None
        return hits.get_option_at_index(hits.highlighted).id

    @on(Input.Submitted, "#q")
    def _submitted(self) -> None:
        self.dismiss(self._chosen())

    @on(OptionList.OptionSelected, "#hits")
    def _selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear":
            self.dismiss("")
        else:
            self.dismiss(self._chosen() if event.button.id == "ok" else None)


class TextPrompt(_Modal):
    """One line of text, or None."""

    def __init__(self, title: str, default: str = "", placeholder: str = "") -> None:
        super().__init__()
        self._heading, self._default, self._placeholder = title, default, placeholder

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{escape(self._heading)}[/b]")
            yield Input(value=self._default, placeholder=self._placeholder, id="value")
            with Horizontal():
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#value", Input).focus()

    @on(Input.Submitted, "#value")
    def _submitted(self) -> None:
        self.dismiss(self.query_one("#value", Input).value.strip() or None)

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self.dismiss(self.query_one("#value", Input).value.strip() or None
                     if event.button.id == "ok" else None)


class Chooser(_Modal):
    """Pick one of a few options; returns its id or None."""

    def __init__(self, title: str, options: list[tuple[str, str]]) -> None:
        super().__init__()
        self._heading, self._options = title, options

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]{escape(self._heading)}[/b]")
            yield OptionList(*[Option(escape(label), id=oid) for oid, label in self._options],
                             id="choices")
            with Horizontal():
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        lst = self.query_one("#choices", OptionList)
        lst.highlighted = 0
        lst.focus()

    @on(OptionList.OptionSelected, "#choices")
    def _selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)

    @on(Button.Pressed)
    def _pressed(self) -> None:
        self.dismiss(None)


class ImportDialog(_Modal):
    """A local path or an https URL of an llms file to bring into the store."""

    def __init__(self, concept: str | None) -> None:
        super().__init__()
        self._concept = concept

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[b]Import an llms file[/b]"
                        + (f"  [dim]attach to {escape(self._concept)}[/dim]"
                           if self._concept else ""))
            yield Input(placeholder="~/path/to/llms.txt  or  https://host/llms-full.txt", id="src")
            yield Static("Saved under $LLMSX_HOME/imports/<host or folder>/ and listed in the "
                         "Library (L). Only llms*.txt and *_llms.md names; 50 MB max.",
                         classes="hint")
            with Horizontal():
                yield Button("Import", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#src", Input).focus()

    @on(Input.Submitted, "#src")
    def _submitted(self) -> None:
        self.dismiss(self.query_one("#src", Input).value.strip() or None)

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self.dismiss(self.query_one("#src", Input).value.strip() or None
                     if event.button.id == "ok" else None)


PANELS: tuple[tuple[str, str], ...] = (
    ("outline", "Outline (left pane)"),
    ("detail", "Detail tabs (right pane)"),
    ("status", "Status line"),
    ("footer", "Key footer"),
    ("tab-facts", "Facts tab"),
    ("tab-skill", "Skill tab"),
    ("tab-references", "Reference tabs"),
    ("tab-llms", "llms-family tabs"),
)


def panel_config(cfg: dict) -> dict[str, bool]:
    raw = cfg.get("panels") if isinstance(cfg.get("panels"), dict) else {}
    return {key: bool(raw.get(key, True)) for key, _label in PANELS}


class PanelSettings(_Modal):
    """Show or hide each window; stored under `panels` in config.json."""

    def __init__(self, current: dict[str, bool]) -> None:
        super().__init__()
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[b]Windows[/b]  [dim]untick to hide[/dim]")
            for key, label in PANELS:
                yield Checkbox(label, value=self._current.get(key, True), id=f"panel-{key}")
            with Horizontal():
                yield Button("Save", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "ok":
            self.dismiss(None)
            return
        self.dismiss({key: self.query_one(f"#panel-{key}", Checkbox).value for key, _ in PANELS})


# --------------------------------------------------------------------------- #
# the skill runner

class SkillRunner(_Modal):
    """Pick a skill and a target; returns (skill, target) or None."""

    def __init__(self, default_target: str, have_claude: bool) -> None:
        super().__init__()
        self._default, self._have_claude = default_target, have_claude

    def compose(self) -> ComposeResult:
        options = [(f"{label}  [{kind}]", sid)
                   for sid, (label, kind, _t) in store.SKILL_RUNS.items()]
        with Vertical():
            yield Label("[b]Run a skill with claude -p[/b]")
            if not self._have_claude:
                yield Static("claude CLI not found on PATH — nothing can run from here.",
                             classes="hint")
            yield Select(options, value="dr", id="skill", allow_blank=False)
            yield Label("target — a concept name, an https URL, a file or folder, or a skill id")
            yield Input(self._default, id="target")
            yield Static("One job per confirmation; the TUI suspends while it runs. Research "
                         "skills update concept-tree/tree.json, which is validated afterwards.",
                         classes="hint")
            with Horizontal():
                yield Button("Run", id="ok", variant="primary", disabled=not self._have_claude)
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#target", Input).focus()

    def _ok(self) -> None:
        self.dismiss((str(self.query_one("#skill", Select).value),
                      self.query_one("#target", Input).value.strip()))

    @on(Input.Submitted, "#target")
    def _submitted(self) -> None:
        if self._have_claude:
            self._ok()

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        self._ok() if event.button.id == "ok" else self.dismiss(None)


# --------------------------------------------------------------------------- #
# the ledger screen

class Ledger(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back"), Binding("q", "app.pop_screen", "Back")]
    DEFAULT_CSS = """
    Ledger #ledger-controls { height: auto; padding: 0 1; }
    Ledger #ledger-body { height: 1fr; padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="ledger-controls"):
            yield Select([(f"last {d} days", d) for d in (1, 7, 30, 90, 365)], value=30,
                         id="days", allow_blank=False)
            yield Select([(k, k) for k in ("file", "kind", "project", "via", "path")], value="file",
                         id="by", allow_blank=False)
        with VerticalScroll(id="ledger-body"):
            yield Markdown("", id="ledger-md")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — access ledger"
        self._render_report()

    @on(Select.Changed)
    def _changed(self) -> None:
        self._render_report()

    def _render_report(self) -> None:
        from textual.css.query import NoMatches
        try:
            days = int(self.query_one("#days", Select).value)
            by = str(self.query_one("#by", Select).value)
            md = self.query_one("#ledger-md", Markdown)
        except NoMatches:      # a Select.Changed fired while the screen was still composing
            return
        head = (f"# llms access ledger — last {days} days, by {by}\n\n"
                "Every read of an llms file by an MCP tool, `llmsx concepts serve` or a Claude "
                "Code `Read`; a shell `cat` is not recorded.\n\n")
        md.update(head + store.ledger_report(days, by))


# --------------------------------------------------------------------------- #
# the job log: one running claude job, streamed

@dataclass
class JobState:
    """One `claude -p` job as the app tracks it: the lines shown so far, the
    raw log file, and the cancel flag the worker thread polls."""
    what: str
    log: Path
    lines: list[str] = field(default_factory=list)
    cancel: threading.Event = field(default_factory=threading.Event)
    done: bool = False
    state: str = "running"


class JobLog(Screen):
    """The running (or last) job, one line per event as it happens. Escape
    hides the screen and the job keeps running (`o` brings it back); `x`
    cancels the job, which restores the tree snapshot."""
    BINDINGS = [Binding("escape", "app.pop_screen", "Hide (job keeps running)"),
                Binding("q", "app.pop_screen", "Hide", show=False),
                Binding("x", "cancel_job", "Cancel job")]
    DEFAULT_CSS = """
    JobLog #job-head { height: auto; padding: 0 1; color: $text-muted; }
    JobLog #job-log { height: 1fr; padding: 0 1; }
    """

    def __init__(self, job: JobState) -> None:
        super().__init__()
        self.job = job

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="job-head")
        yield RichLog(id="job-log", wrap=True, markup=False, highlight=False, auto_scroll=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — job"
        log = self.query_one("#job-log", RichLog)
        for line in self.job.lines:
            log.write(line)
        self.refresh_head()

    def append(self, line: str) -> None:
        self.query_one("#job-log", RichLog).write(line)

    def refresh_head(self) -> None:
        j = self.job
        if not j.done:
            state = "cancelling…" if j.cancel.is_set() else "running (escape hides, x cancels)"
        else:
            state = j.state
        self.query_one("#job-head", Static).update(Text(f"{j.what} — {state} · log: {j.log}"))

    def action_cancel_job(self) -> None:
        if not self.job.done:
            self.job.cancel.set()
        self.refresh_head()


# --------------------------------------------------------------------------- #
# the library screen

class Library(Screen):
    """Directory · Blog · Skills · Imports, each a table with a preview."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back"), Binding("q", "app.pop_screen", "Back"),
                Binding("b", "bundle", "Bundle ±"), Binding("d", "delete_import", "Remove import",
                                                             show=False)]
    DEFAULT_CSS = """
    Library #lib-left { width: 48%; min-width: 40; }
    Library #lib-right { width: 1fr; padding: 0 1; }
    Library DataTable { height: 1fr; }
    Library #lib-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, repo: Path, on_bundle: Callable[[Path, str, str], str]) -> None:
        super().__init__()
        self.repo = repo
        self._on_bundle = on_bundle
        self._rows: dict[str, dict[str, dict]] = {}
        self._current: tuple[Path, str, str] | None = None   # (path, kind, label)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="lib-left"), TabbedContent(id="lib-tabs"):
                with TabPane("Directory", id="lib-directory"):
                    yield DataTable(id="tbl-directory", cursor_type="row")
                with TabPane("Blog", id="lib-blog"):
                    yield DataTable(id="tbl-blog", cursor_type="row")
                with TabPane("Skills", id="lib-skills"):
                    yield DataTable(id="tbl-skills", cursor_type="row")
                with TabPane("Imports", id="lib-imports"):
                    yield DataTable(id="tbl-imports", cursor_type="row")
            with VerticalScroll(id="lib-right"):
                yield Markdown("_select a row_", id="lib-md")
        yield Static("", id="lib-status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — library"
        self._status("reading the directory, posts, skills and imports…")
        app, repo = self.app, self.repo

        def work() -> None:      # the file walks happen off the event loop
            data = {"directory": store.directory_sites(repo),
                    "blog": store.content_pages(repo, "blog"),
                    "skills": store.skill_pages(repo),
                    "imports": store.import_catalog()}
            app.call_from_thread(self._fill_tables, data)
        app.run_worker(work, thread=True, group="library", exclusive=True)

    def _status(self, text: str) -> None:
        self.query_one("#lib-status", Static).update(Text(text))

    def _fill_tables(self, data: dict | None = None) -> None:
        if data is None:
            data = {"directory": store.directory_sites(self.repo),
                    "blog": store.content_pages(self.repo, "blog"),
                    "skills": store.skill_pages(self.repo),
                    "imports": store.import_catalog()}
        t = self.query_one("#tbl-directory", DataTable)
        t.clear(columns=True)
        t.add_columns("grade", "score", "pages", "site")
        self._rows["directory"] = {}
        for s in data["directory"]:
            key = str(s["key"])
            self._rows["directory"][key] = s
            t.add_row(str(s.get("grade", "")), str(s.get("score", "")), str(s.get("pages", "")),
                      str(s.get("name") or key), key=key)
        t = self.query_one("#tbl-blog", DataTable)
        t.clear(columns=True)
        t.add_columns("date", "title")
        self._rows["blog"] = {}
        for e in data["blog"]:
            self._rows["blog"][e["id"]] = e
            t.add_row(e["date"], e["title"], key=e["id"])
        t = self.query_one("#tbl-skills", DataTable)
        t.clear(columns=True)
        t.add_columns("skill", "title")
        self._rows["skills"] = {}
        for e in data["skills"]:
            self._rows["skills"][e["id"]] = e
            t.add_row(e["id"], e["title"], key=e["id"])
        t = self.query_one("#tbl-imports", DataTable)
        t.clear(columns=True)
        t.add_columns("imported", "kind", "source")
        self._rows["imports"] = {}
        for e in data["imports"]:
            self._rows["imports"][e["path"]] = e
            t.add_row(str(e.get("imported", ""))[:10], str(e.get("kind", "")),
                      str(e.get("source", ""))[:60], key=e["path"])
        counts = {k: len(v) for k, v in self._rows.items()}
        self._status(f"{counts['directory']} sites · {counts['blog']} posts · "
                     f"{counts['skills']} skills · {counts['imports']} imports")

    @on(DataTable.RowHighlighted)
    def _highlight(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        self._show(event.data_table.id or "", str(event.row_key.value))

    def _show(self, table_id: str, key: str) -> None:
        md = self.query_one("#lib-md", Markdown)
        self._current = None
        if table_id == "tbl-directory":
            s = self._rows["directory"].get(key) or {}
            f = store.mirror_file(key)
            head = (f"# {store.md_escape(s.get('name') or key)}\n\n"
                    f"- grade **{store.md_escape(s.get('grade', '?'))}** · "
                    f"score {s.get('score', '?')} "
                    f"· {s.get('pages', '?')} pages · {s.get('category', '')}\n"
                    f"- {store.md_escape(s.get('url', ''))}\n\n")
            if f:
                self._current = (f, "llms", str(s.get("name") or key))
                md.update(head + "---\n\n" + read_preview(f))
            else:
                md.update(head + "_the mirrored llms-full.txt is not on this box (hub only); "
                                 "the URL above serves it_")
        elif table_id == "tbl-blog":
            e = self._rows["blog"].get(key)
            if e:
                self._current = (e["path"], "reference", e["title"])
                md.update(read_preview(e["path"]))
        elif table_id == "tbl-skills":
            e = self._rows["skills"].get(key)
            if e:
                self._current = (e["path"], "skill", e["id"])
                md.update(read_preview(e["path"]))
        elif table_id == "tbl-imports":
            e = self._rows["imports"].get(key)
            if e:
                p = Path(e["path"])
                self._current = (p, "llms", e.get("concept") or p.stem)
                src = store.md_escape(e.get("source", ""))
                md.update(f"_imported {e.get('imported', '')} from {src}_\n\n---\n\n"
                          + read_preview(p))

    def action_bundle(self) -> None:
        if not self._current:
            self._status("select a row with a file behind it first")
            return
        path, kind, label = self._current
        self._status(self._on_bundle(path, kind, label))

    def action_delete_import(self) -> None:
        if not self._current or self.query_one("#lib-tabs", TabbedContent).active != "lib-imports":
            self._status("open the Imports tab and select an import to remove")
            return
        if store.remove_import(str(self._current[0])):
            self._status(f"removed import {self._current[0]}")
            self._fill_tables()


# --------------------------------------------------------------------------- #
# capture: braindump and journal

class Braindump(Screen):
    """A place to dump; ctrl+s saves the text verbatim (through the braindump
    skill's own script when it is on this box), then `p` parses the saved
    dump with the braindump skill via claude -p."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back"), Binding("ctrl+s", "save", "Save dump"),
                Binding("ctrl+p", "parse", "Parse with the braindump skill")]
    DEFAULT_CSS = """
    Braindump #dump { height: 1fr; }
    Braindump #dump-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, on_parse: Callable[[Path], None]) -> None:
        super().__init__()
        self._on_parse = on_parse
        self._saved: Path | None = None

    def compose(self) -> ComposeResult:
        from textual.widgets import TextArea
        yield Header()
        yield Static("Dump what is in your head. ctrl+s saves it verbatim; ctrl+p runs the "
                     "braindump skill on the saved dump (categorised llms files + to-do items).",
                     classes="hint")
        yield TextArea("", id="dump")
        yield Static("", id="dump-status")
        yield Footer()

    def on_mount(self) -> None:
        from textual.widgets import TextArea
        self.title = "llmsx explorer — braindump"
        self.query_one("#dump", TextArea).focus()

    def _status(self, text: str) -> None:
        self.query_one("#dump-status", Static).update(Text(text))

    def action_save(self, then_parse: bool = False) -> None:
        """Save in a thread: the braindump script can take seconds."""
        from textual.widgets import TextArea
        text = self.query_one("#dump", TextArea).text
        if not text.strip():
            self._status("nothing to save")
            return
        app = self.app
        self._status("saving…")

        def work() -> None:
            try:
                saved, how = store.save_braindump(text)
            except (ValueError, OSError, subprocess.SubprocessError) as exc:
                app.call_from_thread(self._status, f"not saved: {exc}")
                return
            app.call_from_thread(self._saved_ok, saved, how, then_parse)
        app.run_worker(work, thread=True, group="braindump", exclusive=True)

    def _saved_ok(self, saved: Path, how: str, then_parse: bool) -> None:
        self._saved = saved
        self._status(f"saved via {how}: {saved}  (ctrl+p to parse)")
        if then_parse:
            self._on_parse(saved)

    def action_parse(self) -> None:
        if self._saved is None:
            self.action_save(then_parse=True)
            return
        self._on_parse(self._saved)


class Journal(Screen):
    """Dated entries under $LLMSX_HOME/journal/; today's on the right."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back"), Binding("ctrl+s", "save", "Save"),
                Binding("ctrl+n", "today", "Today"),
                Binding("ctrl+p", "to_llms", "Journal → llms family")]
    DEFAULT_CSS = """
    Journal #jr-left { width: 24; }
    Journal #jr-list { height: 1fr; }
    Journal #jr-text { height: 1fr; }
    Journal #jr-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, on_to_llms: Callable[[Path], None]) -> None:
        super().__init__()
        self._on_to_llms = on_to_llms
        self._date = ""

    def compose(self) -> ComposeResult:
        from textual.widgets import TextArea
        yield Header()
        with Horizontal():
            with Vertical(id="jr-left"):
                yield OptionList(id="jr-list")
            with Vertical():
                yield Label("", id="jr-date")
                yield TextArea("", id="jr-text")
        yield Static("", id="jr-status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — journal"
        self._refresh_list()
        self.action_today()

    def _status(self, text: str) -> None:
        self.query_one("#jr-status", Static).update(Text(text))

    def _refresh_list(self) -> None:
        lst = self.query_one("#jr-list", OptionList)
        lst.clear_options()
        for d in store.journal_entries():
            lst.add_option(Option(d, id=d))

    def _open(self, date: str) -> None:
        from textual.widgets import TextArea
        self._date = date
        self.query_one("#jr-date", Label).update(
            f"[b]{date}[/b]  [dim]{store.journal_path(date)}[/dim]")
        self.query_one("#jr-text", TextArea).text = store.read_journal(date)
        self.query_one("#jr-text", TextArea).focus()

    def action_today(self) -> None:
        from datetime import UTC, datetime
        self._open(datetime.now(UTC).date().isoformat())

    @on(OptionList.OptionSelected, "#jr-list")
    def _pick(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:
            self._open(event.option.id)

    def action_save(self) -> None:
        from textual.widgets import TextArea
        if not self._date:
            return
        try:
            p = store.save_journal(self._date, self.query_one("#jr-text", TextArea).text)
        except (ValueError, OSError) as exc:
            self._status(f"not saved: {exc}")
            return
        self._refresh_list()
        self._status(f"saved {p}")

    def action_to_llms(self) -> None:
        self.action_save()
        self._on_to_llms(store.journal_dir())



# --------------------------------------------------------------------------- #
# flashcards and quiz

class Flashcards(Screen):
    """Front: the concept name and its parent. Space flips; 1 = got it,
    2 = again. Progress is Leitner boxes in $LLMSX_HOME/flashcards.json."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back"), Binding("space", "flip", "Flip"),
                Binding("1", "grade_right", "Got it"), Binding("2", "grade_wrong", "Again")]
    DEFAULT_CSS = """
    Flashcards #card { height: 1fr; padding: 1 2; }
    Flashcards #fc-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, cards: list[dict]) -> None:
        super().__init__()
        self._all = cards
        self._progress = store.load_progress()
        self._session = int(self._progress.get("_session", {}).get("n", 0)) + 1
        self._queue = store.due_cards([c for c in cards if c["id"] != "_session"],
                                      self._progress, self._session)
        self._shown = False
        self._done = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="card"):
            yield Markdown("", id="fc-md")
        yield Static("", id="fc-status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — flashcards"
        self._show()

    def _current(self) -> dict | None:
        return self._queue[0] if self._queue else None

    def _show(self) -> None:
        c = self._current()
        md = self.query_one("#fc-md", Markdown)
        if not c:
            md.update(f"# Done\n\n{self._done} card(s) reviewed this session. "
                      "Nothing else is due; come back later.")
            self.query_one("#fc-status", Static).update(Text("esc to go back"))
            return
        hint = f"\n\n_under {store.md_escape(c['hint'])}_" if c["hint"] else ""
        tags = (" · " + " ".join(f"#{t}" for t in c["tags"])) if c["tags"] else ""
        if not self._shown:
            md.update(f"# {store.md_escape(c['front'])}{hint}\n\n---\n\n_space to flip_")
        else:
            facts = "".join(f"- {store.md_escape(f)}\n" for f in c["facts"])
            md.update(f"# {store.md_escape(c['front'])}{hint}\n\n{store.md_escape(c['back'])}\n\n"
                      f"{facts}\n---\n\n_1 = got it · 2 = again_")
        box = int(self._progress.get(c["id"], {}).get("box", 1))
        self.query_one("#fc-status", Static).update(
            Text(f"{len(self._queue)} due · box {box}/{store.FLASHCARD_BOXES}{tags}"))

    def action_flip(self) -> None:
        if self._current():
            self._shown = not self._shown
            self._show()

    def _grade(self, correct: bool) -> None:
        c = self._current()
        if not c or not self._shown:
            return
        store.grade_card(self._progress, c["id"], correct, self._session)
        self._progress["_session"] = {"n": self._session}
        store.save_progress(self._progress)
        self._queue.pop(0)
        self._done += 1
        self._shown = False
        self._show()

    def action_grade_right(self) -> None:
        self._grade(True)

    def action_grade_wrong(self) -> None:
        self._grade(False)


class Quiz(Screen):
    """Multiple choice: a summary or fact is shown, pick the concept (1-4)."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Back")] + [
        Binding(str(i), f"answer({i})", f"Option {i}", show=False) for i in range(1, 5)]
    DEFAULT_CSS = """
    Quiz #quiz-body { height: 1fr; padding: 1 2; }
    Quiz #quiz-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, cards: list[dict], seed: int | None = None) -> None:
        import random
        super().__init__()
        self._cards = cards
        self._rng = random.Random(seed)
        self._order = list(cards)
        self._rng.shuffle(self._order)
        self._i = 0
        self._score = 0
        self._q: dict | None = None
        self._answered: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="quiz-body"):
            yield Markdown("", id="quiz-md")
        yield Static("", id="quiz-status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — quiz"
        self._next()

    def _next(self) -> None:
        if self._i >= len(self._order):
            self.query_one("#quiz-md", Markdown).update(
                f"# Finished\n\nScore: **{self._score} / {len(self._order)}**\n\n_esc to go back_")
            self._q = None
            return
        self._q = store.quiz_question(self._order[self._i], self._cards, self._rng)
        self._answered = None
        self._render_q()

    def _render_q(self) -> None:
        q = self._q
        if not q:
            return
        lines = [f"# Question {self._i + 1} of {len(self._order)}", "",
                 store.md_escape(q["prompt"]), "", "Which concept is this?", ""]
        for n, opt in enumerate(q["options"], 1):
            mark = ""
            if self._answered is not None:
                if opt == q["answer"]:
                    mark = "  ✓"
                elif opt == self._answered:
                    mark = "  ✗"
            lines.append(f"{n}. {store.md_escape(opt)}{mark}")
        if self._answered is not None:
            lines += ["", "_press any option key for the next question_"]
        self.query_one("#quiz-md", Markdown).update("\n".join(lines))
        self.query_one("#quiz-status", Static).update(Text(f"score {self._score} / {self._i}"))

    def action_answer(self, n: int) -> None:
        q = self._q
        if not q:
            return
        if self._answered is not None:
            self._i += 1
            self._next()
            return
        if n < 1 or n > len(q["options"]):
            return
        self._answered = q["options"][n - 1]
        if self._answered == q["answer"]:
            self._score += 1
        self._render_q()


# --------------------------------------------------------------------------- #
# hotkey cheat sheet
# --------------------------------------------------------------------------- #

class HotkeyHelp(_Modal):
    """The cheat sheet modal that appears when pressing '?'."""

    DEFAULT_CSS = _Modal.DEFAULT_CSS + """
    HotkeyHelp > Vertical { width: 95; max-width: 95%; height: 85%; }
    HotkeyHelp Markdown { padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[b]Keyboard Shortcuts & Explorer Quick Actions[/b]  [dim](press ? or esc to close)[/dim]")
            with VerticalScroll(classes="tall"):
                yield Markdown(self._help_text())
            with Horizontal():
                yield Button("Close (esc)", id="cancel", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#cancel", Button).focus()

    @staticmethod
    def _help_text() -> str:
        return """
### Quick Research Actions & Monitoring
| Action / Key | Function | Description |
| :--- | :--- | :--- |
| **`⚡ /dr`** | Immediate /dr | Start deep research job on selected concept immediately |
| **`+ Queue`** | Add to Queue | Append selected concept to `RESEARCH_QUEUE.md` |
| **`🐇 Rabbithole`** | Rabbithole | Start depth-first exhaustive research (`deep` mode) |
| **`🧭 Concept Explorer`**| Family Explorer | Map semantic concept family around selected subject |
| **`R`** | Research Dialog | Mode picker modal; **Enter submits immediately without closing dropdown** |
| **`u`** | Queue Viewer | Active research queue viewer & real-time live job monitor |
| **`o`** | Job Log | View streamed JSON output of current or latest Claude job |

### Navigation & Outline
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`/`** | Focus Filter | Type to filter concepts and aliases in the outline |
| **`Right / Left`** | Expand / Collapse | Expand or collapse tree node at cursor |
| **`[` / `]`** | Prev / Next Tab | Switch between detail tabs (Overview, Facts, Skill, Highlights, etc.) |
| **`r`** | Reload | Refresh concept tree and local state from disk |
| **`T`** | Cycle Filter | Cycle outline filter: all / frontier / researched / tagged |

### Highlights, Annotations & Curation
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`h`** | Add Highlight | Save selected lines / quote with personal annotation |
| **`H`** | Highlights Manager | Browse, search, copy, or jump to saved concept highlights |
| **`m`** | Mark Review | Mark concept as `needs-review` in `marks.json` |
| **`f`** | Mark Further | Mark concept for further research and auto-queue |
| **`x`** | Clear Mark | Remove mark from concept |
| **`t`** | Tags | Edit comma-separated tags for concept |
| **`l`** | Link | Link related concepts in `tree.json` |
| **`n`** | Notes | Open local notes for concept |
| **`e`** | $EDITOR | Open current file tab in `$EDITOR` |
| **`E`** | Edit Node | Edit summary, aliases, or add child in `tree.json` |

### Learning, Capture & Tools
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`F`** | Flashcards | Spaced repetition flashcards (5-box Leitner system) |
| **`Q`** | Quiz | Multiple-choice quiz generated from concept facts |
| **`W`** | Braindump | Freeform capture screen; parse into llms with `ctrl+p` |
| **`J`** | Journal | Daily dated journaling; compile into context |
| **`L`** | Library | Browse directory, blog, skills, and imports with previews |
| **`G`** | Ledger | View access ledger report across corpus |
| **`S`** | Skills | Launch any installed skill with target |
| **`b` / `B`** | Bundle ± / Export | Add file to bundle; export bundle collection |
| **`X`** | Export Menu | Export concept, branch, file, or bundle as markdown |
| **`s`** | Git Sync | Git pull (`--ff-only`) safely |
| **`c`** | Commit & Push | Stage allow-listed files only, commit and push |
| **`,`** | Settings | Configure repos, push target, and GitHub token |
| **`?`** | Help | Show this keyboard shortcut guide |
| **`q`** | Quit | Exit Explorer |
"""


# --------------------------------------------------------------------------- #
# highlights and annotations
# --------------------------------------------------------------------------- #

class AddHighlight(_Modal):
    """Add a highlight and personal annotation for a concept."""

    BINDINGS = [Binding("escape", "cancel", "Cancel"), Binding("ctrl+s", "save", "Save")]
    DEFAULT_CSS = _Modal.DEFAULT_CSS + """
    AddHighlight > Vertical { height: 80%; width: 90; }
    AddHighlight TextArea { height: 1fr; }
    """

    def __init__(self, concept: str, initial_text: str = "") -> None:
        super().__init__()
        self._concept, self._initial_text = concept, initial_text

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"[b]Add Highlight & Annotation:[/b] {escape(self._concept or 'General')}")
            yield Label("Highlight text / lines to save:")
            yield TextArea(self._initial_text, id="text")
            yield Label("Annotation / notes (optional):")
            yield Input(placeholder="Why this is significant, connections to other ideas...", id="note")
            with Horizontal():
                yield Button("Save Highlight (ctrl+s)", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#text", TextArea).focus()

    def action_save(self) -> None:
        text = self.query_one("#text", TextArea).text.strip()
        note = self.query_one("#note", Input).value.strip()
        if not text:
            return
        self.dismiss((text, note))

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.action_save()
        else:
            self.dismiss(None)


class HighlightsScreen(Screen):
    """Browse and manage all saved highlights and annotations across concepts."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("q", "app.pop_screen", "Back", show=False),
        Binding("enter", "jump_to_concept", "Jump to Concept"),
        Binding("d", "delete_highlight", "Delete Highlight"),
        Binding("c", "copy_highlight", "Copy Quote"),
    ]
    DEFAULT_CSS = """
    HighlightsScreen #hl-left { width: 45%; min-width: 35; }
    HighlightsScreen #hl-right { width: 1fr; padding: 0 1; }
    HighlightsScreen DataTable { height: 1fr; }
    HighlightsScreen #hl-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, on_jump: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self._on_jump = on_jump
        self._highlights: list[dict] = []
        self._selected_hl: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="hl-left"):
                yield DataTable(id="hl-table", cursor_type="row")
            with VerticalScroll(id="hl-right"):
                yield Markdown("_select a highlight to view details_", id="hl-md")
        yield Static("", id="hl-status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — highlights & annotations"
        self._refresh_list()

    def _refresh_list(self) -> None:
        self._highlights = store.load_highlights()
        table = self.query_one("#hl-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Date", "Concept", "Snippet")
        for h in self._highlights:
            date_str = str(h.get("created_at", ""))[:10]
            concept = h.get("concept", "General")
            snippet = " ".join(h.get("text", "").split())[:45]
            table.add_row(date_str, concept, snippet, key=h.get("id"))
        self._status(f"{len(self._highlights)} highlight(s) saved · press 'd' to delete, 'enter' to jump, 'c' to copy")

    def _status(self, text: str) -> None:
        self.query_one("#hl-status", Static).update(Text(text))

    @on(DataTable.RowHighlighted)
    def _highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        hl_id = str(event.row_key.value)
        self._selected_hl = next((h for h in self._highlights if h.get("id") == hl_id), None)
        if self._selected_hl:
            self._render_selected(self._selected_hl)

    def _render_selected(self, h: dict) -> None:
        md = self.query_one("#hl-md", Markdown)
        c_name = h.get("concept", "General")
        stamp = h.get("created_at", "")
        lines = [f"# {store.md_escape(c_name)}", f"**Saved:** `{stamp}` · [Jump to concept](concept:{store.slugify(c_name)})\n", "---", ""]
        for line in h.get("text", "").splitlines():
            lines.append(f"> {store.md_escape(line)}")
        if h.get("note"):
            lines.append(f"\n### Annotation / Notes\n{store.md_escape(h['note'])}\n")
        lines.append("\n---\n_Press `enter` to jump to this concept in the tree, `c` to copy quote, `d` to delete._")
        md.update("\n".join(lines))

    def action_jump_to_concept(self) -> None:
        if not self._selected_hl or not self._on_jump:
            return
        concept = self._selected_hl.get("concept")
        if concept:
            self.app.pop_screen()
            self._on_jump(concept)

    def action_delete_highlight(self) -> None:
        if not self._selected_hl:
            return
        hl_id = self._selected_hl.get("id", "")
        if store.remove_highlight(hl_id):
            self._status(f"removed highlight {hl_id}")
            self._refresh_list()

    def action_copy_highlight(self) -> None:
        if not self._selected_hl:
            return
        quote = self._selected_hl.get("text", "")
        store.copy_to_clipboard(quote)
        self._status("copied highlight quote to clipboard")


# --------------------------------------------------------------------------- #
# active research queue viewer & monitor
# --------------------------------------------------------------------------- #

class QueueViewer(Screen):
    """View the research queue, monitor active jobs in real-time, and manage queue items."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("q", "app.pop_screen", "Back", show=False),
        Binding("r", "run_selected", "Run selected"),
        Binding("a", "add_item", "Add concept"),
        Binding("x", "cancel_job", "Cancel job"),
        Binding("o", "open_job_log", "Job log"),
        Binding("R", "refresh", "Refresh"),
    ]
    DEFAULT_CSS = """
    QueueViewer #qv-head { height: auto; padding: 0 1; background: $surface; }
    QueueViewer #qv-active-box { height: auto; max-height: 10; border: round $primary; padding: 0 1; margin: 0 1; }
    QueueViewer #qv-active-log { height: 6; }
    QueueViewer #qv-table-container { height: 1fr; padding: 0 1; }
    QueueViewer DataTable { height: 1fr; }
    QueueViewer #qv-buttons { height: auto; padding: 0 1; }
    QueueViewer #qv-buttons Button { margin-right: 1; }
    QueueViewer #qv-status { height: auto; padding: 0 1; color: $text-muted; }
    """

    def __init__(self, repo: Path, get_job: Callable[[], JobState | None],
                 on_run: Callable[[str, str, str | None], None],
                 on_job_screen: Callable[[JobState], None]) -> None:
        super().__init__()
        self.repo = repo
        self._get_job = get_job
        self._on_run = on_run
        self._on_job_screen = on_job_screen
        self._items: list[dict] = []
        self._selected_item: dict | None = None
        self._timer = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="qv-head"):
            yield Label("[b]Active Job & Research Queue[/b]", id="qv-title")
            with Vertical(id="qv-active-box"):
                yield Static("", id="qv-active-status")
                yield RichLog(id="qv-active-log", wrap=True, markup=False, highlight=False, auto_scroll=True)
        with Horizontal(id="qv-buttons"):
            yield Button("▶ Run Selected (r)", id="btn-qv-run", variant="primary")
            yield Button("+ Add Concept (a)", id="btn-qv-add")
            yield Button("📜 Job Log (o)", id="btn-qv-log")
            yield Button("⏹ Cancel Job (x)", id="btn-qv-cancel", variant="error")
            yield Button("🔄 Refresh (R)", id="btn-qv-refresh")
            yield Button("Back (esc)", id="btn-qv-back")
        with Vertical(id="qv-table-container"):
            yield DataTable(id="qv-table", cursor_type="row")
        yield Static("", id="qv-status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer — research queue & monitor"
        self._refresh_all()
        self._timer = self.set_interval(1.0, self._refresh_live)

    def _refresh_all(self) -> None:
        self._refresh_queue()
        self._refresh_live()

    def _refresh_queue(self) -> None:
        self._items = store.load_queue(self.repo)
        table = self.query_one("#qv-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Status", "Concept", "Parent", "Mode")
        for item in self._items:
            status = "✓ Done" if item.get("done") else "⏳ Pending"
            concept = item.get("concept", "")
            parent = item.get("parent") or "—"
            mode = item.get("mode") or "dr"
            table.add_row(status, concept, parent, mode, key=concept)
        pending = sum(1 for i in self._items if not i.get("done"))
        done = sum(1 for i in self._items if i.get("done"))
        self._status(f"{len(self._items)} queued item(s) ({pending} pending, {done} done)")

    def _refresh_live(self) -> None:
        job = self._get_job()
        status_lbl = self.query_one("#qv-active-status", Static)
        log_widget = self.query_one("#qv-active-log", RichLog)
        cancel_btn = self.query_one("#btn-qv-cancel", Button)
        if job is None:
            status_lbl.update(Text("No research job has been launched this session.", style="dim"))
            cancel_btn.disabled = True
            return
        if not job.done:
            status_lbl.update(Text.assemble(
                ("RUNNING: ", "bold green"),
                (f"{job.what}  ", "bold"),
                (f"(log: {job.log})", "dim")
            ))
            cancel_btn.disabled = False
        else:
            style = "bold cyan" if job.state == "ok" else "bold yellow"
            status_lbl.update(Text.assemble(
                (f"COMPLETED ({job.state}): ", style),
                (f"{job.what}  ", "bold"),
                (f"(log: {job.log})", "dim")
            ))
            cancel_btn.disabled = True
        log_widget.clear()
        for line in job.lines[-6:]:
            log_widget.write(line)

    def _status(self, text: str) -> None:
        self.query_one("#qv-status", Static).update(Text(text))

    @on(DataTable.RowHighlighted)
    def _row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        concept = str(event.row_key.value)
        self._selected_item = next((i for i in self._items if i.get("concept") == concept), None)

    def action_run_selected(self) -> None:
        if not self._selected_item:
            self._status("select a queue item to run")
            return
        concept = self._selected_item["concept"]
        mode = self._selected_item.get("mode") or "dr"
        parent = self._selected_item.get("parent")
        self._on_run(concept, mode, parent)

    def action_add_item(self) -> None:
        def done(name: str | None) -> None:
            if not name:
                return
            try:
                added = store.queue_concept(self.repo, name, None, "dr")
                self._refresh_queue()
                self._status(f"queued {name}" if added else f"already queued: {name}")
            except Exception as exc:
                self._status(f"error queuing: {exc}")
        self.app.push_screen(TextPrompt("Add Concept to Research Queue", "", "Concept name"), done)

    def action_cancel_job(self) -> None:
        job = self._get_job()
        if job and not job.done:
            job.cancel.set()
            self._status("cancellation requested...")
            self._refresh_live()

    def action_open_job_log(self) -> None:
        job = self._get_job()
        if job:
            self._on_job_screen(job)
        else:
            self._status("no job log to view")

    def action_refresh(self) -> None:
        self._refresh_all()
        self._status("queue refreshed")

    @on(Button.Pressed)
    def _button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-qv-run":
            self.action_run_selected()
        elif event.button.id == "btn-qv-add":
            self.action_add_item()
        elif event.button.id == "btn-qv-log":
            self.action_open_job_log()
        elif event.button.id == "btn-qv-cancel":
            self.action_cancel_job()
        elif event.button.id == "btn-qv-refresh":
            self.action_refresh()
        elif event.button.id == "btn-qv-back":
            self.app.pop_screen()


"""app.py — the hub-manager Textual application.

Tabs:
  Queue    pipeline queue table; add/retry/delete items; start/stop manager
  Health   one-shot + auto-refreshed subsystem checks
  Concepts concept tree: click a node for its skill/research/related/indexes;
           greyed nodes are known frontier points nobody has researched yet
  Docsets  indexed docsets; click a row for its detail + source file;
           semantic / fuzzy / regex search against the selected one
  Index    semantically index a mirror file into a docset; manage watch dirs
  MCP      server status, tool inventory, env config; launch HTTP transport
  Scripts  run any hub script with args, streamed output
  Logs     tail the hub log files
  Settings persisted hub-manager options

Keys: q quit · r refresh current tab. Per-tab keys shown in-tab.
"""

from __future__ import annotations

import argparse
import json
import os
import time

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (Button, DataTable, Footer, Header, Input, Label,
                             RichLog, Select, Static, TabbedContent, TabPane,
                             Tree)

from . import (ask_client, core, docsets, doctor, health, llms_full, mcp_demo, queue_model,
               remotes, runner, scripts_registry, settings, usage)
from . import __version__

STATUS_STYLE = {
    "done": "green", "running": "yellow", "pending": "cyan", "failed": "red",
}
HEALTH_REFRESH_SECS = 30
JOB_FLUSH_SECS = 0.5  # batch cadence for streaming subprocess output


def styled(text: str, style: str) -> str:
    return f"[{style}]{text}[/{style}]"


def _coverage_line() -> str:
    """Knowledge-gap one-liner from ask history (semantic_ops.coverage).

    Runs in-process: it reads a jsonl file and (only when gaps exist) embeds a
    handful of short queries — cheap next to the transcript scan it renders
    beside. Never raises into the UI."""
    try:
        from semantic_ops import coverage
        return coverage.summary_line()
    except Exception as exc:  # noqa: BLE001 — a status line must never crash the tab
        return f"coverage: unavailable ({exc})"


# --------------------------------------------------------------------------- #
# modals
# --------------------------------------------------------------------------- #

class PromptScreen(ModalScreen[str | None]):
    """One-line text prompt; dismisses with the value or None."""

    CSS = """
    PromptScreen { align: center middle; }
    #prompt-box { width: 80; height: auto; border: round $accent;
                  background: $surface; padding: 1 2; }
    """

    def __init__(self, title: str, placeholder: str = "", value: str = ""):
        super().__init__()
        self._title, self._placeholder, self._value = title, placeholder, value

    def compose(self) -> ComposeResult:
        with Vertical(id="prompt-box"):
            yield Label(self._title)
            yield Input(value=self._value, placeholder=self._placeholder,
                        id="prompt-input")
            yield Label("[dim]Enter = OK · Esc = cancel[/dim]")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    @on(Input.Submitted, "#prompt-input")
    def _submit(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)

    def key_escape(self) -> None:
        self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    CSS = """
    ConfirmScreen { align: center middle; }
    #confirm-box { width: 70; height: auto; border: round $error;
                   background: $surface; padding: 1 2; }
    #confirm-buttons { height: auto; align-horizontal: center; }
    """

    def __init__(self, question: str):
        super().__init__()
        self._question = question

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(self._question)
            with Horizontal(id="confirm-buttons"):
                yield Button("Yes", variant="error", id="confirm-yes")
                yield Button("No", variant="primary", id="confirm-no")

    @on(Button.Pressed, "#confirm-yes")
    def _yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#confirm-no")
    def _no(self) -> None:
        self.dismiss(False)

    def key_escape(self) -> None:
        self.dismiss(False)


class ItemDetailScreen(ModalScreen[None]):
    """Queue-row expand: stage checklist, per-box shard evidence, time
    budget, and box/Ollama health for one queue item. Content streams in via
    update_text() once the background worker finishes -- opens immediately
    with a loading placeholder rather than blocking the UI thread."""

    CSS = """
    ItemDetailScreen { align: center middle; }
    #detail-box { width: 90%; height: 85%; border: round $accent;
                  background: $surface; padding: 1 2; }
    #detail-body { height: 1fr; }
    """

    def __init__(self, title: str):
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="detail-box"):
            yield Label(self._title)
            with VerticalScroll(id="detail-body"):
                yield Static("Loading…", id="detail-text")
            yield Label("[dim]Esc / Enter = close[/dim]")

    def update_text(self, text: str) -> None:
        self.query_one("#detail-text", Static).update(text)

    def key_escape(self) -> None:
        self.dismiss(None)

    def key_enter(self) -> None:
        self.dismiss(None)


# --------------------------------------------------------------------------- #
# app
# --------------------------------------------------------------------------- #

def _box_quiet(host: str) -> bool:
    """Is this box inside its quiet window right now (box_schedule)?"""
    try:
        import box_schedule
        return bool(host) and box_schedule.is_quiet(host)
    except Exception:  # noqa: BLE001
        return False


class HubManagerApp(App):
    TITLE = f"hub-manager v{__version__} — Global AI Hub"
    CSS = """
    #queue-table, #health-table, #docsets-table, #llmsfull-table { height: 1fr; }
    .pane-log { height: 1fr; border: round $primary; }
    .row-inputs { height: auto; }
    .row-inputs Input { width: 1fr; }
    .hint { color: $text-muted; height: auto; }
    #concept-tree { height: 1fr; border: round $primary; }
    #research-mode { width: 42; }
    #docset-mode { width: 16; }
    #docset-search { width: auto; }
    #llmsfull-status { width: 14; }
    #llmsfull-mode { width: 12; }
    #llmsfull-search { width: auto; }
    #settings-form { height: auto; }
    #settings-form Input { width: 40; }
    .setting-label { padding-top: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("a", "add_url", "Add site", show=False),
        Binding("s", "start_manager", "Start pipeline", show=False),
        Binding("x", "stop_manager", "Stop pipeline", show=False),
        Binding("f", "retry_failed", "Retry failed", show=False),
        Binding("e", "retry_item", "Requeue row", show=False),
        Binding("d", "delete_item", "Delete row", show=False),
        Binding("c", "recrawl_item", "Recrawl row", show=False),
        Binding("C", "recrawl_all", "Recrawl all done", show=False),
        Binding("g", "diagnose_check", "Diagnose", show=False),
        Binding("t", "remediate_check", "Start/fix", show=False),
        Binding("k", "stop_check", "Stop", show=False),
        Binding("u", "restore_checks", "Restore checks", show=False),
        Binding("Q", "toggle_quiet_hours", "Quiet hours on/off", show=False),
        Binding("question_mark", "script_help", "Script docs", show=False),
        Binding("K", "kill_remote_pid", "Kill remote PID", show=False),
        Binding("D", "weekly_digest", "Weekly digest", show=False),
        Binding("ctrl+p", "tool_palette", "Which tool?", show=False),
        Binding("o", "cycle_sort", "Sort by", show=False),
        Binding("O", "reverse_sort", "Reverse sort", show=False),
        Binding("slash", "focus_filter", "Filter", show=False),
        Binding("n", "queue_concept", "Queue concept for research", show=False),
        Binding("R", "launch_research", "Launch research on concept", show=False),
        Binding("p", "polish_docset", "Polish facts (Claude)", show=False),
        Binding("i", "index_llms_full", "Index llms-full as docset", show=False),
        Binding("v", "edit_llms_full", "Edit llms-full in $EDITOR", show=False),
        Binding("w", "discover_directories", "Discover llms-full directories", show=False),
    ]

    QUEUE_SORTS = ("status", "url", "updated")
    DOCSET_SORTS = ("docset", "pages", "chunks", "updated")
    LLMSFULL_SORTS = llms_full.SORTS

    def __init__(self):
        super().__init__()
        self.settings = settings.load()
        self.jobs: dict[str, runner.ProcJob] = {}
        self.job_logs: dict[str, RichLog] = {}
        self._log_state: tuple | None = None  # (name, mtime, size) last shown
        self._ext_api_up = False  # probed in the health worker, shown in queue
        self._usage_scanned = False  # transcript scan runs on first tab entry
        self._script_help_cache: dict[str, tuple[str, str]] = {}
        self._remotes_scanned = False
        self._repos_scanned = False
        self._repos_cache: dict[str, object] = {}  # label -> RepoStatus, for clean action
        self._remotes_repos: dict[str, object] = {}  # host -> RepoStatus, for clean action
        self._queue_sort = 0  # index into QUEUE_SORTS
        self._queue_sort_rev = False
        self._docset_sort = 0  # index into DOCSET_SORTS
        self._docset_sort_rev = False
        self._docsets_cache: list[dict] = []  # last-fetched entries, re-filtered/sorted locally
        self._llmsfull_sort = 0  # index into LLMSFULL_SORTS
        self._llmsfull_sort_rev = False
        self._llmsfull_cache: list[dict] = []
        self._jobs_settled: set[str] = set()  # job slots whose exit was already acted on
        self._job_chains: dict[str, list[list[str]]] = {}  # slot -> argvs still to run

    # ------------------------------------------------------------------ #
    # layout
    # ------------------------------------------------------------------ #

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab-queue"):
            with TabPane("Queue", id="tab-queue"):
                yield Static("", id="queue-summary", classes="hint")
                yield DataTable(id="queue-table", cursor_type="row",
                                zebra_stripes=True)
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="filter by url/status/machine… "
                                "([b]/[/b] to focus)", id="queue-filter")
                yield Static(
                    "[b]a[/b] add site · [b]s[/b] start pipeline · [b]x[/b] stop"
                    " · [b]f[/b] retry all failed · [b]e[/b] requeue row"
                    " · [b]d[/b] delete row · [b]c[/b] recrawl row"
                    " · [b]C[/b] recrawl ALL done (2nd round) · [b]o[/b]/[b]O[/b] sort"
                    " · [b]/[/b] filter · [b]r[/b] refresh",
                    classes="hint")
            with TabPane("Health", id="tab-health"):
                yield DataTable(id="health-table", cursor_type="row",
                                zebra_stripes=True)
                yield Static(
                    f"[b]g[/b] diagnose row · [b]t[/b] start/fix"
                    " · [b]k[/b] stop · [b]x[/b] disable check"
                    " · [b]u[/b] restore disabled · [b]r[/b] re-run "
                    f"(auto every {HEALTH_REFRESH_SECS}s)", classes="hint")
                yield RichLog(id="health-log", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("Concepts", id="tab-concepts"):
                yield Tree("concept tree", id="concept-tree")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="filter concepts… (only matching "
                                "branches are shown)", id="concept-filter")
                with Horizontal(classes="row-inputs"):
                    yield Select([("dr — research it, build a skill", "dr"),
                                  ("family — map the family, find gaps", "family"),
                                  ("deep — saturate this one concept", "deep")],
                                 value="dr", allow_blank=False,
                                 id="research-mode")
                yield Static("click a node for its skill, research and "
                             "neighbours · [dim]dim = frontier: known to the "
                             "tree, never researched[/dim] · [b]n[/b] queue it · "
                             "[b]R[/b] launch research now (spawns an agent)",
                             classes="hint")
                yield RichLog(id="concept-detail", classes="pane-log",
                              wrap=True, markup=True)
            with TabPane("Docsets", id="tab-docsets"):
                yield DataTable(id="docsets-table", cursor_type="row",
                                zebra_stripes=True)
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="filter by docset name… "
                                "([b]/[/b] to focus, [b]o[/b] to sort)",
                                id="docsets-filter")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="search the docset selected above…",
                                id="docset-query")
                    yield Select([(m, m) for m in docsets.SEARCH_MODES],
                                 value="semantic", allow_blank=False,
                                 id="docset-mode")
                    yield Button("Search docset", id="docset-search",
                                 variant="primary")
                yield Static("click a row for its detail and source file · "
                             "[b]semantic[/b] queries the vector index, "
                             "[b]fuzzy[/b]/[b]regex[/b] scan the source mirror "
                             "(or the indexed chunks when it is not on this "
                             "box) · [b]e[/b] refresh (refine + reindex both "
                             "layers) · [b]p[/b] polish facts with Claude · "
                             "[b]c[/b] expand (recrawl at a higher page cap) · "
                             "[b]d[/b] delete docset", classes="hint")
                # markup on: the detail block renders a file:// link. Raw
                # indexer/search output is written as rich Text so its
                # brackets are never parsed as markup.
                yield RichLog(id="docset-results", classes="pane-log",
                              wrap=True, markup=True)
            with TabPane("LLMs-full", id="tab-llmsfull"):
                yield DataTable(id="llmsfull-table", cursor_type="row",
                                zebra_stripes=True)
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="filter by key / name / site / "
                                "category… ([b]/[/b] focus, [b]o[/b] sort)",
                                id="llmsfull-filter")
                    yield Select([(m, m) for m in llms_full.STATUSES],
                                 value="ok", allow_blank=False,
                                 id="llmsfull-status")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="search inside the file selected above…",
                                id="llmsfull-query")
                    yield Select([(m, m) for m in llms_full.SEARCH_MODES],
                                 value="fuzzy", allow_blank=False,
                                 id="llmsfull-mode")
                    yield Button("Search file", id="llmsfull-search",
                                 variant="primary")
                yield Static("the local llms-full.txt mirror (llms-full/) — "
                             "click a row for its detail, file link and page "
                             "titles · [b]fuzzy[/b]/[b]regex[/b] scan the file, "
                             "hits carry their Source: page · [b]a[/b] add a "
                             "llms-full.txt URL · [b]w[/b] discover sites from "
                             "another directory (archived privately) · "
                             "[b]e[/b] re-download row · [b]c[/b] re-compile "
                             "catalog + fetch new/failed · [b]i[/b] index row "
                             "as a docset · [b]v[/b] edit file in $EDITOR · "
                             "[b]d[/b] delete file",
                             classes="hint")
                yield RichLog(id="llmsfull-results", classes="pane-log",
                              wrap=True, markup=True)
            with TabPane("Ask", id="tab-ask"):
                yield Static("Federated ask — codebase + docsets + logs + git "
                             "+ symbols + memory, RRF-fused and LLM-answered "
                             "with [n] citations. Prefix with [b]?[/b] for "
                             "retrieve-only sources (no LLM).", classes="hint")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="ask the hub anything…",
                                id="ask-query")
                yield RichLog(id="ask-results", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("Index", id="tab-index"):
                yield Static("Index a mirror .md (or any text/markdown file) "
                             "into a queryable docset:", classes="hint")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="/path/to/mirror.md",
                                id="index-path")
                yield Static("Watch dirs (idle-indexer semantic file index) — "
                             "add a folder:", classes="hint")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="/path/to/folder",
                                id="watch-path")
                yield RichLog(id="index-log", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("MCP", id="tab-mcp"):
                yield Static("", id="mcp-status", classes="hint")
                yield DataTable(id="mcp-table", cursor_type="row",
                                zebra_stripes=True)
                with Horizontal(classes="row-inputs"):
                    yield Button("Probe", id="mcp-probe", variant="primary")
                    yield Button(f"Start HTTP :{core.MCP_PORT}",
                                 id="mcp-start")
                    yield Button("Stop HTTP", id="mcp-stop", variant="error")
                yield Static("[b]Enter[/b] on a tool row runs a representative "
                             "query against live hub data (read-only; mutating "
                             "tools show their command instead)", classes="hint")
                yield RichLog(id="mcp-log", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("Scripts", id="tab-scripts"):
                yield Select([], id="script-select",
                             prompt="pick a script to run")
                with Horizontal(classes="row-inputs"):
                    yield Input(placeholder="arguments", id="script-args")
                    yield Button("Run", id="script-run", variant="primary")
                    yield Button("Kill", id="script-kill", variant="error")
                yield Static("choosing a script shows its usage + how-to "
                             "below and prefills the most likely arguments "
                             "([b]?[/b] re-shows it)", classes="hint")
                yield RichLog(id="script-log", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("Logs", id="tab-logs"):
                yield Select([(name, name) for name in core.LOG_FILES],
                             id="log-select", value="pipeline_manager")
                yield RichLog(id="log-view", classes="pane-log", wrap=False,
                              markup=False)
            with TabPane("Remotes", id="tab-remotes"):
                yield Static("", id="remotes-summary", classes="hint")
                yield DataTable(id="remotes-table", cursor_type="row",
                                zebra_stripes=True)
                yield Static("[b]r[/b] refresh · [b]k[/b] unload selected "
                             "model from VRAM (host row = all) · [b]g[/b] ssh "
                             "diagnostics (load, top CPU, who queries ollama) "
                             "· [b]K[/b] kill a remote PID (ssh) · [b]t[/b] "
                             "clean that host's repo (hard-reset to origin) "
                             "· [b]Q[/b] quiet-hours schedule on/off (vacation)",
                             classes="hint")
                yield RichLog(id="remotes-log", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("Repos", id="tab-repos"):
                yield Static("", id="repos-summary", classes="hint")
                yield DataTable(id="repos-table", cursor_type="row",
                                zebra_stripes=True)
                yield Static("git status (fetch + ahead/behind/dirty) for "
                             "this box + every host in Settings > "
                             "ssh_targets · [b]r[/b] refresh · [b]t[/b] clean "
                             "dirty + hard-reset to origin (DESTROYS local "
                             "changes)", classes="hint")
                yield RichLog(id="repos-log", classes="pane-log", wrap=True,
                              markup=False)
            with TabPane("Usage", id="tab-usage"):
                yield Static("", id="usage-summary", classes="hint")
                yield Static("", id="coverage-summary", classes="hint")
                yield DataTable(id="usage-table", cursor_type="row",
                                zebra_stripes=True)
                yield DataTable(id="leverage-table", cursor_type="row",
                                zebra_stripes=True)
                yield Static(
                    "[b]D[/b] build weekly semantic digest · "
                    "[b]r[/b] rescan (last 7 days) · savings are ESTIMATES: a "
                    "semantic query ≈ 800 retrieved tokens vs naive ingestion "
                    "of an average mirror doc; a skill load vs re-deriving "
                    "from its corpus. Prices per hub_manager/usage.py PRICES.",
                    classes="hint")
            with TabPane("Settings", id="tab-settings"), Vertical(id="settings-form"):
                for key, label in (
                        ("max_pages", "Crawl page cap per docset"),
                        ("crawlers", "Concurrent crawls"),
                        ("refresh_secs", "Auto-refresh seconds"),
                        ("log_lines", "Log tail depth"),
                        ("query_top", "Docset query top-N"),
                        ("mirror_clone", "Browsable site clone (1=on, 0=off)"),
                        ("local_only", "Pipeline --local-only (1=mirror on this box; "
                                       "remotes lack llms_acquire)"),
                        ("ollama_urls", "HUB_OLLAMA_URLS override (blank = default)"),
                        ("embed_model", "HUB_EMBED_MODEL override (blank = default)"),
                        ("ssh_targets", "SSH targets for Remotes (host=user@host, comma-sep)")):
                    yield Label(label, classes="setting-label")
                    yield Input(value=str(self.settings[key]),
                                id=f"set-{key.replace('_', '-')}")
                yield Button("Save settings", id="settings-save",
                             variant="primary")
                yield Static("", id="settings-note", classes="hint")
        yield Footer()

    # ------------------------------------------------------------------ #
    # startup / refresh plumbing
    # ------------------------------------------------------------------ #

    def on_mount(self) -> None:
        qt = self.query_one("#queue-table", DataTable)
        qt.add_columns("status", "step", "left", "att", "updated", "machines", "url", "error")
        ht = self.query_one("#health-table", DataTable)
        ht.add_columns("", "subsystem", "detail")
        dt = self.query_one("#docsets-table", DataTable)
        dt.add_columns("docset", "pages", "chunks", "model", "updated")
        lf = self.query_one("#llmsfull-table", DataTable)
        lf.add_columns("key", "name", "category", "status", "size", "pages", "fetched")
        mt = self.query_one("#mcp-table", DataTable)
        mt.add_columns("tool / env", "description / value")
        ut = self.query_one("#usage-table", DataTable)
        ut.add_columns("model", "reqs", "input", "output", "cache read",
                       "cache write", "est cost")
        lt = self.query_one("#leverage-table", DataTable)
        lt.add_columns("kind", "semantic index / skill", "uses",
                       "est tokens saved", "est cost saved")
        rt = self.query_one("#remotes-table", DataTable)
        rt.add_columns("host / loaded model", "weight", "latency",
                       "VRAM", "ctx", "keep-alive expires", "status",
                       "ready / daemons", "last work", "indexed", "git")
        rpt = self.query_one("#repos-table", DataTable)
        rpt.add_columns("box", "branch", "commit", "status")
        sel = self.query_one("#script-select", Select)
        self._scripts = scripts_registry.discover()
        sel.set_options([(f"{s.name} — {s.description}"[:90], i)
                         for i, s in enumerate(self._scripts)])
        self.refresh_queue()
        self.refresh_health()
        self.refresh_concepts()
        self.refresh_docsets()
        self.refresh_llmsfull()
        self.refresh_mcp()
        refresh = max(1, int(self.settings["refresh_secs"]))  # 0 would busy-spin
        self.set_interval(refresh, self.refresh_queue)
        self.set_interval(HEALTH_REFRESH_SECS, self.refresh_health)
        self.set_interval(refresh, self.refresh_logs)
        self.set_interval(JOB_FLUSH_SECS, self._flush_jobs)

    def on_unmount(self) -> None:
        """Quitting must not orphan spawned jobs (they run detached in their
        own sessions and would keep holding Ollama slots)."""
        for job in self.jobs.values():
            if job.running:
                job.terminate()

    def action_refresh(self) -> None:
        active = self.query_one(TabbedContent).active
        {"tab-queue": self.refresh_queue,
         "tab-health": self.refresh_health,
         "tab-concepts": self.refresh_concepts,
         "tab-docsets": self.refresh_docsets,
         "tab-llmsfull": self.refresh_llmsfull,
         "tab-mcp": self.refresh_mcp,
         "tab-usage": self.refresh_usage,
         "tab-remotes": self.refresh_remotes,
         "tab-repos": self.refresh_repos,
         "tab-logs": self.refresh_logs}.get(active, self.refresh_queue)()

    # ------------------------------------------------------------------ #
    # queue tab
    # ------------------------------------------------------------------ #

    def refresh_queue(self) -> None:
        table = self.query_one("#queue-table", DataTable)
        selected = table.cursor_row
        table.clear()
        items = queue_model.load_items()
        activity = queue_model.extension_activity()
        query = self.query_one("#queue-filter", Input).value.strip().lower()

        rows = []
        for it in items:
            machines = queue_model.machines_for(it)
            if query and query not in it.url.lower() \
                    and query not in it.status.lower() \
                    and query not in machines.lower():
                continue
            step, left = queue_model.stage_progress(it, activity)
            rows.append((it, step, left, machines))

        order = {"running": 0, "failed": 1, "pending": 2, "done": 3}
        sort_key = self.QUEUE_SORTS[self._queue_sort]
        if sort_key == "status":
            rows.sort(key=lambda r: (order.get(r[0].status, 9), r[0].url))
        elif sort_key == "url":
            rows.sort(key=lambda r: r[0].url)
        elif sort_key == "updated":
            rows.sort(key=lambda r: r[0].updated)
        if self._queue_sort_rev:
            rows.reverse()

        for it, step, left, machines in rows:
            style = STATUS_STYLE.get(it.status, "white")
            table.add_row(styled(it.status, style), step, left,
                          str(it.attempts), it.updated, machines,
                          it.url, it.error[:80], key=it.url)
        # live crawls (CLI or Chrome-extension /save-/crawl) from *_state.json
        for act in activity:
            if query and query not in act["host"].lower():
                continue
            table.add_row(
                styled("live", "magenta"), "mirror",
                f"{act['crawled']}p crawled, {act['queued']} queued",
                "-", core.age_str(act["updated"]), "-", act["host"],
                "(active crawl — read-only row)", key=f"ext:{act['host']}")
        pid = queue_model.manager_pid()
        counts = queue_model.summary_line(queue_model.summary(items))
        mgr = styled(f"manager RUNNING (pid {pid})", "green") if pid else \
            styled("manager stopped", "red")
        ext = styled("ext API up", "green") if self._ext_api_up else \
            styled("ext API down", "dim")
        self.query_one("#queue-summary", Static).update(
            f"{mgr} · {counts} · {ext} :{core.EXT_API_PORT}")
        if selected is not None and table.row_count:
            table.move_cursor(row=min(selected, table.row_count - 1))

    def _selected_key(self, table_id: str) -> str | None:
        """Row key of the cursor row in a DataTable (shared by queue/docsets)."""
        table = self.query_one(table_id, DataTable)
        if not table.row_count:
            return None
        try:
            return str(table.coordinate_to_cell_key(
                (table.cursor_row, 0)).row_key.value)
        except Exception:  # noqa: BLE001
            return None

    def _selected_url(self) -> str | None:
        key = self._selected_key("#queue-table")
        if key and key.startswith("ext:"):
            self.notify("live extension-crawl row — read-only", severity="warning")
            return None
        return key

    @on(DataTable.RowSelected, "#queue-table")
    def _queue_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter/click on a queue row: expand into the full per-item report
        (stages, per-box shard evidence, time budget, box/Ollama health)."""
        key = str(event.row_key.value) if event.row_key else ""
        if not key or key.startswith("ext:"):
            return
        items = {it.url: it for it in queue_model.load_items()}
        item = items.get(key)
        if item is None:
            return
        screen = ItemDetailScreen(f"[b]Queue item[/b]: {key}")
        self.push_screen(screen)
        self._build_item_report(screen, item)

    @work(thread=True, exclusive=True, group="queue-detail")
    def _build_item_report(self, screen: ItemDetailScreen, item) -> None:
        try:
            report = queue_model.build_item_report(item)
        except Exception as exc:  # noqa: BLE001 - a bad report must not kill the app
            self.call_from_thread(
                screen.update_text,
                f"[red]could not build report for[/red] {item.url}\n"
                f"{type(exc).__name__}: {exc}")
            return
        report += "\n\n[b]Box health[/b]\n"
        mgr_pid = queue_model.manager_pid()
        mgr = f"[green]running[/green] (pid {mgr_pid})" if mgr_pid else "[red]stopped[/red]"
        serve = "[green]up[/green]" if queue_model.serve_alive() else "[dim]down[/dim]"
        report += (f"  pipeline_manager: {mgr}\n"
                   f"  chrome-extension server: {serve}\n")
        for check in health.check_ollama_hosts():
            style = "green" if check.ok else "red"
            state = "ok" if check.ok else "DOWN"
            report += f"  {check.name}: [{style}]{state}[/{style}] — {check.detail}\n"
        self.call_from_thread(screen.update_text, report)

    def action_recrawl_item(self) -> None:
        # `c` is per-tab: Queue = recrawl the row, Docsets = expand the docset
        active = self.query_one(TabbedContent).active
        if active == "tab-docsets":
            self._expand_docset()
            return
        if active == "tab-llmsfull":
            self._refresh_all_llmsfull()
            return
        if active != "tab-queue":
            return
        url = self._selected_url()
        if url and self._queue_op(queue_model.recrawl, [url]) is not None:
            self.notify(f"reset for full recrawl: {url} "
                        f"(cap {self.settings['max_pages']} pages)")
            self.refresh_queue()

    def action_recrawl_all(self) -> None:
        if self.query_one(TabbedContent).active != "tab-queue":
            return

        def done(yes: bool) -> None:
            if yes:
                n = self._queue_op(queue_model.recrawl)
                if n is not None:
                    self.notify(f"reset {n} done item(s) for a 2nd round at "
                                f"{self.settings['max_pages']} pages")
                self.refresh_queue()
        self.push_screen(ConfirmScreen(
            "Recrawl ALL done sites (2nd round)?\nEvery completed docset "
            f"reruns mirror→distill→index at the {self.settings['max_pages']}-"
            "page cap. Crawls resume incrementally."), done)

    def action_cycle_sort(self) -> None:
        """'o' cycles the active tab's sort column (Queue and Docsets tabs
        only); 'O' reverses the current column's direction."""
        active = self.query_one(TabbedContent).active
        if active == "tab-queue":
            self._queue_sort = (self._queue_sort + 1) % len(self.QUEUE_SORTS)
            self._queue_sort_rev = False
            self.notify(f"sort: {self.QUEUE_SORTS[self._queue_sort]}")
            self.refresh_queue()
        elif active == "tab-docsets":
            self._docset_sort = (self._docset_sort + 1) % len(self.DOCSET_SORTS)
            self._docset_sort_rev = False
            self.notify(f"sort: {self.DOCSET_SORTS[self._docset_sort]}")
            self._render_docsets_cached()
        elif active == "tab-llmsfull":
            self._llmsfull_sort = (self._llmsfull_sort + 1) % len(self.LLMSFULL_SORTS)
            self._llmsfull_sort_rev = False
            self.notify(f"sort: {self.LLMSFULL_SORTS[self._llmsfull_sort]}")
            self._render_llmsfull_cached()

    def action_reverse_sort(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "tab-queue":
            self._queue_sort_rev = not self._queue_sort_rev
            self.notify(f"sort: {self.QUEUE_SORTS[self._queue_sort]} "
                        f"({'desc' if self._queue_sort_rev else 'asc'})")
            self.refresh_queue()
        elif active == "tab-docsets":
            self._docset_sort_rev = not self._docset_sort_rev
            self.notify(f"sort: {self.DOCSET_SORTS[self._docset_sort]} "
                        f"({'desc' if self._docset_sort_rev else 'asc'})")
            self._render_docsets_cached()
        elif active == "tab-llmsfull":
            self._llmsfull_sort_rev = not self._llmsfull_sort_rev
            self.notify(f"sort: {self.LLMSFULL_SORTS[self._llmsfull_sort]} "
                        f"({'desc' if self._llmsfull_sort_rev else 'asc'})")
            self._render_llmsfull_cached()

    def action_focus_filter(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "tab-queue":
            self.query_one("#queue-filter", Input).focus()
        elif active == "tab-docsets":
            self.query_one("#docsets-filter", Input).focus()
        elif active == "tab-llmsfull":
            self.query_one("#llmsfull-filter", Input).focus()

    @on(Input.Changed, "#queue-filter")
    def _queue_filter_changed(self, event: Input.Changed) -> None:
        self.refresh_queue()

    @on(Input.Changed, "#docsets-filter")
    def _docsets_filter_changed(self, event: Input.Changed) -> None:
        self._render_docsets_cached()

    def _queue_op(self, fn, *args) -> object | None:
        """Run a queue mutation, surfacing QueueStateError instead of crashing."""
        try:
            return fn(*args)
        except (queue_model.QueueStateError, ValueError) as exc:
            self.notify(str(exc), severity="error", timeout=10)
            return None

    def action_add_url(self) -> None:
        if self.query_one(TabbedContent).active == "tab-llmsfull":
            self._add_llmsfull()
            return

        def done(value: str | None) -> None:
            if value:
                added = self._queue_op(queue_model.add_urls, value.split())
                if added is not None:
                    self.notify(f"queued {added} site(s)")
                self.refresh_queue()
        self.push_screen(PromptScreen("Add docset seed URL(s), space-separated",
                                      "https://docs.example.com/"), done)

    def action_start_manager(self) -> None:
        result = queue_model.start_manager(
            max_pages=self.settings["max_pages"],
            crawlers=self.settings["crawlers"],
            env=settings.stage_env(self.settings),
            local_only=bool(self.settings.get("local_only", 1)))
        msg = result if isinstance(result, str) else f"started pid {result}"
        self.notify(f"pipeline manager: {msg}")
        self.refresh_queue()

    def action_stop_manager(self) -> None:
        # `x` is per-tab: Queue = stop pipeline manager, Health = disable check
        if self.query_one(TabbedContent).active == "tab-health":
            self._disable_selected_check()
            return

        def done(yes: bool) -> None:
            if yes:
                self.notify(f"pipeline manager: {queue_model.stop_manager()}")
                self.refresh_queue()
        self.push_screen(ConfirmScreen("Stop the running pipeline manager?"),
                         done)

    def action_retry_failed(self) -> None:
        n = self._queue_op(queue_model.retry)
        if n is not None:
            self.notify(f"requeued {n} failed item(s)")
        self.refresh_queue()

    def action_retry_item(self) -> None:
        # `e` is per-tab: Queue = requeue the row, Docsets = re-embed (refresh),
        # LLMs-full = re-download the row
        active = self.query_one(TabbedContent).active
        if active == "tab-docsets":
            self._reindex_docset()
            return
        if active == "tab-llmsfull":
            self._redownload_llmsfull()
            return
        url = self._selected_url()
        if url and self._queue_op(queue_model.retry, [url]) is not None:
            self.notify(f"requeued {url}")
            self.refresh_queue()

    def action_delete_item(self) -> None:
        # `d` is per-tab: Queue = drop the row, Docsets = drop the index,
        # LLMs-full = drop the mirrored file
        active = self.query_one(TabbedContent).active
        if active == "tab-docsets":
            self._delete_docset()
            return
        if active == "tab-llmsfull":
            self._delete_llmsfull()
            return
        url = self._selected_url()
        if not url:
            return

        def done(yes: bool) -> None:
            if yes and self._queue_op(queue_model.remove, url) is not None:
                self.notify(f"removed {url}")
                self.refresh_queue()
        self.push_screen(
            ConfirmScreen(f"Remove from queue and seed list?\n{url}"), done)

    # ------------------------------------------------------------------ #
    # health tab
    # ------------------------------------------------------------------ #

    def _disabled_checks(self) -> set[str]:
        return {c.strip() for c in
                str(self.settings.get("disabled_checks", "")).split(",")
                if c.strip()}

    @work(thread=True, exclusive=True, group="health")
    def refresh_health(self) -> None:
        from textual.worker import get_current_worker
        checks = health.run_all(disabled=self._disabled_checks())
        self._ext_api_up = queue_model.serve_alive()
        if get_current_worker().is_cancelled:
            return  # superseded run must not render stale data
        self.call_from_thread(self._render_health, checks)

    def _render_health(self, checks: list[health.HealthCheck]) -> None:
        table = self.query_one("#health-table", DataTable)
        table.clear()
        for i, c in enumerate(checks):
            style = {"True": "green", "False": "red"}.get(str(c.ok), "dim")
            table.add_row(c.icon, styled(c.name, style), c.detail,
                          key=c.check_id or f"row-{i}")

    def _selected_check(self) -> str | None:
        """check_id of the selected health row (None when row has no doctor)."""
        key = self._selected_key("#health-table")
        if not key or key.startswith("row-"):
            return None
        return key

    def action_diagnose_check(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "tab-remotes":
            self._remote_ssh_diagnose()
            return
        if active != "tab-health":
            return
        check_id = self._selected_check()
        log = self.query_one("#health-log", RichLog)
        if not check_id:
            log.write("select a check row with a subsystem id first")
            return
        log.write(f">>> diagnosing {check_id} ...")
        self._run_diagnose(check_id)

    @work(thread=True, exclusive=True, group="diagnose")
    def _run_diagnose(self, check_id: str) -> None:
        report = "\n".join(doctor.diagnose(check_id))
        remedies = doctor.remedies(check_id)
        if remedies:
            report += "\nremedies: " + " · ".join(
                f"[{r.action}] {r.label}" for r in remedies) + \
                "  (t = start/fix, k = stop)"
        self.call_from_thread(
            self.query_one("#health-log", RichLog).write, report)

    def action_remediate_check(self) -> None:
        active = self.query_one(TabbedContent).active
        if active in ("tab-repos", "tab-remotes"):
            self.action_clean_repo()
            return
        if active != "tab-health":
            return
        check_id = self._selected_check()
        log = self.query_one("#health-log", RichLog)
        if not check_id:
            log.write("select a check row first")
            return
        if not any(r.action == "start" for r in doctor.remedies(check_id)):
            log.write(f"no start/fix remedy for {check_id}")
            return
        log.write(f">>> remediating {check_id} ...")
        self._run_remedy(check_id, "start")

    def action_stop_check(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "tab-remotes":
            self.action_unload_remote()
            return
        if active != "tab-health":
            return
        check_id = self._selected_check()
        log = self.query_one("#health-log", RichLog)
        if not check_id:
            log.write("select a check row first")
            return
        if not any(r.action == "stop" for r in doctor.remedies(check_id)):
            log.write(f"no stop remedy for {check_id}")
            return
        self._run_remedy(check_id, "stop")

    @work(thread=True, group="remedy")
    def _run_remedy(self, check_id: str, action: str) -> None:
        result = doctor.start(check_id) if action == "start" else \
            doctor.stop(check_id)
        self.call_from_thread(
            self.query_one("#health-log", RichLog).write, result)
        time.sleep(2)  # give the process a moment before re-checking
        self.call_from_thread(self.refresh_health)

    def _disable_selected_check(self) -> None:
        check_id = self._selected_check()
        log = self.query_one("#health-log", RichLog)
        if not check_id:
            log.write("select a check row first")
            return
        disabled = self._disabled_checks() | {check_id}
        self.settings = settings.save(
            {"disabled_checks": ",".join(sorted(disabled))})
        log.write(f"disabled check {check_id} (u restores all; also editable "
                  "in Settings)")
        self.refresh_health()

    def action_restore_checks(self) -> None:
        if self.query_one(TabbedContent).active != "tab-health":
            return
        self.settings = settings.save({"disabled_checks": ""})
        self.query_one("#health-log", RichLog).write("all checks restored")
        self.refresh_health()

    def action_toggle_quiet_hours(self) -> None:
        """[Q] on Remotes: suspend the quiet-hours schedule, or restore it.

        Suspending is what you want on vacation or any day a box is free: the
        hub uses it normally until you turn the schedule back on. Suspending
        also restarts the box's hub services, since the last eviction stopped
        them.
        """
        if self.query_one(TabbedContent).active != "tab-remotes":
            return
        log = self.query_one("#remotes-log", RichLog)
        try:
            import box_schedule
        except Exception as exc:  # noqa: BLE001
            log.write(f"quiet hours unavailable: {exc}")
            return
        suspended = any(box_schedule.suspension(h)
                        for h in box_schedule._load_quiet())
        self._quiet_hours_worker(not suspended)

    @work(thread=True, exclusive=True, group="quiet-hours")
    def _quiet_hours_worker(self, suspend: bool) -> None:
        """ssh work, so it must not run on the UI thread."""
        import io
        import contextlib
        import box_schedule
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            args = argparse.Namespace(host=None, days=None, until=None,
                                      no_resume=False)
            (box_schedule.cmd_off if suspend else box_schedule.cmd_on)(args)
        self.call_from_thread(
            self.query_one("#remotes-log", RichLog).write, buf.getvalue().strip())
        self.call_from_thread(self.refresh_remotes)

    # ------------------------------------------------------------------ #
    # concepts tab
    # ------------------------------------------------------------------ #

    def _concept_tree(self):
        """Load the tree fresh each time — it is edited by /dr, the research
        queue and skill-tree-architect between refreshes, so a cached copy
        goes stale without any event this app would see."""
        import concept_tree as ct
        return ct, ct.ConceptTree.load()

    def refresh_concepts(self) -> None:
        try:
            ct, tree = self._concept_tree()
        except Exception as exc:  # noqa: BLE001 - a bad tree must not kill the tab
            self.query_one("#concept-detail", RichLog).write(
                Text(f"could not load the concept tree: {exc}"))
            return
        self._concepts = tree
        widget = self.query_one("#concept-tree", Tree)
        widget.clear()
        needle = self.query_one("#concept-filter", Input).value.strip().lower()

        def matches(concept: str) -> bool:
            """A branch survives the filter if it or any descendant matches,
            so filtering never hides the path to a hit."""
            if not needle:
                return True
            if needle in concept.lower():
                return True
            return any(needle in c.lower() for c, _l, _s in tree.walk(concept))

        def add(parent, concept: str, seen: set):
            if concept in seen:      # name links can cycle
                return
            seen.add(concept)
            st = tree.status(concept)
            style = {ct.FRONTIER: "dim italic",
                     ct.IN_PROGRESS: "bold yellow"}.get(st, "")
            label = Text(concept, style=style)
            if st == ct.FRONTIER:
                label.append("  (frontier)", style="dim")
            elif st == ct.IN_PROGRESS:
                label.append("  (researching…)", style="yellow")
            kids = [c for c in tree.children(concept) if matches(c)]
            node = (parent.add(label, data=concept, expand=bool(needle))
                    if kids else parent.add_leaf(label, data=concept))
            for child in kids:
                add(node, child, seen)

        seen: set = set()
        for root in tree.roots():
            if matches(root):
                add(widget.root, root, seen)
        orphans = [c for c in tree.orphan_frontier() if matches(c)]
        if orphans:
            # Frontier concepts with no known parent would otherwise render
            # nowhere at all -- invisible rather than absent.
            bucket = widget.root.add(Text("(unparented frontier)", style="dim"),
                                     data=None, expand=True)
            for c in orphans:
                bucket.add_leaf(Text(c, style="dim italic"), data=c)
        widget.root.expand()

        counts = (f"{len(tree.by_concept)} researched · "
                  f"{len(tree.frontier)} frontier")
        if tree.in_progress:
            counts += f" · {len(tree.in_progress)} researching"
        problems = tree.validate()
        log = self.query_one("#concept-detail", RichLog)
        log.clear()
        log.write(f"[b]concept tree[/b] — {counts}")
        if problems:
            log.write(f"[red]{len(problems)} structural problem(s)[/red] "
                      f"(run [b]concept_tree.py validate[/b]):")
            for line in problems[:5]:
                log.write(Text(f"  {line}"))
            if len(problems) > 5:
                log.write(Text(f"  … and {len(problems) - 5} more"))

    @on(Input.Changed, "#concept-filter")
    def _concept_filter_changed(self, event: Input.Changed) -> None:
        self.refresh_concepts()

    @on(Tree.NodeSelected, "#concept-tree")
    def _concept_selected(self, event: Tree.NodeSelected) -> None:
        concept = event.node.data
        if not concept:
            return
        try:
            ct, tree = self._concept_tree()
            d = ct.detail(tree, concept)
        except Exception as exc:  # noqa: BLE001
            self.query_one("#concept-detail", RichLog).write(
                Text(f"detail failed for {concept}: {exc}"))
            return
        log = self.query_one("#concept-detail", RichLog)
        log.clear()
        log.write(f"[b]{concept}[/b]  [dim]({d['status']})[/dim]")
        if d["status"] == "frontier":
            log.write(f"  [dim]{d['whyGreyed']} — source: "
                      f"{d['frontierSource']}[/dim]")
            log.write("  press [b]q[/b] to queue it for research")
        else:
            log.write(f"  skill      {d.get('skillId') or '-'}")
            for path in d.get("skillPaths") or []:
                log.write(Text(f"             {path}"))
            if d.get("skillId") and not d.get("skillPaths"):
                log.write("             [red]not installed anywhere[/red]")
            log.write(f"  researched {d.get('researchedAt') or '-'}  "
                      f"sources {d.get('sourcesCount', '-')}  "
                      f"concepts {d.get('conceptsCount', '-')}")
            if d.get("skillSummary"):
                log.write("")
                log.write(Text(d["skillSummary"]))
        log.write("")
        log.write(f"  parent     {d.get('parent') or '-'}")
        log.write(f"  children   {', '.join(d.get('children') or []) or '-'}")
        log.write(f"  siblings   {', '.join(d.get('siblings') or []) or '-'}")

    def _selected_concept(self) -> str | None:
        node = self.query_one("#concept-tree", Tree).cursor_node
        return node.data if node else None

    def action_launch_research(self) -> None:
        """Spawn a headless research run for the selected concept.

        Behind a confirm because it starts an autonomous agent that costs
        tokens and edits the tree -- not something a stray keypress should do.
        """
        if self.query_one(TabbedContent).active != "tab-concepts":
            return
        concept = self._selected_concept()
        if not concept:
            self.notify("select a concept first", severity="warning")
            return
        mode = str(self.query_one("#research-mode", Select).value)
        import concept_tree as ct
        tree = ct.ConceptTree.load()
        parent = tree.related(concept).get("parent")
        argv = ct.research_argv(concept, mode, parent)
        if argv is None:
            self.notify("claude binary not found — cannot launch research",
                        severity="error")
            return

        def go(yes: bool) -> None:
            if not yes:
                return
            log = self.query_one("#concept-detail", RichLog)
            log.write(f"\n[b]launching {mode} research on {concept}[/b] "
                      f"[dim](writes back into tree.json)[/dim]")
            self._start_job("research", argv, log)
            job = self.jobs.get("research")
            if job is not None and job.proc.pid:
                # Marked with the JOB's pid so a crashed agent self-clears on
                # the next read rather than pinning the node forever.
                ct.mark_in_progress(concept, mode, job.proc.pid)
                self._research_concept = concept
                self.refresh_concepts()

        self.push_screen(ConfirmScreen(
            f"Launch {mode.upper()} research on '{concept}'?\n\n"
            f"This spawns a headless Claude agent that costs tokens and will "
            f"edit concept-tree/tree.json."), go)

    def action_queue_concept(self) -> None:
        """Park the selected concept in RESEARCH_QUEUE.md, which is what /dr
        and process-research-queue consume."""
        if self.query_one(TabbedContent).active != "tab-concepts":
            return
        concept = self._selected_concept()
        if not concept:
            self.notify("select a concept first", severity="warning")
            return
        try:
            ct, tree = self._concept_tree()
            parent = tree.related(concept).get("parent")
            added = ct.queue_concept(concept, parent)
        except Exception as exc:  # noqa: BLE001
            self.notify(f"queue failed: {exc}", severity="error")
            return
        self.notify(f"queued {concept}" if added else f"{concept} already queued")
        self.refresh_concepts()

    # ------------------------------------------------------------------ #
    # docsets tab
    # ------------------------------------------------------------------ #

    @work(thread=True, exclusive=True, group="docsets")
    def refresh_docsets(self) -> None:
        from textual.worker import get_current_worker
        ok, text = docsets.list_docsets()
        if get_current_worker().is_cancelled:
            return  # superseded run must not render stale data
        self.call_from_thread(self._render_docsets, ok, text)

    def _render_docsets(self, ok: bool, text: str) -> None:
        table = self.query_one("#docsets-table", DataTable)
        table.clear()
        if not ok:
            table.add_row("(error)", "", "", "", text[:120])
            return
        # docset_indexer `list` emits a JSON array of docset dicts
        try:
            entries = json.loads(text) if text.strip() else []
        except json.JSONDecodeError:
            table.add_row("(error)", "", "", "", f"unparseable list output: {text[:100]}")
            return
        self._docsets_cache = entries
        self._render_docsets_cached()

    def _render_docsets_cached(self) -> None:
        """Re-filter/re-sort the last-fetched docset list without re-running
        the (subprocess-backed) list_docsets() call -- so typing in the
        filter box or pressing 'o' to sort stays instant."""
        table = self.query_one("#docsets-table", DataTable)
        table.clear()
        query = self.query_one("#docsets-filter", Input).value.strip().lower()
        entries = [e for e in self._docsets_cache
                  if query in str(e.get("docset", "")).lower()]

        sort_key = self.DOCSET_SORTS[self._docset_sort]
        if sort_key in ("pages", "chunks"):
            entries = sorted(entries, key=lambda e: e.get(sort_key) or 0)
        elif sort_key == "updated":
            entries = sorted(entries, key=lambda e: e.get("updated_at") or "")
        else:
            entries = sorted(entries, key=lambda e: str(e.get("docset", "")))
        if self._docset_sort_rev:
            entries.reverse()

        for e in entries:
            key = e.get("docset", "?")
            table.add_row(key, str(e.get("pages", "?")), str(e.get("chunks", "?")),
                         f"{e.get('model', '?')} [{e.get('backend', '?')}]",
                         e.get("updated_at", ""), key=key)

    def _selected_docset(self) -> str | None:
        return self._selected_key("#docsets-table")

    def _docset_entry(self, key: str) -> dict | None:
        return next((e for e in self._docsets_cache
                     if str(e.get("docset")) == key), None)

    def _docset_log(self, text: str, *, markup: bool = False) -> None:
        """Write to the pane below the table. Indexer/search output goes
        through rich Text so its brackets are never read as markup."""
        log = self.query_one("#docset-results", RichLog)
        log.write(text if markup else Text(text))

    @on(DataTable.RowSelected, "#docsets-table")
    def _docset_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter/click on a docset row: bring that docset up in the pane
        below — counts, embedding model, and a link to the source mirror."""
        key = str(event.row_key.value) if event.row_key else ""
        entry = self._docset_entry(key)
        if entry is None:
            return
        self.query_one("#docset-results", RichLog).clear()
        self._docset_log(docsets.docset_detail(entry), markup=True)

    @on(Input.Submitted, "#docset-query")
    def _docset_query(self, event: Input.Submitted) -> None:
        self._start_docset_search()

    @on(Button.Pressed, "#docset-search")
    def _docset_search_pressed(self) -> None:
        self._start_docset_search()

    def _start_docset_search(self) -> None:
        """Run the search box against the selected docset in the chosen mode:
        semantic goes to the vector index (subprocess), fuzzy/regex scan the
        source mirror in-process."""
        docset = self._selected_docset()
        if not docset:
            self._docset_log("select a docset row first")
            return
        box = self.query_one("#docset-query", Input)
        question = box.value.strip()
        if not question:
            return
        mode = str(self.query_one("#docset-mode", Select).value)
        # disable until the worker finishes: semantic spawns a heavyweight
        # chroma+embed subprocess and fuzzy/regex read a whole mirror file, so
        # unbounded concurrent searches must not stack
        box.disabled = True
        self._docset_log(f">>> [{mode}] [{docset}] {question}")
        if mode == "semantic":
            self._run_query(docset, question)
            return
        entry = self._docset_entry(docset) or {}
        self._run_file_search(docset, str(entry.get("source_path") or ""),
                              question, mode)

    @work(thread=True, exclusive=True, group="docset-query")
    def _run_query(self, docset: str, question: str) -> None:
        ok, text = docsets.query(docset, question,
                                 top=self.settings["query_top"])
        self.call_from_thread(self._render_query_result,
                              text if text else ("ok" if ok else "query failed"))

    @work(thread=True, exclusive=True, group="docset-query")
    def _run_file_search(self, docset: str, path: str, question: str,
                         mode: str) -> None:
        # A line scan is grep-shaped, so the semantic top-N (5 by default) is
        # too stingy to be useful here -- floor it at 20. search_docset falls
        # back to the docset's stored text when the source mirror is not on
        # this box (replicated docsets carry the index, not the file).
        ok, text = docsets.search_docset(
            docset, path, question, mode,
            top=max(self.settings["query_top"], 20))
        self.call_from_thread(self._render_query_result,
                              text if text else ("ok" if ok else "search failed"))

    def _render_query_result(self, text: str) -> None:
        self._docset_log(text)
        box = self.query_one("#docset-query", Input)
        box.disabled = False
        box.focus()

    # -- row actions: delete / refresh (re-embed) / expand (recrawl) ------- #

    def _delete_docset(self) -> None:
        """`d` on a docset row: drop its vectors, stored pages and registry
        row. Confirmed first — the index is minutes of embedding to rebuild,
        and on this box (the sole writer) the next replicate push removes it
        from every other box too."""
        docset = self._selected_docset()
        if not docset:
            self.notify("select a docset row first", severity="warning")
            return
        entry = self._docset_entry(docset) or {}

        def done(yes: bool) -> None:
            if yes:
                self._docset_log(f">>> deleting docset {docset}")
                self._run_docset_delete(docset)
        self.push_screen(ConfirmScreen(
            f"Delete docset {docset}?\n{entry.get('pages', '?')} pages / "
            f"{entry.get('chunks', '?')} chunks are dropped from the index; "
            "the source mirror file is left alone."), done)

    @work(thread=True, exclusive=True, group="docset-delete")
    def _run_docset_delete(self, docset: str) -> None:
        ok, text = docsets.delete(docset)
        self.call_from_thread(self._docset_deleted, docset, ok, text)

    def _docset_deleted(self, docset: str, ok: bool, text: str) -> None:
        self._docset_log(text or ("deleted" if ok else "delete failed"))
        if ok:
            self.notify(f"deleted docset {docset}")
        else:
            self.notify(f"delete failed: {docset}", severity="error", timeout=10)
        self.refresh_docsets()

    def _docset_source(self, verb: str) -> tuple[str, str] | None:
        """(docset key, local mirror path) for the cursor row, or None with
        the reason logged — every refresh-type action needs both."""
        docset = self._selected_docset()
        if not docset:
            self.notify("select a docset row first", severity="warning")
            return None
        entry = self._docset_entry(docset) or {}
        src = str(entry.get("source_path") or "")
        if not src:
            self._docset_log(f"{docset}: no source path recorded — cannot "
                             f"{verb}; use c (expand) to recrawl instead")
            return None
        src = os.path.expanduser(src)
        if not os.path.isfile(src):
            self._docset_log(f"{docset}: source mirror not on this box "
                             f"({src}) — use c (expand) to recrawl instead")
            return None
        return docset, src

    def _reindex_docset(self) -> None:
        """`e` on a docset row: the refresh chain — docset_refine all (clean,
        triage, snippets/tables/definitions, LLM units, reference.md), then
        the raw index from the clean mirror, then the facts index — under the
        same key. Needs the mirror on this box."""
        found = self._docset_source("refresh")
        if not found:
            return
        docset, src = found
        self._docset_log(f">>> refreshing {docset}: refine → index raw → index facts")
        self._start_job_chain("index", docsets.refresh_argvs(src, docset),
                              self.query_one("#docset-results", RichLog))

    def action_polish_docset(self) -> None:
        """`p` on a docset row: the claude -p proofreading pass over the
        docset's LLM units, then re-render and re-index the facts layer.
        Confirmed first — it spends Claude usage."""
        if self.query_one(TabbedContent).active != "tab-docsets":
            return
        found = self._docset_source("polish")
        if not found:
            return
        docset, src = found

        def done(yes: bool) -> None:
            if yes:
                self._docset_log(f">>> polishing {docset} with Claude, then reindexing facts")
                self._start_job_chain("index", docsets.refresh_argvs(src, docset, polish=True),
                                      self.query_one("#docset-results", RichLog))
        self.push_screen(ConfirmScreen(
            f"Polish {docset}'s LLM units with Claude?\nRuns claude -p over every "
            "batch of 40 units (spends Claude usage), then reindexes the fact layer."),
            done)

    def _start_job_chain(self, slot: str, argvs: list[list[str]], log: RichLog) -> None:
        """Run argvs one after another in `slot`; the next starts from the
        job-flush timer only when the previous exited 0."""
        if not argvs:
            return
        self._job_chains[slot] = list(argvs[1:])
        self._start_job(slot, argvs[0], log)

    def _expand_docset(self) -> None:
        """`c` on a docset row: recrawl its site at a (possibly higher) page
        cap so mirror→distill→index rerun and the docset grows. The crawler
        is resumable, so raising the cap extends the existing mirror rather
        than starting over. A docset with no queue item gets one added."""
        docset = self._selected_docset()
        if not docset:
            self.notify("select a docset row first", severity="warning")
            return
        entry = self._docset_entry(docset) or {}
        url = docsets.queue_url_for(entry, queue_model.load_items())
        if url is None:
            self._prompt_seed_for_docset(docset)
            return
        cap = self.settings["max_pages"]

        def done(value: str | None) -> None:
            if not value:
                return
            try:
                pages = max(1, int(value))
            except ValueError:
                self.notify(f"not a number: {value}", severity="error")
                return
            if pages > cap:
                self.settings = settings.save({"max_pages": pages})
            if self._queue_op(queue_model.recrawl, [url]) is None:
                return
            msg = f"expand {docset}: recrawl {url} at {pages} pages queued"
            if queue_model.manager_pid():
                msg += (" — pipeline manager is running with its old cap; "
                        "restart it (x then s) if you raised it")
            elif pages > cap:
                msg += " — press s to start the pipeline"
            self.notify(msg, timeout=12)
            self._docset_log(msg)
            self.refresh_queue()
        self.push_screen(PromptScreen(
            f"Expand {docset}: recrawl {url} up to how many pages? "
            f"(current cap {cap})", value=str(cap)), done)

    def _prompt_seed_for_docset(self, docset: str) -> None:
        host = docset.split("__", 1)[0]

        def done(value: str | None) -> None:
            if not value:
                return
            added = self._queue_op(queue_model.add_urls, value.split())
            if added is None:
                return
            msg = f"expand {docset}: queued {added} seed URL(s); press s to run"
            self.notify(msg)
            self._docset_log(msg)
            self.refresh_queue()
        self.push_screen(PromptScreen(
            f"{docset} has no pipeline-queue item. Seed URL to crawl:",
            f"https://{host}/"), done)

    # ------------------------------------------------------------------ #
    # llms-full tab — the local llms-full.txt mirror
    # ------------------------------------------------------------------ #

    def refresh_llmsfull(self) -> None:
        """Re-read catalog + manifest (two small JSON files, so no worker)
        under the status filter, then render through the local filter/sort."""
        status = str(self.query_one("#llmsfull-status", Select).value or "ok")
        try:
            using_mirror = llms_full.using_repo_mirror()
            self._llmsfull_cache = llms_full.rows(status=status)
        except Exception as exc:  # noqa: BLE001 — a corrupt manifest must not kill the TUI
            self._llmsfull_cache = []
            self._llmsfull_log(f"could not read the llms-full mirror: {exc}")
        else:
            if using_mirror:
                self._llmsfull_log(
                    "no live mirror at this box's HUB_LLMS_FULL_DIR — showing the repo's "
                    "vendored mirror (same data as the site's Directory page). Press "
                    "[b]c[/b] to compile + download into the live hub.", markup=True)
        self._render_llmsfull_cached()

    def _render_llmsfull_cached(self) -> None:
        table = self.query_one("#llmsfull-table", DataTable)
        table.clear()
        query = self.query_one("#llmsfull-filter", Input).value.strip().lower()
        entries = [e for e in self._llmsfull_cache
                   if not query or query in " ".join(
                       str(e.get(k) or "") for k in
                       ("key", "name", "site", "category", "url")).lower()]
        entries = llms_full.sort_rows(entries, self.LLMSFULL_SORTS[self._llmsfull_sort],
                                      self._llmsfull_sort_rev)
        for e in entries:
            st = e.get("status", "?")
            color = {"ok": "green", "failed": "red", "rejected": "yellow",
                     "missing": "red"}.get(st, "dim")
            table.add_row(e["key"], (e.get("name") or "")[:28], (e.get("category") or "")[:18],
                          styled(st, color), llms_full.size_str(e.get("bytes")),
                          str(e.get("pages", 0)), (e.get("fetched_at") or "")[:10],
                          key=e["key"])

    def _selected_llmsfull(self) -> dict | None:
        key = self._selected_key("#llmsfull-table")
        if not key:
            self.notify("select a row first", severity="warning")
            return None
        entry = next((e for e in self._llmsfull_cache if e["key"] == key), None)
        if entry is None:
            self.notify(f"{key} vanished — refresh", severity="warning")
        return entry

    def _llmsfull_log(self, text: str, *, markup: bool = False) -> None:
        log = self.query_one("#llmsfull-results", RichLog)
        log.write(text if markup else Text(text))

    @on(Input.Changed, "#llmsfull-filter")
    def _llmsfull_filter_changed(self, event: Input.Changed) -> None:
        self._render_llmsfull_cached()

    @on(Select.Changed, "#llmsfull-status")
    def _llmsfull_status_changed(self, event: Select.Changed) -> None:
        self.refresh_llmsfull()

    @on(DataTable.RowSelected, "#llmsfull-table")
    def _llmsfull_row_selected(self, event: DataTable.RowSelected) -> None:
        key = str(event.row_key.value) if event.row_key else ""
        entry = next((e for e in self._llmsfull_cache if e["key"] == key), None)
        if entry is None:
            return
        self.query_one("#llmsfull-results", RichLog).clear()
        self._llmsfull_log(llms_full.detail(entry), markup=True)

    @on(Input.Submitted, "#llmsfull-query")
    def _llmsfull_query(self, event: Input.Submitted) -> None:
        self._start_llmsfull_search()

    @on(Button.Pressed, "#llmsfull-search")
    def _llmsfull_search_pressed(self) -> None:
        self._start_llmsfull_search()

    def _start_llmsfull_search(self) -> None:
        entry = self._selected_llmsfull()
        if entry is None:
            return
        box = self.query_one("#llmsfull-query", Input)
        question = box.value.strip()
        if not question:
            return
        mode = str(self.query_one("#llmsfull-mode", Select).value)
        box.disabled = True
        self._llmsfull_log(f">>> [{mode}] [{entry['key']}] {question}")
        self._run_llmsfull_search(str(entry.get("file") or ""), question, mode)

    @work(thread=True, exclusive=True, group="llmsfull-search")
    def _run_llmsfull_search(self, path: str, question: str, mode: str) -> None:
        ok, text = llms_full.search_file(path, question, mode,
                                         top=max(self.settings["query_top"], 20))
        self.call_from_thread(self._render_llmsfull_search,
                              text if text else ("ok" if ok else "search failed"))

    def _render_llmsfull_search(self, text: str) -> None:
        self._llmsfull_log(text)
        box = self.query_one("#llmsfull-query", Input)
        box.disabled = False
        box.focus()

    # -- row actions: add / re-download / refresh-all / index / edit / delete -- #

    def _llmsfull_jobs(self, argvs: list[list[str]], banner: str) -> None:
        self._llmsfull_log(f">>> {banner}")
        self._start_job_chain("llmsfull", argvs,
                              self.query_one("#llmsfull-results", RichLog))

    def action_discover_directories(self) -> None:
        """`w` (llms-full tab only): queue an aggregator/directory URL to
        check for llms-full.txt sites beyond the three `compile` already
        crawls. The page itself is archived privately; only the site URLs
        it points at ever reach the public catalog."""
        if self.query_one(TabbedContent).active != "tab-llmsfull":
            return

        def done(value: str | None) -> None:
            if not value:
                return
            url = value.strip()
            self._llmsfull_jobs(llms_full.library_discover_argvs(url),
                                f"discovering from {url}: check → incorporate → download")
        self.push_screen(PromptScreen(
            "Queue a directory/aggregator URL to check for llms-full.txt sites "
            "(the page is archived privately, never published)",
            "https://some-directory.example/"), done)

    def _add_llmsfull(self) -> None:
        """`a`: seed one or more llms-full.txt URLs into the catalog and fetch
        them now (compile --seed …, then download --only per URL)."""
        def done(value: str | None) -> None:
            if not value:
                return
            urls = value.split()
            self._llmsfull_jobs(llms_full.add_argvs(urls),
                                f"adding {len(urls)} llms-full.txt URL(s): compile + download")
        self.push_screen(PromptScreen("Add llms-full.txt URL(s), space-separated",
                                      "https://docs.example.com/llms-full.txt"), done)

    def _redownload_llmsfull(self) -> None:
        """`e`: re-fetch the row's file (any status) — `download --refresh --only`."""
        entry = self._selected_llmsfull()
        if entry is None:
            return
        self._llmsfull_jobs([llms_full.redownload_argv(entry)],
                            f"re-downloading {entry['key']} from {entry['url']}")

    def _refresh_all_llmsfull(self) -> None:
        """`c`: re-compile the catalog from the public directories, then fetch
        everything new and retry the failures (what the weekly timer does)."""
        def done(yes: bool) -> None:
            if yes:
                self._llmsfull_jobs(llms_full.refresh_all_argvs(),
                                    "compile catalog from the directories, then "
                                    "download new + retry failed")
        self.push_screen(ConfirmScreen(
            "Re-compile the llms-full catalog and download new/failed entries?\n"
            "Hits llms-txt-hub, llmstxt.site and directory.llmstxt.cloud, then "
            "fetches every catalog entry not yet mirrored (minutes)."), done)

    def action_index_llms_full(self) -> None:
        """`i`: export the row's file in banner format under text-mirror/ and
        index it as docset <key> — it then appears on the Docsets tab, where
        e/p refine and polish it like any other docset."""
        if self.query_one(TabbedContent).active != "tab-llmsfull":
            return
        entry = self._selected_llmsfull()
        if entry is None:
            return
        if entry.get("status") != "ok":
            self._llmsfull_log(f"{entry['key']}: not downloaded ({entry.get('status')}) — "
                               "press e to fetch it first")
            return
        self._llmsfull_log(f">>> indexing {entry['key']}: export mirror → docset index")
        self._start_job_chain("index", llms_full.index_argvs(entry),
                              self.query_one("#llmsfull-results", RichLog))

    def action_edit_llms_full(self) -> None:
        """`v`: open the row's file in $VISUAL/$EDITOR (the TUI suspends
        until the editor exits, then re-reads the manifest)."""
        if self.query_one(TabbedContent).active != "tab-llmsfull":
            return
        entry = self._selected_llmsfull()
        if entry is None:
            return
        path = str(entry.get("file") or "")
        if not path or not os.path.isfile(path):
            self._llmsfull_log(f"{entry['key']}: no file on this box to edit")
            return
        import subprocess
        argv = llms_full.editor_argv(path)
        try:
            with self.suspend():
                subprocess.run(argv, check=False)
        except OSError as exc:
            self._llmsfull_log(f"editor failed: {' '.join(argv)}: {exc}")
            return
        self._llmsfull_log(f"edited {path} with {argv[0]}")
        self.refresh_llmsfull()

    def _delete_llmsfull(self) -> None:
        """`d`: drop the mirrored file and its manifest row (the catalog row
        stays, so the next compile+download would fetch it again)."""
        entry = self._selected_llmsfull()
        if entry is None:
            return

        def done(yes: bool) -> None:
            if not yes:
                return
            out = llms_full.delete(entry["key"])
            if out.get("deleted"):
                self.notify(f"deleted {entry['key']}")
                self._llmsfull_log(f"deleted {entry['key']} "
                                   f"(file removed: {out.get('file_removed')})")
            else:
                self.notify(f"delete failed: {out.get('error')}", severity="error")
            self.refresh_llmsfull()
        self.push_screen(ConfirmScreen(
            f"Delete the mirrored file for {entry['key']}?\n"
            f"{llms_full.size_str(entry.get('bytes'))} bytes / {entry.get('pages', 0)} "
            "pages are removed from llms-full/files/ along with the manifest row; "
            "the catalog entry stays (a re-compile + download fetches it again)."), done)

    # ------------------------------------------------------------------ #
    # ask tab
    # ------------------------------------------------------------------ #

    @on(Input.Submitted, "#ask-query")
    def _ask_query(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        if not raw:
            return
        retrieve_only = raw.startswith("?")
        question = raw.lstrip("?").strip()
        if not question:
            return
        log = self.query_one("#ask-results", RichLog)
        # disable until the worker finishes: each ask spawns an embed+LLM
        # subprocess, so unbounded concurrent asks must not stack
        self.query_one("#ask-query", Input).disabled = True
        log.write(f">>> {'[sources] ' if retrieve_only else ''}{question}")
        self._run_ask(question, retrieve_only)

    @work(thread=True, exclusive=True, group="ask-query")
    def _run_ask(self, question: str, retrieve_only: bool) -> None:
        ok, text = ask_client.run_ask(question, retrieve_only=retrieve_only)
        self.call_from_thread(self._render_ask_result,
                              text if text else ("ok" if ok else "ask failed"))

    def _render_ask_result(self, text: str) -> None:
        self.query_one("#ask-results", RichLog).write(text)
        box = self.query_one("#ask-query", Input)
        box.disabled = False
        box.focus()

    # ------------------------------------------------------------------ #
    # index tab
    # ------------------------------------------------------------------ #

    @on(Input.Submitted, "#index-path")
    def _index_path(self, event: Input.Submitted) -> None:
        path = os.path.expanduser(event.value.strip())
        log = self.query_one("#index-log", RichLog)
        if not path:
            return
        if not os.path.isfile(path):
            log.write(f"not a file: {path}")
            return
        log.write(f">>> indexing {path}")
        argv = [core.python_for_hub(), str(core.INDEXER_SCRIPT), "index", path]
        self._start_job("index", argv, log)

    @on(Input.Submitted, "#watch-path")
    def _watch_path(self, event: Input.Submitted) -> None:
        path = os.path.expanduser(event.value.strip())
        log = self.query_one("#index-log", RichLog)
        if not path:
            return
        if not os.path.isdir(path):
            log.write(f"not a directory: {path}")
            return
        existing = []
        if core.WATCH_DIRS.exists():
            existing = [ln.strip() for ln in
                        core.WATCH_DIRS.read_text().splitlines() if ln.strip()]
        if path in existing:
            log.write(f"already watched: {path}")
            return
        with core.WATCH_DIRS.open("a") as fh:
            fh.write(path + "\n")
        log.write(f"added to watch_dirs.txt: {path} "
                  "(idle-indexer picks it up next cycle)")

    # ------------------------------------------------------------------ #
    # mcp tab
    # ------------------------------------------------------------------ #

    MCP_TOOLS = [
        ("hub_search_codebase", "semantic search over the hub file index (hub.db)"),
        ("hub_ask", "federated ask over every corpus, RRF-fused, LLM-answered with citations"),
        ("hub_route", "which local skill / agent / MCP tool fits a task"),
        ("hub_search_symbols", "function/class-granularity semantic code search"),
        ("hub_index_docset", "chunk+embed a web-text-mirror file into a docset index"),
        ("hub_query_docset", "semantic query against an indexed docset"),
        ("hub_list_docsets", "list indexed docsets"),
        ("hub_delete_docset", "delete a docset (dry run unless confirm=true)"),
        ("hub_docset_index", "a docset's exported llms.txt / llms-facts.txt / manifest"),
        ("hub_llms_full_list", "local llms-full.txt mirror: which sites have one"),
        ("hub_llms_full_read", "a slice or one page of a mirrored llms-full.txt"),
        ("hub_concept_tree", "concept tree outline; frontier nodes marked"),
        ("hub_concept_lookup", "everything the hub knows about one concept"),
        ("hub_concept_frontier", "concepts known but never researched"),
        ("hub_concept_queue", "park a concept in the research queue"),
        ("hub_distill_run", "kick off distillers' offline stages (mirror/extract/bulk)"),
        ("hub_memory_search", "search the llm-memory-pyramid"),
        ("hub_memory_stats", "memory pyramid context-budget stats"),
    ]
    MCP_ENV = ["HUB_DIR", "HUB_MCP_PORT", "HUB_OLLAMA_URLS", "HUB_EMBED_MODEL",
               "HUB_DOCSET_DB", "HUB_DOCSET_BACKEND", "DISTILLERS_DIR",
               "NAPMEM_DIR"]

    def refresh_mcp(self) -> None:
        table = self.query_one("#mcp-table", DataTable)
        table.clear()
        for name, desc in self.MCP_TOOLS:
            table.add_row(styled(name, "cyan"), desc, key=name)
        for var in self.MCP_ENV:
            val = os.environ.get(var, "")
            table.add_row(styled(var, "magenta"),
                          val or "[dim](unset — default)[/dim]",
                          key=f"env:{var}")
        self._probe_mcp()

    @on(DataTable.RowSelected, "#mcp-table")
    def _mcp_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter on a tool row: run its representative query on live data."""
        key = str(event.row_key.value) if event.row_key else ""
        if not key or key.startswith("env:"):
            return
        log = self.query_one("#mcp-log", RichLog)
        log.write(f">>> demo: {key}")
        self._run_mcp_demo(key)

    @work(thread=True, exclusive=True, group="mcp-demo")
    def _run_mcp_demo(self, tool: str) -> None:
        desc, argv = mcp_demo.build(tool)
        log = self.query_one("#mcp-log", RichLog)
        self.call_from_thread(log.write, desc)
        if argv is None:
            return
        self.call_from_thread(log.write, "$ " + " ".join(
            a if len(a) < 80 else a[:77] + "..." for a in argv))
        import subprocess
        try:
            out = subprocess.run(argv, capture_output=True, text=True,
                                 timeout=180,
                                 env={**os.environ, **settings.stage_env()})
            text = (out.stdout + ("\n" + out.stderr
                                  if out.stderr.strip() else "")).strip()
            result = text[:6000] or f"(exit {out.returncode}, no output)"
        except (OSError, subprocess.TimeoutExpired) as exc:
            result = f"demo failed: {exc}"
        self.call_from_thread(log.write, result)

    @work(thread=True, exclusive=True, group="mcp")
    def _probe_mcp(self) -> None:
        check = health.check_mcp()
        job = self.jobs.get("mcp")
        extra = f" · HTTP job pid {job.proc.pid}" if job and job.running else ""
        style = "green" if check.ok else "yellow"
        self.call_from_thread(
            self.query_one("#mcp-status", Static).update,
            styled(f"{check.name}: {check.detail}", style) + extra +
            " · stdio mode is client-spawned (see docs/MCP.md)")

    @on(Button.Pressed, "#mcp-probe")
    def _mcp_probe_btn(self) -> None:
        self._probe_mcp()

    @on(Button.Pressed, "#mcp-start")
    def _mcp_start(self) -> None:
        log = self.query_one("#mcp-log", RichLog)
        job = self.jobs.get("mcp")
        if job and job.running:
            log.write("HTTP server already running")
            return
        argv = [core.python_for_hub(), str(core.MCP_SERVER), "--http",
                str(core.MCP_PORT)]
        log.write(f">>> {' '.join(argv)}")
        self._start_job("mcp", argv, log)
        self.set_timer(2, self._probe_mcp)

    @on(Button.Pressed, "#mcp-stop")
    def _mcp_stop(self) -> None:
        job = self.jobs.get("mcp")
        log = self.query_one("#mcp-log", RichLog)
        if job and job.running:
            job.terminate()
            log.write("sent SIGTERM to HTTP server")
        else:
            log.write("no HTTP server job to stop (externally started servers "
                      "must be stopped where they were launched)")
        self.set_timer(2, self._probe_mcp)

    # ------------------------------------------------------------------ #
    # scripts tab
    # ------------------------------------------------------------------ #

    @on(Select.Changed, "#script-select")
    def _script_pick(self, event: Select.Changed) -> None:
        if event.value is Select.BLANK:
            return
        info = self._scripts[int(event.value)]
        self.query_one("#script-args", Input).value = ""
        self.query_one("#script-args", Input).placeholder = \
            info.arg_hint or "arguments"
        # choosing a script immediately shows its usage + how-to below
        self.query_one("#script-log", RichLog).write(f">>> docs: {info.name}")
        self._run_script_help(int(event.value))

    @on(Button.Pressed, "#script-run")
    def _script_run(self) -> None:
        sel = self.query_one("#script-select", Select)
        log = self.query_one("#script-log", RichLog)
        if sel.value is Select.BLANK:
            log.write("pick a script first")
            return
        info = self._scripts[int(sel.value)]
        args_line = self.query_one("#script-args", Input).value
        try:
            argv = scripts_registry.build_argv(info, args_line)
        except ValueError as exc:  # shlex: unbalanced quote etc.
            log.write(f"bad arguments: {exc}")
            return
        log.write(f">>> {' '.join(argv)}")
        self._start_job("script", argv, log)

    def action_script_help(self) -> None:
        """? on the Scripts tab: full docs + --help, and prefill likely args."""
        if self.query_one(TabbedContent).active != "tab-scripts":
            return
        sel = self.query_one("#script-select", Select)
        log = self.query_one("#script-log", RichLog)
        if sel.value is Select.BLANK:
            log.write("pick a script first")
            return
        info = self._scripts[int(sel.value)]
        log.write(f">>> docs: {info.name}")
        self._run_script_help(int(sel.value))

    @work(thread=True, exclusive=True, group="script-help")
    def _run_script_help(self, index: int) -> None:
        info = self._scripts[index]
        cached = self._script_help_cache.get(info.name)
        if cached is None:
            doc = scripts_registry.full_docstring(info)
            help_text = scripts_registry.help_output(info)
            args = scripts_registry.likely_args(info)
            report = (f"===== {info.name} =====\n{doc}\n\n"
                      f"----- --help -----\n{help_text}")
            if args:
                report += f"\n\nlikely invocation prefilled: {args}"
            cached = (report, args)
            self._script_help_cache[info.name] = cached
        self.call_from_thread(self._render_script_help, *cached)

    def _render_script_help(self, report: str, args: str) -> None:
        self.query_one("#script-log", RichLog).write(report)
        if args:
            self.query_one("#script-args", Input).value = args

    @on(Button.Pressed, "#script-kill")
    def _script_kill(self) -> None:
        job = self.jobs.get("script")
        log = self.query_one("#script-log", RichLog)
        if job and job.running:
            job.terminate()
            log.write("killed")
        else:
            log.write("nothing running")

    def _start_job(self, slot: str, argv: list[str], log: RichLog) -> None:
        old = self.jobs.get(slot)
        if old and old.running and slot != "mcp":
            log.write("previous job still running — kill it first")
            return
        try:
            # no on_line callback: output is batched by the _flush_jobs timer
            # so a chatty child can't flood the event loop line-by-line
            self.jobs[slot] = runner.ProcJob(
                argv, env=settings.stage_env(self.settings))
            self.job_logs[slot] = log
        except OSError as exc:
            log.write(f"spawn failed: {exc}")

    def _clear_finished_research(self) -> None:
        """Drop the in-progress marker once the agent exits.

        Driven off the existing job timer rather than a callback: the job runs
        detached, so nothing else would notice it finished.
        """
        concept = getattr(self, "_research_concept", None)
        if not concept:
            return
        job = self.jobs.get("research")
        if job is not None and job.running:
            return
        import concept_tree as ct
        ct.clear_in_progress(concept)
        self._research_concept = None
        rc = job.returncode if job is not None else None
        self.notify(f"research on {concept} finished"
                    + (f" (exit {rc})" if rc else ""))
        if self.query_one(TabbedContent).active == "tab-concepts":
            self.refresh_concepts()

    def _flush_jobs(self) -> None:
        """Timer: drain each job's pending output into its log in one write.
        Output is written as plain Text — a child's stray `[...]` must never
        be parsed as Rich markup, and the docsets pane has markup on."""
        self._clear_finished_research()
        for slot, job in list(self.jobs.items()):
            lines = job.drain_ui()
            log = self.job_logs.get(slot)
            if lines and log is not None:
                log.write(Text("\n".join(lines)))
            if not job.running and slot not in self._jobs_settled:
                self._jobs_settled.add(slot)
                chain = self._job_chains.get(slot)
                if chain and job.returncode == 0:
                    # a refresh chain: start the next command in the slot
                    nxt = chain.pop(0)
                    if log is not None:
                        log.write(Text(f">>> {' '.join(nxt[1:4])} …"))
                    self._jobs_settled.discard(slot)
                    self._start_job(slot, nxt, log or self.query_one("#index-log", RichLog))
                    continue
                if chain:
                    self._job_chains.pop(slot, None)  # a failed step ends the chain
                    if log is not None:
                        log.write(Text("chain stopped: previous step failed"))
                if slot == "index":
                    # an index run (Index tab or Docsets refresh) changes the
                    # docset list — re-list once, when the job has exited
                    self.refresh_docsets()
                    self.refresh_llmsfull()  # an exported mirror shows in detail
                if slot == "llmsfull":
                    self.refresh_llmsfull()
            elif job.running:
                self._jobs_settled.discard(slot)

    # ------------------------------------------------------------------ #
    # remotes tab
    # ------------------------------------------------------------------ #

    @work(thread=True, exclusive=True, group="remotes")
    def refresh_remotes(self) -> None:
        from textual.worker import get_current_worker
        self._remotes_scanned = True
        self.call_from_thread(
            self.query_one("#remotes-summary", Static).update,
            "probing pool hosts (http + ssh) ...")
        hosts = remotes.all_hosts_readiness()
        if get_current_worker().is_cancelled:
            return
        repos = {r.label: r for r in remotes.all_repo_status()}
        if get_current_worker().is_cancelled:
            return
        self.call_from_thread(self._render_remotes, hosts, repos)

    def _quiet_summary(self) -> str:
        """Schedule state for the Remotes header, including any suspension."""
        try:
            import box_schedule
            quiet = box_schedule.quiet_hosts()
            susp = {h: box_schedule.suspension(h)
                    for h in box_schedule._load_quiet()}
            active = [f"{h} ({w})" for h, w in susp.items() if w]
            if active:
                return " · schedule OFF: " + ", ".join(active)
            if quiet:
                return " · quiet now: " + ", ".join(quiet)
            return " · schedule on, no box quiet"
        except Exception:  # noqa: BLE001 — the tab must render regardless
            return ""

    def _render_remotes(self, hosts: list, repos: dict | None = None) -> None:
        from urllib.parse import urlparse
        repos = repos or {}
        self._remotes_repos = repos  # cached for action_clean_repo lookup
        table = self.query_one("#remotes-table", DataTable)
        table.clear()
        total_vram = 0.0
        for h in hosts:
            style = "green" if h.alive else "red"
            state = "up" if h.alive else f"DOWN: {h.error[:40]}"
            if h.ssh_ok is None:
                ready_note = styled("ready", "green") if h.ready else "http-only"
            elif h.ssh_ok:
                ready_note = (f"{styled('ready', 'green') if h.ready else 'not ready'}"
                              f" · {len(h.daemons_up)}/3 daemons")
            else:
                ready_note = styled("ssh down", "red")
            host_name = urlparse(h.url).hostname or ""
            repo = repos.get(host_name)
            git_note = repo.summary if repo else "-"
            if _box_quiet(host_name):
                # a box excluded by the schedule is neither down nor broken;
                # say so, or its idle row reads as a fault
                state = styled("QUIET (schedule)", "yellow")
                ready_note = "handed back to its owner"
            indexed = (f"{h.indexed_files:,} files"
                      + (f" / {h.indexed_embeddings:,} emb" if h.indexed_embeddings else "")
                      if h.indexed_files is not None else "-")
            table.add_row(styled(h.url, style), str(h.weight),
                          f"{h.latency_ms:.0f} ms" if h.alive else "-",
                          f"{h.vram_gb:.1f} GB" if h.loaded else "-",
                          "-", "-",
                          f"{state} · {h.models_available} models",
                          ready_note, h.last_activity or "unknown", indexed,
                          git_note, key=f"host|{h.url}")
            for m in h.loaded:
                total_vram += m.vram_gb
                hot = m.vram_gb > 10
                table.add_row(
                    "  └ " + styled(m.name, "yellow" if hot else "cyan"),
                    "", "", f"{m.vram_gb:.1f} GB", f"{m.context:,}",
                    m.expires_at,
                    styled("HOT — k to unload", "yellow") if hot else "loaded",
                    "", "", "", "",
                    key=f"model|{h.url}|{m.name}")
        up = sum(1 for h in hosts if h.alive)
        self.query_one("#remotes-summary", Static).update(
            f"{up}/{len(hosts)} hosts up · {total_vram:.1f} GB VRAM in use "
            f"across the pool{self._quiet_summary()}")

    def _selected_remote_url(self) -> str | None:
        key = self._selected_key("#remotes-table")
        if not key:
            return None
        return key.split("|")[1]

    def _remote_ssh_diagnose(self) -> None:
        url = self._selected_remote_url()
        log = self.query_one("#remotes-log", RichLog)
        if not url:
            log.write("select a host row first")
            return
        log.write(f">>> ssh diagnostics: {url} ...")
        self._run_ssh_diagnose(url)

    @work(thread=True, exclusive=True, group="remotes-ssh")
    def _run_ssh_diagnose(self, url: str) -> None:
        report = remotes.ssh_diagnose(url)
        self.call_from_thread(
            self.query_one("#remotes-log", RichLog).write, report)

    def action_kill_remote_pid(self) -> None:
        if self.query_one(TabbedContent).active != "tab-remotes":
            return
        url = self._selected_remote_url()
        log = self.query_one("#remotes-log", RichLog)
        if not url:
            log.write("select a host row first")
            return

        def got_pid(value: str | None) -> None:
            if not value or not value.strip().isdigit():
                if value:
                    log.write(f"not a PID: {value}")
                return
            pid = int(value)

            def confirmed(yes: bool) -> None:
                if yes:
                    log.write(f">>> kill -TERM {pid} on {url}")
                    self._run_ssh_kill(url, pid)
            self.push_screen(ConfirmScreen(
                f"SIGTERM PID {pid} on {url}?\n(run g first to identify it)"),
                confirmed)
        self.push_screen(PromptScreen(
            f"PID to kill on {url} (see the g diagnostics output)", "e.g. 8224"),
            got_pid)

    @work(thread=True, group="remotes-kill")
    def _run_ssh_kill(self, url: str, pid: int) -> None:
        result = remotes.ssh_kill(url, pid)
        self.call_from_thread(
            self.query_one("#remotes-log", RichLog).write, result)

    def action_unload_remote(self) -> None:
        key = self._selected_key("#remotes-table")
        log = self.query_one("#remotes-log", RichLog)
        if not key:
            log.write("select a host or model row first")
            return
        parts = key.split("|")
        self._run_unload(parts)

    @work(thread=True, group="remotes-unload")
    def _run_unload(self, parts: list[str]) -> None:
        if parts[0] == "model":
            results = [remotes.unload(parts[1], parts[2])]
        else:
            results = remotes.unload_all(parts[1])
        log = self.query_one("#remotes-log", RichLog)
        self.call_from_thread(log.write, "\n".join(results))
        time.sleep(2)
        self.call_from_thread(self.refresh_remotes)

    # ------------------------------------------------------------------ #
    # repos tab
    # ------------------------------------------------------------------ #

    @work(thread=True, exclusive=True, group="repos")
    def refresh_repos(self) -> None:
        from textual.worker import get_current_worker
        self._repos_scanned = True
        self.call_from_thread(
            self.query_one("#repos-summary", Static).update,
            "fetching + checking git status on every box ...")
        repos = remotes.all_repo_status()
        if get_current_worker().is_cancelled:
            return
        self.call_from_thread(self._render_repos, repos)

    def _render_repos(self, repos: list) -> None:
        self._repos_cache = {r.label: r for r in repos}  # for action_clean_repo
        table = self.query_one("#repos-table", DataTable)
        table.clear()
        for r in repos:
            style = "green" if r.reachable and not (r.ahead or r.behind or r.dirty) \
                else "yellow" if r.reachable else "red"
            table.add_row(styled(r.label, style), r.branch or "-",
                          r.commit or "-", styled(r.summary, style),
                          key=r.label)
        behind = sum(1 for r in repos if r.behind or r.dirty)
        unreachable = sum(1 for r in repos if not r.reachable)
        self.query_one("#repos-summary", Static).update(
            f"{len(repos)} box(es) · {behind} out of date/dirty · "
            f"{unreachable} unreachable")

    def action_clean_repo(self) -> None:
        """[t] on the Repos or Remotes tab: hard-reset the selected box's
        repo to origin/<branch> and discard uncommitted changes. Destructive
        — always confirmed first."""
        active = self.query_one(TabbedContent).active
        if active == "tab-repos":
            label = self._selected_key("#repos-table")
            log = self.query_one("#repos-log", RichLog)
            cache = self._repos_cache
        elif active == "tab-remotes":
            key = self._selected_key("#remotes-table")
            if not key or not key.startswith("host|"):
                self.query_one("#remotes-log", RichLog).write(
                    "select a host row first (not a loaded-model row)")
                return
            from urllib.parse import urlparse
            label = urlparse(key.split("|", 1)[1]).hostname or ""
            log = self.query_one("#remotes-log", RichLog)
            cache = self._remotes_repos
        else:
            return
        repo = cache.get(label)
        if not label or repo is None:
            log.write("select a repo row first (r to refresh if empty)")
            return
        if not repo.reachable:
            log.write(f"{label}: repo unreachable ({repo.error}) — nothing to clean")
            return
        if not (repo.dirty or repo.ahead or repo.behind):
            log.write(f"{label}: already clean and up to date")
            return

        def confirmed(yes: bool) -> None:
            if not yes:
                return
            log.write(f">>> cleaning {label} ({repo.summary}) ...")
            self._run_clean_repo(label, log)
        self.push_screen(ConfirmScreen(
            f"Hard-reset {label} to origin/{repo.branch or '?'}?\n"
            f"Current: {repo.summary}\n"
            "This DISCARDS all uncommitted changes and untracked files."),
            confirmed)

    @work(thread=True, group="repo-clean")
    def _run_clean_repo(self, label: str, log: RichLog) -> None:
        result = remotes.clean_repo(label)
        self.call_from_thread(log.write, result)
        active = self.query_one(TabbedContent).active
        if active == "tab-repos":
            self.call_from_thread(self.refresh_repos)
        elif active == "tab-remotes":
            self.call_from_thread(self.refresh_remotes)

    # ------------------------------------------------------------------ #
    # logs tab
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # usage tab
    # ------------------------------------------------------------------ #

    def on_key(self, event) -> None:
        """Down-arrow on the tab bar descends focus into the active pane's
        first focusable widget (tables/inputs), instead of doing nothing."""
        from textual.widgets import Tabs
        if event.key != "down" or not isinstance(self.focused, Tabs):
            return
        pane = self.query_one(TabbedContent).active_pane
        if pane is None:
            return
        for widget in pane.query("*"):
            if widget.can_focus and widget.display:
                widget.focus()
                event.stop()
                return

    @on(TabbedContent.TabActivated)
    def _tab_activated(self, event: TabbedContent.TabActivated) -> None:
        # first entry to the Usage tab triggers the (heavy) transcript scan
        if event.pane.id == "tab-usage" and not self._usage_scanned:
            self.refresh_usage()
        if event.pane.id == "tab-remotes" and not self._remotes_scanned:
            self.refresh_remotes()
        if event.pane.id == "tab-repos" and not self._repos_scanned:
            self.refresh_repos()

    def action_tool_palette(self) -> None:
        """ctrl+p — describe a task, get the local skills/agents/MCP tools
        that fit it (semantic_ops.router), rendered on the Ask tab."""
        def _run(task: str | None) -> None:
            if not task:
                return
            self.query_one(TabbedContent).active = "tab-ask"
            self.query_one("#ask-results", RichLog).write(f">>> which tool: {task}")
            self._run_route(task)
        self.push_screen(PromptScreen("Which tool/agent/skill fits this task?",
                                      placeholder="e.g. review this PR for bugs"),
                         _run)

    @work(thread=True, exclusive=True, group="route")
    def _run_route(self, task: str) -> None:
        ok, text = ask_client.run_module(
            ["-m", "semantic_ops.router", "route", task, "--top", "5"], timeout=180)
        self.call_from_thread(
            self.query_one("#ask-results", RichLog).write,
            text if text.strip() else ("no matches" if ok else "route failed"))

    def action_weekly_digest(self) -> None:
        """Usage tab: build a topic digest of everything indexed this week."""
        if self.query_one(TabbedContent).active != "tab-usage":
            return
        self.query_one("#usage-summary", Static).update(
            "building weekly semantic digest ...")
        self._build_weekly_digest()

    @work(thread=True, exclusive=True, group="digest")
    def _build_weekly_digest(self) -> None:
        ok, text = ask_client.run_module(
            ["-m", "semantic_ops.digest", "weekly", "--days", "7"], timeout=900)
        self.call_from_thread(
            self.query_one("#usage-summary", Static).update,
            text.strip().splitlines()[-1] if text.strip()
            else ("digest done" if ok else "digest failed"))

    @work(thread=True, exclusive=True, group="usage")
    def refresh_usage(self) -> None:
        from textual.worker import get_current_worker
        self._usage_scanned = True
        self.call_from_thread(
            self.query_one("#usage-summary", Static).update,
            "scanning transcripts ...")
        report = usage.scan(days=7)
        if get_current_worker().is_cancelled:
            return
        self.call_from_thread(self._render_usage, report)

    def _render_usage(self, report: usage.UsageReport) -> None:
        ut = self.query_one("#usage-table", DataTable)
        ut.clear()
        totals = [0, 0, 0, 0, 0]
        for mu in sorted(report.models.values(), key=lambda m: -m.cost):
            cache_write = mu.cache_write_5m + mu.cache_write_1h
            ut.add_row(styled(mu.model, "cyan"), str(mu.requests),
                       f"{mu.input_tokens:,}", f"{mu.output_tokens:,}",
                       f"{mu.cache_read:,}", f"{cache_write:,}",
                       f"${mu.cost:,.2f}")
            for i, v in enumerate((mu.requests, mu.input_tokens,
                                   mu.output_tokens, mu.cache_read,
                                   cache_write)):
                totals[i] += v
        ut.add_row(styled("TOTAL", "bold"), str(totals[0]), f"{totals[1]:,}",
                   f"{totals[2]:,}", f"{totals[3]:,}", f"{totals[4]:,}",
                   styled(f"${report.total_cost:,.2f}", "bold"))
        lt = self.query_one("#leverage-table", DataTable)
        lt.clear()
        events = sorted(report.leverage.values(),
                        key=lambda e: -e.saved_cost())
        for ev in events:
            style = "magenta" if ev.kind == "skill" else "cyan"
            lt.add_row(ev.kind, styled(ev.name, style), str(ev.count),
                       f"{ev.saved_tokens:,}", f"${ev.saved_cost():,.2f}")
        if not events:
            lt.add_row("-", "no hub tool / skill uses found in window",
                       "-", "-", "-")
        self.query_one("#usage-summary", Static).update(
            f"last {report.days} days · {report.files_scanned} transcript "
            f"file(s) · spend {styled(f'${report.total_cost:,.2f}', 'yellow')}"
            f" · est saved by hub leverage "
            f"{styled(f'${report.total_saved:,.2f}', 'green')}")
        self.query_one("#coverage-summary", Static).update(_coverage_line())

    # ------------------------------------------------------------------ #
    # logs tab
    # ------------------------------------------------------------------ #

    def refresh_logs(self) -> None:
        if self.query_one(TabbedContent).active != "tab-logs":
            return
        sel = self.query_one("#log-select", Select)
        if sel.value is Select.BLANK:
            return
        name = str(sel.value)
        path = core.LOG_FILES[name]
        try:
            stat = path.stat()
            state = (name, stat.st_mtime_ns, stat.st_size)
        except OSError:
            state = (name, 0, 0)
        if state == self._log_state:
            return  # unchanged file: skip the re-read + full re-render
        self._log_state = state
        view = self.query_one("#log-view", RichLog)
        view.clear()
        view.write(core.tail_file(path, self.settings["log_lines"]))

    @on(Select.Changed, "#log-select")
    def _log_pick(self) -> None:
        self._log_state = None  # force redraw for the newly selected file
        self.refresh_logs()

    # ------------------------------------------------------------------ #
    # settings tab
    # ------------------------------------------------------------------ #

    @on(Button.Pressed, "#settings-save")
    def _settings_save(self) -> None:
        values = {}
        invalid = []
        for key in settings.DEFAULTS:
            widget = self.query_one(f"#set-{key.replace('_', '-')}", Input)
            value = widget.value.strip()
            if isinstance(settings.DEFAULTS[key], int):
                try:
                    int(value)
                except ValueError:
                    invalid.append(key)  # save() drops these silently — say so
                    continue
            values[key] = value
        self.settings = settings.save(values)
        note = (f"saved to {settings.SETTINGS_PATH} — refresh intervals apply "
                "on next launch")
        if invalid:
            note += f" · IGNORED invalid: {', '.join(invalid)}"
        self.query_one("#settings-note", Static).update(note)
        self.notify("settings saved" +
                    (f" (ignored: {', '.join(invalid)})" if invalid else ""))


def main() -> None:
    HubManagerApp().run()


if __name__ == "__main__":
    main()

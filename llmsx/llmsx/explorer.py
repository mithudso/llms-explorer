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
* research (`R`) → one `claude -p` job for one concept, streamed live in the
  job log screen (the TUI never suspends for it),
  tree snapshotted before and validated after — or a queue row when the
  `claude` binary is not installed;
* sync (`s`) → `git pull --ff-only`; commit (`c`) → stage only the
  allow-listed files, commit, push with the token through `GIT_ASKPASS`.

Tags (`t`) live in `marks.json` next to the marks; links (`l`) are a
`relatedConcepts` list on the node in `tree.json`; `T` cycles the outline
filter (all / frontier / researched / tagged). `L` opens the Library
(the site's directory, blog, skills, and imported llms files), `G` the
access-ledger report, `S` the skill runner (research stack, crawl-to-llms
family, every deep optimizer), `I` imports an llms file from disk or the
web, `W` the braindump screen and `J` the journal; `,` holds the token and
which windows are shown; `[` / `]` switch detail tabs. `N` adds a local
root and `M` moves a concept under another — an overlay in
`$LLMSX_HOME/local-tree.json` that never reaches the repo — which `F`
(flashcards, Leitner boxes) and `Q` (multiple-choice quiz) learn from over
the selected branch; `X` exports a concept, a branch, the current file or
the bundle as markdown under `$LLMSX_HOME/exports/`.

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
import sys
from collections.abc import Callable
from pathlib import Path

from . import explorer_screens as screens
from . import explorer_store as store

try:
    from rich.markup import escape
    from rich.text import Text
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, Vertical, VerticalScroll
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
    try:
        from textual.widgets._select import SelectOverlay
    except ImportError:  # pragma: no cover
        SelectOverlay = None
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "llmsx explorer needs Textual — install it with:  pip install 'llmsx[tui]'"
    ) from exc

logger = logging.getLogger(__name__)

#: Largest file the Markdown widget is asked to render; llms-full.txt can be
#: hundreds of KB and the widget is not built for that.
_MAX_RENDER_BYTES = 200_000
#: Wall-clock cap on one headless claude job (research or a skill run).
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

_Modal = screens._Modal


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


class ResearchSelect(Select):
    """Pick a research mode; Enter immediately submits the modal without closing."""

    BINDINGS = [
        Binding("down,up,space", "show_overlay", "Show menu", show=False),
        Binding("enter", "submit_mode", "Submit", show=False),
    ]

    def action_submit_mode(self) -> None:
        if self.screen and hasattr(self.screen, "_submit_current"):
            self.screen._submit_current()


class Research(_Modal):
    """Pick a mode and provider; returns (mode, provider) or mode, or None.
    Without the active provider CLI binary only `queue` is offered, and the
    screen says why. Pressing Enter inside the selection dropdown immediately submits."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "submit_enter", "Submit", show=False),
    ]

    def __init__(self, concept: str, parent: str | None, have_claude: bool | None = None,
                 provider: str | None = None, have_agent: bool | None = None) -> None:
        super().__init__()
        self._concept, self._parent_name = concept, parent
        self._provider = (provider or store.active_provider()).strip().lower()
        if have_claude is not None:
            self._have_agent = have_claude
        elif have_agent is not None:
            self._have_agent = have_agent
        else:
            self._have_agent = store.has_provider_binary(self._provider)
        self._have_claude = self._have_agent

    def compose(self) -> ComposeResult:
        modes = list(store.RESEARCH_MODES) if self._have_agent else ["queue"]
        prov_label = store.PROVIDER_LABELS.get(self._provider, self._provider)
        prov_options = [(lbl, p) for p, lbl in store.PROVIDER_LABELS.items()]
        with Vertical():
            yield Label(f"[b]Research:[/b] {escape(self._concept)}"
                        + (f"  [dim]under {escape(self._parent_name)}[/dim]"
                           if self._parent_name else ""))
            with Horizontal(id="provider-row"):
                yield Label("Engine: ", classes="lbl-provider")
                yield Select(prov_options, value=self._provider, id="provider", allow_blank=False)
            if not self._have_agent:
                yield Static(f"{prov_label} CLI not found on PATH — only `queue` is available "
                             "(the row lands in RESEARCH_QUEUE.md for a box that has it).",
                             classes="hint", id="provider-hint")
            else:
                yield Static(f"Using {prov_label} runner.", classes="hint", id="provider-hint")
            yield Static("dr = /dr skill · family = concept-family-explorer · deep = rabbithole"
                         " · crawl = crawl-to-llms-txt · full = full-suite (the whole stack) · "
                         "queue = append a queue row only", classes="hint")
            yield ResearchSelect([(m, m) for m in modes], value=modes[0], id="mode", allow_blank=False)
            with Horizontal(id="modal-quick-actions"):
                yield Button("⚡ /dr", id="quick-dr", variant="primary")
                yield Button("+ Queue", id="quick-queue")
                yield Button("🐇 Rabbithole", id="quick-deep")
                yield Button("🧭 Concept Explorer", id="quick-family")
            with Horizontal():
                yield Button("Run one job" if self._have_agent else "Queue", id="ok",
                             variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#mode", ResearchSelect).focus()

    @on(Select.Changed, "#provider")
    def _provider_changed(self, event: Select.Changed) -> None:
        new_p = str(event.value)
        self._provider = new_p
        self._have_agent = store.has_provider_binary(new_p)
        self._have_claude = self._have_agent
        lbl = store.PROVIDER_LABELS.get(new_p, new_p)
        hint = self.query_one("#provider-hint", Static)
        if not self._have_agent:
            hint.update(Text(f"{lbl} CLI not found on PATH — only `queue` is available."))
            modes = ["queue"]
        else:
            hint.update(Text(f"Using {lbl} runner."))
            modes = list(store.RESEARCH_MODES)
        mode_sel = self.query_one("#mode", ResearchSelect)
        mode_sel.set_options([(m, m) for m in modes])
        ok_btn = self.query_one("#ok", Button)
        ok_btn.label = "Run one job" if self._have_agent else "Queue"

    def _submit_current(self) -> None:
        try:
            mode = str(self.query_one("#mode", ResearchSelect).value)
        except Exception:
            mode = "dr" if self._have_agent else "queue"
        self.dismiss((mode, self._provider))

    def action_submit_enter(self) -> None:
        self._submit_current()

    if SelectOverlay is not None:
        @on(SelectOverlay.UpdateSelection)
        def _overlay_selection(self, event) -> None:
            event.stop()
            try:
                sel = self.query_one("#mode", ResearchSelect)
                val = sel._options[event.option_index][1]
                self.dismiss((str(val), self._provider))
            except Exception:
                self._submit_current()

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self._submit_current()
        elif event.button.id == "quick-dr":
            self.dismiss(("dr", self._provider))
        elif event.button.id == "quick-queue":
            self.dismiss(("queue", self._provider))
        elif event.button.id == "quick-deep":
            self.dismiss(("deep", self._provider))
        elif event.button.id == "quick-family":
            self.dismiss(("family", self._provider))
        else:
            self.dismiss(None)


class Settings(_Modal):
    """LLM provider selection, API keys (Google, Codex, Copilot, Ollama, Claude),
    model overrides, repo_url, push target, and GitHub token.
    The key fields are masked and their values are never echoed back in status lines.
    "Test Provider" and "Test token" run in background thread workers."""

    DEFAULT_CSS = _Modal.DEFAULT_CSS + """
    Settings > Vertical {
        width: 82; max-width: 95%; height: auto; max-height: 100%;
        border: round $primary; padding: 0 1; background: $surface;
    }
    Settings Input { height: 1; border: none; padding: 0 1; background: $surface-lighten-1; }
    Settings Select { height: 1; border: none; padding: 0 1; }
    Settings #provider-row { height: 1; margin-bottom: 0; }
    Settings #provider-row > Select { width: 1fr; height: 1; border: none; }
    Settings #provider-row > Input { width: 1fr; height: 1; border: none; margin-left: 1; }
    Settings #remotes-row { height: 1; margin-bottom: 0; }
    Settings #remotes-row > Input { width: 1fr; height: 1; border: none; margin-right: 1; }
    Settings #remotes-row > Input:last-child { margin-right: 0; }
    Settings #settings-buttons { margin-top: 1; height: 3; }
    Settings #settings-buttons Button { margin-right: 1; }
    """

    def __init__(self, cfg: dict, env_token: bool, tester: Callable[[str, str], str]) -> None:
        super().__init__()
        self._cfg, self._env_token, self._tester = cfg, env_token, tester
        self._current_prov = (cfg.get("provider") or store.active_provider()).strip().lower()
        self._provider_keys: dict[str, str] = {}
        if isinstance(cfg.get("api_keys"), dict):
            for p, k in cfg["api_keys"].items():
                if isinstance(k, str):
                    self._provider_keys[p] = k
        if "anthropic_api_key" in cfg and "claude" not in self._provider_keys:
            self._provider_keys["claude"] = str(cfg["anthropic_api_key"])
        if "github_token" in cfg and "copilot" not in self._provider_keys:
            self._provider_keys["copilot"] = str(cfg["github_token"])

    def _key_label(self, prov: str) -> str:
        env_vars = store.PROVIDER_KEY_ENV_VARS.get(prov, ())
        has_env = any(bool(os.environ.get(k)) for k in env_vars)
        env_suffix = " [dim][env set][/dim]" if has_env else ""
        name = store.PROVIDER_LABELS.get(prov, prov)
        return f"{name} API Key{env_suffix}"

    def compose(self) -> ComposeResult:
        cfg = self._cfg
        prov_options = [(lbl, p) for p, lbl in store.PROVIDER_LABELS.items()]
        active_p = self._current_prov
        active_model = cfg.get("models", {}).get(active_p, "") if isinstance(cfg.get("models"), dict) else ""
        has_env_gh = bool(os.environ.get("LLMSX_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))

        with Vertical():
            yield Label("[b]Settings & Provider Configuration[/b]  [dim]stored 0600 at "
                        + escape(str(store.config_path())) + "[/dim]")

            yield Label("Active Provider & Model Override")
            with Horizontal(id="provider-row"):
                yield Select(prov_options, value=active_p, id="provider", allow_blank=False)
                yield Input(active_model, placeholder=store.PROVIDER_DEFAULT_MODELS.get(active_p, "model override"), id="model")

            yield Label(self._key_label(active_p), id="lbl-provider-key")
            yield Input(self._provider_keys.get(active_p, ""), placeholder="API key (blank keeps, '-' clears)", id="provider_key")

            yield Label("repo_url & push_url (git remote / fork)")
            with Horizontal(id="remotes-row"):
                yield Input(cfg.get("repo_url") or store.DEFAULT_REPO_URL, id="repo_url")
                yield Input(cfg.get("push_url") or "origin", id="push_url")

            yield Label("GitHub token — blank keeps current; type `-` to remove" + (" [dim][env set][/dim]" if has_env_gh else ""))
            yield Input(cfg.get("github_token") or "", placeholder="ghp_… / gho_…", id="token")

            yield Static("", id="test-result", classes="hint")
            with Horizontal(id="settings-buttons"):
                yield Button("Windows…", id="panels")
                yield Button("Test token", id="test")
                yield Button("Test provider", id="test-provider")
                yield Button("Save", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    @on(Select.Changed, "#provider")
    def _provider_changed(self, event: Select.Changed) -> None:
        new_p = str(event.value)
        typed_key = self.query_one("#provider_key", Input).value
        if typed_key:
            self._provider_keys[self._current_prov] = typed_key
        self._current_prov = new_p
        lbl = self.query_one("#lbl-provider-key", Label)
        lbl.update(Text.from_markup(self._key_label(new_p)))
        key_input = self.query_one("#provider_key", Input)
        key_input.value = self._provider_keys.get(new_p, "")
        model_input = self.query_one("#model", Input)
        model_input.placeholder = store.PROVIDER_DEFAULT_MODELS.get(new_p, "default")
        model_input.value = self._cfg.get("models", {}).get(new_p, "") if isinstance(self._cfg.get("models"), dict) else ""

    def _values(self) -> dict:
        prov = str(self.query_one("#provider", Select).value)
        typed_key = self.query_one("#provider_key", Input).value
        if typed_key:
            self._provider_keys[prov] = typed_key
        tok = self.query_one("#token", Input).value
        if tok and "copilot" not in self._provider_keys:
            self._provider_keys["copilot"] = tok
        return {
            "provider": prov,
            "model": self.query_one("#model", Input).value.strip(),
            "provider_keys": dict(self._provider_keys),
            "key_google": self._provider_keys.get("google", ""),
            "key_codex": self._provider_keys.get("codex", ""),
            "key_ollama": self._provider_keys.get("ollama", ""),
            "key_claude": self._provider_keys.get("claude", ""),
            "token": tok,
            "repo_url": self.query_one("#repo_url", Input).value.strip(),
            "push_url": self.query_one("#push_url", Input).value.strip() or "origin",
        }

    def _show_test_result(self, text: str) -> None:
        try:
            self.query_one("#test-result", Static).update(Text(text))
        except Exception as exc:  # the modal was dismissed before the test finished
            logger.debug("test result dropped: %s", exc)

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self._values())
        elif event.button.id == "panels":
            self.dismiss({**self._values(), "token": "", "panels": True})
        elif event.button.id == "test":
            v = self._values()
            self._show_test_result("testing git token…")
            tester, show = self._tester, self._show_test_result
            app = self.app

            def work() -> None:
                result = tester(v["push_url"], v["token"])
                try:
                    app.call_from_thread(show, result)
                except RuntimeError:   # app already exited
                    pass
            app.run_worker(work, thread=True, group="token-test", exclusive=True)
        elif event.button.id == "test-provider":
            v = self._values()
            prov = v["provider"]
            key_val = self._provider_keys.get(prov, "")
            if not key_val and prov == "copilot":
                key_val = v.get("token", "")
            self._show_test_result(f"testing provider {prov}…")
            show = self._show_test_result
            app = self.app

            def work() -> None:
                result = store.test_provider_key(prov, key_val)
                try:
                    app.call_from_thread(show, result)
                except RuntimeError:
                    pass
            app.run_worker(work, thread=True, group="provider-test", exclusive=True)
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
        if node is not None and node.allow_expand and not node.is_expanded:
            node.expand()
            return
        # nothing left to open: move on to the detail tabs
        self.screen.focus_next()

    def action_collapse_node(self) -> None:
        node = self.cursor_node
        if node is None:
            return
        if node.is_expanded:
            node.collapse()
        elif node.parent is not None and node.parent is not self.root:
            self.select_node(node.parent)
            self.scroll_to_node(node.parent)
        else:
            # at a root with nothing to close: move back to the filter box
            self.screen.focus_previous()


# --------------------------------------------------------------------------- #
# the app
# --------------------------------------------------------------------------- #

class Explorer(App):
    CSS = """
    #left { width: 42%; min-width: 30; }
    #outline { height: 1fr; border: round $primary; }
    #right { width: 1fr; }
    #quick-actions { height: auto; max-height: 3; padding: 0; align: left middle; }
    #quick-actions Button { margin-right: 1; height: 3; min-width: 5; padding: 0 1; }
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
        Binding("ctrl+b", "batch_research", "Batch research", show=False),
        Binding("R", "research", "Research"),
        Binding("o", "job_log", "Job log", show=False),
        Binding("u", "queue_viewer", "Queue", show=False),
        Binding("a", "toggle_autopilot", "Auto /dr", show=False),
        Binding("h", "add_highlight", "Highlight", show=False),
        Binding("H", "view_highlights", "Highlights", show=False),
        Binding("question_mark", "help", "Help", key_display="?"),
        Binding("s", "sync", "Sync"),
        Binding("c", "commit", "Commit+push"),
        Binding("comma", "settings", "Settings", key_display=","),
        Binding("t", "tags", "Tags"),
        Binding("l", "link", "Link", show=False),
        Binding("T", "cycle_filter", "Filter type", show=False),
        Binding("L", "library", "Library"),
        Binding("G", "ledger", "Ledger", show=False),
        Binding("S", "skills", "Skills"),
        Binding("I", "import_llms", "Import", show=False),
        Binding("W", "braindump", "Braindump", show=False),
        Binding("J", "journal", "Journal", show=False),
        Binding("N", "new_root", "New local root", show=False),
        Binding("M", "move_concept", "Move (local)", show=False),
        Binding("F", "flashcards", "Flashcards", show=False),
        Binding("Q", "quiz", "Quiz", show=False),
        Binding("X", "export_menu", "Export", show=False),
        Binding("left_square_bracket", "prev_tab", "Prev tab", show=False, key_display="["),
        Binding("right_square_bracket", "next_tab", "Next tab", show=False, key_display="]"),
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
        self._type_filter = "all"   # store.FILTERS
        self._active_pane = "pane-overview"   # kept by TabActivated: `active` updates async
        self._hidden_panes: set[str] = set()  # tabs hidden by the Windows settings
        self._import_busy = False
        self._overlay = store.load_overlay()  # local roots and moves, never committed
        self._panels = screens.panel_config(store.load_config())
        self._job: screens.JobState | None = None   # the running or last claude job
        self._autopilot: bool = False               # continuous frontier /dr runner

    @property
    def _main(self):
        """The workbench screen. `App.query_one` only sees the *active*
        screen, so a status update or refresh landing while the job log,
        Library or Ledger is on top must address this one explicitly."""
        stack = self.screen_stack
        return stack[0] if stack else self.screen

    # ------------------------------------------------------------------ #
    # layout

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left"):
                yield Input(placeholder="filter concepts and aliases…  (/)", id="filter")
                yield OutlineTree("concept tree", id="outline")
            with Vertical(id="right"):
                with Horizontal(id="quick-actions"):
                    yield Button("⚡ /dr", id="btn-dr", variant="primary")
                    yield Button("+ Queue", id="btn-queue")
                    yield Button("🐇 Rabbithole", id="btn-rabbithole")
                    yield Button("🧭 Family", id="btn-family")
                    yield Button("📚 Batch", id="btn-batch")
                    yield Button("🚀 Auto", id="btn-auto")
                    yield Button("📋 Queue", id="btn-view-queue")
                    yield Button("🔖 Highlight", id="btn-highlight")
                    yield Button(f"🤖 {store.active_provider()}", id="btn-provider")
                    yield Button("❓ Help", id="btn-help")
                with TabbedContent(id="tabs"):
                    yield TabPane("Overview", Markdown("", id="md-overview"), id="pane-overview")
                    yield TabPane("Facts", Markdown("", id="md-facts"), id="pane-facts")
                    yield TabPane("Skill", Markdown("", id="md-skill"), id="pane-skill")
                    yield TabPane("Highlights", Markdown("", id="md-highlights"), id="pane-highlights")
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "llmsx explorer"
        self.sub_title = str(self.repo)
        self._load()
        self._render_outline()
        self._apply_panels()
        if self._auto_sync:
            self.action_sync()

    def _apply_panels(self) -> None:
        """Show or hide each window per the `panels` config."""
        p = self._panels
        self._main.query_one("#left").display = p.get("outline", True)
        self._main.query_one("#right").display = p.get("detail", True)
        self._main.query_one("#status").display = p.get("status", True)
        self._main.query_one(Footer).display = p.get("footer", True)

    # ------------------------------------------------------------------ #
    # data

    def _status(self, text: str) -> None:
        self._main.query_one("#status", Static).update(Text(text))

    def _load(self) -> None:
        try:
            self._tree_nodes = store.load_raw_tree(self.repo / store.TREE_REL)
        except (FileNotFoundError, ValueError) as exc:
            self._tree_nodes = []
            logger.warning("could not load the tree: %s", exc)
            self._status(f"could not load the tree: {exc}")
        self._overlay = store.load_overlay()
        self._outline = store.apply_overlay(store.build_outline(self._tree_nodes), self._overlay)
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
            if name in store.local_root_names(self._overlay):
                label = Text(name, style="bold")
                label.append("  (local root)", style="dim magenta")
                return label
            label = Text(name, style="dim italic")
            label.append("  (frontier)", style="dim")
            tags = store.tags_of(self._marks, store.slugify(name))
            if tags:
                label.append("  #" + " #".join(tags[:3]), style="magenta")
            if name in self._queued:
                label.append("  queued", style="dim cyan")
            return label
        label = Text(name)
        if name in self._overlay.get("moves", {}):
            label.append(" ↷", style="magenta")
        if node["slug"] in self._available:
            label.append(" ●", style="cyan")
        mark = self._marks.get(node["slug"])
        if isinstance(mark, dict):
            if mark.get("state"):
                label.append(f"  [{mark.get('state')}]", style="bold yellow")
            tags = store.tags_of(self._marks, node["slug"])
            if tags:
                label.append("  #" + " #".join(tags[:3]), style="magenta")
        if name in self._queued:
            label.append("  queued", style="dim cyan")
        return label

    def _render_outline(self) -> None:
        tree = self._main.query_one("#outline", OutlineTree)
        tree.clear()
        o = self._outline
        if not o:
            return
        needle = self._main.query_one("#filter", Input).value.strip().lower()
        keep = self._matching(needle)
        kind = self._type_filter

        def passes_type(name: str) -> bool:
            if kind == "frontier":
                return o.is_frontier(name)
            if kind == "researched":
                return not o.is_frontier(name)
            if kind == "tagged":
                return bool(store.tags_of(self._marks, store.tag_key(name, o)))
            return True

        def wanted(name: str) -> bool:
            if keep is not None and name not in keep:
                return False
            if kind == "all":
                return True
            # a branch stays visible when any descendant passes the type filter
            return passes_type(name) or any(wanted(k) for k in o.children.get(name, []))

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
                     f"bundle {len(self._bundle)} file(s) · filter: {kind}")

    @on(Input.Changed, "#filter")
    def _filter_changed(self) -> None:
        # one rebuild per pause in typing, not one per keystroke over 4,500 rows
        if self._filter_timer is not None:
            self._filter_timer.stop()
        self._filter_timer = self.set_timer(0.15, self._render_outline)

    @on(Input.Submitted, "#filter")
    def _filter_submitted(self) -> None:
        self._main.query_one("#outline", OutlineTree).focus()

    def action_focus_filter(self) -> None:
        self._main.query_one("#filter", Input).focus()

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
        tabs = self._main.query_one("#tabs", TabbedContent)
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
        self._try_set("pane-highlights", lambda: self._set_highlights(name, slug), name)
        if node is None:
            self._pane_source["pane-facts"] = f"_{_NOT_AVAILABLE['frontier']}_"
            self._pane_source["pane-skill"] = f"_{_NOT_AVAILABLE['frontier']}_"
        else:
            self._try_set("pane-facts", lambda: self._set_facts(name, slug), name)
            self._try_set("pane-skill", lambda: self._set_skill(node), name)
            if self._panels.get("tab-llms", True):
                self._try_set(None, lambda: self._set_llms(slug), name)
        for pid, key in (("pane-facts", "tab-facts"), ("pane-skill", "tab-skill"),
                         ("pane-highlights", "tab-highlights")):
            if self._panels.get(key, True):
                self._hidden_panes.discard(pid)
                tabs.show_tab(pid)
            else:
                self._hidden_panes.add(pid)
                tabs.hide_tab(pid)
        if self._active_pane in self._hidden_panes:
            self._step_tab(1)
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

    def _set_highlights(self, name: str, slug: str) -> None:
        hls = store.highlights_for_concept(slug)
        self._pane_source["pane-highlights"] = store.highlights_markdown(hls, name)

    def _set_overview(self, name: str, node: dict | None, slug: str) -> None:
        note = store.read_note(slug) if node else ""
        md = store.overview_markdown(node, name, self._outline, self._marks, note,
                                     name in self._queued)
        tags = store.tags_of(self._marks, store.tag_key(name, self._outline))
        extra = []
        if tags:
            extra.append("- **tags:** " + ", ".join(f"#{store.md_escape(t)}" for t in tags))
        links = store.related_of(node)
        if links:
            extra += ["", "## Linked concepts", ""]
            extra += [f"- [{store.md_escape(r)}](concept:{store.slugify(r)})" for r in links]
        hls = store.highlights_for_concept(slug)
        if hls:
            extra += ["", f"## Highlights & Annotations ({len(hls)})", ""]
            for h in hls[:5]:
                for line in h.get("text", "").splitlines():
                    extra.append(f"> {store.md_escape(line)}")
                if h.get("note"):
                    extra.append(f"_Note: {store.md_escape(h['note'])}_")
                extra.append("")
        if extra:
            md += "\n" + "\n".join(extra) + "\n"
        self._pane_source["pane-overview"] = md

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
            if self._panels.get("tab-references", True):
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
        self._main.query_one("#tabs", TabbedContent).add_pane(TabPane(title, Markdown(""), id=pid))
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
            pane = self._main.query_one(f"#{pid}", TabPane)
            pane.query_one(Markdown).update(text)
        except Exception as exc:  # the pane may already be gone (re-render in flight)
            logger.debug("pane %s not filled: %s", pid, exc)
            return
        self._filled.add(pid)

    @on(TabbedContent.TabActivated, "#tabs")
    def _tab_activated(self, event: TabbedContent.TabActivated) -> None:
        if event.pane.id:
            self._active_pane = event.pane.id
        self._fill(event.pane.id)

    @on(Markdown.LinkClicked)
    def _link_clicked(self, event: Markdown.LinkClicked) -> None:
        """`concept:<slug>` links (linked concepts in the overview) jump to
        that node; every other link is left alone (a TUI opens nothing)."""
        href = event.href or ""
        if not href.startswith("concept:"):
            return
        event.prevent_default()
        self.jump_to(href[len("concept:"):])

    def _resolve_name(self, slug_or_name: str) -> str | None:
        """A concept name from a slug (researched), an exact frontier name, or
        a frontier name's slug — in that order."""
        o = self._outline
        if not o:
            return None
        node = o.by_slug.get(slug_or_name)
        if node:
            return node["concept"]
        frontier = {k for kids in o.children.values() for k in kids if o.is_frontier(k)}
        if slug_or_name in frontier:
            return slug_or_name
        for k in frontier:
            if store.slugify(k) == slug_or_name:
                return k
        return None

    def jump_to(self, slug_or_name: str) -> None:
        name = self._resolve_name(slug_or_name)
        if not name:
            self._status(f"no concept for {slug_or_name!r}")
            return
        tree = self._main.query_one("#outline", OutlineTree)
        for tn in self._walk_nodes(tree.root):
            if tn.data == name:
                parent = tn.parent
                while parent is not None:
                    parent.expand()
                    parent = parent.parent
                tree.select_node(tn)
                tree.scroll_to_node(tn)
                tree.focus()
                return
        self._select(name)

    @staticmethod
    def _walk_nodes(root):
        stack = list(root.children)
        while stack:
            n = stack.pop(0)
            yield n
            stack.extend(n.children)

    def action_prev_tab(self) -> None:
        self._step_tab(-1)

    def action_next_tab(self) -> None:
        self._step_tab(1)

    def _step_tab(self, delta: int) -> None:
        tabs = self._main.query_one("#tabs", TabbedContent)
        # ContentSwitcher flips `display` on panes itself; visibility for the
        # user is "not hidden by the Windows settings"
        panes = [p.id for p in tabs.query(TabPane) if p.id and p.id not in self._hidden_panes]
        if not panes:
            return
        try:
            i = panes.index(self._active_pane)
        except ValueError:
            i = 0
        target = panes[(i + delta) % len(panes)]
        self._active_pane = target
        tabs.active = target
        tabs.focus()

    def _current_file(self) -> tuple[Path, str] | None:
        return self._pane_files.get(self._main.query_one("#tabs", TabbedContent).active)

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
    # tags, links, filter

    def action_tags(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return
        key = store.tag_key(name, self._outline)

        def done(tags: list[str] | None) -> None:
            if tags is None:
                return

            def apply() -> str:
                self._marks = store.set_tags(self.repo, key, tags)
                self._refresh(name, reload=False)
                return f"tags for {name}: " + (", ".join(store.tags_of(self._marks, key)) or "none")
            self._guarded("tags", apply)
        self.push_screen(screens.TagEditor(name, store.tags_of(self._marks, key),
                                           store.all_tags(self._marks)), done)

    def action_link(self) -> None:
        node = self._require_node()
        if not node:
            return

        def done(target: str | None) -> None:
            if not target:
                return

            def apply() -> str:
                store.link_concepts(self._tree_nodes, node["concept"], target)
                store.save_raw_tree(self._tree_nodes, self.repo / store.TREE_REL)
                self._refresh(node["concept"])
                return f"linked {node['concept']} → {target} (tree.json)"
            self._guarded("link", apply)
        self.push_screen(screens.LinkPicker(node["concept"], self._outline), done)

    def action_cycle_filter(self) -> None:
        i = store.FILTERS.index(self._type_filter)
        self._type_filter = store.FILTERS[(i + 1) % len(store.FILTERS)]
        self._render_outline()

    # ------------------------------------------------------------------ #
    # local tree: new roots and moves (never committed)

    def action_new_root(self) -> None:
        def done(name: str | None) -> None:
            if not name:
                return

            def apply() -> str:
                store.add_local_root(name)
                self._refresh()
                return f"local root added: {name} (in {store.overlay_path()}, never committed)"
            self._guarded("new root", apply)
        self.push_screen(screens.TextPrompt("New local root", "", "Root name"), done)

    def action_move_concept(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return

        def done(target: str | None) -> None:
            if target is None:
                return

            def apply() -> str:
                store.move_concept(name, target or None)
                self._refresh(name)
                return (f"moved {name} under {target} (local only)" if target
                        else f"{name} back under its repo parent")
            self._guarded("move", apply)
        self.push_screen(screens.LinkPicker(name, self._outline, title="Move under",
                                            extra=store.local_root_names(self._overlay),
                                            allow_clear=True), done)

    # ------------------------------------------------------------------ #
    # flashcards, quiz, export

    def _learn_names(self) -> list[str]:
        """The branch under the selected concept (or the whole tree)."""
        o = self._outline
        if not o:
            return []
        start = [self._selected] if self._selected else list(o.roots)
        out: list[str] = []
        seen: set[str] = set()
        stack = list(start)
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            out.append(cur)
            stack.extend(o.children.get(cur, []))
        return out

    def _with_cards(self, then: Callable[[list[dict]], None]) -> None:
        """Build the cards in a thread (one pack read per concept: a whole
        tree is hundreds of files), then hand them to `then` on the loop."""
        names, repo, outline, marks = self._learn_names(), self.repo, self._outline, self._marks
        self._status(f"building cards for {len(names)} concept(s)…")

        def work() -> None:
            cards = store.cards_for(repo, outline, names, marks)
            self._post(then, cards)
        self.run_worker(work, thread=True, group="cards", exclusive=True)

    def action_flashcards(self) -> None:
        def then(cards: list[dict]) -> None:
            if not cards:
                self._status("no researched concepts with a summary or facts under the selection")
                return
            self._status(f"{len(cards)} card(s)")
            self.push_screen(screens.Flashcards(cards))
        self._with_cards(then)

    def action_quiz(self) -> None:
        def then(cards: list[dict]) -> None:
            if len(cards) < 4:
                self._status("a quiz needs at least four researched concepts under the selection")
                return
            self._status(f"{len(cards)} card(s)")
            self.push_screen(screens.Quiz(cards))
        self._with_cards(then)

    def action_export_menu(self) -> None:
        name = self._selected
        current = self._current_file()
        options = [("concept", f"This concept as markdown ({name})" if name
                    else "This concept")]
        options.append(("branch", f"This branch (everything under {name})" if name
                        else "This branch"))
        if current:
            options.append(("file", f"The current file ({current[0].name})"))
        if self._bundle:
            options.append(("bundle", f"The bundle as one collection ({len(self._bundle)} files)"))

        def done(choice: str | None) -> None:
            if not choice:
                return

            def apply() -> str:
                if choice == "concept" and name:
                    out = store.export_concept(self.repo, self._outline, name, self._marks)
                elif choice == "branch" and name:
                    out = store.export_branch(self.repo, self._outline, name, self._marks)
                elif choice == "file" and current:
                    out = store.export_file(current[0], current[1])
                elif choice == "bundle":
                    out = store.export_bundle_markdown(list(self._bundle.values()), "bundle")
                else:
                    return "nothing to export: select a concept first"
                return f"exported {out}"
            self._guarded("export", apply)
        self.push_screen(screens.Chooser("Export to markdown", options), done)

    # ------------------------------------------------------------------ #
    # screens: library, ledger, skills, import, braindump, journal

    def _bundle_add(self, path: Path, kind: str, label: str) -> str:
        key = str(path.resolve())
        if key in self._bundle:
            del self._bundle[key]
            return f"removed from bundle: {path}"
        self._bundle[key] = store.bundle_item(path, kind, label)
        return f"added to bundle ({len(self._bundle)}): {path}"

    def action_library(self) -> None:
        self.push_screen(screens.Library(self.repo, self._bundle_add))

    def action_ledger(self) -> None:
        self.push_screen(screens.Ledger())

    def action_skills(self) -> None:
        default = self._selected or ""

        def done(result: tuple[str, str] | None) -> None:
            if not result:
                return
            skill, target = result
            try:
                argv = store.skill_argv(skill, target)
            except ValueError as exc:
                self._status(f"refusing to run {skill}: {exc}")
                return
            self._run_job(argv, f"{skill} on {target}")
        self.push_screen(screens.SkillRunner(default, store.claude_binary() is not None), done)

    def action_import_llms(self) -> None:
        concept = self._selected

        def done(source: str | None) -> None:
            if not source:
                return
            if self._import_busy:
                self._status("an import is already running; try again when it finishes")
                return
            self._import_busy = True
            self._status(f"importing {source}…")

            def finish() -> None:
                self._import_busy = False

            def work() -> None:
                try:
                    entry = store.import_llms(source, concept)
                except Exception as exc:  # network and file errors alike land in the status line
                    logger.warning("import of %r failed: %s", source, exc)
                    self._post(self._status, f"import failed: {exc}")
                    return
                finally:
                    self._post(finish)
                self._post(self._status, f"imported to {entry['path']} (see Library → Imports)")
            self.run_worker(work, thread=True, group="import")
        self.push_screen(screens.ImportDialog(concept), done)

    def action_braindump(self) -> None:
        def parse(path: Path) -> None:
            argv = store.braindump_argv(path)
            if not argv:
                self._status("claude CLI not found on PATH; the dump is saved, parse it later")
                return
            self._run_job(argv, f"braindump on {path.name}")
        self.push_screen(screens.Braindump(parse))

    def action_journal(self) -> None:
        def to_llms(folder: Path) -> None:
            try:
                argv = store.skill_argv("notes-to-llms-txt", str(folder))
            except ValueError as exc:
                self._status(f"refusing: {exc}")
                return
            if not argv:
                self._status("claude CLI not found on PATH")
                return
            self._run_job(argv, f"notes-to-llms-txt on {folder}")
        self.push_screen(screens.Journal(to_llms))

    def _run_job(self, argv: list[str], what: str, provider: str | None = None) -> None:
        """One research or skill agent job in a thread worker. The TUI stays up: the job
        log screen streams every event as it happens, escape hides it while
        the job keeps running, `x` there cancels, `o` brings it back. The
        tree is snapshotted before and validated after; a cancelled or
        timed-out job gets the snapshot restored."""
        if self._job is not None and not self._job.done:
            self._status(f"a job is already running ({self._job.what}); "
                         "o shows it, x there cancels it")
            return
        snapshot = store.snapshot_tree(self.repo)
        job = screens.JobState(what, store.job_log_path(what))
        self._job = job
        repo = self.repo
        prov = provider or store.active_provider()
        timeout = (10800 if prov == "ollama" and "LLMSX_RESEARCH_TIMEOUT" not in os.environ
                   else _RESEARCH_TIMEOUT_S)

        def work() -> None:
            result = store.run_claude_job(
                argv, repo, timeout=timeout, log=job.log,
                emit=lambda text: self._post(self._job_line, job, text), cancel=job.cancel,
                provider=prov)
            self._post(self._job_done, job, result, snapshot)
        self._status(f"running {what} (timeout {timeout}s) — o shows the log")
        self.run_worker(work, thread=True, group="job", exclusive=False)
        self.push_screen(screens.JobLog(job))

    def action_batch_research(self) -> None:
        """Research every unique frontier label below the selected concept."""
        root = self._selected
        if not root or not self._outline:
            self._status("select a concept branch first")
            return
        runner = self.repo / "hub" / "scripts" / "frontier_research_batch.py"
        if not runner.is_file():
            self._status(f"batch runner is missing: {runner}")
            return
        rows = store.frontier_under(self._outline, root)
        if not rows:
            self._status(f"no frontier concepts under {root}")
            return
        concepts = [str(row["concept"]) for row in rows]
        run_dir, _concepts_file = store.frontier_batch_paths(root, concepts)
        completed = store.completed_frontier_batch_count(run_dir / "results.jsonl")

        def confirmed(jobs: int | None) -> None:
            if jobs is None:
                return
            try:
                run_dir, concepts_file, resumed = store.write_frontier_batch(
                    root, rows, jobs=jobs)
            except (OSError, ValueError) as exc:
                self._status(f"could not prepare frontier batch: {exc}")
                return
            self._run_frontier_batch(runner, concepts_file, run_dir, jobs,
                                     len(concepts), resumed)

        self.push_screen(screens.BatchResearch(root, concepts, completed=completed), confirmed)

    def _run_frontier_batch(self, runner: Path, concepts_file: Path, run_dir: Path,
                            jobs: int, count: int, resumed: bool) -> None:
        if self._job is not None and not self._job.done:
            self._status(f"a job is already running ({self._job.what}); o shows it")
            return
        argv = [sys.executable, str(runner), "--repo", str(self.repo),
                "--run-dir", str(run_dir), "--concepts", str(concepts_file),
                "--jobs", str(jobs)]
        label = "resume" if resumed else "start"
        job = screens.JobState(f"MongoDB frontier batch {label} ({count} concepts)",
                               store.job_log_path(f"frontier batch {run_dir.name}"))
        self._job = job

        def work() -> None:
            result = store.run_claude_job(
                argv, self.repo, timeout=24 * 60 * 60, log=job.log,
                emit=lambda line: self._post(self._job_line, job, line),
                cancel=job.cancel, provider="batch")
            spec = store.frontier_batch_sync_spec(run_dir)
            if spec:
                helper = (Path.home() / ".claude/skills/concept-family-explorer/scripts/"
                          "sync_trees.py")
                if helper.is_file():
                    sync = subprocess.run(
                        [sys.executable, str(helper), "--spec", str(spec), "--repo",
                         str(self.repo), "--hub-dir", str(Path.home() / ".global-ai-hub"),
                         "--apply", "--regen"], cwd=self.repo, text=True,
                        capture_output=True, timeout=1800, check=False)
                    detail = (sync.stdout + "\n" + sync.stderr).strip()
                    self._post(self._job_line, job, f"tree sync exit {sync.returncode}: {detail}")
                else:
                    self._post(self._job_line, job,
                               f"tree sync skipped: helper missing at {helper}")
            self._post(self._frontier_batch_done, job, result, run_dir)

        action = "resuming" if resumed else "starting"
        self._status(f"{action} frontier batch: {count} concepts, {jobs} concurrent · "
                     f"checkpoint {run_dir / 'results.jsonl'} · o shows the log")
        self.run_worker(work, thread=True, group="job", exclusive=False)
        self.push_screen(screens.JobLog(job))

    def _frontier_batch_done(self, job: screens.JobState, result: store.JobResult,
                             run_dir: Path) -> None:
        job.done = True
        if result.returncode == 0 and result.status == "ok":
            job.state = "ok"
            status = "completed"
            message = f"done — {job.what}; checkpoint: {run_dir / 'results.jsonl'}"
        elif result.status == "cancelled":
            job.state = "cancelled"
            status = "paused"
            message = f"batch cancelled and resumable — {run_dir / 'results.jsonl'}"
        elif result.returncode == 2:
            job.state = "paused"
            status = "paused"
            message = f"batch paused by its research runner — {run_dir / 'results.jsonl'}"
        else:
            job.state = result.status
            status = "failed"
            message = (f"batch {result.status}: {result.message} · checkpoint: "
                       f"{run_dir / 'results.jsonl'}")
        try:
            store.finish_frontier_batch(run_dir, status, result.message)
        except (OSError, ValueError) as exc:
            logger.warning("could not update frontier batch checkpoint %s: %s", run_dir, exc)
        self._job_line(job, message)
        shown = self._job_screen(job)
        if shown is not None:
            shown.refresh_head()
        self._status(message)

    def _job_screen(self, job: screens.JobState) -> screens.JobLog | None:
        top = self.screen
        return top if isinstance(top, screens.JobLog) and top.job is job else None

    def _job_line(self, job: screens.JobState, text: str) -> None:
        shown = self._job_screen(job)
        for line in text.split("\n"):
            job.lines.append(line)
            if shown is not None:
                shown.append(line)

    def _job_done(self, job: screens.JobState, result: store.JobResult, snapshot: str) -> None:
        job.done, job.state = True, result.status
        if result.status in ("timeout", "cancelled"):
            store.restore_tree_snapshot(self.repo, snapshot)
            ok, msg = False, f"{result.message}; tree snapshot restored"
        elif result.status == "oserror":
            ok, msg = False, result.message
        else:
            ok, msg = store.verify_tree_after_run(self.repo, snapshot)
            if result.status == "error":
                ok, msg = False, f"runner reported an error: {result.message} · {msg}"
        if not ok:
            logger.warning("job %r failed: %s", job.what, msg)
        self._refresh()
        line = ("done — " if ok else "FAILED — ") + f"{job.what}: {msg}"
        self._job_line(job, line)
        shown = self._job_screen(job)
        if shown is not None:
            shown.refresh_head()
        self._status(f"{line}  (log: {job.log})")
        if getattr(self, "_autopilot", False):
            if ok:
                self.set_timer(0.5, self._autopilot_step)
            else:
                self._autopilot = False
                self._update_autopilot_button()
                self._status(f"autopilot stopped after job failure: {msg}")

    def action_job_log(self) -> None:
        if self._job is None:
            self._status("no job has run yet — R researches the selected concept, S runs a skill")
            return
        if self._job_screen(self._job) is None:
            self.push_screen(screens.JobLog(self._job))

    # ------------------------------------------------------------------ #
    # editing

    def action_edit_node(self) -> None:
        """Edit the node in `$EDITOR` (the pane hands the terminal to vim or
        whatever is set); the in-app form is the fallback when no editor is
        configured."""
        node = self._require_node()
        if not node:
            return
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if editor:
            self._edit_node_in_editor(node, editor)
            return
        self._edit_node_in_form(node)

    def _edit_node_in_editor(self, node: dict, editor: str) -> None:
        import tempfile
        key = node["slug"]
        text = store.node_edit_text(node).replace(
            "## tags\n", "## tags\n" + "".join(f"{t}\n" for t in store.tags_of(self._marks, key)))
        tmpdir = store.home() / "tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f"llmsx-edit-{key}-", suffix=".md", dir=str(tmpdir))
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        try:
            argv = shlex.split(editor, posix=(os.name != "nt")) + [tmp]
            with self.suspend():
                rc = subprocess.call(argv)
            edited = Path(tmp).read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            self._status(f"could not run {editor!r}: {exc}")
            return
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        if rc != 0:
            self._status(f"{editor} exited {rc}; nothing changed")
            return

        def apply() -> str:
            fields = store.parse_node_edit(edited)
            if fields is None:
                return "edit cancelled (file emptied)"
            store.apply_node_edit(self._tree_nodes, node["concept"], fields)
            store.save_raw_tree(self._tree_nodes, self.repo / store.TREE_REL)
            self._marks = store.set_tags(self.repo, key, fields.get("tags", []))
            self._refresh(node["concept"])
            return f"saved {store.TREE_REL} and tags: {node['concept']}"
        self._guarded("edit", apply)

    def _edit_node_in_form(self, node: dict) -> None:
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
        active_provider = store.active_provider()

        def done(result: tuple[str, str] | str | None) -> None:
            if not result:
                return
            if isinstance(result, tuple):
                mode, provider = result
            else:
                mode, provider = result, active_provider
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
            # Call _run_research tolerating lambdas with only 3 positional args in tests
            import inspect
            sig = inspect.signature(self._run_research)
            if len(sig.parameters) >= 4 or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                self._run_research(name, mode, parent, provider=provider)
            else:
                self._run_research(name, mode, parent)
        self.push_screen(Research(name, parent, provider=active_provider), done)

    def _run_research(self, name: str, mode: str, parent: str | None, provider: str | None = None) -> None:
        prov = provider or store.active_provider()
        argv = store.research_argv(name, mode, parent, provider=prov)
        if not argv:
            lbl = "claude" if prov == "claude" else store.PROVIDER_LABELS.get(prov, prov)
            self._status(f"{lbl} CLI not found on PATH")
            return
        try:
            import inspect
            sig = inspect.signature(self._run_job)
            if "provider" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                self._run_job(argv, f"{mode} research on {name}", provider=prov)
            else:
                self._run_job(argv, f"{mode} research on {name}")
        except Exception:
            self._run_job(argv, f"{mode} research on {name}")

    def action_help(self) -> None:
        self.push_screen(screens.HotkeyHelp())

    def action_queue_viewer(self) -> None:
        self.push_screen(screens.QueueViewer(
            self.repo,
            get_job=lambda: self._job,
            on_run=self._run_from_queue,
            on_job_screen=lambda j: self.push_screen(screens.JobLog(j)),
        ))

    def _run_from_queue(self, concept: str, mode: str, parent: str | None) -> None:
        why = store.unsafe_name_reason(concept)
        if why:
            self._status(f"refusing to build a research prompt: the concept name {why}")
            return
        self._run_research(concept, mode, parent)

    def action_add_highlight(self) -> None:
        name = self._selected or ""

        def done(result: tuple[str, str] | None) -> None:
            if not result:
                return
            text, note = result

            def apply() -> str:
                store.add_highlight(name, text, note)
                self._refresh(name, reload=False)
                return f"saved highlight for {name or 'General'}"
            self._guarded("highlight", apply)
        self.push_screen(screens.AddHighlight(name), done)

    def action_view_highlights(self) -> None:
        self.push_screen(screens.HighlightsScreen(on_jump=self.jump_to))

    def action_quick_dr(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return
        why = store.unsafe_name_reason(name)
        if why:
            self._status(f"refusing to build a research prompt: the concept name {why}")
            return
        parent = self._outline.parent_of(name) if self._outline else None
        node = self._node(name)
        if node and node.get("parentConcept"):
            parent = node["parentConcept"]
        if parent and not store.safe_name(parent):
            parent = None
        self._run_research(name, "dr", parent)

    def action_quick_queue(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return
        parent = self._outline.parent_of(name) if self._outline else None
        node = self._node(name)
        if node and node.get("parentConcept"):
            parent = node["parentConcept"]

        def apply() -> str:
            added = store.queue_concept(self.repo, name, parent, "dr")
            self._refresh(name)
            return f"queued {name}" if added else f"already queued: {name}"
        self._guarded("queue", apply)

    def action_quick_rabbithole(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return
        why = store.unsafe_name_reason(name)
        if why:
            self._status(f"refusing to build a research prompt: the concept name {why}")
            return
        parent = self._outline.parent_of(name) if self._outline else None
        node = self._node(name)
        if node and node.get("parentConcept"):
            parent = node["parentConcept"]
        if parent and not store.safe_name(parent):
            parent = None
        self._run_research(name, "deep", parent)

    def action_quick_concept_explorer(self) -> None:
        name = self._selected
        if not name:
            self._status("select a concept first")
            return
        why = store.unsafe_name_reason(name)
        if why:
            self._status(f"refusing to build a research prompt: the concept name {why}")
            return
        parent = self._outline.parent_of(name) if self._outline else None
        node = self._node(name)
        if node and node.get("parentConcept"):
            parent = node["parentConcept"]
        if parent and not store.safe_name(parent):
            parent = None
        self._run_research(name, "family", parent)

    def action_toggle_autopilot(self) -> None:
        self._autopilot = not self._autopilot
        self._update_autopilot_button()
        if self._autopilot:
            self._status("autopilot started: scanning frontiers…")
            self._autopilot_step()
        else:
            self._status("autopilot stopped")

    def _update_autopilot_button(self) -> None:
        try:
            btn = self._main.query_one("#btn-auto", Button)
            if self._autopilot:
                btn.label = "🚀 Auto: ON"
                btn.variant = "warning"
            else:
                btn.label = "🚀 Auto"
                btn.variant = "default"
        except Exception:
            pass

    def _autopilot_step(self) -> None:
        if not getattr(self, "_autopilot", False):
            return
        if self._job is not None and self._job.state == "running":
            return
        if not self._outline:
            self._refresh(reload=True)
        if not self._outline:
            self._autopilot = False
            self._update_autopilot_button()
            self._status("autopilot stopped: tree outline not available")
            return

        frontier = store.frontier_concepts(self._outline)
        if frontier:
            target = frontier[0]
            parent = self._outline.parent_of(target)
            self._select(target)
            self._status(f"autopilot: running /dr on frontier '{target}' ({len(frontier)} remaining)")
            self._run_research(target, "dr", parent)
        else:
            target = store.most_used_concept(self.repo, self._outline)
            if not target:
                self._autopilot = False
                self._update_autopilot_button()
                self._status("autopilot: no concepts available to expand")
                return
            parent = self._outline.parent_of(target)
            self._select(target)
            self._status(f"autopilot: no frontier left; expanding most-used concept '{target}' with concept-family-explorer")
            self._run_research(target, "family", parent)

    @on(Button.Pressed)
    def _quick_action_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-dr":
            self.action_quick_dr()
        elif bid == "btn-queue":
            self.action_quick_queue()
        elif bid == "btn-rabbithole":
            self.action_quick_rabbithole()
        elif bid in ("btn-family", "btn-concept-explorer"):
            self.action_quick_concept_explorer()
        elif bid == "btn-batch":
            self.action_batch_research()
        elif bid == "btn-auto":
            self.action_toggle_autopilot()
        elif bid == "btn-view-queue":
            self.action_queue_viewer()
        elif bid == "btn-highlight":
            self.action_add_highlight()
        elif bid == "btn-help":
            self.action_help()
        elif bid == "btn-provider":
            self.action_settings()

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
                prov = values.get("provider")
                if prov:
                    store.set_provider(prov)
                if values.get("model"):
                    store.set_provider_model(prov or store.active_provider(), values["model"])
                pkeys = values.get("provider_keys")
                if isinstance(pkeys, dict):
                    for kprov, kval in pkeys.items():
                        if kval == "-":
                            store.set_provider_api_key(kprov, "")
                        elif kval.strip():
                            store.set_provider_api_key(kprov, kval.strip())
                tok = values.get("token")
                if tok == "-":
                    store.set_github_token("")
                elif tok and tok.strip():
                    store.set_github_token(tok)

                try:
                    self._main.query_one("#btn-provider", Button).label = f"🤖 {store.active_provider()}"
                except Exception:
                    pass
                return f"settings saved: {p} (mode 0600)"
            self._guarded("settings", apply)
            if values.get("panels"):
                self.action_panels()
        self.push_screen(Settings(cfg, bool(os.environ.get("LLMSX_GITHUB_TOKEN")), tester), done)

    def action_panels(self) -> None:
        def done(panels: dict[str, bool] | None) -> None:
            if panels is None:
                return

            def apply() -> str:
                cfg = store.load_config()
                cfg["panels"] = panels
                p = store.save_config(cfg)
                self._panels = panels
                self._apply_panels()
                if self._selected:
                    self._refresh(reload=False)
                hidden = [k for k, v in panels.items() if not v]
                shown = ("hidden " + ", ".join(hidden)) if hidden else "all shown"
                return f"windows saved to {p}: {shown}"
            self._guarded("windows", apply)
        self.push_screen(screens.PanelSettings(self._panels), done)


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
        handler = logging.FileHandler(str(log), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
        root = logging.getLogger()
        for old in list(root.handlers):      # `llmsx` main() already pointed the root at stderr
            root.removeHandler(old)
        root.addHandler(handler)
        root.setLevel(min(root.level or logging.WARNING, logging.WARNING))
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

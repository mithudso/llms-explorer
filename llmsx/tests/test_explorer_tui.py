# llmsx/tests/test_explorer_tui.py — the Textual workbench, driven headless by Pilot.
# ruff: noqa: E501
from __future__ import annotations

import asyncio
import contextlib
import json
import subprocess

import pytest

pytest.importorskip("textual")

from llmsx import explorer_store as es  # noqa: E402
from conftest import INJECTION, make_repo  # noqa: E402


async def _settle(app, pilot, delay: float = 0.0):
    """One tick for the message/mount, the render and git workers to finish,
    one more for the dismiss callback and the status update. `delay` lets the
    filter's 0.15 s debounce timer fire."""
    await pilot.pause(delay) if delay else await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _run(coro_factory, repo):
    from llmsx.explorer import Explorer

    async def go():
        app = Explorer(repo, auto_sync=False)
        async with app.run_test(size=(140, 44)) as pilot:
            await coro_factory(app, pilot)
        return app

    return asyncio.run(go())


def _labels(tree):
    out = []

    def walk(node):
        for child in node.children:
            out.append(str(child.label))
            walk(child)
    walk(tree.root)
    return out


def _status(app) -> str:
    from textual.widgets import Static
    return str(app.query_one("#status", Static).render())


def _md(app, widget_id: str) -> str:
    """The markdown source of a Markdown widget, or of the one inside a TabPane."""
    from textual.widgets import Markdown, TabPane
    node = app.query_one(f"#{widget_id}")
    if isinstance(node, TabPane):
        node = node.query_one(Markdown)
    return node._markdown or ""


def test_outline_renders_roots_and_frontier_and_filter_reveals_nested(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from textual.widgets import Input
        from llmsx.explorer import OutlineTree
        tree = app.query_one("#outline", OutlineTree)
        labels = _labels(tree)
        assert labels[0].startswith("Root Domain")
        assert any(lbl.startswith("Kid Concept") and "●" in lbl for lbl in labels)
        assert any("Ghost Concept" in lbl and "(frontier)" in lbl for lbl in labels)
        app.query_one("#filter", Input).value = "kiddo"       # an alias, not the name
        await _settle(app, pilot, 0.3)
        assert [lbl.split("  ")[0].rstrip(" ●") for lbl in _labels(tree)] == ["Root Domain", "Kid Concept"]
        app.query_one("#filter", Input).value = "ghost"       # a frontier concept, by name
        await _settle(app, pilot, 0.3)
        assert [lbl.split("  ")[0] for lbl in _labels(tree)] == ["Root Domain", "Ghost Concept"]
        app.query_one("#filter", Input).value = "zzz"
        await _settle(app, pilot, 0.3)
        assert _labels(tree) == []
        app.query_one("#filter", Input).value = ""
        await _settle(app, pilot, 0.3)
        assert len(_labels(tree)) == 3

    _run(check, repo)


def test_selecting_a_node_renders_in_place_and_keeps_injection_literal(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from textual.widgets import TabbedContent
        app._select("Kid Concept")
        await _settle(app, pilot)
        assert app._selected == "Kid Concept"
        assert len(app.screen_stack) == 1, "selection never pushes a screen"
        assert "Kid Concept" in _md(app, "md-overview") and INJECTION in _md(app, "md-overview")
        tabs = app.query_one("#tabs", TabbedContent)
        assert _md(app, "md-facts") == "", "a non-active tab renders lazily"
        tabs.active = "pane-facts"
        await _settle(app, pilot)
        assert "Definitions" in _md(app, "md-facts") and INJECTION in _md(app, "md-facts")
        tabs.active = "pane-skill"
        await _settle(app, pilot)
        assert "Kid skill" in _md(app, "md-skill") and INJECTION in _md(app, "md-skill")
        titles = [str(p._title) for p in tabs.query("TabPane")]
        assert "ref: depth" in titles and "llms" in titles
        ref_id = [p.id for p in tabs.query("TabPane") if str(p._title) == "ref: depth"][0]
        assert _md(app, ref_id) == "", "a dynamic pane is empty until opened"
        tabs.active = ref_id
        await _settle(app, pilot)
        assert "First paragraph" in _md(app, ref_id) and "&lt;script>" in _md(app, ref_id)
        app._fill("pane-that-does-not-exist")          # a pane removed by a re-render
        assert "pane-that-does-not-exist" not in app._filled
        assert (repo / es.TREE_REL).read_text().count(INJECTION) == 1, "nothing acted on the text"
        app._select("Ghost Concept")
        await _settle(app, pilot)
        assert "frontier" in _md(app, "md-overview")
        tabs.active = "pane-facts"
        await _settle(app, pilot)
        assert "not available" in _md(app, "md-facts")

    _run(check, repo)


def test_marks_and_queue_row_via_the_modals(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from llmsx.explorer import Confirm, MarkFurther, OutlineTree
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_clear_mark()
        await _settle(app, pilot)
        assert not (repo / es.MARKS_REL).exists(), "clearing an absent mark writes nothing"
        app.action_mark_review()
        await _settle(app, pilot)
        assert isinstance(app.screen, Confirm)
        app.screen.dismiss(True)
        await _settle(app, pilot)
        assert json.loads((repo / es.MARKS_REL).read_text())["kid-concept"]["state"] == "needs-review"
        app.action_mark_further()
        await _settle(app, pilot)
        assert isinstance(app.screen, MarkFurther)
        app.screen.query_one("#note").value = "go deeper"
        app.screen._ok()
        await _settle(app, pilot)
        marks = json.loads((repo / es.MARKS_REL).read_text())
        assert marks["kid-concept"] == {"state": "further-research", "at": marks["kid-concept"]["at"], "note": "go deeper"}
        assert (repo / es.QUEUE_REL).read_text().endswith("- [ ] Concept: `Kid Concept` | Parent: `Root Domain` | Mode: `dr`\n")
        assert any("[further-research]" in lbl for lbl in _labels(app.query_one("#outline", OutlineTree)))
        app.action_clear_mark()
        await _settle(app, pilot)
        assert json.loads((repo / es.MARKS_REL).read_text()) == {}

    _run(check, repo)


def test_notes_land_in_home_and_edit_node_writes_tree(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from llmsx.explorer import EditNode, Notes, OutlineTree
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_notes()
        await _settle(app, pilot)
        assert isinstance(app.screen, Notes)
        app.screen.dismiss("remember: " + INJECTION)
        await _settle(app, pilot)
        assert (home / "notes" / "kid-concept.md").read_text() == "remember: " + INJECTION + "\n"
        assert not list(repo.rglob("kid-concept.md"))
        assert "remember: " + INJECTION in _md(app, "md-overview")
        app.action_edit_node()
        await _settle(app, pilot)
        assert isinstance(app.screen, EditNode)
        app.screen.dismiss({"summary": "edited", "aliases": ["kiddo"], "add_child": "New Frontier"})
        await _settle(app, pilot)
        nodes = json.loads((repo / es.TREE_REL).read_text())
        assert nodes[1]["summary"] == "edited" and nodes[1]["childConcepts"] == ["New Frontier"]
        assert nodes[0]["extraKey"] == {"keep": True}
        assert any("New Frontier" in lbl for lbl in _labels(app.query_one("#outline", OutlineTree)))

    _run(check, repo)


def test_bundle_toggle_and_export(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    monkeypatch.setattr(es, "copy_to_clipboard", lambda _t: False)

    async def check(app, pilot):
        from textual.widgets import TabbedContent
        from llmsx.explorer import Bundle
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_bundle_toggle()
        await _settle(app, pilot)
        assert app._bundle == {} and "no file behind it" in _status(app)
        tabs = app.query_one("#tabs", TabbedContent)
        tabs.active = "pane-skill"
        await _settle(app, pilot)
        app.action_bundle_toggle()
        await _settle(app, pilot)
        assert len(app._bundle) == 1
        tabs.active = "pane-facts"
        await _settle(app, pilot)
        app.action_bundle_toggle()
        await _settle(app, pilot)
        assert len(app._bundle) == 2
        app.action_bundle_screen()
        await _settle(app, pilot)
        assert isinstance(app.screen, Bundle)
        app.screen.dismiss("my-bundle")
        await _settle(app, pilot)
        out = home / "bundles" / "my-bundle"
        data = json.loads((out / "bundle.json").read_text())
        assert {d["kind"] for d in data} == {"skill", "pack"}
        assert (out / "bundle.md").read_text().startswith("# Bundle: my-bundle\n")
        assert "bundle exported" in _status(app)
        ref_id = [p.id for p in tabs.query("TabPane") if str(p._title) == "ref: depth"][0]
        tabs.active = ref_id
        await _settle(app, pilot)
        app.action_bundle_toggle()
        await _settle(app, pilot)
        assert any(str(p._title).endswith("✓") for p in tabs.query("TabPane")), "bundled files are ticked"
        app.action_bundle_screen()
        await _settle(app, pilot)
        app.screen.dismiss("")
        await _settle(app, pilot)
        assert app._bundle == {} and "bundle cleared" in _status(app)

    _run(check, repo)


def test_research_without_claude_only_queues(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    monkeypatch.setattr(es.shutil, "which", lambda _n: None)

    async def check(app, pilot):
        from llmsx.explorer import Research
        app._select("Ghost Concept")
        await _settle(app, pilot)
        app.action_research()
        await _settle(app, pilot)
        assert isinstance(app.screen, Research)
        assert not app.screen._have_claude
        app.screen.dismiss("queue")
        await _settle(app, pilot)
        assert (repo / es.QUEUE_REL).read_text().endswith("- [ ] Concept: `Ghost Concept` | Parent: `Root Domain`\n")

    _run(check, repo)


def test_run_research_hands_the_job_to_the_background_runner(tmp_path, home, monkeypatch):
    """The suspend-and-block path is gone (test_explorer_jobs.py covers the
    runner); research builds the argv and hands it to `_run_job`."""
    repo = make_repo(tmp_path, git=False)
    monkeypatch.setattr(es, "research_argv", lambda *_a, **_k: ["claude", "-p", "x"])
    jobs = []

    async def check(app, pilot):
        monkeypatch.setattr(app, "_run_job", lambda argv, what: jobs.append((argv, what)))
        app._select("Kid Concept")
        await _settle(app, pilot)
        app._run_research("Kid Concept", "dr", "Root Domain")
        await _settle(app, pilot)
        assert jobs == [(["claude", "-p", "x"], "dr research on Kid Concept")]
        monkeypatch.setattr(es, "research_argv", lambda *_a, **_k: None)
        app._run_research("Kid Concept", "dr", "Root Domain")
        await _settle(app, pilot)
        assert "claude CLI not found" in _status(app)

    _run(check, repo)


def test_research_refuses_unsafe_names_only_for_prompt_modes(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    nodes = json.loads((repo / es.TREE_REL).read_text())
    nodes[0]["childConcepts"].append("Bad`Name`")
    (repo / es.TREE_REL).write_text(json.dumps(nodes))
    monkeypatch.setattr(es.shutil, "which", lambda _n: "/usr/bin/claude")
    from llmsx import explorer
    monkeypatch.setattr(explorer.subprocess, "run", lambda *_a, **_k: pytest.fail("must not launch"))

    async def check(app, pilot):
        app._select("Bad`Name`")
        await _settle(app, pilot)
        app.action_research()
        await _settle(app, pilot)
        app.screen.dismiss("dr")
        await _settle(app, pilot)
        assert "refusing to build a research prompt" in _status(app)
        app.action_research()
        await _settle(app, pilot)
        app.screen.dismiss("queue")
        await _settle(app, pilot)
        assert "queue failed" in _status(app) and "Bad`Name`" not in (repo / es.QUEUE_REL).read_text(), "a backtick name cannot become a queue row either"

    _run(check, repo)


def test_pull_failure_is_reported_in_the_status_line_not_raised(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)

    def boom(_repo):
        raise es.GitError("fatal: no remote")
    monkeypatch.setattr(es, "git_pull", boom)

    async def check(app, pilot):
        app.action_sync()
        await _settle(app, pilot)
        assert "sync (git pull --ff-only) failed, working offline: fatal: no remote" in _status(app)
        monkeypatch.setattr(es, "git_pull", lambda _r: "Already up to date.")
        app.action_sync()
        await _settle(app, pilot)
        assert _status(app) == "sync: Already up to date."

    _run(check, repo)


def test_git_actions_are_serialised_and_posts_survive_app_exit(tmp_path, home, monkeypatch):
    import threading
    repo = make_repo(tmp_path, git=False)
    gate = threading.Event()
    calls = []

    def slow_pull(_repo):
        calls.append("pull")
        gate.wait(5)
        return "Already up to date."
    monkeypatch.setattr(es, "git_pull", slow_pull)

    async def check(app, pilot):
        app.action_sync()
        await pilot.pause()
        app.action_sync()
        await pilot.pause()
        assert "already running; sync skipped" in _status(app)
        app._commit_and_push("explorer: x", "origin")      # the commit half shares the slot
        await pilot.pause()
        assert "already running; commit skipped" in _status(app)
        gate.set()
        await _settle(app, pilot)
        assert calls == ["pull"] and _status(app) == "sync: Already up to date."
        assert not app._git_busy

        def closed(*_a, **_k):
            raise RuntimeError("closed")
        monkeypatch.setattr(app, "call_from_thread", closed)
        app._post(lambda: None)          # must not raise

    _run(check, repo)


def test_filter_debounce_collapses_keystrokes_and_render_survives_io_errors(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from textual.widgets import Input
        from llmsx.explorer import OutlineTree
        renders = []
        original = app._render_outline
        monkeypatch.setattr(app, "_render_outline", lambda: renders.append(1) or original())
        box = app.query_one("#filter", Input)
        for v in ("k", "ki", "kid"):
            box.value = v
            await pilot.pause(0.02)
        await _settle(app, pilot, 0.3)
        assert renders == [1], "three keystrokes inside the debounce window render once"
        assert [lbl.split("  ")[0].rstrip(" ●") for lbl in _labels(app.query_one("#outline", OutlineTree))] == ["Root Domain", "Kid Concept"]

        from textual.widgets import TabbedContent
        app._select("Kid Concept")
        await _settle(app, pilot)
        tabs = app.query_one("#tabs", TabbedContent)
        tabs.active = "pane-facts"
        await _settle(app, pilot)
        assert "Definitions" in _md(app, "md-facts")

        def boom(*_a):
            raise OSError("disk swapped")
        monkeypatch.setattr(es, "pack_path", boom)
        app._select("Root Domain")
        await _settle(app, pilot)
        assert "could not read this concept" in _md(app, "md-facts"), "the failing pane says so"
        assert "Root Domain" in _md(app, "md-overview"), "the overview still rendered"
        assert "Definitions" not in _md(app, "md-facts"), "no stale pane from the previous concept"
        assert len(app.screen_stack) == 1

        # a status fetch that fails inside the commit worker releases the git slot
        def status_boom(_r):
            raise es.GitError("boom")
        monkeypatch.setattr(es, "changed_allowlisted", status_boom)
        app.action_commit()
        await _settle(app, pilot)
        assert _status(app) == "git status failed: boom" and not app._git_busy
        assert len(app.screen_stack) == 1

        # a re-selection before the previous render finishes leaves no orphan panes
        app._select("Kid Concept")
        app._select("Ghost Concept")
        await _settle(app, pilot)
        app._select("Kid Concept")
        await _settle(app, pilot)
        assert app._pending_removal == []
        titles = [str(p._title) for p in tabs.query("TabPane")]
        assert titles.count("ref: depth") == 1 and titles.count("llms") == 1

    _run(check, repo)


def test_commit_refuses_when_nothing_allowlisted_changed(tmp_path, home, git_template):
    repo = make_repo(tmp_path, template=git_template)

    async def check(app, pilot):
        (repo / "README.md").write_text("dirty\n")
        app.action_commit()
        await _settle(app, pilot)
        assert len(app.screen_stack) == 1
        assert "nothing to commit" in _status(app)

    _run(check, repo)


def test_commit_flow_commits_then_pushes_only_with_a_token(tmp_path, home, monkeypatch, git_template):
    repo = make_repo(tmp_path, template=git_template)
    pushed = []
    monkeypatch.setattr(es, "git_push", lambda _r, remote, token: pushed.append((remote, token)) or "ok")

    async def check(app, pilot):
        from llmsx.explorer import Confirm
        app._select("Kid Concept")
        await _settle(app, pilot)
        es.set_mark(repo, "kid-concept", "needs-review")
        app.action_commit()
        await _settle(app, pilot)
        assert isinstance(app.screen, Confirm)
        app.screen.dismiss(True)
        await _settle(app, pilot)
        assert "; not pushed (no token" in _status(app) and pushed == []
        log = subprocess.run(["git", "log", "--format=%s", "-1"], cwd=repo, capture_output=True, text=True).stdout
        assert log.strip() == "explorer: Kid Concept"
        es.set_mark(repo, "kid-concept", "further-research")
        es.set_github_token("ghp_tokentoken")
        app.action_commit()
        await _settle(app, pilot)
        app.screen.dismiss(True)
        await _settle(app, pilot)
        assert pushed == [("origin", "ghp_tokentoken")] and "pushed to origin" in _status(app)
        monkeypatch.setattr(es, "commit_allowlisted", lambda *_a: (_ for _ in ()).throw(es.GitError("boom")))
        es.set_mark(repo, "root-domain", "needs-review")
        app.action_commit()
        await _settle(app, pilot)
        app.screen.dismiss(True)
        await _settle(app, pilot)
        assert _status(app) == "commit failed: boom"

    _run(check, repo)


def test_unsafe_names_stay_out_of_commit_messages_and_queue_rows(tmp_path, home, git_template, monkeypatch):
    repo = make_repo(tmp_path, template=git_template)
    nodes = json.loads((repo / es.TREE_REL).read_text())
    nodes[1]["concept"] = "Kid `rm -rf` Concept"
    nodes[0]["childConcepts"] = ["Kid `rm -rf` Concept", "Ghost Concept"]
    (repo / es.TREE_REL).write_text(json.dumps(nodes))
    subprocess.run(["git", "commit", "-qam", "rename"], cwd=repo, check=True)

    async def check(app, pilot):
        from llmsx.explorer import Confirm, MarkFurther
        app._select("Kid `rm -rf` Concept")
        await _settle(app, pilot)
        app.action_mark_further()
        await _settle(app, pilot)
        assert isinstance(app.screen, MarkFurther)
        app.screen._ok()
        await _settle(app, pilot)
        assert "mark failed" in _status(app) and "backtick" in _status(app)
        assert "rm -rf" not in (repo / es.QUEUE_REL).read_text()
        es.set_mark(repo, "kid-concept", "needs-review")
        app.action_commit()
        await _settle(app, pilot)
        assert isinstance(app.screen, Confirm)
        assert "rm -rf" not in app.screen._body and "update concept tree" in app.screen._body
        app.screen.dismiss(False)
        await _settle(app, pilot)

    _run(check, repo)


def test_settings_save_validate_and_test_token(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    seen = []
    monkeypatch.setattr(es, "test_token", lambda _r, remote, token: seen.append((remote, token)) or "ok: 1 branch(es)")

    async def check(app, pilot):
        from textual.widgets import Static
        from llmsx.explorer import Settings
        app.action_settings()
        await _settle(app, pilot)
        assert isinstance(app.screen, Settings)
        assert app.screen._tester("https://github.com/me/fork.git", "ghp_abcdefgh") == "ok: 1 branch(es)"
        assert seen == [("https://github.com/me/fork.git", "ghp_abcdefgh")]
        app.screen.query_one("#token").value = "ghp_abcdefgh"
        await pilot.click("#test")
        await _settle(app, pilot)
        assert "ok: 1 branch" in str(app.screen.query_one("#test-result", Static).render())
        app.screen.dismiss({"repo_url": "https://github.com/me/x.git", "push_url": "https://github.com/me/fork.git", "token": "ghp_abcdefgh"})
        await _settle(app, pilot)
        cfg = es.load_config()
        assert cfg == {"repo_url": "https://github.com/me/x.git", "push_url": "https://github.com/me/fork.git", "github_token": "ghp_abcdefgh"}
        assert "settings saved" in _status(app)
        app.action_settings()
        await _settle(app, pilot)
        app.screen.dismiss({"repo_url": "https://github.com/me/x.git", "push_url": "ext::sh", "token": "-"})
        await _settle(app, pilot)
        assert "settings failed: push_url" in _status(app)
        assert es.load_config()["github_token"] == "ghp_abcdefgh", "a rejected save changes nothing"
        app.action_settings()
        await _settle(app, pilot)
        app.screen.dismiss({"repo_url": "https://github.com/me/x.git", "push_url": "origin", "token": "-"})
        await _settle(app, pilot)
        assert "github_token" not in es.load_config()

    _run(check, repo)


def test_edit_file_uses_editor_or_explains(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    from llmsx import explorer
    calls = []
    monkeypatch.setattr(explorer.subprocess, "call", lambda argv: calls.append(argv) or 0)
    monkeypatch.setattr(explorer.Explorer, "suspend", lambda self: contextlib.nullcontext())

    async def check(app, pilot):
        from textual.widgets import TabbedContent
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_edit_file()
        await _settle(app, pilot)
        assert "no file behind it" in _status(app) and calls == []
        app.query_one("#tabs", TabbedContent).active = "pane-skill"
        await _settle(app, pilot)
        monkeypatch.delenv("EDITOR", raising=False)
        monkeypatch.delenv("VISUAL", raising=False)
        app.action_edit_file()
        await _settle(app, pilot)
        assert "$EDITOR is not set" in _status(app) and calls == []
        monkeypatch.setenv("EDITOR", "myeditor --flag")
        app.action_edit_file()
        await _settle(app, pilot)
        skill = repo / es.SKILLS_REL / "kidskill" / "SKILL.md"
        assert calls == [["myeditor", "--flag", str(skill)]] and "exited 0" in _status(app)
        monkeypatch.setenv("EDITOR", "vim '")
        app.action_edit_file()
        await _settle(app, pilot)
        assert "could not run" in _status(app) and len(calls) == 1

    _run(check, repo)


def test_run_entry_point_clones_or_explains(tmp_path, home, monkeypatch, capsys):
    from llmsx import explorer
    monkeypatch.setattr(explorer.Explorer, "run", lambda self: None)
    assert explorer.run(repo=str(tmp_path)) == 2
    assert "no concept tree at" in capsys.readouterr().out
    checkout = make_repo(tmp_path, git=False)
    monkeypatch.setattr(es, "find_repo", lambda *_a: checkout)
    monkeypatch.setattr(es, "clone_repo", lambda *_a: pytest.fail("must not clone inside a checkout"))
    assert explorer.run() == 0
    monkeypatch.setattr(es, "find_repo", lambda *_a: None)
    cloned = []

    def fake_clone(url, dest):
        cloned.append((url, dest))
        (dest / "concept-tree").mkdir(parents=True)
        (dest / "concept-tree" / "tree.json").write_text("[]")
        return dest
    monkeypatch.setattr(es, "clone_repo", fake_clone)
    assert explorer.run() == 0
    assert cloned == [(es.DEFAULT_REPO_URL, home / "llms-explorer")]
    assert "cloning" in capsys.readouterr().out

    def interrupted(_u, _d):
        raise KeyboardInterrupt
    monkeypatch.setattr(es, "clone_repo", interrupted)
    assert explorer.run() == 130

    def failed(_u, _d):
        raise es.GitError("network down")
    monkeypatch.setattr(es, "clone_repo", failed)
    assert explorer.run() == 2
    assert "clone failed: network down" in capsys.readouterr().out


def test_quick_action_buttons_and_hotkeys(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    from llmsx import explorer_screens as screens

    async def check(app, pilot):
        from textual.widgets import Button
        app._select("Kid Concept")
        app.query_one("#outline").focus()
        await _settle(app, pilot)

        # 1. Hotkey '?' or Help button opens HotkeyHelp
        await pilot.press("question_mark")
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.HotkeyHelp)
        await pilot.press("escape")
        await _settle(app, pilot)

        app.action_help()
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.HotkeyHelp)
        await pilot.press("escape")
        await _settle(app, pilot)

        # 2. Queue viewer hotkey 'u' or button opens QueueViewer
        app.query_one("#outline").focus()
        await pilot.press("u")
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.QueueViewer)
        await pilot.press("escape")
        await _settle(app, pilot)

        app.action_queue_viewer()
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.QueueViewer)
        await pilot.press("escape")
        await _settle(app, pilot)

        # 3. + Queue button queues selected concept
        await pilot.click("#btn-queue")
        await _settle(app, pilot)
        assert "queued Kid Concept" in _status(app)
        queue_text = (repo / es.QUEUE_REL).read_text()
        assert "Kid Concept" in queue_text

        # 4. Quick research buttons trigger research
        jobs = []
        app._run_research = lambda c, m, p: jobs.append((c, m, p))
        await pilot.click("#btn-dr")
        await _settle(app, pilot)
        assert jobs == [("Kid Concept", "dr", "Root Domain")]

        await pilot.click("#btn-rabbithole")
        await _settle(app, pilot)
        assert jobs[-1] == ("Kid Concept", "deep", "Root Domain")

        await pilot.click("#btn-family")
        await _settle(app, pilot)
        assert jobs[-1] == ("Kid Concept", "family", "Root Domain")

    _run(check, repo)


def test_highlights_tui_flow(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    from llmsx import explorer_screens as screens
    from textual.widgets import Input, TextArea, TabbedContent

    async def check(app, pilot):
        app._select("Kid Concept")
        app.query_one("#outline").focus()
        await _settle(app, pilot)

        # Press 'h' to add highlight
        await pilot.press("h")
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.AddHighlight)
        app.screen.query_one("#text", TextArea).text = "Incredible conceptual truth"
        app.screen.query_one("#note", Input).value = "Note on kid concept"
        await pilot.press("ctrl+s")
        await _settle(app, pilot)

        # Verify saved in store and status updated
        assert "saved highlight for Kid Concept" in _status(app)
        hls = es.load_highlights()
        assert len(hls) == 1
        assert hls[0]["text"] == "Incredible conceptual truth"

        # Check Highlights tab
        app.query_one("#tabs", TabbedContent).active = "pane-highlights"
        await _settle(app, pilot)
        assert "Incredible conceptual truth" in _md(app, "pane-highlights")
        assert "Note on kid concept" in _md(app, "pane-highlights")

        # Press 'H' to open HighlightsScreen manager
        app.query_one("#outline").focus()
        await pilot.press("H")
        await _settle(app, pilot)
        assert isinstance(app.screen, screens.HighlightsScreen)
        await pilot.press("escape")
        await _settle(app, pilot)

    _run(check, repo)


def test_research_select_enter_submits(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    monkeypatch.setattr(es.shutil, "which", lambda _n: "/usr/bin/claude")
    from llmsx.explorer import Research

    async def check(app, pilot):
        jobs = []
        app._run_research = lambda c, m, p: jobs.append((c, m, p))
        app._select("Kid Concept")
        await _settle(app, pilot)

        app.action_research()
        await _settle(app, pilot)
        assert isinstance(app.screen, Research)

        # Press Enter on ResearchSelect dropdown
        await pilot.press("enter")
        await _settle(app, pilot)
        assert not isinstance(app.screen, Research), "Research modal should dismiss on Enter"
        assert jobs == [("Kid Concept", "dr", "Root Domain")]

    _run(check, repo)

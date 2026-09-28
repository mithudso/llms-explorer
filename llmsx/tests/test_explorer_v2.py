# llmsx/tests/test_explorer_v2.py — tags, links, the editor round-trip, site data, imports,
# the skill runner, capture, and the v2 screens.
# ruff: noqa: E501
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import pytest
from conftest import INJECTION, make_repo

from llmsx import explorer_store as es


# --------------------------------------------------------------------------- #
# store

def test_tags_live_in_marks_and_survive_marks(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    o = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    assert es.tag_key("Kid Concept", o) == "kid-concept" and es.tag_key("Ghost Concept", o) == "ghost-concept"
    marks = es.set_tags(repo, "kid-concept", ["db", " db ", "Storage/Index", ""])
    assert es.tags_of(marks, "kid-concept") == ["db", "Storage/Index"]
    es.set_mark(repo, "kid-concept", "needs-review")
    assert es.tags_of(es.load_marks(repo), "kid-concept") == ["db", "Storage/Index"], "a mark keeps the tags"
    es.set_tags(repo, "ghost-concept", ["frontier-todo"])
    assert es.all_tags(es.load_marks(repo)) == ["Storage/Index", "db", "frontier-todo"]
    marks = es.set_tags(repo, "ghost-concept", [])
    assert "ghost-concept" not in marks, "no state and no tags → no entry"
    with pytest.raises(ValueError):
        es.set_tags(repo, "kid-concept", ["bad`tag"])
    with pytest.raises(ValueError):
        es.set_tags(repo, "../x", ["a"])


def test_links_are_a_tree_key_and_search_finds_targets(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    nodes = es.load_raw_tree(repo / es.TREE_REL)
    es.link_concepts(nodes, "Kid Concept", "Root Domain")
    es.link_concepts(nodes, "Kid Concept", "Root Domain")
    assert nodes[1]["relatedConcepts"] == ["Root Domain"]
    es.save_raw_tree(nodes, repo / es.TREE_REL)
    back = es.load_raw_tree(repo / es.TREE_REL)
    assert es.related_of(back[1]) == ["Root Domain"] and back[0].get("relatedConcepts") is None
    es.unlink_concepts(back, "Kid Concept", "Root Domain")
    assert "relatedConcepts" not in back[1]
    with pytest.raises(ValueError):
        es.link_concepts(nodes, "Kid Concept", "Kid Concept")
    o = es.build_outline(nodes)
    assert es.search_concepts(o, "kiddo") == ["Kid Concept"], "aliases match"
    assert es.search_concepts(o, "ghost") == ["Ghost Concept"], "frontier names are offered too"
    assert es.search_concepts(o, "zzz") == []


def test_node_edit_text_round_trips_and_cancels_on_empty(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    nodes = es.load_raw_tree(repo / es.TREE_REL)
    text = es.node_edit_text(nodes[1])
    assert "## summary\nA kid. " in text and "## aliases\nkiddo\n" in text and "## tags\n" in text
    fields = es.parse_node_edit(text.replace("A kid. " + INJECTION, "edited summary")
                               .replace("## childConcepts\n", "## childConcepts\nNew Kid\n")
                               .replace("## relatedConcepts\n", "## relatedConcepts\nRoot Domain\n")
                               .replace("## tags\n", "## tags\nt1\nt2\n"))
    assert fields == {"summary": "edited summary", "aliases": ["kiddo"], "childConcepts": ["New Kid"],
                      "relatedConcepts": ["Root Domain"], "tags": ["t1", "t2"]}
    es.apply_node_edit(nodes, "Kid Concept", fields)
    assert nodes[1]["summary"] == "edited summary" and nodes[1]["childConcepts"] == ["New Kid"]
    assert nodes[1]["relatedConcepts"] == ["Root Domain"] and nodes[0]["extraKey"] == {"keep": True}
    assert es.parse_node_edit("# only comments\n\n") is None
    with pytest.raises(ValueError):
        es.parse_node_edit("## bogus\nx\n")
    with pytest.raises(ValueError):
        es.parse_node_edit("stray text\n## summary\nx\n")
    es.apply_node_edit(nodes, "Kid Concept", {"summary": "", "aliases": [], "childConcepts": ["Kid Concept"], "relatedConcepts": []})
    assert "summary" not in nodes[1] and nodes[1]["childConcepts"] == [], "a self-child is dropped"


def test_site_data_readers(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    data = repo / "site" / "src" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "directory.json").write_text(json.dumps({"sites": [
        {"key": "b.dev", "name": "B", "grade": "B", "pages": 5, "url": "https://b.dev/llms-full.txt"},
        {"key": "a.dev", "name": "A", "grade": "A", "pages": 2, "url": "https://a.dev/llms-full.txt"}]}))
    blog = repo / "site" / "src" / "content" / "blog"
    blog.mkdir(parents=True)
    (blog / "old.md").write_text('---\ntitle: "Old post"\ndate: "2026-01-01"\ndescription: >-\n  folded\n  description\n---\n# Old\n')
    (blog / "new.md").write_text('---\ntitle: "New post"\ndate: "2026-02-01"\n---\n# New\n')
    skills = repo / "site" / "src" / "content" / "skills"
    skills.mkdir(parents=True)
    (skills / "kidskill.md").write_text('---\ntitle: "/kid — the kid skill"\ndescription: "Does kid things."\norder: 2\n---\n')
    sites = es.directory_sites(repo)
    assert [s["key"] for s in sites] == ["a.dev", "b.dev"], "grade A first"
    posts = es.content_pages(repo, "blog")
    assert [p["title"] for p in posts] == ["New post", "Old post"] and posts[1]["description"] == "folded description"
    sk = es.skill_pages(repo)
    assert [s["id"] for s in sk] == ["kidskill"] and sk[0]["title"] == "/kid — the kid skill"
    assert es.mirror_file("../etc") is None and es.content_pages(repo, "nope") == []


def test_import_local_and_catalog(tmp_path, home):
    src = tmp_path / "notes" / "llms-facts.txt"
    src.parent.mkdir()
    src.write_text("# facts\n\n- one\n")
    entry = es.import_llms(str(src), concept="Kid Concept")
    dest = Path(entry["path"])
    assert dest == home / "imports" / "notes" / "llms-facts.txt" and dest.read_text() == "# facts\n\n- one\n"
    assert entry["kind"] == "facts" and entry["concept"] == "Kid Concept" and entry["source"] == str(src.resolve())
    assert [e["path"] for e in es.import_catalog()] == [str(dest)]
    es.import_llms(str(src))                      # re-import replaces, no duplicate row
    assert len(es.import_catalog()) == 1
    with pytest.raises(ValueError):
        es.import_llms(str(tmp_path / "notes" / "README.md"))
    with pytest.raises(FileNotFoundError):
        es.import_llms(str(tmp_path / "missing" / "llms.txt"))
    assert es.remove_import(str(dest)) and not dest.exists() and es.import_catalog() == []
    assert es.remove_import(str(dest)) is False


def test_import_from_the_web_uses_the_host_as_the_folder(tmp_path, home, monkeypatch):
    import io
    import urllib.request

    class Resp(io.BytesIO):
        def geturl(self):
            return "https://docs.example.com/llms-full.txt"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Opener:
        def open(self, req, timeout=0):
            return Resp(b"# remote\n")
    monkeypatch.setattr(urllib.request, "build_opener", lambda *h: Opener())
    entry = es.import_llms("https://docs.example.com/llms-full.txt")
    assert entry["path"] == str(home / "imports" / "docs.example.com" / "llms-full.txt")
    assert entry["kind"] == "full" and Path(entry["path"]).read_text() == "# remote\n"
    entry = es.import_llms("https://docs.example.com/weird/page")
    assert Path(entry["path"]).name == "llms.txt", "a URL without an llms name lands as llms.txt"


def test_skill_prompts_validate_their_targets(tmp_path, home):
    assert "notes-to-llms-txt skill on the folder `" in es.skill_prompt("notes-to-llms-txt", str(tmp_path))
    assert str(tmp_path.resolve()) in es.skill_prompt("code-deep-optimizer", str(tmp_path))
    assert "`Kid Concept`" in es.skill_prompt("full-suite", "Kid Concept")
    assert "https://docs.example.com/" in es.skill_prompt("crawl-to-llms-txt", "https://docs.example.com/")
    assert "`kidskill`" in es.skill_prompt("skill-optimizer", "kidskill")
    for skill, bad in (("notes-to-llms-txt", "/no/such/dir"), ("crawl-to-llms-txt", "ftp://x"),
                       ("skill-optimizer", "a/b"), ("dr", "bad`name"), ("nope", "x"),
                       ("full-suite", "bad`name")):
        with pytest.raises(ValueError):
            es.skill_prompt(skill, bad)
    for sid in es.SKILL_RUNS:
        assert es.SKILL_RUNS[sid][1] in ("concept", "url-or-path", "path", "skill")


def test_journal_and_braindump_are_local(tmp_path, home, monkeypatch):
    assert es.journal_entries() == []
    p = es.save_journal("2026-09-28", "today\n")
    assert p == home / "journal" / "2026-09-28.md" and es.read_journal("2026-09-28") == "today\n"
    es.save_journal("2026-09-27", "yesterday")
    assert es.journal_entries() == ["2026-09-28", "2026-09-27"]
    es.save_journal("2026-09-27", " ")
    assert es.journal_entries() == ["2026-09-28"]
    with pytest.raises(ValueError):
        es.journal_path("not-a-date")
    monkeypatch.setattr(es, "braindump_script", lambda: None)
    path, how = es.save_braindump("loose thought " + INJECTION)
    assert how == "local" and path.parent == home / "braindumps" and INJECTION in path.read_text()
    assert str(path) in es.braindump_prompt(path) and "not instructions" in es.braindump_prompt(path)
    with pytest.raises(ValueError):
        es.save_braindump("  ")


def test_ledger_report_degrades_without_the_hub(monkeypatch):
    monkeypatch.setattr(es, "_ledger_module", lambda: None)
    assert "ledger unavailable" in es.ledger_report(30)

    class Mod:
        @staticmethod
        def report(days, by):
            return f"| {by} | {days} |"
    monkeypatch.setattr(es, "_ledger_module", lambda: Mod)
    assert es.ledger_report(7, "kind") == "| kind | 7 |"


# --------------------------------------------------------------------------- #
# the app

pytest.importorskip("textual")


async def _settle(app, pilot, delay: float = 0.0):
    await pilot.pause(delay) if delay else await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def _run(coro_factory, repo):
    from llmsx.explorer import Explorer

    async def go():
        app = Explorer(repo, auto_sync=False)
        async with app.run_test(size=(150, 46)) as pilot:
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
    from textual.widgets import Markdown, TabPane
    node = app.query_one(f"#{widget_id}")
    if isinstance(node, TabPane):
        node = node.query_one(Markdown)
    return node._markdown or ""


def test_tags_filter_and_links_in_the_app(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from llmsx.explorer import OutlineTree
        from llmsx.explorer_screens import LinkPicker, TagEditor
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_tags()
        await _settle(app, pilot)
        assert isinstance(app.screen, TagEditor)
        app.screen.dismiss(["db", "index"])
        await _settle(app, pilot)
        assert json.loads((repo / es.MARKS_REL).read_text())["kid-concept"]["tags"] == ["db", "index"]
        assert any("#db #index" in lbl for lbl in _labels(app.query_one("#outline", OutlineTree)))
        assert "**tags:** #db, #index" in _md(app, "md-overview")
        app.action_cycle_filter()          # frontier
        await _settle(app, pilot)
        labels = [lbl.split("  ")[0] for lbl in _labels(app.query_one("#outline", OutlineTree))]
        assert labels == ["Root Domain", "Ghost Concept"] and "filter: frontier" in _status(app)
        app.action_cycle_filter()          # researched
        await _settle(app, pilot)
        assert "Ghost Concept" not in " ".join(_labels(app.query_one("#outline", OutlineTree)))
        app.action_cycle_filter()          # tagged
        await _settle(app, pilot)
        labels = [lbl.split("  ")[0].rstrip(" ●") for lbl in _labels(app.query_one("#outline", OutlineTree))]
        assert labels == ["Root Domain", "Kid Concept"]
        app.action_cycle_filter()          # all
        await _settle(app, pilot)
        assert len(_labels(app.query_one("#outline", OutlineTree))) == 3
        app.action_link()
        await _settle(app, pilot)
        assert isinstance(app.screen, LinkPicker)
        app.screen.dismiss("Root Domain")
        await _settle(app, pilot)
        assert json.loads((repo / es.TREE_REL).read_text())[1]["relatedConcepts"] == ["Root Domain"]
        assert "[Root Domain](concept:root-domain)" in _md(app, "md-overview")
        app.jump_to("root-domain")
        await _settle(app, pilot)
        assert app._selected == "Root Domain"

    _run(check, repo)


def test_editor_round_trip_writes_tree_and_tags(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    import contextlib

    from llmsx import explorer
    monkeypatch.setattr(explorer.Explorer, "suspend", lambda self: contextlib.nullcontext())
    monkeypatch.setenv("EDITOR", "fake-editor")

    def fake_call(argv):
        path = Path(argv[-1])
        text = path.read_text()
        path.write_text(text.replace("## summary\nA kid. " + INJECTION, "## summary\nvim wrote this")
                        .replace("## tags\n", "## tags\nfrom-vim\n"))
        return 0
    monkeypatch.setattr(explorer.subprocess, "call", fake_call)

    async def check(app, pilot):
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_edit_node()
        await _settle(app, pilot)
        assert len(app.screen_stack) == 1, "no modal when an editor is configured"
        nodes = json.loads((repo / es.TREE_REL).read_text())
        assert nodes[1]["summary"] == "vim wrote this"
        assert json.loads((repo / es.MARKS_REL).read_text())["kid-concept"]["tags"] == ["from-vim"]
        assert "saved concept-tree/tree.json and tags" in _status(app)
        monkeypatch.setattr(explorer.subprocess, "call", lambda argv: Path(argv[-1]).write_text("") or 0)
        app.action_edit_node()
        await _settle(app, pilot)
        assert "edit cancelled" in _status(app)

    _run(check, repo)


def test_panels_hide_windows_and_persist(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from llmsx.explorer_screens import PanelSettings
        app.action_panels()
        await _settle(app, pilot)
        assert isinstance(app.screen, PanelSettings)
        app.screen.dismiss({"outline": True, "detail": True, "status": False, "footer": False,
                            "tab-facts": False, "tab-skill": True, "tab-references": False, "tab-llms": False})
        await _settle(app, pilot)
        assert es.load_config()["panels"]["status"] is False
        assert app.query_one("#status").display is False
        app._select("Kid Concept")
        await _settle(app, pilot)
        from textual.widgets import TabbedContent, TabPane
        tabs = app.query_one("#tabs", TabbedContent)
        titles = [str(p._title) for p in tabs.query(TabPane)]
        assert "pane-facts" in app._hidden_panes and "pane-skill" not in app._hidden_panes
        assert not tabs.get_tab("pane-facts").display and tabs.get_tab("pane-skill").display
        assert "ref: depth" not in titles and "llms" not in titles

    _run(check, repo)


def test_library_ledger_skills_import_and_capture_screens(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)
    data = repo / "site" / "src" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "directory.json").write_text(json.dumps({"sites": [{"key": "a.dev", "name": "A", "grade": "A", "pages": 2, "url": "https://a.dev/llms-full.txt"}]}))
    monkeypatch.setattr(es, "_ledger_module", lambda: None)
    jobs = []
    monkeypatch.setattr(es, "claude_binary", lambda: "/usr/bin/claude")

    async def check(app, pilot):
        from llmsx.explorer_screens import Braindump, ImportDialog, Journal, Ledger, Library, SkillRunner
        from textual.widgets import DataTable
        app.action_library()
        await _settle(app, pilot)
        assert isinstance(app.screen, Library)
        assert app.screen.query_one("#tbl-directory", DataTable).row_count == 1
        assert app.screen.query_one("#tbl-skills", DataTable).row_count == 1
        app.screen.action_bundle()
        await _settle(app, pilot)
        app.pop_screen()
        await _settle(app, pilot)
        app.action_ledger()
        await _settle(app, pilot)
        assert isinstance(app.screen, Ledger) and "ledger unavailable" in _md(app.screen, "ledger-md")
        app.pop_screen()
        await _settle(app, pilot)
        monkeypatch.setattr(app, "_run_job", lambda argv, what: jobs.append((argv, what)))
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_skills()
        await _settle(app, pilot)
        assert isinstance(app.screen, SkillRunner)
        app.screen.dismiss(("full-suite", "Kid Concept"))
        await _settle(app, pilot)
        assert jobs and jobs[-1][1] == "full-suite on Kid Concept" and "full-suite skill" in jobs[-1][0][2]
        app.action_skills()
        await _settle(app, pilot)
        app.screen.dismiss(("notes-to-llms-txt", "/no/such/folder"))
        await _settle(app, pilot)
        assert "refusing to run notes-to-llms-txt" in _status(app)
        app.action_import_llms()
        await _settle(app, pilot)
        assert isinstance(app.screen, ImportDialog)
        src = tmp_path / "llms.txt"
        src.write_text("# x\n")
        app.screen.dismiss(str(src))
        await _settle(app, pilot)
        assert "imported to" in _status(app) and len(es.import_catalog()) == 1
        app.action_braindump()
        await _settle(app, pilot)
        assert isinstance(app.screen, Braindump)
        from textual.widgets import TextArea
        app.screen.query_one("#dump", TextArea).text = "a loose thought"
        monkeypatch.setattr(es, "braindump_script", lambda: None)
        app.screen.action_parse()
        await _settle(app, pilot)
        assert jobs[-1][1].startswith("braindump on") and list((home / "braindumps").glob("*.md"))
        app.pop_screen()
        await _settle(app, pilot)
        app.action_journal()
        await _settle(app, pilot)
        assert isinstance(app.screen, Journal)
        app.screen.query_one("#jr-text", TextArea).text = "dear diary"
        app.screen.action_save()
        await _settle(app, pilot)
        assert len(es.journal_entries()) == 1
        app.screen.action_to_llms()
        await _settle(app, pilot)
        assert jobs[-1][1].startswith("notes-to-llms-txt on") and str(home / "journal") in jobs[-1][0][2]

    _run(check, repo)


def test_arrow_keys_move_focus_and_brackets_switch_tabs(tmp_path, home):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from llmsx.explorer import OutlineTree
        from textual.widgets import TabbedContent
        tree = app.query_one("#outline", OutlineTree)
        tree.focus()
        await _settle(app, pilot)
        root = tree.root.children[0]
        tree.select_node(root)
        await _settle(app, pilot)
        await pilot.press("right")             # expands Root Domain
        await _settle(app, pilot)
        assert root.is_expanded
        await pilot.press("down", "right")     # Kid Concept is a leaf: focus moves on
        await _settle(app, pilot)
        assert app.focused is not tree
        tree.focus()
        tree.select_node(root)
        await _settle(app, pilot)
        await pilot.press("left")              # collapses
        await pilot.press("left")              # at a collapsed root: back to the filter
        await _settle(app, pilot)
        assert app.focused is app.query_one("#filter")
        app._select("Kid Concept")
        await _settle(app, pilot)
        tabs = app.query_one("#tabs", TabbedContent)
        before = tabs.active
        app.action_next_tab()
        await _settle(app, pilot)
        assert tabs.active != before
        app.action_prev_tab()
        await _settle(app, pilot)
        assert tabs.active == before

    _run(check, repo)


def test_cli_still_parses(tmp_path):
    import os
    import sys
    out = subprocess.run([sys.executable, "-m", "llmsx", "explorer", "--help"], capture_output=True, text=True,
                         env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])})
    assert out.returncode == 0


# --------------------------------------------------------------------------- #
# local overlay, flashcards, quiz, export

def test_local_overlay_adds_roots_and_moves_without_touching_the_repo(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    before = (repo / es.TREE_REL).read_text()
    o = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    es.add_local_root("My Study Plan")
    es.move_concept("Kid Concept", "My Study Plan")
    ov = es.load_overlay()
    assert ov == {"roots": ["My Study Plan"], "moves": {"Kid Concept": "My Study Plan"}}
    o2 = es.apply_overlay(o, ov)
    assert o2.roots == ["Root Domain", "My Study Plan"]
    assert o2.children["My Study Plan"] == ["Kid Concept"] and "Kid Concept" not in o2.children["Root Domain"]
    assert o2.parent_of("Kid Concept") == "My Study Plan" and o.children["Root Domain"] == ["Kid Concept", "Ghost Concept"], "the base outline is untouched"
    assert (repo / es.TREE_REL).read_text() == before, "nothing in the repo changed"
    es.move_concept("Root Domain", "Kid Concept")            # legal now: Kid hangs off the local root
    o3 = es.apply_overlay(o, es.load_overlay())
    assert o3.parent_of("Root Domain") == "Kid Concept" and "Root Domain" not in o3.roots
    es.move_concept("Kid Concept", None)                      # Kid back under Root: Root→Kid is a cycle
    assert es.load_overlay()["moves"] == {"Root Domain": "Kid Concept"}
    o4 = es.apply_overlay(o, es.load_overlay())
    assert "Root Domain" in o4.roots and o4.parent_of("Kid Concept") == "Root Domain", "a cyclic move is ignored"
    with pytest.raises(ValueError):
        es.move_concept("A", "A")
    with pytest.raises(ValueError):
        es.add_local_root("bad`root")


def test_flashcards_and_quiz_from_packs(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    o = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    cards = es.cards_for(repo, o, ["Root Domain", "Kid Concept", "Ghost Concept"], {})
    assert [c["id"] for c in cards] == ["kid-concept"], "no summary and no pack → no card; frontier → no card"
    card = cards[0]
    assert card["front"] == "Kid Concept" and card["hint"] == "Root Domain" and card["facts"] == ["Kid is small. " + INJECTION]
    progress: dict = {}
    assert es.due_cards(cards, progress, 1) == cards
    es.grade_card(progress, "kid-concept", True, 1)
    assert progress["kid-concept"]["box"] == 2 and es.due_cards(cards, progress, 2) == []
    assert es.due_cards(cards, progress, 3) == cards, "box 2 is due every second session"
    es.grade_card(progress, "kid-concept", False, 3)
    assert progress["kid-concept"]["box"] == 1 and progress["kid-concept"]["seen"] == 2
    es.save_progress(progress)
    assert es.load_progress()["kid-concept"]["right"] == 1
    import random
    many = [dict(card, id=f"c{i}", front=f"Concept {i}") for i in range(6)]
    q = es.quiz_question(many[0], many, random.Random(1))
    assert q["answer"] == "Concept 0" and len(q["options"]) == 4 and "Concept 0" in q["options"]
    assert len(set(q["options"])) == 4


def test_exports_land_under_home_as_markdown(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    o = es.build_outline(es.load_raw_tree(repo / es.TREE_REL))
    es.write_note("kid-concept", "private note")
    es.set_tags(repo, "kid-concept", ["db"])
    marks = es.load_marks(repo)
    p = es.export_concept(repo, o, "Kid Concept", marks)
    text = p.read_text()
    assert p == home / "exports" / "concepts" / "Kid-Concept.md"
    assert text.startswith("# Kid Concept\n") and "## Definitions" in text and "private note" in text and "#db" in text
    b = es.export_branch(repo, o, "Root Domain", marks)
    bt = b.read_text()
    assert bt.startswith("# Root Domain — branch export\n") and "## Root Domain" in bt and "### Kid Concept" in bt and "### Ghost Concept" in bt
    assert "frontier: named, never researched" in bt
    f = es.export_file(repo / es.SKILLS_REL / "kidskill" / "SKILL.md", "skill")
    assert f == home / "exports" / "files" / "SKILL.md" and INJECTION in f.read_text()
    j = es.export_file(repo / es.PACKS_REL / "kid-concept.json", "pack")
    assert j.read_text().startswith("# kid-concept.json\n\n```\n")
    items = [es.bundle_item(repo / es.SKILLS_REL / "kidskill" / "SKILL.md", "skill", "Kid Concept")]
    c = es.export_bundle_markdown(items, "my set")
    assert c == home / "exports" / "collections" / "my-set.md" and "## SKILL.md for Kid Concept" in c.read_text()


def test_local_roots_moves_flashcards_quiz_and_export_in_the_app(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    nodes = json.loads((repo / es.TREE_REL).read_text())
    for i in range(4):
        nodes.append({"concept": f"Extra {i}", "slug": f"extra-{i}", "parentConcept": "Root Domain",
                      "childConcepts": [], "summary": f"Extra summary {i}", "aliases": []})
    nodes[0]["childConcepts"] += [f"Extra {i}" for i in range(4)]
    (repo / es.TREE_REL).write_text(json.dumps(nodes))

    async def check(app, pilot):
        from llmsx.explorer import OutlineTree
        from llmsx.explorer_screens import Chooser, Flashcards, LinkPicker, Quiz, TextPrompt
        app.action_new_root()
        await _settle(app, pilot)
        assert isinstance(app.screen, TextPrompt)
        app.screen.dismiss("Study Plan")
        await _settle(app, pilot)
        assert any("Study Plan" in lbl and "(local root)" in lbl for lbl in _labels(app.query_one("#outline", OutlineTree)))
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_move_concept()
        await _settle(app, pilot)
        assert isinstance(app.screen, LinkPicker)
        app.screen.dismiss("Study Plan")
        await _settle(app, pilot)
        assert app._outline.parent_of("Kid Concept") == "Study Plan"
        assert json.loads((repo / es.TREE_REL).read_text())[1]["parentConcept"] == "Root Domain", "the repo tree is untouched"
        assert not (repo / es.MARKS_REL).exists()
        app._select("Root Domain")
        await _settle(app, pilot)
        app.action_flashcards()
        await _settle(app, pilot)
        assert isinstance(app.screen, Flashcards)
        assert "_space to flip_" in _md(app.screen, "fc-md")
        app.screen.action_flip()
        await _settle(app, pilot)
        assert "Extra summary" in _md(app.screen, "fc-md")
        app.screen.action_grade_right()
        await _settle(app, pilot)
        assert es.load_progress()
        app.pop_screen()
        await _settle(app, pilot)
        app.action_quiz()
        await _settle(app, pilot)
        assert isinstance(app.screen, Quiz)
        assert "Question 1 of" in _md(app.screen, "quiz-md")
        app.screen.action_answer(1)
        await _settle(app, pilot)
        assert "✓" in _md(app.screen, "quiz-md")
        app.pop_screen()
        await _settle(app, pilot)
        app.action_export_menu()
        await _settle(app, pilot)
        assert isinstance(app.screen, Chooser)
        app.screen.dismiss("branch")
        await _settle(app, pilot)
        assert "exported" in _status(app) and (home / "exports" / "branches" / "Root-Domain.md").is_file()

    _run(check, repo)


# --------------------------------------------------------------------------- #
# review follow-ups

def test_import_refuses_redirects_off_http_and_paths_that_escape(tmp_path, home, monkeypatch):
    import io
    import urllib.request

    class Resp(io.BytesIO):
        def __init__(self, data, url):
            super().__init__(data)
            self._url = url

        def geturl(self):
            return self._url

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Opener:
        def __init__(self, url):
            self._url = url

        def open(self, req, timeout=0):
            return Resp(b"secret", self._url)
    monkeypatch.setattr(urllib.request, "build_opener", lambda *h: Opener("file:///Users/x/.llmsx/config.json"))
    with pytest.raises(ValueError, match="redirect"):
        es.import_llms("https://evil.example/llms.txt")
    monkeypatch.setattr(urllib.request, "build_opener", lambda *h: Opener("https://ok.example/llms.txt"))
    assert es.import_llms("https://ok.example/llms.txt")["kind"] == "index"
    entry = es.import_llms("https://../../llms.txt")          # a `..` host is neutralised to `web`
    assert Path(entry["path"]).parent == home / "imports" / "web"
    assert es._under(es.imports_dir(), Path(entry["path"])) is not None
    monkeypatch.setattr(es, "_import_dest", lambda src, name: es.imports_dir() / ".." / name)
    with pytest.raises(ValueError, match="escapes"):
        es.import_llms("https://ok.example/llms.txt")


def test_credential_scan_covers_more_than_github(tmp_path):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "site" / "tools"))
    import gen_downloads as gd
    for bad in (b"token = abcdefghijklmnopqrstuvwxyz1234", b"AKIAABCDEFGHIJKLMNOP", b"xoxb-1234567890-abc",
                b"-----BEGIN RSA PRIVATE KEY-----", b"ghp_" + b"a" * 24, b"api_key: 'ABCDEFGHIJKLMNOPQRST'"):
        assert gd._CREDENTIAL.search(bad), bad
    for ok in (b"TOKEN_RE = re.compile(...)", b"the token goes through settings", b"secret_length = 8"):
        assert not gd._CREDENTIAL.search(ok), ok


def test_library_rows_preview_and_bundle(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    data = repo / "site" / "src" / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "directory.json").write_text(json.dumps({"sites": [{"key": "a.dev", "name": "A site", "grade": "A", "pages": 2, "url": "https://a.dev/llms-full.txt"}]}))

    async def check(app, pilot):
        from textual.widgets import DataTable, TabbedContent
        from llmsx.explorer_screens import Library
        app.action_library()
        await _settle(app, pilot)
        scr = app.screen
        assert isinstance(scr, Library)
        scr._show("tbl-directory", "a.dev")
        assert "A site" in _md(scr, "lib-md") and "grade **A**" in _md(scr, "lib-md") and scr._current is None
        scr.query_one("#lib-tabs", TabbedContent).active = "lib-skills"
        await _settle(app, pilot)
        scr._show("tbl-skills", "kidskill")
        assert "Kid skill" in _md(scr, "lib-md") and scr._current[1] == "skill"
        scr.action_bundle()
        await _settle(app, pilot)
        assert len(app._bundle) == 1
        table = scr.query_one("#tbl-directory", DataTable)
        assert table.row_count == 1

    _run(check, repo)


def test_hidden_active_pane_steps_off_jump_frontier_export_file_bundle_import_failure(tmp_path, home, monkeypatch):
    repo = make_repo(tmp_path, git=False)

    async def check(app, pilot):
        from textual.widgets import TabbedContent
        from llmsx.explorer_screens import Chooser, ImportDialog, PanelSettings
        app._select("Kid Concept")
        await _settle(app, pilot)
        tabs = app.query_one("#tabs", TabbedContent)
        tabs.active = "pane-facts"
        await _settle(app, pilot)
        assert app._active_pane == "pane-facts"
        app.action_panels()
        await _settle(app, pilot)
        assert isinstance(app.screen, PanelSettings)
        app.screen.dismiss({"outline": True, "detail": True, "status": True, "footer": True,
                            "tab-facts": False, "tab-skill": True, "tab-references": True, "tab-llms": True})
        await _settle(app, pilot)
        assert app._active_pane != "pane-facts" and app._active_pane not in app._hidden_panes
        app.jump_to("ghost-concept")
        await _settle(app, pilot)
        assert app._selected == "Ghost Concept"
        app._select("Kid Concept")
        await _settle(app, pilot)
        tabs.active = "pane-skill"
        await _settle(app, pilot)
        app.action_export_menu()
        await _settle(app, pilot)
        assert isinstance(app.screen, Chooser)
        app.screen.dismiss("file")
        await _settle(app, pilot)
        assert list((home / "exports" / "files").glob("*.md"))
        app.action_bundle_toggle()
        await _settle(app, pilot)
        app.action_export_menu()
        await _settle(app, pilot)
        app.screen.dismiss("bundle")
        await _settle(app, pilot)
        assert list((home / "exports" / "collections").glob("*.md"))
        monkeypatch.setattr(es, "import_llms", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
        app.action_import_llms()
        await _settle(app, pilot)
        assert isinstance(app.screen, ImportDialog)
        app.screen.dismiss("https://x.example/llms.txt")
        await _settle(app, pilot)
        assert "import failed: boom" in _status(app) and not app._import_busy and es.import_catalog() == []

    _run(check, repo)


def test_quiz_with_exactly_four_cards_and_journal_pick_and_link_search(tmp_path, home):
    repo = make_repo(tmp_path, git=False)
    nodes = json.loads((repo / es.TREE_REL).read_text())
    for i in range(3):
        nodes.append({"concept": f"Extra {i}", "slug": f"extra-{i}", "parentConcept": "Root Domain",
                      "childConcepts": [], "summary": f"Extra summary {i}", "aliases": []})
    nodes[0]["childConcepts"] += [f"Extra {i}" for i in range(3)]
    (repo / es.TREE_REL).write_text(json.dumps(nodes))
    es.save_journal("2026-09-27", "yesterday")
    es.add_local_root("Study Plan")

    async def check(app, pilot):
        from textual.widgets import Input, OptionList, TextArea
        from llmsx.explorer_screens import Journal, LinkPicker, Quiz
        app._select("Root Domain")
        await _settle(app, pilot)
        app.action_quiz()
        await _settle(app, pilot)
        assert isinstance(app.screen, Quiz), "exactly four researched concepts is enough"
        app.pop_screen()
        await _settle(app, pilot)
        app.action_journal()
        await _settle(app, pilot)
        assert isinstance(app.screen, Journal)
        app.screen._open("2026-09-27")
        await _settle(app, pilot)
        assert app.screen._date == "2026-09-27" and app.screen.query_one("#jr-text", TextArea).text.strip() == "yesterday"
        app.pop_screen()
        await _settle(app, pilot)
        app._select("Kid Concept")
        await _settle(app, pilot)
        app.action_move_concept()
        await _settle(app, pilot)
        assert isinstance(app.screen, LinkPicker)
        app.screen.query_one("#q", Input).value = "stud"
        await _settle(app, pilot)
        hits = app.screen.query_one("#hits", OptionList)
        assert hits.option_count == 1 and "local root" in str(hits.get_option_at_index(0).prompt)
        app.screen.query_one("#q", Input).value = "ghost"
        await _settle(app, pilot)
        assert "(frontier)" in str(hits.get_option_at_index(0).prompt)
        app.screen.dismiss(None)
        await _settle(app, pilot)

    _run(check, repo)

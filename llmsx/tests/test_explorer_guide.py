# llmsx/tests/test_explorer_guide.py — the user guide shipped in the package.
from __future__ import annotations

import asyncio
import re

import pytest

from llmsx import explorer_store as es
from llmsx.__main__ import main


def test_guide_ships_and_covers_every_main_screen_key():
    text = es.guide_text()
    assert text.startswith("# LLMSX Explorer — User Guide")
    assert "https://llms-explorer.com/explorer/guide/" in text
    pytest.importorskip("textual")
    from llmsx.explorer import Explorer
    keys = {b.key for b in Explorer.BINDINGS}
    shown = {"question_mark": "?", "comma": ",", "slash": "/",
             "left_square_bracket": "[", "right_square_bracket": "]",
             "super+f,ctrl+f": "ctrl+f", "down": "↓", "up": "↑"}
    ref = text.split("## 16. Key reference", 1)[1]
    for key in keys:
        assert f"`{shown.get(key, key)}`" in ref, f"key {key!r} missing from the key reference"


def test_guide_toc_anchors_exist():
    text = es.guide_text()
    headings = {re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")
                for h in re.findall(r"^## (.+)$", text, re.M)}
    for anchor in re.findall(r"\]\(#([^)]+)\)", text):
        assert anchor in headings, anchor


def test_cli_guide_flag_prints_the_guide(capsys):
    assert main(["explorer", "--guide"]) == 0
    assert capsys.readouterr().out.startswith("# LLMSX Explorer — User Guide")


def test_g_and_help_button_open_the_guide(tmp_path, home):
    pytest.importorskip("textual")
    from conftest import make_repo
    from llmsx.explorer import Explorer
    from llmsx.explorer_screens import GuideScreen, HotkeyHelp
    repo = make_repo(tmp_path, git=False)

    async def go():
        app = Explorer(repo, auto_sync=False)
        async with app.run_test(size=(140, 44)) as pilot:
            await pilot.press("g")
            await pilot.pause()
            assert isinstance(app.screen, GuideScreen)
            md = app.screen.query_one("#guide-md")
            assert "The scratchpad" in md._markdown
            await pilot.press("escape")
            await pilot.pause()
            app.action_help()
            await pilot.pause()
            assert isinstance(app.screen, HotkeyHelp)
            app.screen.query_one("#guide").press()
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, GuideScreen)

    asyncio.run(go())

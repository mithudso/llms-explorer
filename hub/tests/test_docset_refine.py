"""docset_refine: strip/triage, deterministic extraction, LLM units, render."""

import json

from docset_refine import clean, extract, mirror_io, polish, render, units

FOOTER = "You can access Claude Code with a Claude Pro or Max plan."


def PAGE(url, body):
    return f"\n\n{'=' * 90}\nURL: {url}\n{'=' * 90}\n\n{body}\n"


HOOKS = (
    """# Hooks reference

Hooks are user-defined shell commands that run at specific points.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | allow |
| 2 | block |

```bash
claude --version
```

- Terminal
- VS Code
- Desktop app
- Web

[Configuration](https://code.claude.com#configuration)
"""
    + FOOTER
)


def _mirror(tmp_path):
    p = tmp_path / "code.claude.com.md"
    p.write_text(
        PAGE(
            "https://code.claude.com/docs/en/hooks",
            HOOKS + "\n\n" + "Hooks let you run commands at lifecycle points. " * 10,
        )
        + PAGE(
            "https://code.claude.com/docs/en/quickstart",
            "# Quickstart\n\nRun `claude` in any project directory to start a session.\n\n"
            + "Then describe what you want in plain language. " * 12
            + "\n\n"
            + FOOTER,
        )
        + PAGE("https://code.claude.com/customers/ramp", "# Ramp\n\nRamp loves it.\n\n" + FOOTER)
        + PAGE(
            "https://code.claude.com/docs/en/changelog",
            "# Changelog\n\n## 2.1.0\n\n- Added hooks\n\n## 2.0.0\n\n- Initial\n\n" + FOOTER,
        )
    )
    return p


# ------------------------------------------------------------------ clean --


def test_boilerplate_is_lines_shared_across_pages(tmp_path):
    pages = mirror_io.read_pages(_mirror(tmp_path))
    boiler = clean.boilerplate_lines(pages, min_share=0.05)
    assert FOOTER in boiler
    assert "Hooks are user-defined shell commands that run at specific points." not in boiler


def test_strip_page_drops_chrome_but_never_fence_contents():
    text = clean.strip_page(HOOKS, {FOOTER})
    assert FOOTER not in text
    assert "[Configuration](https://code.claude.com#configuration)" not in text  # link-only
    assert "- Terminal" not in text  # nav run
    assert "```bash\nclaude --version\n```" in text
    assert "| 0 | allow |" in text


def test_strip_page_keeps_chrome_lookalikes_inside_a_fence():
    text = "```txt\n" + FOOTER + "\n- Terminal\n- VS Code\n- Desktop app\n- Web\n```\n"
    assert clean.strip_page(text, {FOOTER}) == text.rstrip("\n")


def test_classify_by_url_and_shape():
    assert clean.classify("https://h/docs/en/hooks", HOOKS) == "reference"
    assert clean.classify("https://h/docs/en/quickstart", "# Q\n\n" + "prose. " * 80) == "guide"
    assert clean.classify("https://h/customers/ramp", "# R\n\ntext") == "marketing"
    assert clean.classify("https://h/docs/en/changelog", "# C") == "changelog"
    assert clean.classify("https://h/docs", "- [a](https://h/a)\n- [b](https://h/b)\n") == "index"
    assert clean.classify("https://h/", "# Home\n\n" + "prose. " * 80) == "marketing"


def test_mdx_components_flatten_to_markdown():
    mdx = """<Steps>
  <Step title="Install the plugin">
    Run the installer.
  </Step>
</Steps>
<Tip>
  Use `claude update`.
</Tip>
<Update label="August 19, 2026" description="v2.1.40">
- Added X
</Update>
<Tabs>
  <Tab title="macOS">
    ```bash
    <NotATag>
    ```
  </Tab>
</Tabs>
<div style={{maxWidth: "500px"}}>
  <img src="/x.png" />
</div>
{/* hidden */}
<Card title="Hooks" href="/hooks">
  Run commands.
</Card>
"""
    got = clean.mdx_to_markdown(mdx)
    assert "### Install the plugin" in got and "Run the installer." in got
    assert "**Tip:**" in got and "<Tip>" not in got
    assert "## August 19, 2026 — v2.1.40" in got and "</Update>" not in got
    assert "**macOS**" in got and "    <NotATag>" in got  # fence content untouched
    assert "<div" not in got and "<img" not in got and "hidden" not in got
    assert "**Hooks**" in got and "Run commands." in got


def test_mdx_inline_callouts_widgets_and_fence_props():
    mdx = (
        "<Note>`TaskOutput` is deprecated.</Note>\n<ContactSalesCard />\n"
        "```json settings.json theme={null}\n{}\n```\n"
    )
    got = clean.mdx_to_markdown(mdx)
    assert got.splitlines()[0] == "**Note:** `TaskOutput` is deprecated."
    assert "ContactSalesCard" not in got
    assert "```json settings.json\n{}\n```" in got


def test_changelog_entries_split_on_version_headings():
    entries = clean.changelog_entries(
        "# Changelog\n\n## 2.1.0\n\n- Added hooks\n\n## 2.0.0\n\n- Initial"
    )
    assert [e["version"] for e in entries] == ["2.1.0", "2.0.0"]
    assert "Added hooks" in entries[0]["text"]
    dated = clean.changelog_entries("## August 19, 2026\n\n- Added X\n\n## 2025-12-12\n\n- Y")
    assert [e["date"] for e in dated] == ["2026-08-19", "2025-12-12"]


def test_clean_run_writes_clean_mirror_and_pages_json(tmp_path):
    m = _mirror(tmp_path)
    r = clean.run(m)
    assert r["pages"] == 4 and r["kept"] == 3  # marketing page dropped
    clean_pages = mirror_io.read_pages(tmp_path / "code.claude.com.clean.md")
    assert [p["url"].rsplit("/", 1)[1] for p in clean_pages] == ["hooks", "quickstart", "changelog"]
    assert FOOTER not in (tmp_path / "code.claude.com.clean.md").read_text()
    meta = json.loads((tmp_path / "code.claude.com.reference" / "pages.json").read_text())
    assert {p["class"] for p in meta} == {"reference", "guide", "changelog"}
    assert meta[0]["headings"][:2] == ["Hooks reference", "Exit codes"]
    assert meta[0]["title"] == "Hooks reference"


# ---------------------------------------------------------------- extract --


def _page(text=HOOKS, url="https://h/docs/en/hooks", cls="reference", headings=None):
    return {
        "url": url,
        "class": cls,
        "text": text,
        "title": "Hooks reference",
        "headings": headings or [],
    }


def test_snippets_carry_heading_and_language():
    snips = extract.snippets(_page())
    assert len(snips) == 1
    s = snips[0]
    assert s["type"] == "snippet" and s["origin"] == "code"
    assert s["code"] == {"lang": "bash", "body": "claude --version"}
    assert s["anchor"] == "#exit-codes" and s["text"] == "Exit codes: claude --version"
    assert s["source_url"] == "https://h/docs/en/hooks" and s["keywords"] == ["bash"]


def test_snippet_title_beats_heading_and_indented_fences_dedent():
    text = '## Setup\n\n  ```json settings.json\n  {\n    "a": 1\n  }\n  ```\n'
    s = extract.snippets(_page(text))[0]
    assert s["text"] == "settings.json: {" and s["code"]["body"] == '{\n  "a": 1\n}'
    assert s["keywords"] == ["json", "settings.json"]


def test_tables_become_parameter_units():
    rows = extract.tables(_page())
    assert [r["text"] for r in rows] == ["0: allow", "2: block"]
    assert rows[0]["keywords"] == ["Code", "Meaning"] and rows[0]["origin"] == "table"
    wide = "| Var | Default | Meaning |\n| --- | --- | --- |\n| `X` | 1 | does x |\n"
    assert extract.tables(_page(wide))[0]["text"] == "`X`: Default=1; Meaning=does x"


def test_definitions_pair_heading_with_first_paragraph():
    defs = extract.definitions(_page())
    assert defs[0]["text"] == (
        "Hooks reference — Hooks are user-defined shell commands that run at specific points."
    )
    assert defs[0]["anchor"] == "#hooks-reference" and defs[0]["origin"] == "heading"
    # a heading followed by a table/fence, or a short line, yields no definition
    assert [d["text"].split(" — ")[0] for d in defs] == ["Hooks reference"]


def test_definitions_merge_a_lead_in_with_the_list_that_answers_it():
    """A first paragraph that only promises what follows ("… the following:")
    used to be emitted alone because the list under it starts with `- `; the
    unit was a promise with no body. It now carries the list; a lead-in
    followed by a table or fence is still emitted alone (that body becomes its
    own unit)."""
    page = _page(
        "## Cache TTL options\n\nThe cache supports the following durations:\n\n"
        "- 5 minutes (default), refreshed on each hit\n- 1 hour, billed at 2x base input\n\n"
        "## Pricing\n\nThe price depends on the model:\n\n"
        "| Model | Write |\n| --- | --- |\n| Opus | $6 |\n"
    )
    texts = [d["text"] for d in extract.definitions(page)]
    assert texts[0].startswith("Cache TTL options — The cache supports the following durations:")
    assert "5 minutes (default)" in texts[0]
    assert texts[1] == "Pricing — The price depends on the model:"


def test_changes_from_changelog_pages():
    page = _page(
        "# Changelog\n\n## 2.1.0 — August 19, 2026\n\n- Added hooks\n- Fixed X\n",
        url="https://h/docs/en/changelog",
        cls="changelog",
    )
    ch = extract.changes(page)
    assert ch[0]["type"] == "change" and ch[0]["text"] == "2.1.0: - Added hooks - Fixed X"
    assert ch[0]["keywords"] == ["2.1.0", "2026-08-19"]


def test_extract_and_render_end_to_end(tmp_path):
    m = _mirror(tmp_path)
    clean.run(m)
    counts = extract.run(m)
    assert counts["code"] == 1 and counts["table"] == 2 and counts["changelog"] == 2
    ids = [
        u["id"]
        for u in mirror_io.read_jsonl(tmp_path / "code.claude.com.reference" / "structured.jsonl")
    ]
    assert len(ids) == len(set(ids))  # ids unique across pages
    out = render.run(m)
    ref = (tmp_path / "code.claude.com.reference" / "reference.md").read_text()
    assert "## Hooks reference\n<https://code.claude.com/docs/en/hooks>" in ref
    assert "  ```bash\n  claude --version\n  ```" in ref
    assert "— https://code.claude.com/docs/en/hooks#exit-codes" in ref
    assert out["units_by_origin"]["table"] == 2 and out["units"] == len(ids)
    assert (tmp_path / "code.claude.com.reference" / "all_units.jsonl").exists()


# ------------------------------------------------------------------ units --


def test_parse_reply_is_tolerant_of_prose_think_blocks_and_bad_items():
    reply = (
        "<think>hmm</think>Sure! Here you go:\n"
        '[{"type":"fact","text":"Hooks run before every tool call in the loop.",'
        '"keywords":"x"},'
        '{"type":"bogus","text":"x"},{"type":"actionable","text":"short"}]\nDone.'
    )
    got = units.parse_reply(reply)
    assert [u["type"] for u in got] == ["fact"] and got[0]["keywords"] == ["x"]
    assert units.parse_reply("not json") == [] and units.parse_reply("") == []


def test_sections_split_long_pages_at_h2():
    text = "# T\n\nintro\n\n## A\n\n" + "a " * 60 + "\n\n## B\n\n" + "b " * 60
    secs = units.sections({"text": text}, max_chars=150)
    assert [s["anchor"] for s in secs] == ["", "#a", "#b"]
    assert units.sections({"text": "short"}, max_chars=150) == [{"anchor": "", "text": "short"}]


def test_prose_only_drops_fences_and_tables_but_marks_them():
    got = units.prose_only(HOOKS)
    assert "claude --version" not in got and "| 0 | allow |" not in got
    assert "[code block]" in got and "Hooks are user-defined shell commands" in got


def test_extract_page_skips_pages_with_no_prose():
    page = {
        "url": "https://h/x",
        "class": "reference",
        "text": "# T\n\n```bash\nls\n```\n\n| a | b |\n| - | - |\n| 1 | 2 |\n",
    }
    assert units.extract_page(page, generate=lambda *a, **k: "[]") == []


def test_extract_page_uses_prompt_and_tags_origin():
    seen = {}

    def fake_generate(prompt, model=None, timeout=None, options=None, think=None):
        seen["prompt"], seen["options"], seen["think"] = prompt, options, think
        return (
            '[{"type":"actionable","text":"Run claude --version to check the version.",'
            '"keywords":["version"]}]'
        )

    page = {
        "url": "https://h/docs/en/hooks",
        "class": "reference",
        "text": HOOKS + "\n\n" + "Prose about hooks and their lifecycle. " * 12,
    }
    got = units.extract_page(page, generate=fake_generate)
    assert "https://h/docs/en/hooks" in seen["prompt"] and "[code block]" in seen["prompt"]
    assert "claude --version" not in seen["prompt"]  # code already extracted deterministically
    assert got[0]["origin"] == "llm" and got[0]["source_url"] == "https://h/docs/en/hooks"
    assert got[0]["id"] == "u000001" and got[0]["keywords"] == ["version"]
    assert seen["think"] is False and seen["options"]["num_ctx"] == 8192
    assert units.llm_options("x" * 40_000)["num_ctx"] == 16384  # sized to the prompt


def test_dedup_drops_near_duplicates_by_embedding():
    us = [
        {"id": "a", "text": "Hooks run before tool calls."},
        {"id": "b", "text": "Hooks run before tool calls!"},  # exact after normalization
        {"id": "c", "text": "Hooks execute prior to each tool call."},  # semantic dup
        {"id": "d", "text": "Skills sync across sessions."},
    ]
    vecs = {
        "Hooks run before tool calls.": [1, 0],
        "Hooks execute prior to each tool call.": [0.99, 0.1],
        "Skills sync across sessions.": [0, 1],
    }
    kept = units.dedup(us, embed=lambda texts, model=None: [vecs[t] for t in texts], threshold=0.9)
    assert [u["id"] for u in kept] == ["a", "d"]


def test_units_run_is_resumable_and_skips_excluded_classes(tmp_path):
    m = _mirror(tmp_path)
    clean.run(m)
    calls = []

    def gen(prompt, model=None, timeout=None, options=None, think=None):
        calls.append(prompt)
        if "quickstart" in prompt:
            raise RuntimeError("host down")
        return (
            '[{"type":"fact","text":"Hooks are user-defined shell commands that run at points."}]'
        )

    embed = lambda t, model=None: [[1.0] for _ in t]  # noqa: E731
    r = units.run(m, generate=gen, embed=embed, log=lambda s: None)
    assert r["pages"] == 2 and r["done"] == 1 and r["failed"] == 1  # hooks ok, quickstart failed
    assert r["units"] == 1 and r["_rc"] == 3  # 50% failed -> stage fails
    n = len(calls)
    r2 = units.run(m, generate=gen, embed=embed, log=lambda s: None)
    assert len(calls) == n + 1 and r2["done"] == 1  # only the failed page retried
    assert [
        u["id"]
        for u in mirror_io.read_jsonl(tmp_path / "code.claude.com.reference" / "units.jsonl")
    ] == ["u000001"]


# ----------------------------------------------------------------- polish --


def test_polish_apply_edits_by_id_and_drops():
    us = [
        {
            "id": "u1",
            "type": "fact",
            "text": "Hooks runs before tool call",
            "source_url": "https://h/x",
            "anchor": "#a",
        },
        {
            "id": "u2",
            "type": "statement",
            "text": "Claude Code is loved by teams everywhere.",
            "source_url": "https://h/x",
            "anchor": "",
        },
        {
            "id": "u3",
            "type": "fact",
            "text": "Untouched unit stays exactly as it was.",
            "source_url": "https://h/x",
            "anchor": "",
        },
    ]
    reply = (
        'Here:\n[{"id":"u1","text":"Hooks run before every tool call.","type":"concept"},'
        '{"id":"u2","drop":true},{"id":"zz","text":"ignored"}]'
    )
    out, dropped = polish.apply(us, reply)
    assert [u["id"] for u in out] == ["u1", "u3"] and dropped == 1
    assert out[0]["text"] == "Hooks run before every tool call." and out[0]["anchor"] == "#a"
    assert out[0]["type"] == "concept" and out[0]["polished"] is True
    assert "polished" not in out[1]
    assert polish.apply(us, "garbage") == (us, 0)


def test_polish_run_calls_claude_per_batch_and_resumes(tmp_path):
    ref = tmp_path / "code.claude.com.reference"
    ref.mkdir()
    (tmp_path / "code.claude.com.md").write_text("")
    (ref / "units.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    "id": f"u{i}",
                    "type": "fact",
                    "text": f"fact number {i} about hooks",
                    "source_url": "https://h/docs/x",
                    "anchor": "",
                }
            )
            for i in range(3)
        )
        + "\n"
    )
    calls = []

    def fake_claude(prompt, model):
        calls.append(model)
        assert "https://h/docs" in prompt and '"id": "u0"' in prompt
        return json.dumps(
            [{"id": "u0", "text": "Fact zero about hooks."}, {"id": "u1", "drop": True}]
        )

    r = polish.run(
        tmp_path / "code.claude.com.md",
        model="claude-sonnet-5",
        run_claude=fake_claude,
        log=lambda s: None,
    )
    assert r == {
        "units": 3,
        "polished": 2,
        "dropped": 1,
        "batches": 1,
        "failed_batches": 0,
        "model": "claude-sonnet-5",
    } and calls == ["claude-sonnet-5"]
    lines = (ref / "units.polished.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["text"] == "Fact zero about hooks."
    polish.run(
        tmp_path / "code.claude.com.md",
        model="claude-sonnet-5",
        run_claude=fake_claude,
        log=lambda s: None,
    )
    assert len(calls) == 1  # state file says batch 0 is done


def test_run_claude_uses_headless_cli_and_raises_on_failure():
    seen = {}

    class R:
        returncode, stdout, stderr = 0, "[]", ""

    def fake_run(argv, **kw):
        seen["argv"], seen["input"] = argv, kw["input"]
        return R()

    assert polish.run_claude("PROMPT", "claude-sonnet-5", run=fake_run) == "[]"
    assert seen["argv"][:4] == ["claude", "-p", "--model", "claude-sonnet-5"]
    assert seen["input"] == "PROMPT"
    R.returncode = 1
    try:
        polish.run_claude("PROMPT", "m", run=fake_run)
    except RuntimeError as e:
        assert "exited 1" in str(e)
    else:
        raise AssertionError("expected RuntimeError")


def test_render_reids_the_merged_units(tmp_path):
    """structured.jsonl and units.jsonl both start at u000001; all_units.jsonl
    must not carry duplicates (chroma raises DuplicateIDError)."""
    m = _mirror(tmp_path)
    clean.run(m)
    extract.run(m)
    ref = tmp_path / "code.claude.com.reference"
    (ref / "units.jsonl").write_text(
        json.dumps(
            {
                "id": "u000001",
                "type": "fact",
                "text": "Hooks run before tool calls happen.",
                "source_url": "https://code.claude.com/docs/en/hooks",
                "anchor": "",
                "origin": "llm",
            }
        )
        + "\n"
    )
    render.run(m)
    ids = [u["id"] for u in mirror_io.read_jsonl(ref / "all_units.jsonl")]
    assert len(ids) == len(set(ids)) and ids[-1] == f"u{len(ids):06d}"
    assert json.loads((ref / "units.jsonl").read_text())["id"] == "u000001"  # source untouched


# ------------------------------------------------------------- export_llms --


def test_export_writes_index_full_small_facts_and_manifest(tmp_path):
    from docset_refine import export_llms

    m = _mirror(tmp_path)
    (tmp_path / "code.claude.com_state.json").write_text(json.dumps({"acquire": "llms-full"}))
    clean.run(m)
    extract.run(m)
    render.run(m)
    r = export_llms.run(m)
    d = tmp_path / "code.claude.com.llms"
    idx = (d / "llms.txt").read_text()
    assert idx.startswith("# code.claude.com documentation\n\n> ")
    assert "## Optional" in idx and "changelog" in idx.split("## Optional")[1]  # changelog demoted
    assert (
        "(https://code.claude.com/docs/en/hooks.md): Hooks are user-defined" in idx
    )  # .md twin + description
    full = (d / "llms-full.txt").read_text()
    assert full.splitlines()[0].startswith("<!-- llms-full grammar: mintlify")
    assert "# Hooks reference\nSource: https://code.claude.com/docs/en/hooks\n" in full
    facts = (d / "llms-facts.txt").read_text()
    assert "- [snippet] Exit codes: claude --version" in facts
    assert "— https://code.claude.com/docs/en/hooks#exit-codes" in facts
    man = json.loads((d / "manifest.json").read_text())
    assert set(man["files"]) == {"llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt"}
    assert man["files"]["llms-full.txt"]["tokens"] >= 1 and man["acquired"] == "llms-full"
    assert r["pages"] == 3
    # the exported llms-full round-trips through the acquisition splitter
    import llms_acquire as la

    assert [p["url"] for p in la.split_llms_full(full)][
        0
    ] == "https://code.claude.com/docs/en/hooks"


def test_family_index_links_product_indexes_with_counts(tmp_path):
    from docset_refine import export_llms

    m = _mirror(tmp_path)
    clean.run(m)
    extract.run(m)
    render.run(m)
    export_llms.run(m)
    out = tmp_path / "family" / "llms.txt"
    r = export_llms.family(
        [m], "Acme docs", "All Acme products.", out, base_url="https://hub.local/llms"
    )
    text = out.read_text()
    assert text.startswith("# Acme docs\n\n> All Acme products.\n")
    assert (
        "- [code.claude.com documentation](https://hub.local/llms/code.claude.com.llms/llms.txt): "
        "3 pages, ~"
    ) in text
    assert "## Facts" in text and "code.claude.com.llms/llms-facts.txt" in text
    assert r["products"] == 1


# ------------------------------------------------ extract: anchors + clipping --


def test_anchors_fall_back_to_a_real_source_heading():
    """Cleaning renders MDX <Step title> as a heading the site never anchors;
    units under it must anchor to the nearest heading that exists on the
    source page (1,124 dangling anchors on the code.claude.com pilot)."""
    text = (
        "## Install\n\nInstall the CLI before opening any view in the app.\n\n"
        "### Open Agent View\n\nOpens the agent view for the current session.\n\n"
        "```bash\nclaude view\n```\n"
    )
    real = {"https://h/docs/en/x": {"install"}}
    page = _page(text, url="https://h/docs/en/x")
    s = extract.snippets(page, real=real)[0]
    assert s["anchor"] == "#install" and s["text"] == "Open Agent View: claude view"
    d = extract.definitions(page, real=real)
    assert [x["anchor"] for x in d] == ["#install", "#install"]
    assert d[1]["text"].startswith("Open Agent View — ")  # label keeps the synthetic title
    # no real-heading map -> unchanged behaviour
    assert extract.snippets(page)[0]["anchor"] == "#open-agent-view"


def test_real_headings_ignores_fenced_hashes():
    pages = [{"url": "https://h/p/", "text": "# Top\n\n```sh\n# not a heading\n```\n\n## Real\n"}]
    assert extract.real_headings(pages) == {"https://h/p": {"top", "real"}}


def test_wide_table_rows_and_long_paragraphs_are_clipped():
    cells = " | ".join(f"c{i}" for i in range(12))
    vals = " | ".join("v" * 60 for _ in range(12))
    wide = f"| name | {cells} |\n|{'---|' * 13}\n| `X` | {vals} |\n"
    row = extract.tables(_page(wide))[0]
    assert len(row["text"]) <= extract.MAX_UNIT_CHARS and row["text"].endswith("…")
    para = "## Big\n\n" + "word " * 200 + "\n"
    d = extract.definitions(_page(para))[0]
    assert len(d["text"]) <= extract.MAX_DEF_CHARS + len("Big — ") and d["text"].endswith("…")
    three = "## Three\n\nOne here. Two here. Three here. Four here.\n"
    assert extract.definitions(_page(three))[0]["text"] == "Three — One here. Two here."
    ch = extract.changes(
        _page(
            "# Changelog\n\n## 1.0 — August 1, 2026\n\n" + "- item " * 200,
            url="https://h/c",
            cls="changelog",
        )
    )[0]
    assert len(ch["text"]) <= extract.MAX_UNIT_CHARS and ch["text"].endswith("…")


def test_small_variant_never_exceeds_its_budget():
    from docset_refine import export_llms

    pages = [
        {"url": f"https://h/p{i}", "title": f"P{i}", "class": "reference", "text": "x" * 950}
        for i in range(10)
    ]
    out = export_llms.build_small(pages, max_chars=3000)
    assert len(out) <= 3000
    assert out.count("\n# P") == 2  # exact rendering cost: 92 + 3 * 970 fits, 4 does not
    assert export_llms.build_small(pages, max_chars=50) == export_llms.build_full([])


def test_oversize_index_splits_hub_and_spoke(tmp_path, monkeypatch):
    from docset_refine import export_llms

    m = _mirror(tmp_path)
    clean.run(m)
    extract.run(m)
    render.run(m)
    monkeypatch.setattr(export_llms, "INDEX_SPLIT_BYTES", 200)  # force the split on 3 pages
    r = export_llms.run(m)
    d = tmp_path / "code.claude.com.llms"
    root = (d / "llms.txt").read_text()
    assert "## Sections" in root and r["sections"] >= 1
    spokes = sorted(p.relative_to(d).as_posix() for p in d.glob("*/llms.txt"))
    assert spokes and all(f"]({s})" in root for s in spokes)  # root links every spoke
    assert "pages, ~" in root and "tokens" in root  # counts travel with links
    spoke = (d / spokes[0]).read_text()
    assert (
        spoke.startswith("# code.claude.com documentation — ")
        and "(https://code.claude.com/docs/en/" in spoke
    )
    assert "https://code.claude.com/docs/en/hooks.md" not in root  # pages live in spokes only
    man = json.loads((d / "manifest.json").read_text())
    assert man["sections"] == spokes and all(s in man["files"] for s in spokes)
    # regenerating without the split removes stale section dirs
    monkeypatch.setattr(export_llms, "INDEX_SPLIT_BYTES", 10_000_000)
    export_llms.run(m)
    assert not list(d.glob("*/llms.txt")) and "## Sections" not in (d / "llms.txt").read_text()


def test_split_recurses_by_path_and_falls_back_to_parts():
    from docset_refine import export_llms

    desc = "A description long enough to make every leaf exceed the tiny budget used here. " * 2
    nested = [
        {
            "url": f"https://h/docs/a/{sub}/p{i}",
            "title": f"{sub}{i}",
            "class": "guide",
            "text": desc,
        }
        for sub in ("b", "c")
        for i in range(3)
    ]
    flat = [
        {"url": f"https://h/docs/z/p{i}", "title": f"z{i}", "class": "guide", "text": desc}
        for i in range(5)
    ]
    defs = {p["url"]: desc for p in nested + flat}
    export_llms.PART_PAGES, saved = 2, export_llms.PART_PAGES
    try:
        root, spokes = export_llms.build_split_index(
            nested + flat, "H docs", "S.", defs, max_bytes=400
        )
    finally:
        export_llms.PART_PAGES = saved
    assert "## Sections" in root and "](a/llms.txt)" in root and "](z/llms.txt)" in root
    # a/ is a hub over b/ and c/ (split by the next path segment)
    assert "## Sections" in spokes["a/llms.txt"] and {"a/b/llms.txt", "a/c/llms.txt"} <= set(spokes)
    assert "](b/llms.txt)" in spokes["a/llms.txt"]  # hub links are relative to the hub
    # z/ has no further path structure -> fixed-size parts
    assert "## Sections" in spokes["z/llms.txt"] and {
        "z/part-1/llms.txt",
        "z/part-3/llms.txt",
    } <= set(spokes)
    leaves = [v for k, v in spokes.items() if "## Sections" not in v]
    links = sum(v.count("](https://h/docs/") for v in leaves)
    assert links == len(nested + flat)  # every page in exactly one leaf
    assert not any("](https://h/docs/" in v for v in spokes.values() if "## Sections" in v)


def test_export_overrides_survive_regeneration(tmp_path):
    from docset_refine import export_llms

    m = _mirror(tmp_path)
    clean.run(m)
    extract.run(m)
    render.run(m)
    ov = tmp_path / "code.claude.com.llms.overrides.json"
    ov.write_text(
        json.dumps(
            {
                "title": "Claude Code docs",
                "summary": "Hand summary.",
                "section_order": ["Hooks", "Getting started"],
            }
        )
    )
    export_llms.run(m)
    d = tmp_path / "code.claude.com.llms"
    idx = (d / "llms.txt").read_text()
    assert idx.startswith("# Claude Code docs\n\n> Hand summary.\n")
    man = json.loads((d / "manifest.json").read_text())
    assert man["overrides"]["title"] == "Claude Code docs"
    ov.unlink()  # second run: overrides now come from the manifest
    export_llms.run(m)
    assert (d / "llms.txt").read_text().startswith("# Claude Code docs\n\n> Hand summary.\n")
    assert export_llms.run(m, title="CLI wins")["title"] == "CLI wins"

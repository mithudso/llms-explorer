"""docset_refine topical: pool parsers, dedupe, skeleton from the concept tree,
keyword + embedding assignment, the written files, manifest, registration."""

import json

import pytest

import concept_tree as ct
from docset_refine import topical

NODES = [
    {"concept": "llms.txt and LLM-readable documentation", "skillId": "document-formats",
     "parentConcept": None, "researchedAt": "2026-08-30",
     "childConcepts": ["llms.txt specification v2", "llms-full.txt page grammars",
                       "Content Signals"]},
    {"concept": "llms.txt specification v2", "skillId": "document-formats",
     "parentConcept": "llms.txt and LLM-readable documentation", "childConcepts": [],
     "researchedAt": "2026-08-30", "aliases": ["spec", "llmstxt.org"]},
    {"concept": "llms-full.txt page grammars", "skillId": "document-formats",
     "parentConcept": "llms.txt and LLM-readable documentation", "childConcepts": [],
     "researchedAt": "2026-08-30"},
]

REF_MD = """# llms.txt — the spec

## 2. The spec, v2

The llms.txt specification is a markdown file at a site root with an H1 and a blockquote.[^1]
Sections are H2 headers containing `- [name](url): description` link lists.[^1][^2]
- Keep the `## Optional` section last so a consumer can skip it.[^1]

## 3. Grammars

| Host | Grammar | Evidence |
|---|---|---|
| Mintlify | `# Title` / `Source:` | 100k-char split[^3] |

llms-full.txt is not in the spec; three page grammars exist in the wild.[^3]
Cursor breaks above 50k tokens, so big files are unstable.[^4]
A sentence with a dangling footnote.[^9]
Short.[^1]

```md
# Not a fact
Source: x.[^1]
```

## References
[^1]: https://llmstxt.org/ — spec
[^2]: https://llmstxt.org/changes.md — changes
[^3]: https://www.mintlify.com/docs/ai/llmstxt — grammar
[^4]: https://forum.cursor.com/t/llms-txt — cursor
"""

FACTS_TXT = """# X — facts

## Y
- [parameter] `X-Markdown-Tokens` header carries the token count — https://developers.cloudflare.com/llms#headers
- [statement] llms-full.txt is not in the spec; three page grammars exist in the wild. — https://other.example/dup
- broken line without a dash-source
"""


@pytest.fixture
def tree(tmp_path, monkeypatch):
    tp = tmp_path / "tree.json"
    tp.write_text(json.dumps(NODES))
    (tmp_path / "RESEARCH_QUEUE.md").write_text("# q\n")
    monkeypatch.setattr(ct, "TREE_PATH", tp)
    monkeypatch.setattr(ct, "QUEUE_PATH", tmp_path / "RESEARCH_QUEUE.md")
    monkeypatch.setattr(ct, "STATE_PATH", tmp_path / "research_state.json", raising=False)
    t = ct.ConceptTree.load()
    ct.ensure_slugs(t.nodes)
    return t


def test_parse_reference_md_anchors_each_footnoted_sentence(tmp_path):
    p = tmp_path / "llms-txt.md"
    p.write_text(REF_MD)
    recs, rej = topical.parse_reference_md(p, 1)
    texts = [r["text"] for r in recs]
    assert texts[0].startswith("The llms.txt specification is a markdown file")
    assert recs[0]["type"] == "definition" and recs[0]["source"] == "https://llmstxt.org/"
    two = next(r for r in recs if r["text"].startswith("Sections are H2"))
    assert two["also"] == ["https://llmstxt.org/changes.md"]        # second footnote rides along
    assert "`- [name](url): description`" in two["text"]
    assert "- [name](url): description" in two["keywords"]
    keep = next(r for r in recs if r["text"].startswith("Keep the"))
    assert keep["type"] == "actionable"
    cursor = next(r for r in recs if "Cursor breaks" in r["text"])
    assert cursor["type"] == "problem"
    assert all("Not a fact" not in r["text"] for r in recs)          # fenced block skipped
    assert all(r["text"] != "Short" for r in recs)                    # too short
    assert rej == [{"file": "llms-txt.md", "line": "A sentence with a dangling footnote.",
                    "reason": "footnote 9 has no url"}]
    assert cursor["heading"] == "3. Grammars" and "3. Grammars" not in cursor["keywords"]
    row = next(r for r in recs if r["text"].startswith("Mintlify — "))
    assert row["text"] == "Mintlify — Grammar: `# Title` / `Source:`; Evidence: 100k-char split"
    assert row["source"] == "https://www.mintlify.com/docs/ai/llmstxt"
    assert all(not r["text"].startswith("Host — ") for r in recs)      # header row has no footnote
    assert recs[0]["file"] == "llms-txt"
    assert recs[0]["verified"] == ""


def test_parse_reference_md_tables_leadins_footnotes(tmp_path):
    md = r"""# T
verified-as-of: 2026-08-30

## 1. What it is, in one paragraph

A markdown file — `/llms.txt` at a site root — that maps a site for agents.[^1]

## 2. Structure

Structure, in order (verbatim):[^1]
- An H1 with the name of the project
- A blockquote with a short summary of the project
- 10–50 links for a product index is the usual range of a good file.[^2]

| Producer | Page block | Sample |
|---|---|---|
| Firecrawl | `<\|firecrawl-page-N\|>` delimiter | n/a[^3] |
| Docusaurus core | none | — [^2] |

Content-Type may be `text/plain \| text/markdown` for the twin.[^3][^3][^4]

[^1]: https://llmstxt.org/ — spec
[^2]: https://a.example/x and https://b.example/y — two
[^3]: https://firecrawl.dev/ — fc
[^4]: https://c.example/ — c
"""
    p = tmp_path / "spoke.md"
    p.write_text(md)
    recs, rej = topical.parse_reference_md(p, 1)
    t = {r["text"]: r for r in recs}
    first = next(r for r in recs if r["text"].startswith("A markdown file"))
    assert first["type"] == "definition" and first["verified"] == "2026-08-30"
    # lead-in ending in ":" is dropped; its bullets inherit the footnote
    assert "Structure, in order (verbatim):" not in t
    assert t["An H1 with the name of the project"]["source"] == "https://llmstxt.org/"
    # leading digits survive the list-marker strip
    ten = next(r for r in recs if "links for a product index" in r["text"])
    assert ten["text"].startswith("10–50 links")
    assert ten["source"] == "https://a.example/x" and ten["also"] == ["https://b.example/y"]
    # a later footnote's host named in the sentence never steals the source
    (tmp_path / "s2.md").write_text(
        "Spec v2 says a file covers its subpath; developers.cloudflare.com applies it.[^1][^2]\n\n"
        "[^1]: https://llmstxt.org/ — spec\n"
        "[^2]: https://developers.cloudflare.com/llms.txt — cf\n")
    r2, _ = topical.parse_reference_md(tmp_path / "s2.md", 1)
    assert r2[0]["source"] == "https://llmstxt.org/"
    assert r2[0]["also"] == ["https://developers.cloudflare.com/llms.txt"]
    # table: escaped pipes kept, header labels inlined, dead cells dropped
    fc = next(r for r in recs if r["text"].startswith("Firecrawl"))
    assert fc["text"] == "Firecrawl — Page block: `<|firecrawl-page-N|>` delimiter"
    assert all(not r["text"].startswith("Docusaurus core") for r in recs)   # only 1 live cell
    # pipe inside backticks is not a column edge; repeated footnote not repeated in also
    ct_ = next(r for r in recs if r["text"].startswith("Content-Type"))
    assert "`text/plain | text/markdown`" in ct_["text"]
    assert ct_["also"] == ["https://c.example/"]
    assert rej == []


def test_near_dedupe_merges_paraphrases_keeping_sources():
    pool = [topical._rec(1, "statement", "97% of files get zero AI requests", "https://a"),
            topical._rec(2, "statement", "Ninety-seven percent of llms.txt files see no AI traffic",
                         "https://b"),
            topical._rec(3, "statement", "Cursor cannot read llms.txt", "https://c")]
    vec = {"97%": [1, 0], "Ninety": [0.99, 0.14], "Cursor": [0, 1]}

    def embed(texts):
        return [next(v for k, v in vec.items() if t.startswith(k)) for t in texts]
    out = topical.near_dedupe(pool, embed, threshold=0.93)
    assert [r["id"] for r in out] == ["t000001", "t000003"]
    assert out[0]["also"] == ["https://b"]


def test_split_unit_by_sentence_then_clause_keeps_subject():
    long_row = "Tool — " + "; ".join(f"Col{i}: " + "word " * 30 for i in range(4))
    parts = topical._split_unit(long_row)
    assert len(parts) >= 2 and all(p.startswith("Tool — ") for p in parts)
    assert all(len(p) <= topical.MAX_UNIT_CHARS for p in parts)
    three = "One claim here. Second claim here. Third claim here."
    assert topical._split_unit(three) == ["One claim here. Second claim here.", "Third claim here."]
    assert topical._split_unit("short") == ["short"]


def test_prefer_named_host_and_backtick_safe_splits():
    urls = ["https://docs.github.com/llms.txt", "https://docs.anthropic.com/llms.txt"]
    assert topical._prefer_named_host(urls, "Anthropic — docs.anthropic.com/llms.txt sample") == \
        [urls[1], urls[0]]
    assert topical._prefer_named_host(urls, "no host named here") == urls
    assert topical._clause_split("a; `Link: <x>; rel=\"d\"`; c", "; ") == \
        ["a", "`Link: <x>; rel=\"d\"`", "c"]
    # a long sentence with no subject stays whole rather than fragmenting…
    long = "word " * 100
    assert topical._split_unit(long.strip()) == [long.strip()]
    # …unless its semicolon clauses each stand alone as claims
    claims = "; ".join(f"Vendor{i} caps the index at {i}00 characters and splits the overflow "
                       f"into per-group files" for i in range(6))
    parts = topical._split_unit(claims)
    assert len(parts) > 1 and all(len(x) <= topical.MAX_UNIT_CHARS for x in parts)
    assert topical._desc("Alpha beta (gamma delta, epsilon " + "w " * 30) == "Alpha beta"
    assert topical._desc("First sentence here is short. Then a very long tail " + "w " * 30) == \
        "First sentence here is short."
    d = topical._desc("see the `Accept: text/markdown` header and " + "w " * 30)
    assert d.count("`") % 2 == 0


def test_sentences_respect_quotes_and_pronouns():
    t = ('The spec says "agents view the file. The detail lives behind the links." '
         'It is not ratified. Google disagrees. This matters (see A. B. below). Done here.')
    got = topical.sentences(t)
    assert got[0] == 'The spec says "agents view the file. The detail lives behind the links." ' \
                     'It is not ratified.'
    assert got[1] == "Google disagrees. This matters (see A. B. below)."
    assert got[2] == "Done here."


def test_link_targets_describe_only_what_the_target_carries():
    recs = [topical._rec(1, "statement", "Cloudflare Markdown for Agents returns x-markdown-tokens",
                         "https://vercel.com/blog/x"),
            topical._rec(2, "statement", "Vercel proposed Accept: text/markdown negotiation",
                         "https://vercel.com/blog/x"),
            topical._rec(3, "statement", "Starlight and nuxt.com ship small variants",
                         "https://www.mintlify.com/docs/ai/llmstxt")]
    topical._KNOWN_VENDORS.clear()
    topical._KNOWN_VENDORS.update(topical.vendors_in(recs) | {"cloudflare", "starlight"})
    out = topical.link_targets(recs)
    urls = {t["url"]: t for t in out}
    assert urls["https://vercel.com/blog/x"]["description"].startswith("Vercel proposed")
    assert "https://www.mintlify.com/docs/ai/llmstxt" not in urls      # only cross-vendor units
    assert topical.vendors_in(recs) == {"vercel", "mintlify"}


def test_link_title_and_desc_band():
    assert topical.link_title("https://github.com/pawamoy/mkdocs-llmstxt/blob/main/x") == \
        "github.com/pawamoy/mkdocs-llmstxt"
    assert topical.link_title("https://www.mintlify.com/docs/ai/llmstxt") == "mintlify.com/docs/ai"
    assert topical.link_title("https://llmstxt.org/") == "llmstxt.org"
    d = topical._desc("w " * 40)
    assert d.count(" ") == 24 and not d.endswith("…")
    assert topical._desc("a b c d e f g h i j k l m n o p, q r s t u v w x y z aa") == \
        "a b c d e f g h i j k l m n o p"
    assert topical._desc("short one") == "short one"


def test_clean_md_strips_formatting_not_meaning():
    assert topical._clean_md("> **Honesty note.** `llms.txt` is a *proposal*") == \
        "Honesty note. `llms.txt` is a *proposal*"
    assert topical._clean_md("Descriptions are the product.** Every generator") == \
        "Descriptions are the product. Every generator"
    assert topical._rec(1, "statement", "- **Bold** start", "https://s")["text"] == "Bold start"


def test_file_prior_routes_a_spoke_to_its_own_section(tree):
    secs = topical.skeleton(tree, "llms.txt and LLM-readable documentation")
    r = topical._rec(1, "statement", "Ahrefs logs show almost no requests", "https://a",
                     file="llms-full-txt-page-grammars")
    b = topical.assign([r], secs)
    assert [x["id"] for x in b["llms-full.txt page grammars"]] == ["t000001"]
    # an alias names the spoke only by exact stem, never fuzzily
    secs[0]["aliases"].append("spec-notes")
    r2 = topical._rec(2, "statement", "Ahrefs logs show almost no requests", "https://a",
                      file="spec-notes")
    assert topical.assign([r2], secs)["llms.txt specification v2"][0]["id"] == "t000002"
    secs[1]["aliases"].append("llms-full.txt")          # slug llms-fulltxt ≈ llms-txt (0.80)
    assert not topical._file_matches(secs[1], "llms-txt")


def test_parse_facts_txt_and_units_jsonl(tmp_path):
    f = tmp_path / "llms-facts.txt"
    f.write_text(FACTS_TXT)
    recs, rej = topical.parse_facts_txt(f, 1)
    assert recs[0]["type"] == "parameter" and recs[0]["anchor"] == "#headers"
    assert recs[0]["source"] == "https://developers.cloudflare.com/llms"
    assert "X-Markdown-Tokens" in recs[0]["keywords"]
    assert rej[0]["reason"] == "bad fact line"
    u = tmp_path / "units.jsonl"
    u.write_text(json.dumps({"id": "u1", "type": "snippet", "text": "run it",
                             "source_url": "https://a/b", "anchor": "#c",
                             "keywords": ["k"], "code": {"lang": "sh", "body": "claude -p\nx"},
                             "origin": "code"}) + "\n"
                 + json.dumps({"type": "fact", "text": "no source"}) + "\nnot json\n")
    recs, rej = topical.parse_units_jsonl(u, 1)
    assert recs[0]["text"] == "run it — `claude -p`" and recs[0]["origin"] == "code"
    assert [r["reason"] for r in rej] == ["unsourced", "bad json"]


def test_dedupe_merges_sources_as_also(tmp_path):
    (tmp_path / "a.md").write_text(REF_MD)
    (tmp_path / "llms-facts.txt").write_text(FACTS_TXT)
    pool, _ = topical.load_pool([tmp_path / "a.md", tmp_path / "llms-facts.txt"])
    n = len(pool)
    d = topical.dedupe(pool)
    assert len(d) == n - 1
    hit = next(r for r in d if r["text"].startswith("llms-full.txt is not in the spec"))
    assert hit["source"] == "https://www.mintlify.com/docs/ai/llmstxt"
    assert hit["also"] == ["https://other.example/dup"]


def test_skeleton_from_children_marks_frontier(tree):
    secs = topical.skeleton(tree, "llms.txt and LLM-readable documentation")
    assert [s["name"] for s in secs] == ["llms.txt specification v2",
                                         "llms-full.txt page grammars", "Content Signals"]
    assert [s["frontier"] for s in secs] == [False, False, True]
    assert secs[0]["slug"] == "llms-txt-specification-v2"
    assert secs[0]["aliases"] == ["spec", "llmstxt.org"]
    # a childless subject is its own section
    solo = topical.skeleton(tree, "llms.txt specification v2")
    assert solo[0]["name"] == "llms.txt specification v2"
    with pytest.raises(SystemExit):
        topical.skeleton(tree, "nope")


def test_assign_keyword_then_embedding_then_shared(tree):
    secs = topical.skeleton(tree, "llms.txt and LLM-readable documentation")
    pool = [
        topical._rec(1, "definition", "The llms.txt specification v2 requires an H1", "https://s"),
        topical._rec(2, "statement", "llms-full.txt grammars vary per host", "https://g"),
        topical._rec(3, "statement", "Nothing matches any section here", "https://n"),
        topical._rec(4, "statement", "Cursor limit is fifty thousand tokens", "https://c"),
    ]
    # no embed: undecided → Shared
    b = topical.assign(pool, secs)
    assert [r["id"] for r in b["llms.txt specification v2"]] == ["t000001"]
    assert [r["id"] for r in b["llms-full.txt page grammars"]] == ["t000002"]
    assert sorted(r["id"] for r in b[topical.SHARED]) == ["t000003", "t000004"]

    # fake embed: "Cursor" text is near the grammars centroid, "Nothing" is near nothing
    def embed(texts):
        out = []
        for t in texts:
            tl = t.lower()
            if "grammar" in tl or "cursor" in tl:
                out.append([0.0, 1.0])
            elif "specification" in tl:
                out.append([1.0, 0.0])
            else:
                out.append([0.7, 0.7])   # cos ≈ 0.7 to both — above floor, ambiguous
        return out
    b = topical.assign(pool, secs, embed=embed)
    assert "t000004" in [r["id"] for r in b["llms-full.txt page grammars"]]
    # ambiguous-but-above-floor lands in the first max; floor keeps only real misses in Shared
    assert all(r["id"] != "t000004" for r in b[topical.SHARED])
    # type order inside a section: definition before statement
    b2 = topical.assign([pool[1], pool[0]], secs)
    assert [r["type"] for r in b2["llms.txt specification v2"]] == ["definition"]


def test_run_writes_index_facts_manifest_and_registers(tree, tmp_path):
    (tmp_path / "llms-txt.md").write_text(REF_MD)
    (tmp_path / "llms-facts.txt").write_text(FACTS_TXT)
    out = tmp_path / "llms-topical" / "llms-txt.llms"
    man = topical.run([tmp_path / "llms-txt.md", tmp_path / "llms-facts.txt"],
                      "llms.txt and LLM-readable documentation", out, tree=tree,
                      base_url="http://127.0.0.1:8788/t/llms-txt", register=True,
                      log=lambda *_: None)
    idx = (out / "llms.txt").read_text()
    facts = (out / "llms-facts.txt").read_text()
    assert idx.startswith("# llms.txt and LLM-readable documentation\n\n> ")
    assert "<!-- generated by docset_refine topical v1" in idx
    assert "## llms.txt specification v2" in idx
    assert ("- [Facts: llms.txt specification v2](http://127.0.0.1:8788/t/llms-txt/llms-facts.txt"
            "#llms-txt-specification-v2): ") in idx
    assert "- [llmstxt.org](https://llmstxt.org/): The llms.txt specification is a markdown" in idx
    assert "> The llms.txt specification is a markdown file" in idx      # I2: what it is
    assert "This index is for agents and people building, generating or consuming" in idx
    assert "](llms-facts.txt#llms-txt-specification-v2)" not in idx   # base_url → absolute
    assert "## Optional" in idx and "Content Signals — known, unresearched (frontier)" in idx
    assert '<a id="llms-txt-specification-v2"></a>' in facts
    assert "- [definition] The llms.txt specification is a markdown file" in facts
    assert "· also: https://llmstxt.org/changes.md" in facts
    # tail order keywords → verified-as-of → also (what llms_lint's UNIT_RE accepts)
    tailed = [ln for ln in facts.splitlines() if "· also:" in ln and "· keywords:" in ln]
    assert tailed and all(ln.index("· keywords:") < ln.index("· also:") for ln in tailed)
    assert "· keywords:" in facts
    assert (out / "pool.rejected.jsonl").exists()
    units = [json.loads(x) for x in (out / "units.jsonl").read_text().splitlines()]
    assert units and all({"id", "type", "text", "source_url", "keywords", "section"} <= set(u)
                         for u in units)
    # the facts file round-trips through the pool parser with its trailing fields
    back, rej = topical.parse_facts_txt(out / "llms-facts.txt", 1)
    assert rej == [] and len(back) == len(units)
    assert any(b["also"] for b in back)
    assert man["kind"] == "topical" and man["slug"] == "llms-txt"   # = the served dir name
    assert man["sections"]["llms.txt specification v2"]["facts"] >= 3
    assert man["sections"]["Content Signals"]["frontier"] is True
    assert man["files"]["llms-facts.txt"]["tokens"] >= 1
    # registered on the tree node, persisted
    saved = json.loads(ct.TREE_PATH.read_text())
    root = next(n for n in saved if n["concept"] == "llms.txt and LLM-readable documentation")
    assert root["llmsFile"] == "/t/llms-txt/llms.txt"
    assert all("slug" in n for n in saved)

    # overrides survive regeneration
    m = json.loads((out / "manifest.json").read_text())
    m["overrides"] = {"title": "llms.txt (topical)", "summary": "Hand summary."}
    (out / "manifest.json").write_text(json.dumps(m))
    m["overrides"]["section_order"] = ["llms-full.txt page grammars", "llms.txt specification v2"]
    (out / "manifest.json").write_text(json.dumps(m))
    topical.run([tmp_path / "llms-txt.md"], "llms.txt and LLM-readable documentation", out,
                tree=tree, log=lambda *_: None)
    idx = (out / "llms.txt").read_text()
    assert idx.startswith("# llms.txt (topical)\n\n> Hand summary.")
    assert "](llms-facts.txt#llms-txt-specification-v2)" in idx           # relative by default
    heads = [ln for ln in idx.splitlines() if ln.startswith("## ")]
    if "## llms-full.txt page grammars" in heads:
        assert heads.index("## llms-full.txt page grammars") < heads.index(
            "## llms.txt specification v2")


def test_thin_section_goes_to_optional(tree, tmp_path):
    (tmp_path / "f.txt").write_text(
        "- [statement] llms.txt specification v2 needs an H1 — https://s/1\n"
        "- [statement] llms-full.txt page grammars differ — https://g/1\n")
    out = tmp_path / "o"
    topical.run([tmp_path / "f.txt"], "llms.txt and LLM-readable documentation", out,
                tree=tree, log=lambda *_: None)
    idx = (out / "llms.txt").read_text()
    assert "thin — 1 facts, queued for research" in idx
    assert "## llms.txt specification v2" not in idx


def test_cli_topical_no_embed(tree, tmp_path, monkeypatch):
    from docset_refine.__main__ import main
    (tmp_path / "f.txt").write_text(FACTS_TXT)
    out = tmp_path / "o"
    rc = main(["topical", "--from", str(tmp_path / "f.txt"),
               "--subject", "llms.txt and LLM-readable documentation",
               "--out", str(out), "--no-embed"])
    assert rc in (0, None) and (out / "manifest.json").exists()

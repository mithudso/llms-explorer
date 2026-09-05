# site/tests/test_demo_page.py
# ruff: noqa: E501  -- fixture strings and asserted page spans are real lines; wrapping changes what is tested
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_demo  # noqa: E402


class FakeStore:
    def docset_model(self, key): return "m"
    def query(self, key, qvec, top): return [{"score": 0.9, "url": "https://h/a", "seq": 1, "text": "vector hit " + "x" * 400}]
    def keyword_count(self, key): return 1
    def keyword_query(self, key, q, top, mode="any"): return [{"score": 5.0, "url": "https://h/b", "seq": 2, "snippet": "kw hit"}]


def test_record_shape_and_truncation():
    rec = gen_demo.record(FakeStore(), "d__facts", [{"q": "why split big files", "kind": "paraphrase"}],
                          embed=lambda qs, model=None: [[0.1]], today="2026-08-31")
    assert rec["generated"] == "2026-08-31" and rec["docset"] == "d__facts"
    q = rec["questions"][0]
    assert {"keyword", "vector", "hybrid"} <= set(q)
    assert len(q["vector"][0]["text"]) <= 300
    assert q["hybrid"], "hybrid must fuse both legs"
    assert set(q["ms"]) == {"keyword", "vector", "hybrid"}


def test_keyword_leg_carries_text_not_snippet():
    """The three legs are rendered side by side, so every hit has the same four keys —
    the FTS5 leg's `snippet` is normalised to `text` at record time, not in the page."""
    rec = gen_demo.record(FakeStore(), "d__facts", [{"q": "CLAUDE_CODE_SYNC_SKILLS", "kind": "exact-token"}],
                          embed=lambda qs, model=None: [[0.1]], today="2026-08-31")
    hit = rec["questions"][0]["keyword"][0]
    assert {"score", "url", "seq", "text"} <= set(hit)
    assert hit["text"] == "kw hit"


def test_hybrid_is_the_same_rrf_the_hub_serves():
    """k=60, keyed by (url, seq), a hit both legs found outranks a hit one leg found."""
    both = {"score": 0.5, "url": "https://h/a", "seq": 1, "text": "agreed"}
    only = {"score": 0.9, "url": "https://h/b", "seq": 2, "text": "alone"}
    fused = gen_demo.rrf([both, only], [both], top=5)
    assert [h["url"] for h in fused] == ["https://h/a", "https://h/b"]
    # the hub rounds after every addition, so the recording must too
    assert fused[0]["score"] == round(round(1 / 61, 5) + 1 / 61, 5)
    assert fused[0]["legs"] == 2 and fused[1]["legs"] == 1


def test_timings_come_from_the_injected_clock():
    ticks = iter([0.0, 0.002, 0.010, 0.011])   # kw start, kw end/vec start, vec end, fuse end
    rec = gen_demo.record(FakeStore(), "d__facts", [{"q": "q", "kind": "paraphrase"}],
                          embed=lambda qs, model=None: [[0.1]], today="2026-08-31",
                          clock=lambda: next(ticks))
    ms = rec["questions"][0]["ms"]
    assert ms["keyword"] == 2.0 and ms["vector"] == 8.0
    # hybrid runs both legs and then fuses them: it costs the sum, never less than either
    assert ms["hybrid"] == 11.0


def test_questions_are_the_golden_set_plus_exact_token_probes():
    kinds = [q["kind"] for q in gen_demo.QUESTIONS]
    assert len(gen_demo.QUESTIONS) >= 8
    assert kinds.count("exact-token") >= 4 and kinds.count("paraphrase") >= 4
    assert set(kinds) == {"exact-token", "paraphrase"}


def test_committed_demo_is_present_and_labelled():
    d = json.loads((SITE / "src/data/demo.json").read_text())
    assert len(d["questions"]) >= 8
    assert sum(1 for q in d["questions"] if q["kind"] == "exact-token") >= 4
    assert len(d["generated"]) == 10


def test_committed_demo_is_a_real_recording():
    d = json.loads((SITE / "src/data/demo.json").read_text())
    assert d["docset"].startswith("codeclaudecom__codeclaudecom")
    for q in d["questions"]:
        assert q["keyword"] or q["vector"], q["q"]
        assert q["hybrid"], q["q"]
        for leg in ("keyword", "vector", "hybrid"):
            for hit in q[leg]:
                assert hit["url"].startswith("http"), (q["q"], leg)
                assert len(hit["text"]) <= 300, (q["q"], leg)
        assert all(v > 0 for v in q["ms"].values()), q["q"]


def test_demo_page_says_it_is_a_recording_with_its_date():
    page = (SITE / "src/pages/demo.astro").read_text()
    d = json.loads((SITE / "src/data/demo.json").read_text())
    assert "demo.json" in page
    assert "recording" in page.lower()
    assert "generated" in page  # the date is read from the data, never retyped
    assert "/reference/" in page
    assert d["generated"]  # and the recording it labels exists


def test_demo_explorer_island_renders_the_three_legs():
    c = (SITE / "src/components/DemoExplorer.astro").read_text()
    for leg in ("keyword", "vector", "hybrid"):
        assert leg in c
    assert "<script" in c, "the filter is a client island"


def test_semantic_indexing_essay_is_in_the_family():
    text = (SITE / "src/content/blog/semantic-indexing.md").read_text()
    assert text.startswith("---\ntitle:")
    import re
    h2 = re.findall(r"^## (.+)$", text, re.MULTILINE)
    for head in ("The two legs", "Fusing them", "What the recording shows", "Run it yourself"):
        assert head in h2, head
    assert "/demo/" in text


# --- the built page and the prose around it -------------------------------------
DIST = SITE / "dist"
DEMO = json.loads((SITE / "src/data/demo.json").read_text())


def _vector_ms():
    return [q["ms"]["vector"] for q in DEMO["questions"]]


def test_the_first_query_carries_the_connection_cost_and_says_so():
    """The first vector leg in the recording is several times the rest because it opens
    the connection to the embedding host. Unmarked, the very first row a reader sees is
    a false claim about retrieval cost."""
    ms = _vector_ms()
    rest = sorted(ms[1:])
    median = (rest[len(rest) // 2] + rest[~(len(rest) // 2)]) / 2
    assert ms[0] == max(ms), "the recording no longer leads with the cold query"
    assert ms[0] > 4 * median, "warm-up cost gone; re-check the prose before relaxing this"
    html = (DIST / "demo" / "index.html").read_text()
    first = html.split('class="question"')[1]
    assert "first query in the run" in first, "the first row must be marked"
    assert html.count("first query in the run") == 1, "only the first row carries it"
    page = (SITE / "src/pages/demo.astro").read_text()
    assert "one-off cost of opening the connection" in page


def test_the_essay_does_not_call_the_cold_query_a_retrieval_cost():
    """/blog/semantic-indexing/ is where the "same narrow band" claim lives; it has to
    exclude the first query and name the real numbers."""
    essay = (SITE / "src/content/blog/semantic-indexing.md").read_text()
    assert "every vector query *after the first*" in essay
    ms = _vector_ms()
    rest = sorted(ms[1:])
    median = (rest[len(rest) // 2] + rest[~(len(rest) // 2)]) / 2
    assert f"{int(ms[0])} ms" in essay, f"essay must name the cold query's {int(ms[0])} ms"
    assert f"median of {round(median)}" in essay, f"essay must name the median of {round(median)}"


def test_demo_section_advertises_its_published_twin():
    html = (DIST / "demo" / "index.html").read_text()
    assert '<link rel="alternate" type="text/markdown" href="/demo.md"' in html
    assert (DIST / "demo.md").is_file()


def test_the_home_page_links_the_demo():
    assert 'href="/demo/"' in (DIST / "index.html").read_text()

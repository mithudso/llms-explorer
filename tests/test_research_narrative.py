"""All gated auxiliary prose survives projection without becoming factual units."""
import copy
import html
import importlib.util
import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.setenv("LLMS_EXPLORER_REPO", str(ROOT))
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return {
        "compiler": load("narrative_compiler", "scripts/codex_dr_artifacts.py"),
        "lca": load("narrative_lca", ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py"),
        "artifact": load("narrative_artifact", "scripts/research_artifact.py"),
        "gate": load("narrative_gate", "scripts/research_gate.py"),
        "reader": load("narrative_reader", "site/tools/gen_concepts.py"),
        "downloads": load("narrative_downloads", "site/tools/gen_concept_facts.py"),
        "context": load("narrative_context", "site/tools/gen_context.py"),
    }


def documents(gate, count):
    docs = []
    for index in range(count):
        proposed = index == 0
        text = ("If an operator adopts this original design, retain the warning until acknowledgement.\n"
                "Do not infer delivery from an attempted send.") if proposed else (
                    "The cited specification distinguishes acknowledgement from delivery.\n"
                    "This summary preserves that qualification.")
        doc = {
            "concept": f"Document {index}", "canonical_concept_id": f"concept:document-{index}",
            "summary": text,
            "sources": [{"url": f"https://summary-only.test/{index}"}],
            "claims": [{"text": f"Original supported factual statement {index}.",
                        "confidence": "high", "sources": [f"https://fact-only.test/{index}"],
                        "canonical_claim_id": f"clm:{index}", "validation_status": "SUPPORTED",
                        "evidence_ids": [f"ev:fact-{index}"]}],
        }
        assertion = gate.auxiliary_rows(f"document-{index}", doc)[0]
        assertion.update(validation_status="NO-FACTUAL-ASSERTION" if proposed else "SUPPORTED",
                         evidence_ids=[] if proposed else [f"ev:summary-{index}"])
        doc["auxiliary_assertions"] = [assertion]
        docs.append(doc)
    return docs


def all_auxiliary_documents(gate, count):
    docs = documents(gate, count)
    for index, doc in enumerate(docs):
        doc["sources"] = [{"url": f"https://z-context.test/{index}"},
                          {"url": f"https://a-context.test/{index}"}]
        doc["disagreements"] = [{
            "text": (f"Source A permits editing through interface A for document {index}.\n"
                     "Source B separately describes interface B; this does not establish an unnamed command."),
            "sources": [f"https://z-disagreement.test/{index}", f"https://a-disagreement.test/{index}"],
            "conflict": {"status": "attributed", "positions": [
                {"text": "Interface A retains its product limitation.", "evidence": [{"quote": "private-quote-sentinel-A"}]},
                {"text": "Interface B retains its version qualification.", "evidence": [{"quote": "private-quote-sentinel-B"}]}]},
            "evidence": [{"quote": "private-quote-sentinel-complete"}],
        }]
        doc["open_questions"] = [f"Which versions apply to document {index}?",
                                 f"Given the documented limit of 8 operations, which configuration applies to document {index}?"]
        doc["auxiliary_assertions"] = gate.auxiliary_rows(f"document-{index}", doc)
        for row in doc["auxiliary_assertions"]:
            nonfactual = (row["assertion_kind"] == "summary" and index == 0) or (
                row["assertion_kind"] == "open_question" and row["index"] == 0)
            row.update(validation_status="NO-FACTUAL-ASSERTION" if nonfactual else "SUPPORTED",
                       evidence_ids=[] if nonfactual else [f"ev:{row['assertion_kind']}-{index}-{row['index']}"])
    return docs


@pytest.mark.parametrize("count", [1, 2], ids=["individual", "aggregate"])
def test_all_auxiliary_kinds_survive_complete_exports_with_exact_binding_and_no_fact_credit(tmp_path, modules, count):
    compiler = modules["compiler"]
    docs = all_auxiliary_documents(modules["gate"], count)
    private, baseline = tmp_path / "native.llms", tmp_path / "baseline.llms"
    compiler.compile_claims(modules["lca"], private, "All prose", "all-prose", docs,
                            "COMPLETED", artifact_sha="a" * 64, concept_id="concept:all-prose")
    plain = [{key: value for key, value in doc.items() if key != "auxiliary_assertions"} for doc in docs]
    compiler.compile_claims(modules["lca"], baseline, "All prose", "all-prose", plain,
                            "COMPLETED", artifact_sha="a" * 64, concept_id="concept:all-prose")
    files = {name: (private / name).read_text() for name in compiler.PACK_FILES}
    manifest = json.loads(files["manifest.json"])
    before = json.loads((baseline / "manifest.json").read_text())
    assert "narrative" not in before
    for key in ("sources", "facets", "kept_units"):
        assert manifest[key] == before[key]
    assert manifest["kept_units"] == count
    for name in ("units.jsonl", "llms-facts.txt", "concept-graph.json", "llms-small.txt"):
        assert files[name] == (baseline / name).read_text()
    narrative = manifest["narrative"]
    assertions = [row for doc in docs for row in doc["auxiliary_assertions"]]
    assert len(narrative) == len(assertions) == 4 * count
    for projected, original in zip(narrative, assertions):
        for output, canonical in (("assertionId", "claim_id"), ("statementSha256", "claim_sha256"),
                                  ("assertionKind", "assertion_kind"), ("index", "index"),
                                  ("documentSlug", "concept_slug"), ("text", "text"), ("sources", "sources"),
                                  ("validationStatus", "validation_status"), ("evidenceIds", "evidence_ids")):
            assert projected[output] == original[canonical]
        assert files["llms-full.txt"].count(projected["text"]) == 1
        assert projected["text"] not in files["llms-facts.txt"]
        rendered = modules["downloads"].render_narrative([projected])
        assert [rendered.index(f"](<{url}>)") for url in projected["sources"]] == sorted(
            rendered.index(f"](<{url}>)") for url in projected["sources"])
    public_files = compiler.public_pack_files(ROOT, tmp_path / "hub", files, modules["lca"])
    public = modules["artifact"].public_projection(public_files)
    assert public["narrative"] == narrative and len(public["claims"]) == count
    assert public["projection_sha256"] == modules["artifact"].digest(
        {key: value for key, value in public.items() if key != "projection_sha256"})
    exported = tmp_path / "public.llms"
    exported.mkdir()
    for name, text in public_files.items():
        (exported / name).write_text(text)
    pack = modules["reader"].build_one(exported)
    assert pack["narrative"] == narrative
    assert pack["facets"] == modules["reader"].build_one(baseline)["facets"]
    research = json.loads(modules["downloads"].research_download_texts({"all-prose": pack})["all-prose"])
    assert research["narrative"] == narrative and len(research["claims"]) == count
    markdown = modules["downloads"].render_pack(pack, {}, "https://site.test", tmp_path)
    assert f"{count} facts" in markdown
    for row in narrative:
        assert markdown.count(row["text"]) == public_files["llms-full.txt"].count(row["text"]) == 1
        assert row["assertionId"] in markdown and row["statementSha256"] in markdown
    assert "## Source disagreement" in markdown and "## Open question" in markdown
    assert "Question without a factual assertion; contributes no factual evidence." in markdown
    assert all("private-quote-sentinel" not in text for text in public_files.values())


@pytest.mark.parametrize("failure", ["unknown-kind", "stale-summary", "stale-disagreement", "stale-question",
                                     "wrong-index", "boolean-index", "wrong-hash", "wrong-id", "source-order",
                                     "missing-row", "empty-coverage", "duplicate-row", "missing-evidence",
                                     "nonfactual-evidence", "unverified"])
def test_unknown_stale_duplicate_or_incomplete_auxiliary_bindings_block_compilation(tmp_path, modules, failure):
    doc = all_auxiliary_documents(modules["gate"], 1)[0]
    rows = doc["auxiliary_assertions"]
    if failure == "unknown-kind": rows[1]["assertion_kind"] = "unjudged-note"
    elif failure == "stale-summary": doc["summary"] += " Unjudged addition."
    elif failure == "stale-disagreement": doc["disagreements"][0]["text"] += " Unjudged condition."
    elif failure == "stale-question": doc["open_questions"][1] += " An unjudged premise?"
    elif failure == "wrong-index": rows[1]["index"] = 1
    elif failure == "boolean-index": rows[0]["index"] = False
    elif failure == "wrong-hash": rows[1]["claim_sha256"] = "stale"
    elif failure == "wrong-id": rows[1]["claim_id"] = "prose:stale"
    elif failure == "source-order": rows[1]["sources"].reverse()
    elif failure == "missing-row": rows.pop()
    elif failure == "empty-coverage": doc["auxiliary_assertions"] = []
    elif failure == "duplicate-row": rows.append(copy.deepcopy(rows[1]))
    elif failure == "missing-evidence": rows[1]["evidence_ids"] = []
    elif failure == "nonfactual-evidence": rows[2]["evidence_ids"] = ["ev:unexpected"]
    else: rows[1]["validation_status"] = "UNVERIFIED"
    with pytest.raises(ValueError, match="canonical auxiliary"):
        modules["compiler"].compile_claims(modules["lca"], tmp_path / "invalid.llms", doc["concept"],
                                           "invalid", [doc], "COMPLETED", artifact_sha="a" * 64)


def test_duplicate_auxiliary_identity_across_documents_blocks_compilation(tmp_path, modules):
    doc = all_auxiliary_documents(modules["gate"], 1)[0]
    with pytest.raises(ValueError, match="duplicate canonical auxiliary"):
        modules["compiler"].compile_claims(modules["lca"], tmp_path / "duplicate.llms", doc["concept"],
                                           "duplicate", [doc, copy.deepcopy(doc)], "COMPLETED", artifact_sha="a" * 64)


@pytest.mark.parametrize("count", [1, 2], ids=["individual", "aggregate"])
def test_gated_narrative_survives_native_public_reader_and_downloads_without_fact_credit(
        tmp_path, modules, count):
    compiler, lca = modules["compiler"], modules["lca"]
    docs = documents(modules["gate"], count)
    name = docs[0]["concept"] if count == 1 else "Aggregate"
    private = tmp_path / "private.llms"
    compiler.compile_claims(lca, private, name, "pack", docs, "COMPLETED",
                            artifact_sha="a" * 64, concept_id="concept:pack")
    baseline = tmp_path / "baseline.llms"
    plain = [{key: value for key, value in doc.items() if key != "auxiliary_assertions"} for doc in docs]
    compiler.compile_claims(lca, baseline, name, "pack", plain, "COMPLETED",
                            artifact_sha="a" * 64, concept_id="concept:pack")
    files = {filename: (private / filename).read_text() for filename in compiler.PACK_FILES}
    manifest = json.loads(files["manifest.json"])
    original_manifest = json.loads((baseline / "manifest.json").read_text())
    assert manifest["kept_units"] == count
    for key in ("sources", "facets", "kept_units"):
        assert manifest[key] == original_manifest[key]
    for filename in ("units.jsonl", "llms-facts.txt", "concept-graph.json", "llms-small.txt"):
        assert files[filename] == (baseline / filename).read_text()
    assert manifest["summary"] == original_manifest["summary"]
    assert "summary-only.test" not in json.dumps(manifest["sources"])
    narrative = manifest["narrative"]
    assert len(narrative) == count
    for row, doc in zip(narrative, docs):
        assertion = doc["auxiliary_assertions"][0]
        assert row == {
            "assertionId": assertion["claim_id"], "statementSha256": assertion["claim_sha256"],
            "assertionKind": "summary", "index": 0, "documentSlug": assertion["concept_slug"],
            "documentConcept": doc["concept"], "canonicalConceptId": doc["canonical_concept_id"],
            "text": doc["summary"], "sources": assertion["sources"],
            "validationStatus": assertion["validation_status"], "evidenceIds": assertion["evidence_ids"],
        }
        assert files["llms-full.txt"].count(row["text"]) == 1
        assert row["text"] not in files["llms-facts.txt"]
    assert "## Proposed guidance" in files["llms-full.txt"]
    if count == 2:
        assert "## Research summary" in files["llms-full.txt"]
    # Repository export recompiles the scrubbed manifest and factual units.
    public_files = compiler.public_pack_files(ROOT, tmp_path / "hub", files, lca)
    assert json.loads(public_files["manifest.json"])["narrative"] == narrative
    for row in narrative:
        assert public_files["llms-full.txt"].count(row["text"]) == 1
    public = modules["artifact"].public_projection(public_files)
    assert public["narrative"] == narrative
    assert len(public["claims"]) == count
    assert {row["validation_status"] for row in public["claims"]} == {"SUPPORTED"}
    assert not ({row["assertionId"] for row in narrative} & {row["id"] for row in public["claims"]})
    assert public["projection_sha256"] == modules["artifact"].digest(
        {key: value for key, value in public.items() if key != "projection_sha256"})
    exported = tmp_path / "public.llms"
    exported.mkdir()
    for filename, content in public_files.items():
        (exported / filename).write_text(content)
    pack = modules["reader"].build_one(exported)
    baseline_pack = modules["reader"].build_one(baseline)
    assert pack["narrative"] == narrative
    assert pack["facets"] == baseline_pack["facets"]
    research = json.loads(modules["downloads"].research_download_texts({"pack": pack})["pack"])
    assert research["narrative"] == narrative
    facts = [fact for facet in pack["facets"] for fact in facet["facts"]]
    assert research["claims"] == facts
    markdown = modules["downloads"].render_pack(pack, {}, "https://site.test", tmp_path)
    assert f"{count} facts" in markdown
    for row in narrative:
        assert markdown.count(row["text"]) == 1
        assert row["assertionId"] in markdown
        assert row["statementSha256"] in markdown
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "pack.json").write_text(json.dumps(pack))
    assert modules["context"].load_packs(concepts)["pack"]["facts"] == count
    assert {fact["source"] for fact in facts} == {doc["claims"][0]["sources"][0] for doc in docs}


def test_unqualified_summary_or_proposal_flag_does_not_create_qualified_narrative(tmp_path, modules):
    doc = all_auxiliary_documents(modules["gate"], 1)[0]
    prose = [row["text"] for row in doc["auxiliary_assertions"]]
    doc.pop("auxiliary_assertions")
    doc["proposal"] = True
    out = tmp_path / "legacy.llms"
    modules["compiler"].compile_claims(modules["lca"], out, doc["concept"], "legacy", [doc],
                                       "COMPLETED", artifact_sha="a" * 64)
    assert "narrative" not in json.loads((out / "manifest.json").read_text())
    assert all(text not in (out / "llms-full.txt").read_text() for text in prose)
    assert "narrative" not in modules["reader"].build_one(out)


def test_prose_cannot_sneak_into_fact_facets_and_changed_summary_is_rejected(tmp_path, modules):
    with pytest.raises(ValueError, match="nonfactual"):
        modules["reader"].canonical_facets([{"validation_status": "NO-FACTUAL-ASSERTION"}])
    doc = documents(modules["gate"], 1)[0]
    doc["summary"] += " An unjudged addition."
    with pytest.raises(ValueError, match="canonical auxiliary judgment"):
        modules["compiler"].compile_claims(modules["lca"], tmp_path / "changed", doc["concept"],
                                           "changed", [doc], "COMPLETED", artifact_sha="a" * 64)
    doc = documents(modules["gate"], 1)[0]
    doc["claims"][0]["validation_status"] = "NO-FACTUAL-ASSERTION"
    with pytest.raises(ValueError, match="nonfactual"):
        modules["compiler"].compile_claims(modules["lca"], tmp_path / "claim", doc["concept"],
                                           "claim", [doc], "COMPLETED", artifact_sha="a" * 64)


def test_redacted_narrative_preserves_original_verdict_without_claiming_support(modules):
    row = {"assertionId": "prose:original", "statementSha256": "original-hash",
           "documentConcept": "Design", "text": "Public placeholder.",
           "validationStatus": "REDACTED-PROJECTION", "originValidationStatus": "NO-FACTUAL-ASSERTION",
           "evidenceIds": []}
    text = modules["downloads"].render_narrative([row])
    assert "Proposed guidance (redacted projection)" in text
    assert "Gate verdict: `REDACTED-PROJECTION`" in text
    assert "contributes no factual evidence" in text


@pytest.mark.parametrize("verdict", ["SUPPORTED", "NO-FACTUAL-ASSERTION"])
@pytest.mark.parametrize("changed", ["sources", "text", "home-path"])
def test_public_narrative_scrubbing_preserves_origin_and_never_claims_exact_support(
        tmp_path, modules, verdict, changed):
    doc = documents(modules["gate"], 1)[0]
    private_path = str(Path("/") / "Users" / "private-operator" / "snapshot.md")
    withheld = []
    if changed == "sources":
        withheld = ["summary-only.test"]
    elif changed == "text":
        doc["summary"] += " Internal-design-sentinel."
        withheld = ["Internal-design-sentinel"]
    else:
        doc["summary"] += " Record path: " + private_path
        doc["sources"][0]["url"] += "?path=" + private_path
    assertion = modules["gate"].auxiliary_rows("document-0", doc)[0]
    assertion.update(validation_status=verdict, evidence_ids=["ev:summary"] if verdict == "SUPPORTED" else [])
    doc["auxiliary_assertions"] = [assertion]
    compiler = modules["compiler"]
    out = tmp_path / "native.llms"
    compiler.compile_claims(modules["lca"], out, doc["concept"], "pack", [doc], "COMPLETED",
                            artifact_sha="a" * 64)
    files = {name: (out / name).read_text() for name in compiler.PACK_FILES}
    native = json.loads(files["manifest.json"])["narrative"][0]
    public_files = compiler.public_pack_files(ROOT, tmp_path / "hub", files, modules["lca"], withheld)
    projected = modules["artifact"].public_projection(public_files)["narrative"][0]
    assert native["validationStatus"] == verdict
    assert native["text"] == doc["summary"]
    assert projected["validationStatus"] == "REDACTED-PROJECTION"
    assert projected["originValidationStatus"] == verdict
    for key in ("assertionId", "statementSha256", "evidenceIds"):
        assert projected[key] == native[key]
    if changed == "sources":
        assert projected["text"] == native["text"]
        assert projected["sources"] != native["sources"]
    else:
        assert projected["text"] != native["text"]
    for secret in withheld + ([private_path] if changed == "home-path" else []):
        assert all(secret not in content for content in public_files.values())
    assert public_files["llms-full.txt"].count(projected["text"]) == 1
    assert "REDACTED-PROJECTION" in public_files["llms-full.txt"]


def test_all_auxiliary_kinds_preserve_redaction_origin_and_exact_identity(tmp_path, modules):
    doc = all_auxiliary_documents(modules["gate"], 1)[0]
    out = tmp_path / "native.llms"
    compiler = modules["compiler"]
    compiler.compile_claims(modules["lca"], out, doc["concept"], "redacted", [doc], "COMPLETED",
                            artifact_sha="a" * 64)
    files = {name: (out / name).read_text() for name in compiler.PACK_FILES}
    native = json.loads(files["manifest.json"])["narrative"]
    public_files = compiler.public_pack_files(ROOT, tmp_path / "hub", files, modules["lca"],
                                              ["context.test", "disagreement.test"])
    projected = modules["artifact"].public_projection(public_files)["narrative"]
    assert len(projected) == len(native) == 4
    for before, after in zip(native, projected):
        assert after["validationStatus"] == "REDACTED-PROJECTION"
        assert after["originValidationStatus"] == before["validationStatus"]
        for key in ("assertionId", "statementSha256", "assertionKind", "index", "text", "evidenceIds"):
            assert after[key] == before[key]
    assert all("context.test" not in text and "disagreement.test" not in text for text in public_files.values())
    assert "Open question (redacted projection)" in public_files["llms-full.txt"]
    assert "Source disagreement (redacted projection)" in public_files["llms-full.txt"]


def render_actual_narrative(tmp_path, rows):
    node_modules = next((path for path in (
        ROOT / "site/node_modules", Path.home() / "dev/llms-explorer/site/node_modules")
        if (path / "astro").is_dir()), None)
    if node_modules is None or shutil.which("node") is None:
        pytest.skip("installed Astro and node are required for reader rendering")
    page = (ROOT / "site/src/pages/tree/[slug].astro").read_text()
    # Compile the actual narrative block independently; no generated site data,
    # server, or full-site build is needed to exercise the shipped markup.
    block = page.split("      {(pack.narrative ?? [])", 1)[1].split("      {pack.facets.map", 1)[0]
    template = "---\nconst { pack } = Astro.props;\n---\n{(pack.narrative ?? [])" + block
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"template": template, "pack": {"narrative": rows}}))
    script = r"""
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const deps = process.argv[1];
const fixture = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const require = createRequire(deps + '/astro/package.json');
const { transform } = await import(pathToFileURL(require.resolve('@astrojs/compiler-rs')));
const { experimental_AstroContainer } = await import(pathToFileURL(deps + '/astro/dist/container/index.js'));
const compiled = await transform(fixture.template, {
  filename: 'Narrative.astro',
  internalURL: pathToFileURL(require.resolve('astro/compiler-runtime')).href,
  resolvePath: (specifier) => specifier,
});
const { default: component } = await import('data:text/javascript,' + encodeURIComponent(compiled.code));
const container = await experimental_AstroContainer.create();
process.stdout.write(await container.renderToString(component, { props: { pack: fixture.pack } }));
"""
    result = subprocess.run(["node", "--input-type=module", "-e", script, str(node_modules), str(fixture)],
                            capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_actual_reader_narrative_markup_renders_exact_escaped_text_and_gate_provenance(tmp_path, modules):
    doc = documents(modules["gate"], 1)[0]
    assertion = doc["auxiliary_assertions"][0]
    row = {"assertionId": assertion["claim_id"], "statementSha256": assertion["claim_sha256"],
           "documentConcept": "Design", "text": doc["summary"] + '\n<script>alert("x")</script>',
           "validationStatus": "NO-FACTUAL-ASSERTION", "evidenceIds": []}
    rendered = render_actual_narrative(tmp_path, [row])
    assert "Proposed guidance — Design" in rendered
    assert row["text"] in html.unescape(rendered)
    assert rendered.count('class="pack-narrative"') == 1
    assert row["assertionId"] in rendered
    assert row["statementSha256"] in rendered
    assert "NO-FACTUAL-ASSERTION" in rendered
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered


class NarrativeSections(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = {}
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and attrs.get("class") == "pack-narrative":
            self.current = {"links": [], "text": []}
            self.sections[attrs["data-assertion-id"]] = self.current
        elif self.current is not None and tag == "a":
            self.current["links"].append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "section":
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"].append(data)


def test_actual_reader_renders_each_kind_qualifies_questions_and_keeps_safe_source_order(tmp_path, modules):
    rows = modules["compiler"].canonical_narrative(all_auxiliary_documents(modules["gate"], 1)[0])
    safe = ["https://z-source.test/path(with-parens)?a=1&b=2", "https://a-source.test/reference"]
    unsafe = ["javascript:alert(1)", "data:text/html,<script>x</script>", "/Users/private-reader/secret.md",
              "https://user:password@private.test/", "https://llmsx.org/sources/old/report/",
              "https://source.test/path\ninjected", "https://source.test:bad/path", 'https://source.test/"bad']
    rows[1]["sources"] = [safe[0], *unsafe, safe[1]]
    rows[0]["text"] += '\n<script>alert("x")</script>'
    redacted = {**rows[2], "assertionId": "prose:redacted-question", "text": "Public question?",
                "validationStatus": "REDACTED-PROJECTION", "originValidationStatus": "NO-FACTUAL-ASSERTION"}
    rendered = render_actual_narrative(tmp_path, [*rows, redacted])
    parser = NarrativeSections()
    parser.feed(rendered)
    assert len(parser.sections) == 5
    for row in [*rows, redacted]:
        text = " ".join(parser.sections[row["assertionId"]]["text"])
        assert row["text"] in html.unescape(rendered)
        assert row["assertionId"] in text and row["statementSha256"] in text
        assert row["validationStatus"] in text
        assert all(identity in text for identity in row["evidenceIds"])
    assert parser.sections[rows[1]["assertionId"]]["links"] == safe
    assert "Source disagreement" in " ".join(parser.sections[rows[1]["assertionId"]]["text"])
    for row in (rows[2], redacted):
        text = " ".join(parser.sections[row["assertionId"]]["text"])
        assert "Open question" in text and "Question without a factual assertion" in text
        assert "conditional design" not in text and "Proposed guidance" not in text
    premise = " ".join(parser.sections[rows[3]["assertionId"]]["text"])
    assert "Open question" in premise and "Question without a factual assertion" not in premise
    markdown = modules["downloads"].render_narrative([rows[1]])
    assert markdown.index(f"](<{safe[0]}>)") < markdown.index(f"](<{safe[1]}>)")
    assert all(url not in rendered and url not in markdown for url in unsafe)
    assert "&lt;script&gt;" in rendered and '<script>alert("x")</script>' not in rendered

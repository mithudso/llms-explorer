"""Gated auxiliary summaries survive projection without becoming factual units."""
import html
import importlib.util
import json
import shutil
import subprocess
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
    doc = documents(modules["gate"], 1)[0]
    doc.pop("auxiliary_assertions")
    doc["proposal"] = True
    out = tmp_path / "legacy.llms"
    modules["compiler"].compile_claims(modules["lca"], out, doc["concept"], "legacy", [doc],
                                       "COMPLETED", artifact_sha="a" * 64)
    assert "narrative" not in json.loads((out / "manifest.json").read_text())
    assert doc["summary"] not in (out / "llms-full.txt").read_text()
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


def test_actual_reader_narrative_markup_renders_exact_escaped_text_and_gate_provenance(tmp_path, modules):
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
    doc = documents(modules["gate"], 1)[0]
    assertion = doc["auxiliary_assertions"][0]
    row = {"assertionId": assertion["claim_id"], "statementSha256": assertion["claim_sha256"],
           "documentConcept": "Design", "text": doc["summary"] + '\n<script>alert("x")</script>',
           "validationStatus": "NO-FACTUAL-ASSERTION", "evidenceIds": []}
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"template": template, "pack": {"narrative": [row]}}))
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
    rendered = result.stdout
    assert "Proposed guidance — Design" in rendered
    assert row["text"] in html.unescape(rendered)
    assert rendered.count('class="pack-narrative"') == 1
    assert row["assertionId"] in rendered
    assert row["statementSha256"] in rendered
    assert "NO-FACTUAL-ASSERTION" in rendered
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered

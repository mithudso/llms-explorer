#!/usr/bin/env python3
"""Finalize reviewed research and merge only its nine nodes into both trees."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HUB = Path.home() / ".global-ai-hub"
RUN = HUB / "research/litellm-gateway-sdk-engineering"
sys.path.insert(0, str(HUB / "scripts"))


def main() -> None:
    import concept_tree
    import dr_run

    records = json.loads((RUN / "materialized-skills.json").read_text())
    slugs = [RUN.name] + [r["slug"] for r in records]
    assert all(v["verdict"] == "SUPPORTED" for v in json.loads((RUN / "gate.json").read_text())["verdicts"])
    assert json.loads((RUN / "gate-delta-final.json").read_text())["counts"]["SUPPORTED"] == 4
    assert json.loads((RUN / "pack-answer-gate-final.json").read_text())["status"] == "pass"
    assert json.loads((RUN / "hub-meta-final.json").read_text())["summary"] == {"High": 0, "Medium": 0, "Low": 0}
    plan = json.loads((REPO / "docs/research/litellm-full-suite-2026-09-30/plan.json").read_text())
    frontier = [r["concept"] for r in plan["rows"] if r["cvs"] >= plan["threshold"] and r["concept"] not in plan["selected"]]
    backup = RUN / "snapshots/tree-registration"
    backup.mkdir(parents=True, exist_ok=True)
    repo_tree = REPO / "concept-tree/tree.json"
    for path, name in [(concept_tree.TREE_PATH, "global-tree.json"), (repo_tree, "repo-tree.json"),
                       (REPO / "site/src/data/tree.json", "site-tree.json")]:
        if not (backup / name).exists():
            shutil.copy2(path, backup / name)
    # LiteLLM is a product beneath the existing general gateway concept. It is
    # not an alias for all gateway infrastructure, and must not consume that edge.
    with dr_run.run_lock(RUN.name):
        m = dr_run.load_manifest(RUN.name)
        m["parent_concept"] = "AI Gateways & LLM Proxy Infrastructure"
        m["aliases"] = []
        m["gate"] = {"status": "sample-supported", "path": str(RUN / "gate.json"),
                     "delta_path": str(RUN / "gate-delta-final.json"), "sampled": 16, "delta_sampled": 4,
                     "runner": "independent Codex fallback", "runtime_qualification": False}
        dr_run.save_manifest(m)
    results = []
    for slug in slugs:
        m = dr_run.load_manifest(slug)
        if m.get("exit_status"):
            continue
        args = [sys.executable, str(HUB / "scripts/dr_run.py"), "finish", slug,
                "--status", "BUDGET_EXHAUSTED" if slug == RUN.name else "COMPLETED",
                "--stop-reason", "Eight-concept family cap; five above-threshold frontier concepts remain; CFE 9/9b owed" if slug == RUN.name
                else "Materialized from parent standard research; zero additional queries; inherits sampled parent gate",
                "--agents", "3" if slug == RUN.name else "0", "--rounds", "1", "--report", str(RUN / "report.md")]
        if slug != RUN.name:
            args += ["--minutes", "0"]
        r = subprocess.run(args, capture_output=True, text=True, check=True)
        result = json.loads(r.stdout)
        assert result.get("tree") and not result["tree"].get("error"), result
        results.append(result)
    # The official finish writer owns creation/counts. Add only file pointers,
    # qualification and the five unresearched names from the capped plan.
    with dr_run.locked(HUB / "research/.global.lock"):
        nodes = concept_tree.load_nodes()
        owned = [n for n in nodes if n.get("slug") in slugs]
        assert len(owned) == 9
        for n in owned:
            n["llmsFile"] = str(HUB / "llms-concepts" / ("litellm-family.llms" if n["slug"] == RUN.name else n["slug"] + ".llms") / "llms.txt")
            n["researchStatus"] = "BUDGET_EXHAUSTED" if n["slug"] == RUN.name else "COMPLETED"
            n["runtimeQualified"] = False
            if n["slug"] == RUN.name:
                n["publishedDocsFile"] = str(HUB / "skills.llms/docs-litellm-ai/llms.txt")
                n["childConcepts"] = sorted(set(n["childConcepts"]) | set(frontier))
        concept_tree.save_nodes(nodes)
    before = json.loads(repo_tree.read_text())
    merged = json.loads(repo_tree.read_text())
    by_slug = {n["slug"]: n for n in merged}
    for n in owned:
        if n["slug"] in by_slug:
            by_slug[n["slug"]].update(n)
        else:
            merged.append(n)
    broad = next(n for n in merged if n["concept"] == "AI Gateways & LLM Proxy Infrastructure")
    broad["childConcepts"] = list(dict.fromkeys(broad["childConcepts"] + ["LiteLLM gateway and SDK engineering"]))
    assert {n["slug"] for n in before} <= {n["slug"] for n in merged}
    modified_existing = [n["slug"] for n in before if n != next(x for x in merged if x["slug"] == n["slug"])]
    assert set(modified_existing) <= set(slugs) | {broad["slug"]}
    concept_tree.save_nodes(merged, repo_tree)
    summary_path = REPO / "concept-tree/skill-summaries.json"
    summaries = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    for n in owned:
        summaries[n["skillId"]] = n["concept"] + ": source-qualified SDK/gateway guidance; source confidence and deployment limits retained."
    summary_path.write_text(json.dumps(summaries, indent=2) + "\n")
    # Vendor only authored, source-qualified claim summaries/facets for the site's
    # eight pack pages. Never copy the downloaded third-party full corpus.
    spec = importlib.util.spec_from_file_location("gen_concepts", REPO / "site/tools/gen_concepts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    site_paths = []
    for r in records:
        data = module.build_one(HUB / "llms-concepts" / (r["slug"] + ".llms"))
        assert data and sum(len(f["facts"]) for f in data["facets"]) == r["claims"]
        data["evidenceQualification"] = {
            "confidence": json.loads((HUB / "llms-concepts" / (r["slug"] + ".llms/manifest.json")).read_text())["confidence"],
            "runtimeQualified": False, "verifiedAsOf": "2026-09-30",
            "scope": "Documentation and pinned-code research; native provider sources do not certify the gateway implementation."}
        path = REPO / "site/src/data/concepts" / (r["slug"] + ".json")
        path.parent.mkdir(exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        assert "/Users/" not in text and "file://" not in text
        path.write_text(text)
        site_paths.append(str(path.relative_to(REPO)))
    subprocess.run([sys.executable, str(REPO / "site/tools/gen_tree.py"), "--out", str(REPO / "site/src/data/tree.json")], check=True)
    report = {"version": "1.0.1", "registered_slugs": slugs, "frontier_remaining": frontier,
              "repo_before": len(before), "repo_after": len(merged), "repo_modified_existing": modified_existing,
              "global_before": len(json.loads((backup / "global-tree.json").read_text())), "global_after": len(nodes),
              "preserved_existing_nodes": True, "site_pack_files": site_paths, "finish_results": results,
              "source_corpus_vendored": False, "runtime_qualified": False}
    (RUN / "tree-registration.json").write_text(json.dumps(report, indent=2) + "\n")
    print("registered nine nodes in both trees; eight authored pack views vendored")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build this run's scoped FTS/vector indexes and native categorical family index."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HUB = Path.home() / ".global-ai-hub"
RUN = HUB / "research/litellm-gateway-sdk-engineering"
sys.path.insert(0, str(HUB / "scripts"))


def main() -> None:
    from docset_refine import export_llms
    from semantic_ops import router

    records = json.loads((RUN / "materialized-skills.json").read_text())
    env = dict(os.environ, HUB_DOCSET_BACKEND="sqlite", HUB_OLLAMA_URLS="http://localhost:11434=1",
               PYTHONPATH=str(HUB / "scripts"))
    reports = []
    query_dir = RUN / "query-inputs"
    query_dir.mkdir(exist_ok=True)
    # The indexer retains text/type/origin, but not confidence fields. Make the
    # qualification visible in retrieval hits without altering canonical units.
    def query_view(path: Path, slug: str, historical: bool = False) -> Path:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
        for u in rows:
            if historical:
                note = "historical published bundle; partial 50/52 indexed pages; code examples unexecuted; consult the operator reference's adjacent setup gotchas"
            else:
                note = f"evidence confidence: {u['confidence']}; verified-as-of: {u.get('verified_as_of', '2026-09-30')}; documentation/code research, no runtime qualification"
            u["text"] += " [" + note + "]"
        out = query_dir / (slug + ".jsonl")
        out.write_text("".join(json.dumps(u) + "\n" for u in rows))
        return out

    reindex = "--rollup-only" not in sys.argv
    for r in (records if reindex else []):
        slug = r["slug"]
        pack = HUB / "llms-concepts" / f"{slug}.llms"
        name = "concept__" + slug
        view = query_view(pack / "units.jsonl", slug)
        for args in [("index", str(view), "--units", "--name", name),
                     ("keyword-index", name + "__facts")]:
            result = subprocess.run([sys.executable, str(HUB / "scripts/docset_indexer.py"), *args],
                                    capture_output=True, text=True, env=env, check=True)
            report = {"slug": slug, "args": list(args), "stdout": result.stdout, "stderr": result.stderr}
            reports.append(report)
        print("indexed " + slug, flush=True)
    operator = query_view(HUB / "skills.llms/docs-litellm-ai/working-sheet.jsonl", "litellm_operator_reference", historical=True) if reindex else None
    operator_commands = [("index", str(operator), "--units", "--name", "litellm_operator_reference"),
                         ("keyword-index", "litellm_operator_reference__facts")] if reindex else []
    for args in operator_commands:
        result = subprocess.run([sys.executable, str(HUB / "scripts/docset_indexer.py"), *args],
                                capture_output=True, text=True, env=env, check=True)
        reports.append({"slug": "litellm_operator_reference", "args": list(args), "stdout": result.stdout, "stderr": result.stderr})
    if reports:
        (RUN / "concept-indexes.json").write_text(json.dumps(reports, indent=2) + "\n")

    # Translate LCA manifest field names in memory. Use the installed family
    # writer and real pack paths; never rewrite concept manifests as docsets.
    original = export_llms.mirror_io.load_json

    def adapted(path, default=None):
        value = original(path, default=default)
        if value and value.get("kind") == "concept":
            value = dict(value, title=value["concept"],
                         pages=value["source_counts"]["claim_citation_urls"],
                         units=value["kept_units"])
        return value

    export_llms.mirror_io.load_json = adapted
    family = HUB / "llms-concepts/litellm-family.llms"
    family.mkdir(exist_ok=True)
    result = export_llms.family(
        [HUB / "llms-concepts" / (r["slug"] + ".md") for r in records],
        "LiteLLM operator concept family",
        "Eight source-qualified LiteLLM operational concepts, capped at eight and not saturated. "
        "Page counts mean cited URL documents, not complete site coverage. "
        "Internal local index; deployment behavior remains unqualified.", family / "llms.txt")
    assert result["products"] == 8
    family_text = (family / "llms.txt").read_text()
    family_text = family_text.replace("Each product below has its own llms.txt (the authoritative map of that product); "
        "this file links indexes, not pages, so a reader is at most two hops from any page.",
        "This file links the eight pack indexes and their facts layers; original source documents remain linked inside each pack.")
    family_text = family_text.replace("## Products", "<!-- internal -->\n<!-- generated: 2026-09-30; generator: docset_refine.family; rights: private derived navigation -->\n\n## Products", 1)
    lines = []
    notes = ["completion, drop_params and exception contracts",
             "model_list, credentials, health checks and stateful deployment",
             "tool_call_id, partial arguments and SSE event handling",
             "Messages translation, tool_result IDs and Chat routing",
             "num_retries, model-group fallbacks and cooldown policies",
             "budget_duration, virtual key bounds and fail-closed policy",
             "cache isolation, telemetry flags and content capture",
             "ollama_chat, Chat routes, vLLM tools and backend limits"]
    product = 0
    for line in family_text.splitlines():
        if line.startswith("- ["):
            if " facts]" in line:
                line += ", source-qualified claims with original confidence and source citations"
            else:
                line += ", " + notes[product]
                product += 1
        lines.append(line)
    (family / "llms.txt").write_text("\n".join(lines) + "\n")
    result["tokens"] = export_llms._tokens((family / "llms.txt").read_text())
    (family / "manifest.json").write_text(json.dumps({"version": "1.0.1", "kind": "family",
        "generated": "2026-09-30", "generator": "docset_refine.export_llms.family",
        "members": [r["slug"] for r in records], "result": result,
        "scope": "8 concept packs; source-page counts are URL counts; no extra research",
        "index_policy": "member fact layers indexed; navigation-only family needs no duplicate embedding layer"}, indent=2) + "\n")

    # build_registry is incremental. Restrict the new rows to this hub card and
    # the nine new spokes, so unrelated skills, agents and tools stay untouched.
    wanted = {"ai-llm-model-layer", "ai-llm-model-layer/litellm-gateway-sdk-engineering"}
    wanted.update("ai-llm-model-layer/" + r["slug"] for r in records)
    collect = router.collect_all
    router.collect_all = lambda: [r for r in collect() if r["name"] in wanted]
    os.environ["HUB_OLLAMA_URLS"] = env["HUB_OLLAMA_URLS"]
    count = router.build_registry()
    route_checks = []
    for r in records:
        hits = router.route(r["concept"], kinds=("spoke", "skill"), top_k=5)
        expected = "spoke:ai-llm-model-layer/" + r["slug"]
        refs = [h.ref for h in hits]
        assert expected in refs, (r["slug"], refs)
        route_checks.append({"question": r["concept"], "expected": expected,
                             "rank": refs.index(expected) + 1, "results": refs})
    (RUN / "registry-routing.json").write_text(json.dumps({"new_entries": count,
        "scoped_names": sorted(wanted), "route_checks": route_checks}, indent=2) + "\n")
    print("family index: 8 members; registry routes verified", flush=True)


if __name__ == "__main__":
    main()

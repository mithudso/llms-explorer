#!/usr/bin/env python3
"""Materialize focused spokes from the reviewed parent research; no new research calls.

The parent run owns retrieval and its standard-depth authority contract. Child run
records identify their provenance and use dr_run.py for render/install/tree writes.
"""
import json
import subprocess
import sys
from pathlib import Path


def materialize(parent: Path) -> list[dict]:
    script = Path.home() / ".global-ai-hub/scripts/dr_run.py"
    hub = Path.home() / ".claude/skills/ai-llm-model-layer"
    manifest = json.loads((parent / "manifest.json").read_text())
    records = []

    def call(*args: str) -> dict:
        result = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr + result.stdout)
        return json.loads(result.stdout)

    for concept in manifest["concepts"]:
        if concept["status"] != "done":
            continue
        slug, name = concept["slug"], concept["name"]
        result = call("init", name, "--slug", slug, "--depth", "quick", "--hub", "ai-llm-model-layer",
                      "--parent", manifest["topic"], "--concepts", name)
        child = Path(result["paths"]["dir"])
        claims = json.loads((parent / "claims" / f"{slug}.json").read_text())
        claims["telemetry"] = {"queries": 0, "negation_queries": 0, "sources_deep_read": 0,
                               "reused_from": str(parent / "claims" / f"{slug}.json")}
        input_path = child / "parent-claims.json"
        input_path.write_text(json.dumps(claims, indent=2) + "\n")
        call("concept-done", slug, str(input_path))
        installed = hub / "references" / f"{slug}.md"
        description = (
            f"Apply and troubleshoot {name} using source-qualified contracts and documented limitations. "
            f"TRIGGER: {name}; configure or debug this LiteLLM capability. "
            "SKIP: other LiteLLM capabilities -> ai-llm-model-layer "
            "(references/litellm-gateway-sdk-engineering.md); agent workflow design -> ai-agents-orchestration."
        )
        call("render", slug, "--kind", "spoke", "--hub", "ai-llm-model-layer", "--out", str(installed),
             "--title", name, "--description", description, "--version", "1.0.1",
             "--keywords", "litellm,gateway,proxy,sdk,configuration,provider,compatibility,troubleshooting," + name,
             "--tags", "llm,litellm,gateway,reference", "--when", name + "|configure this LiteLLM feature")
        provenance = {"role": "materialized member of parent standard-depth research",
                      "parent_run": str(parent), "claims_source": str(parent / "claims" / f"{slug}.json"),
                      "additional_research_queries": 0,
                      "gate": "inherits the parent sampled claim gate; not an independent full gate"}
        (child / "materialization.json").write_text(json.dumps(provenance, indent=2) + "\n")
        records.append({"concept": name, "slug": slug, "run_dir": str(child),
                        "installed": str(installed), "claims": len(claims["claims"]),
                        "sources": len(claims["sources"]), "role": provenance["role"]})
    (parent / "materialized-skills.json").write_text(json.dumps(records, indent=2) + "\n")
    return records


if __name__ == "__main__":
    print(json.dumps(materialize(Path(sys.argv[1])), indent=2))

#!/usr/bin/env python3
"""Verify the saved LiteLLM family, canonical skills, and both concept trees.

Version 1.0.0. Read-only; no retrieval, model calls, or tree mutations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

VERSION = "1.0.0"
ROOT = Path("/Users/mitch")
SLUGS = [
    "litellm-gateway-sdk-engineering",
    "litellm-sdk-provider-normalization",
    "litellm-proxy-deployment-and-configuration",
    "litellm-tool-calls-and-sse-streaming",
    "litellm-anthropic-messages-interoperability",
    "litellm-routing-retries-and-fallbacks",
    "litellm-virtual-keys-budgets-and-rate-limits",
    "litellm-observability-and-caching",
    "litellm-local-ollama-and-openai-compatible-backends",
]
LOCAL_SKILLS = [
    "local-model-performance-evaluation",
    "local-inference-acceleration-and-kernels",
    "inference-microarchitectures-and-kernel-pipelines",
    "vram-residency-budgeting",
    "rtx5080-egpu-harness",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT / "dev/llms-explorer")
    parser.add_argument("--hub", type=Path, default=ROOT / ".global-ai-hub")
    parser.add_argument("--skills", type=Path, default=ROOT / "dev/skills")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    source = ROOT / ".claude/skills/ai-llm-model-layer"
    canonical = args.skills / "ai-llm-model-layer"
    assert digest(source / "SKILL.md") == digest(canonical / "SKILL.md")
    card = (canonical / "SKILL.md").read_text()
    refs = {}
    for slug in SLUGS:
        relative = f"references/{slug}.md"
        path = canonical / relative
        text = path.read_text()
        assert f"`{relative}`" in card, f"Unrouted skill: {slug}"
        assert digest(path) == digest(source / relative)
        assert digest(path) == digest(
            ROOT / ".agents/skills/ai-llm-model-layer" / relative
        )
        used = set(re.findall(r"\[\^([^\]]+)\](?!:)", text))
        defined = set(re.findall(r"^\[\^([^\]]+)\]:", text, re.MULTILINE))
        assert used <= defined, f"Unresolved citations: {slug}"
        version = (
            "1.0.2"
            if slug == "litellm-local-ollama-and-openai-compatible-backends"
            else "1.0.1"
        )
        assert f'version: "{version}"' in text
        refs[slug] = {
            "path": str(path),
            "sha256": digest(path),
            "citations": len(defined),
        }
    table = card.split("## Sub-skill routing table", 1)[1].split(
        "When two rows overlap", 1
    )[0]
    routed = set(re.findall(r"`(references/[^`]+\.(?:md|txt))`", table))
    assert all((canonical / p).is_file() for p in routed), "Missing hub dependency"
    for skill in LOCAL_SKILLS:
        assert (args.skills / skill / "SKILL.md").is_file(), skill
    trees = []
    for root in (args.repo, args.hub):
        path = root / "concept-tree/tree.json"
        nodes = json.loads(path.read_text())
        by_slug = {n["slug"]: n for n in nodes}
        assert len(by_slug) == len(nodes), "Duplicate tree slugs"
        by_name = {n["concept"]: n for n in nodes}
        selected = {}
        for slug in SLUGS:
            node = by_slug[slug]
            assert node["skillId"] == f"ai-llm-model-layer/references/{slug}.md"
            parent = by_name[node["parentConcept"]]
            assert node["concept"] in parent["childConcepts"], (
                f"Missing parent edge: {slug}"
            )
            assert Path(node["llmsFile"]).is_file()
            assert node["runtimeQualified"] is False
            selected[slug] = node
        for skill in LOCAL_SKILLS[:-1]:
            assert any(n.get("skillId") == skill for n in nodes), skill
        parent = selected[SLUGS[0]]
        assert parent["researchStatus"] == "BUDGET_EXHAUSTED"
        assert Path(parent["publishedDocsFile"]).is_file()
        trees.append(
            {
                "path": str(path),
                "nodes": len(nodes),
                "sha256": digest(path),
                "selected": selected,
            }
        )
    assert trees[0]["selected"] == trees[1]["selected"], "LiteLLM trees disagree"
    # Check the full delivered documentation dependency closure, including
    # metadata linked from the index, without fetching third-party URLs.
    files = sorted((args.hub / "llms-concepts").glob("litellm*.llms/*"))
    files += sorted((args.hub / "skills.llms/docs-litellm-ai").glob("*"))
    link_count = 0
    for path in files:
        if not path.is_file() or path.suffix not in (".txt", ".md"):
            continue
        for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", path.read_text()):
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            target_path = Path(unquote(url.path))
            if not target_path.is_absolute():
                target_path = path.parent / target_path
            elif target_path.is_relative_to(ROOT / ".global-ai-hub"):
                target_path = args.hub / target_path.relative_to(
                    ROOT / ".global-ai-hub"
                )
            assert target_path.is_file(), f"Broken local reference: {path} -> {target}"
            link_count += 1
    # Saved claims are the original research scope, not a fresh truth gate.
    run = ROOT / ".global-ai-hub/research/litellm-gateway-sdk-engineering"
    claims = 0
    for slug in SLUGS[1:]:
        data = json.loads((run / "claims" / f"{slug}.json").read_text())
        text = (canonical / "references" / f"{slug}.md").read_text()
        for claim in data["claims"]:
            assert claim["text"] in text, f"Dropped claim: {slug}"
            claims += 1
    assert claims == 95
    report = {
        "version": VERSION,
        "status": "pass",
        "verified_as_of": "2026-09-30",
        "delta": {
            "canonical_hub_before": "1.1.0",
            "canonical_hub_after": "1.1.1",
            "references_added": 9,
            "local_backend_reference": "1.0.1 -> 1.0.2; retained the already reviewed optional template argument",
        },
        "trees": trees,
        "references": refs,
        "retained_claims": claims,
        "local_document_links": link_count,
        "hub_dependencies": len(routed),
        "preexisting_local_skills": [
            str(args.skills / s / "SKILL.md") for s in LOCAL_SKILLS
        ],
        "runtime_qualified": False,
        "fresh_truth_gate": False,
        "scope": "Structural publication and exact retention of previously reviewed research.",
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "pass",
                "references": 9,
                "claims": claims,
                "local_links": link_count,
                "hub_dependencies": len(routed),
                "tree_nodes": [t["nodes"] for t in trees],
            }
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Wire this run's nine references, with backups and a focused Codex mirror."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def main() -> None:
    home = Path.home()
    run = home / ".global-ai-hub/research/litellm-gateway-sdk-engineering"
    source = home / ".claude/skills/ai-llm-model-layer"
    target = home / ".agents/skills/ai-llm-model-layer"
    manifest = home / ".claude/skill-consolidation/ai-agent-manifest.json"
    backup = run / "snapshots/skill-routing"
    backup.mkdir(parents=True, exist_ok=True)
    for path, name in [(source / "SKILL.md", "claude-SKILL.md"),
                       (target / "SKILL.md", "codex-SKILL.md"), (manifest, "ai-agent-manifest.json")]:
        if not (backup / name).exists():
            shutil.copy2(path, backup / name)
    records = [{"slug": "litellm-gateway-sdk-engineering",
                "concept": "LiteLLM gateway and SDK engineering",
                "installed": str(source / "references/litellm-gateway-sdk-engineering.md")},
               *json.loads((run / "materialized-skills.json").read_text())]
    text = (source / "SKILL.md").read_text()
    description = ("LLM model-layer hub. TRIGGER: training, alignment, architecture, compression, "
                   "kernels, serving, reasoning, routing, observability, LiteLLM gateways. "
                   "SKIP: agent orchestration, RAG, MCP servers, prose editing; use the cross-hub map.")
    text = re.sub(r'description:.*?\norigin:', 'description: ' + json.dumps(description) + '\norigin:', text, count=1, flags=re.S)
    text = text.replace("version: 1.1.0", "version: 1.1.1").replace("updated: '2026-09-29'", "updated: '2026-09-30'")
    keywords = ["pretraining scaling laws", "distributed training", "fine-tuning PEFT LoRA", "SFT RLHF PPO DPO",
                "RLHF infrastructure", "agentic RL", "GGUF AWQ GPTQ INT4 FP8 quantization distillation pruning",
                "PagedAttention batching KV cache speculative decoding TTFT TPOT", "transformer multimodal architecture",
                "reasoning models thinking time local code-gen", "model landscape selection routing cascades",
                "LLM lexical convergence mode collapse typicality diverse decoding", "neural architecture search DARTS ENAS supernets zero-cost proxies hardware-aware",
                "session-instinct continuous learning", "LiteLLM"] + [r["concept"] for r in records]
    if "keywords:\n" not in text.split("---", 2)[1]:
        text = text.replace("related_skills:\n", "keywords:\n" + "".join("- " + json.dumps(k) + "\n" for k in keywords) + "related_skills:\n", 1)
    for r in records:
        ref = Path(r["installed"])
        assert ref.is_file(), ref
        # The narrow description stays in each folded reference's provenance card.
        routing = r["concept"] + "; cited operator guidance and version-specific limitations."
        row = f"| `{r['slug']}` | {routing} | `references/{r['slug']}.md` |\n"
        if row not in text:
            text = text.replace("\nWhen two rows overlap", "\n" + row + "\nWhen two rows overlap", 1)
    (source / "SKILL.md").write_text(text)
    # Refresh the stale migrated hub from the canonical hub. Keep its migration
    # resource-directory notice and backups of both previous versions.
    original_codex = (backup / "codex-SKILL.md").read_text()
    notice = next((line for line in original_codex.splitlines() if line.startswith("Resource directory:")), "")
    mirrored = text
    if notice:
        marker = "# ai-llm-model-layer"
        mirrored = mirrored.replace(marker, notice + "\n\n" + marker, 1)
    (target / "SKILL.md").write_text(mirrored)
    m = json.loads(manifest.read_text())
    spokes = m["hubs"]["ai-llm-model-layer"]["spokes"]
    for r in records:
        ref = Path(r["installed"])
        entry = {"spoke": r["slug"], "referenceFile": f"references/{r['slug']}.md",
                 "routingLine": r["concept"], "srcBytes": ref.stat().st_size}
        existing = next((e for e in spokes if e["spoke"] == r["slug"]), None)
        if existing:
            existing.update(entry)
        else:
            spokes.append(entry)
        (target / "references").mkdir(exist_ok=True)
        shutil.copy2(ref, target / "references" / ref.name)
    m["litellmDelta"] = {"version": "1.0.0", "updated": "2026-09-30", "spokesAdded": len(records)}
    manifest.write_text(json.dumps(m, indent=2) + "\n")
    (run / "skill-routing.json").write_text(json.dumps({"version": "1.0.0", "hub_version": "1.1.1",
        "hub": str(source / "SKILL.md"), "mirror": str(target / "SKILL.md"),
        "backup": str(backup), "references": records}, indent=2) + "\n")
    print(f"wired {len(records)} references; hub v1.1.1; focused Codex mirror refreshed")


if __name__ == "__main__":
    main()

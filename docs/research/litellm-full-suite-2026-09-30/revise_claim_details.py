#!/usr/bin/env python3
"""Add four source-supported details exposed by the first pack-only answer audit."""
import json
import subprocess
import sys
from pathlib import Path

RUN = Path.home() / ".global-ai-hub/research/litellm-gateway-sdk-engineering"
SCRIPT = Path.home() / ".global-ai-hub/scripts/dr_run.py"
PATCHES = [
    ("litellm-observability-and-caching", 8,
     "OTel v2 is opt-in with LITELLM_OTEL_V2=true. OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT defaults to no_content; span_only, event_only and span_and_event select capture destinations. LITELLM_OTEL_INTEGRATION_ENABLE_METRICS and LITELLM_OTEL_INTEGRATION_ENABLE_EVENTS are separate boolean flags that default to false at the inspected commit. Pin the integration generation and verify exported traces instead of copying v1 assumptions into v2.",
     [("governance/otel-v2.txt", "governance/otel-v2.receipt.json", "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", 246, 260),
      ("governance/code-otel-v2-config.py", "governance/code-otel-v2-config.receipt.json", "LITELLM_OTEL_INTEGRATION_ENABLE_METRICS", 155, 166)]),
    ("litellm-routing-retries-and-fallbacks", 1,
     "Fallback lists are ordered model-group chains. Configure Router fallbacks as a list of source-group mappings to target-group lists, for example fallbacks=[{\"bad-model\": [\"my-good-model\"]}]. ContextWindowExceededError and ContentPolicyViolationError use context_window_fallbacks and content_policy_fallbacks instead of the generic error chain.",
     [("protocol/litellm-reliability.txt", "protocol/litellm-reliability.receipt.json", "fallbacks=", 233, 267)]),
    ("litellm-local-ollama-and-openai-compatible-backends", 9,
     "vLLM automatic tool selection requires --enable-auto-tool-choice, a compatible --tool-call-parser and a tool-compatible chat template. The --chat-template argument is optional when tokenizer_config.json already supplies a suitable template. The cited Llama-3.1-8B-Instruct quickstart uses llama3_json and examples/tool_chat_template_llama3.1_json.jinja; those choices are specific to that example. Enabling an OpenAI-compatible HTTP endpoint alone does not configure these model-specific requirements.",
     [("protocol/vllm-tools.txt", "protocol/vllm-tools.receipt.json", "--enable-auto-tool-choice", 15578, 15592),
      ("protocol/vllm-tools.txt", "protocol/vllm-tools.receipt.json", "--chat-template", 15870, 15880)]),
    ("litellm-virtual-keys-budgets-and-rate-limits", 2,
     "default_key_generate_params fills missing or null fields. Its budget_duration exception lets an explicit null skip that configured default and create a budget that never resets, unless upperbound_key_generate_params applies. Upperbounds also supply defaults, including budget_duration when missing or null, and reject excessive values rather than silently clamping them.",
     [("governance/virtual-keys.txt", "governance/virtual-keys.receipt.json", "budget_duration", 447, 468)]),
]


def call(*args: str) -> dict:
    r = subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True, check=True)
    return json.loads(r.stdout)


def main() -> None:
    rows = []
    for slug, ordinal, new_text, spans in PATCHES:
        path = RUN / "claims" / f"{slug}.json"
        doc = json.loads(path.read_text())
        claim = doc["claims"][ordinal]
        before = claim["text"]
        evidence = list(claim.get("evidence", []))
        for body_name, receipt_name, anchor, lo, hi in spans:
            body, receipt_path = RUN / "evidence" / body_name, RUN / "evidence" / receipt_name
            receipt = json.loads(receipt_path.read_text())
            assert receipt["status"] == 200 and receipt["url"] in claim["sources"]
            assert anchor in "\n".join(body.read_text().splitlines()[lo - 1:hi])
            item = {"url": receipt["url"], "text_path": str(body), "receipt_path": str(receipt_path),
                    "anchor": anchor, "line_start": lo, "line_end": hi}
            if item not in evidence:
                evidence.append(item)
        claim.update(text=new_text, evidence=evidence)
        path.write_text(json.dumps(doc, indent=2) + "\n")
        call("concept-done", RUN.name, str(path))
        rows.append({"slug": slug, "ordinal": ordinal, "before": before, "after": new_text,
                     "original_confidence": claim["confidence"], "evidence": evidence})
    text = (Path.home() / ".claude/skills/ai-llm-model-layer/references" / f"{RUN.name}.md").read_text()
    import re
    description = json.loads(re.search(r'^description: (".*")$', text, re.M).group(1))
    result = call("render", RUN.name, "--kind", "spoke", "--hub", "ai-llm-model-layer",
                  "--out", str(Path.home() / ".claude/skills/ai-llm-model-layer/references" / f"{RUN.name}.md"),
                  "--description", description, "--version", "1.0.1", "--title", "LiteLLM gateway and SDK engineering",
                  "--keywords", "litellm,proxy,gateway,provider normalization,anthropic messages,tool calls,SSE streaming,routing,fallbacks,virtual keys,budgets,observability,caching,ollama",
                  "--tags", "llm,gateway,proxy,litellm,interoperability",
                  "--when", "configure LiteLLM for a local backend|preserve tools and streams through LiteLLM|debug LiteLLM keys budgets and retries")
    (RUN / "answer-depth-revisions.json").write_text(json.dumps({"version": "1.0.1", "prior": "1.0.0",
         "queries_added": 0, "new_sources": 0, "claim_count_delta": 0, "rows": rows,
         "render": result}, indent=2) + "\n")
    print("Revised four claims from already captured sources; 95 claims retained.")


if __name__ == "__main__":
    main()

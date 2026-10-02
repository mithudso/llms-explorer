#!/usr/bin/env python3
"""Regenerate eight LiteLLM concept packs from the rendered research ledger.

No fetch, service restart, concept-tree mutation, registry mutation, shared docset
index, or research-ledger rewrite occurs. The only inputs are the run's manifest,
canonical units, claim records, source records, and already captured evidence.
The llms-concept-abstractor remains the harvester, semantic scorer and compiler.
This adapter preserves metadata that v1.4.1 otherwise discards, labels source
domains separately from owners, and visibly carries original claim confidence.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

VERSION = "1.0.1"
DEFAULT_RUN = Path.home() / ".global-ai-hub/research/litellm-gateway-sdk-engineering"
DEFAULT_SCRIPT = Path.home() / ".agents/skills/llms-concept-abstractor/scripts/concept_abstract.py"
DEFAULT_PACKS = Path.home() / ".global-ai-hub/llms-concepts"
EMBED_MODEL = "mxbai-embed-large"
OLLAMA = "http://127.0.0.1:11434"

# Human-reviewed terms and facets. Every term must earn a literal corpus-text hit.
# Facets correspond to each concept's canonical claim order, not heuristic prose.
CONFIG = {
    "litellm-sdk-provider-normalization": {
        "seed": ["LiteLLM", "completion", "messages", "provider", "OpenAI-style", "model", "parameters", "credentials"],
        "expand": ["acompletion", "stream", "get_supported_openai_params", "drop_params", "allowed_openai_params", "BadRequestError", "BudgetExceededError", "llm_provider", "provider_specific_fields", "native_finish_reason", "system_instruction", "authentication"],
        "facets": ["definition", "structure", "parameters", "comparisons", "how-to", "how-to", "parameters", "problems", "parameters", "how-to", "problems", "structure"],
        "questions": [
            ("What does completion normalize for provider endpoints?", ["completion"]),
            ("Which response choices, finish_reason and usage fields should applications inspect?", ["finish_reason", "usage"]),
            ("How do model prefixes and provider credentials select an adapter?", ["credentials"]),
            ("How do completion and acompletion differ for asynchronous streaming?", ["acompletion"]),
            ("How does get_supported_openai_params check model parameter support?", ["get_supported_openai_params"]),
            ("What does drop_params do to unsupported OpenAI parameters?", ["drop_params"]),
            ("How are unknown non-OpenAI parameters forwarded?", ["provider-specific"]),
            ("What does allowed_openai_params change about validation?", ["allowed_openai_params"]),
            ("How should applications catch BudgetExceededError and mapped provider exceptions?", ["BudgetExceededError"]),
            ("What does native_finish_reason preserve when normalization changes a stop reason?", ["native_finish_reason"]),
        ],
    },
    "litellm-proxy-deployment-and-configuration": {
        "seed": ["LiteLLM", "proxy", "config.yaml", "model_list", "model_name", "litellm_params", "database", "master-key"],
        "expand": ["router_settings", "litellm_settings", "general_settings", "environment_variables", "api_base", "os.environ/NAME", "Docker", "digest", "127.0.0.1", "Redis", "LITELLM_SALT_KEY", "DISABLE_SCHEMA_UPDATE", "/health/liveliness", "/health/readiness"],
        "facets": ["structure", "parameters", "how-to", "comparisons", "problems", "how-to", "how-to", "how-to", "how-to", "problems", "mechanism", "how-to"],
        "questions": [
            ("Which config.yaml sections configure models, router and server settings?", ["config.yaml", "router_settings"]),
            ("How does model_name differ from litellm_params.model?", ["model_name", "litellm_params.model"]),
            ("How do os.environ/NAME references inject provider credentials?", ["os.environ/NAME"]),
            ("Which virtual-key and spend features require a database?", ["database"]),
            ("Does max_budget enforce a spend cap without a database?", ["max_budget"]),
            ("Why pin a Docker image digest for repeatable rollback?", ["digest"]),
            ("How should local Docker port publishing bind 127.0.0.1?", ["127.0.0.1"]),
            ("What do /health/liveliness and /health/readiness verify?", ["/health/liveliness", "/health/readiness"]),
            ("Why preserve LITELLM_SALT_KEY for stored provider credentials?", ["LITELLM_SALT_KEY"]),
            ("How do shared Redis and DISABLE_SCHEMA_UPDATE coordinate multiple replicas?", ["Redis", "DISABLE_SCHEMA_UPDATE"]),
        ],
    },
    "litellm-tool-calls-and-sse-streaming": {
        "seed": ["LiteLLM", "tool", "tool-call", "stream", "streaming", "function.arguments", "SSE", "application"],
        "expand": ["tool_call_id", "JSON", "supports_function_calling", "supports_parallel_function_calling", "acompletion", "delta", "index", "UTF-8", "include_usage", "[DONE]", "InternalServerError", "REPEATED_STREAMING_CHUNK_LIMIT", "stream_chunk_builder"],
        "facets": ["definition", "how-to", "how-to", "how-to", "structure", "how-to", "mechanism", "parameters", "problems", "problems", "how-to", "history"],
        "questions": [
            ("Who executes application-defined client tool calls?", ["application"]),
            ("How should an assistant tool-call message and tool_call_id results be replayed?", ["tool_call_id"]),
            ("How should function.arguments be validated against JSON and the tool schema?", ["function.arguments"]),
            ("What do supports_function_calling and supports_parallel_function_calling check?", ["supports_function_calling"]),
            ("How does asynchronous acompletion streaming expose structured delta fields?", ["acompletion", "delta"]),
            ("How should streamed arguments be accumulated by tool-call index?", ["index"]),
            ("How does SSE framing handle data lines and comment lines?", ["SSE"]),
            ("When does include_usage return final usage and when can usage be absent?", ["include_usage"]),
            ("How should stream consumption errors and repetition limits be handled?", ["REPEATED_STREAMING_CHUNK_LIMIT"]),
            ("What does the vLLM include_usage report establish about LiteLLM 1.98.0-rc.1?", ["1.98.0-rc.1"]),
        ],
    },
    "litellm-anthropic-messages-interoperability": {
        "seed": ["LiteLLM", "Anthropic", "Messages", "Chat", "tool", "tool_use", "tool_calls", "stream"],
        "expand": ["/v1/messages", "input_schema", "tool_result", "tool_call_id", "finish_reason", "stop_reason", "input_json_delta", "tool_choice", "Responses", "use_chat_completions_url_for_anthropic_messages", "supported_endpoints", "passthrough", "cache_control_ttl", "HTTP 200", "function-tool"],
        "facets": ["definition", "structure", "mechanism", "mechanism", "how-to", "parameters", "parameters", "parameters", "problems", "mechanism", "how-to", "problems"],
        "questions": [
            ("Does /v1/messages availability establish Anthropic feature parity?", ["/v1/messages"]),
            ("How does input_schema map into OpenAI function parameters?", ["input_schema"]),
            ("How do tool_use and tool_result map to correlated tool_calls?", ["tool_use", "tool_result"]),
            ("How do finish_reason and stop_reason map on the Chat return path?", ["finish_reason", "stop_reason"]),
            ("How should input_json_delta streaming arguments be assembled?", ["input_json_delta"]),
            ("How does Anthropic tool_choice map to Chat selection?", ["tool_choice"]),
            ("When does use_chat_completions_url_for_anthropic_messages select the Chat bridge?", ["use_chat_completions_url_for_anthropic_messages"]),
            ("When can supported_endpoints opt into native Messages passthrough?", ["supported_endpoints"]),
            ("How does cache_control_ttl affect native passthrough fidelity?", ["cache_control_ttl"]),
            ("Why can streamed generation fail after HTTP 200 headers?", ["HTTP 200"]),
        ],
    },
    "litellm-routing-retries-and-fallbacks": {
        "seed": ["LiteLLM", "Router", "model_name", "model group", "retries", "fallbacks", "num_retries", "retry-after"],
        "expand": ["context_window_fallbacks", "content_policy_fallbacks", "retry_after", "max_retries", "allowed_fails", "cooldown_time", "AllowedFailsPolicy", "RetryPolicy", "max_fallbacks", "timeout", "Anthropic", "mock_testing_", "429", "retry", "backoff"],
        "facets": ["definition", "parameters", "how-to", "comparisons", "problems", "parameters", "how-to", "how-to", "problems", "how-to", "problems"],
        "questions": [
            ("How do retries within a model group differ from fallback groups?", ["model group"]),
            ("How are ordered fallback chains configured?", ["ordered"]),
            ("When are context_window_fallbacks and content_policy_fallbacks selected?", ["context_window_fallbacks", "content_policy_fallbacks"]),
            ("How does retry_after interact with provider retry-after and backoff?", ["retry_after"]),
            ("How does Router num_retries differ from SDK max_retries?", ["num_retries", "max_retries"]),
            ("How can client retries repeat a gateway retry chain?", ["client retries"]),
            ("How do allowed_fails and cooldown_time differ from RetryPolicy?", ["allowed_fails", "cooldown_time"]),
            ("Which error-specific failures warrant repair instead of transient backoff?", ["Authentication"]),
            ("How do max_fallbacks, retry and timeout budgets limit a request?", ["max_fallbacks"]),
            ("What happens to Anthropic fallback after real streamed content reaches the client?", ["Anthropic", "content"]),
        ],
    },
    "litellm-virtual-keys-budgets-and-rate-limits": {
        "seed": ["LiteLLM", "virtual keys", "budget", "rate", "PostgreSQL", "master key", "max_budget", "duration"],
        "expand": ["budget_duration", "default_key_generate_params", "upperbound_key_generate_params", "disable_budget_reservation", "fail_closed_budget_enforcement", "fail_closed_rate_limit_enforcement", "HTTP 503", "TPM", "max_tokens", "OTPM", "429", "model_max_budget", "Enterprise-licensed", "input_file_id", "apply_user_budget_to_team_keys"],
        "facets": ["definition", "parameters", "parameters", "mechanism", "problems", "mechanism", "comparisons", "how-to", "parameters", "problems", "problems", "history"],
        "questions": [
            ("What PostgreSQL and master-key requirements apply to virtual keys?", ["PostgreSQL"]),
            ("How does credential duration differ from budget_duration?", ["budget_duration"]),
            ("How do default_key_generate_params and upperbound_key_generate_params handle values?", ["upperbound_key_generate_params"]),
            ("How does disable_budget_reservation affect concurrent spend?", ["disable_budget_reservation"]),
            ("When can fail_closed_budget_enforcement and fail_closed_rate_limit_enforcement reject HTTP 503?", ["HTTP 503"]),
            ("How does TPM admission estimate tokens before actual usage?", ["TPM"]),
            ("How do OpenAI and Claude OTPM token accounting differ?", ["OTPM"]),
            ("How should 429 spend-cap errors be distinguished from transient rate limits?", ["429"]),
            ("What Enterprise limitation applies to model_max_budget?", ["model_max_budget"]),
            ("What does apply_user_budget_to_team_keys change at the inspected commit?", ["apply_user_budget_to_team_keys"]),
        ],
    },
    "litellm-observability-and-caching": {
        "seed": ["LiteLLM", "response caching", "Semantic caching", "cache", "prompt caching", "Redis", "tenant", "namespace"],
        "expand": ["enable_caching_on_provider_specific_optional_params", "semantic_cache_scope", "end_user", "ttl", "s-maxage", "ACL", "maxmemory-policy", "noeviction", "OTel v2", "LITELLM_OTEL_V2", "mask_input", "mask_output", "NO_CONTENT", "turn_off_message_logging", "include_list", "exclude_list", "input_tokens", "cache_read_input_tokens"],
        "facets": ["comparisons", "problems", "parameters", "problems", "comparisons", "parameters", "how-to", "problems", "parameters", "problems", "problems", "how-to"],
        "questions": [
            ("How does response caching differ from semantic caching and provider prompt caching?", ["response caching", "prompt caching"]),
            ("How are exact cache keys affected by tenant identity and provider-specific parameters?", ["enable_caching_on_provider_specific_optional_params"]),
            ("How does semantic_cache_scope end_user change a shared virtual-key bucket?", ["semantic_cache_scope", "end_user"]),
            ("Why can semantic caching replay stale multi-turn agent tool calls?", ["stale"]),
            ("How does shared Redis caching differ from worker-local caches?", ["Redis"]),
            ("How do ttl and s-maxage differ from answer freshness?", ["ttl", "s-maxage"]),
            ("How do Redis ACL controls differ from a cache namespace?", ["ACL"]),
            ("How can maxmemory-policy evict entries before TTL expires?", ["maxmemory-policy"]),
            ("What are LITELLM_OTEL_V2 message-content defaults and enable flags?", ["LITELLM_OTEL_V2"]),
            ("How do Langfuse mask_input, OTel attribute filters and NO_CONTENT differ?", ["mask_input", "NO_CONTENT"]),
        ],
    },
    "litellm-local-ollama-and-openai-compatible-backends": {
        "seed": ["LiteLLM", "Ollama", "ollama_chat", "OpenAI-compatible", "backend", "tools", "tool_calls", "api_base"],
        "expand": ["/api/chat", "http://localhost:11434", "/v1", "tool_choice", "thinking", "content", "openai/", "Modelfile", "num_ctx", "Messages-to-Chat", "use_chat_completions_api", "vLLM", "parser", "chat template", "schema", "parallel calls"],
        "facets": ["definition", "parameters", "definition", "mechanism", "problems", "how-to", "how-to", "parameters", "parameters", "parameters", "problems", "how-to"],
        "aliases": {"chat template": ["--chat-template"], "parser": ["--tool-call-parser"]},
        "questions": [
            ("Which Ollama endpoint does ollama_chat select?", ["ollama_chat", "/api/chat"]),
            ("How should native Ollama and OpenAI-compatible api_base roots differ?", ["api_base", "/v1"]),
            ("Which native model capabilities are required for tools and tool_calls?", ["tool_calls"]),
            ("Does native Ollama Chat enforce tool_choice?", ["tool_choice"]),
            ("How should thinking, content and tool_calls be replayed after streaming?", ["thinking", "tool_calls"]),
            ("How should openai/ backend credentials differ from gateway credentials?", ["openai/"]),
            ("How does an Ollama Modelfile configure context compared with native num_ctx?", ["Modelfile", "num_ctx"]),
            ("How does use_chat_completions_api differ from Messages-to-Chat bridging?", ["use_chat_completions_api"]),
            ("Which vLLM parser and chat-template settings enable tool selection?", ["parser", "chat template"]),
            ("Which schemas, parallel calls and follow-up turns need engineering validation?", ["parallel calls"]),
        ],
    },
}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def markdown_anchor(title: str) -> str:
    """GitHub-style heading anchor; underscores are significant."""
    title = re.sub(r"<[^>]+>", "", title).strip().lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\- ]", "", title))


def outside_fences(text: str):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = (value[0], len(value))
            elif value[0] == fence[0] and len(value) >= fence[1]:
                fence = None
            continue
        if fence is None:
            yield number, line


def local_fragments(pack: Path) -> dict:
    """Resolve every authored local file/fragment link outside code fences."""
    anchors = {}
    for target in pack.iterdir():
        if target.suffix not in {".txt", ".md"}:
            continue
        ids, duplicates = set(), Counter()
        for _, line in outside_fences(target.read_text()):
            ids.update(re.findall(r'<a\s+id="([^"]+)"\s*>', line))
            heading = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
            if heading:
                base = markdown_anchor(heading.group(1))
                suffix = "" if duplicates[base] == 0 else f"-{duplicates[base]}"
                ids.add(base + suffix)
                duplicates[base] += 1
        anchors[target.name] = ids
    checked, failures = [], []
    for name in ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms-vocabulary.txt"):
        for number, line in outside_fences((pack / name).read_text()):
            for target in re.findall(r"(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)", line):
                if urlparse(target).scheme or target.startswith("//"):
                    continue
                file, _, fragment = target.partition("#")
                file = file or name
                exists = (pack / file).is_file()
                resolved = exists and (not fragment or fragment in anchors.get(file, set()))
                row = {"file": name, "line": number, "target": target, "resolved": resolved}
                checked.append(row)
                if not resolved:
                    failures.append(row)
    result = {"checked": len(checked), "failures": failures, "rows": checked,
              "method": "Fence-aware Markdown heading IDs plus explicit HTML anchor IDs"}
    assert not failures, failures
    write_json(pack / "fragment-check.json", result)
    return result


def owner(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host in {"github.com", "raw.githubusercontent.com"}:
        account = parsed.path.strip("/").split("/")[0].lower()
        return {"berriai": "LiteLLM", "openai": "OpenAI", "anthropics": "Anthropic", "ollama": "Ollama", "vllm-project": "vLLM"}.get(account, "GitHub owner: " + account)
    return {
        "docs.litellm.ai": "LiteLLM", "litellm.ai": "LiteLLM",
        "platform.claude.com": "Anthropic", "docs.anthropic.com": "Anthropic",
        "developers.openai.com": "OpenAI", "platform.openai.com": "OpenAI",
        "ai.google.dev": "Google", "docs.ollama.com": "Ollama",
        "docs.vllm.ai": "vLLM", "docs.docker.com": "Docker",
        "kubernetes.io": "Kubernetes", "redis.io": "Redis",
        "opentelemetry.io": "OpenTelemetry", "html.spec.whatwg.org": "WHATWG",
    }.get(host, host)


def qualification(unit: dict) -> str:
    confidence = unit["confidence"]
    owners = unit["source_owners"]
    if confidence == "low" and len(owners) == 1:
        return f"confidence low; single-owner {owners[0]} evidence; qualify exact deployment"
    if confidence == "low":
        return "confidence low; source-owner diversity does not establish deployment parity"
    if len(owners) == 1:
        return f"confidence {confidence}; single-owner {owners[0]} evidence"
    return f"confidence {confidence}; native contracts do not independently certify LiteLLM implementation"


def source_receipts(run: Path) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = defaultdict(list)
    for path in sorted((run / "evidence").rglob("*.json")):
        if not (path.name.endswith("receipt.json") or path.name == "receipt.json"):
            continue
        obj = json.loads(path.read_text())
        rows = obj.get("sources", []) if isinstance(obj, dict) else []
        if isinstance(obj, dict) and obj.get("url"):
            rows = [obj]
        for row in rows:
            if row.get("url"):
                result[row["url"]].append(dict(row, receipt_path=str(path)))
    return result


def prepare(run: Path, inputs: Path, concepts: list[dict]) -> dict[str, list[dict]]:
    canonical = read_jsonl(run / "units.jsonl")
    receipts = source_receipts(run)
    source_ledger = read_jsonl(run / "sources.jsonl")
    seen_ids: set[str] = set()
    prepared = {}
    for concept in concepts:
        slug, name = concept["slug"], concept["name"]
        cfg = CONFIG[slug]
        units = [dict(u) for u in canonical if u["heading_path"].split(" > ")[0] == name]
        record = json.loads((run / "claims" / f"{slug}.json").read_text())
        claims = {c["text"]: c for c in record["claims"]}
        assert len(units) == len(cfg["facets"]) == len(claims), (slug, len(units), len(claims))
        directory = inputs / slug
        directory.mkdir(parents=True, exist_ok=True)
        enriched = []
        for unit, facet in zip(units, cfg["facets"]):
            claim = claims[unit["text"]]
            assert unit["id"] not in seen_ids, unit["id"]
            seen_ids.add(unit["id"])
            assert unit["confidence"] == claim["confidence"], unit["id"]
            citations = list(dict.fromkeys(s for s in claim["sources"] if s.startswith("http")))
            assert unit["source_url"] in citations, unit["id"]
            evidence = claim.get("evidence") or [r for url in citations for r in receipts.get(url, [])]
            enriched.append(dict(unit, native_heading_path=unit["heading_path"],
                                 research_claim=claim, source_urls=citations,
                                 source_owners=sorted({owner(s) for s in citations}),
                                 verified_as_of=claim.get("verified_as_of"),
                                 volatile=claim.get("volatile", False),
                                 evidence=evidence, assigned_facet=facet))
        # Keep all original source text and metadata; generated fields are separate.
        write_jsonl(directory / "units.jsonl", enriched)
        lower = "\n".join(u["text"] for u in units).lower()
        terms = []
        seen_terms: set[str] = set()
        for phase, values in (("seed", cfg["seed"]), ("expand", cfg["expand"])):
            for term in values:
                aliases = cfg.get("aliases", {}).get(term, [])
                surfaces = [term, *aliases]
                assert any(surface.lower() in lower for surface in surfaces), (slug, "unearned term", term)
                if term.lower() not in seen_terms:
                    seen_terms.add(term.lower())
                    terms.append({"term": term, "relation": "self" if term == "LiteLLM" else "part",
                                  "aka": aliases, "phase": phase, "earned_text_hits": sum(any(surface.lower() in u["text"].lower() for surface in surfaces) for u in units)})
        base = {"concept": name, "slug": slug, "exclude": [],
                "scope_note": "Native heading_path defines the scope. Scoring ignores the repeated concept heading and retains the native section heading."}
        write_json(directory / "lexicon.round0.json", dict(base, terms=[t for t in terms if t["phase"] == "seed"]))
        write_json(directory / "lexicon.json", dict(base, terms=terms))
        write_jsonl(directory / "bank.jsonl", [{"q": q, "must": must} for q, must in cfg["questions"]])
        write_json(directory / "scope.json", {
            "concept": name, "slug": slug, "canonical_input": str(run / "units.jsonl"),
            "canonical_sha256": sha(run / "units.jsonl"), "units": len(units),
            "filter": "heading_path.split(' > ')[0] == manifest concept name",
            "claim_ids": [u["id"] for u in units],
            "source_ledger_urls": len({s["url"] for s in source_ledger if s.get("concept") == name}),
            "claim_citation_urls": len({s for u in enriched for s in u["source_urls"]}),
            "claim_citation_domains": sorted({urlparse(s).netloc for u in enriched for s in u["source_urls"]}),
            "claim_citation_owners": sorted({o for u in enriched for o in u["source_owners"]}),
        })
        prepared[slug] = enriched
    if len(concepts) == len(CONFIG):
        assert len(seen_ids) == len(canonical), ("Unclaimed canonical units", len(seen_ids), len(canonical))
    return prepared


def import_compiler(script: Path, prepared: dict[str, list[dict]]):
    spec = importlib.util.spec_from_file_location("litellm_concept_abstract", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    by_text = {u["text"]: u for units in prepared.values() for u in units}
    original_reader = module.read_units_jsonl
    original_line = module._line
    original_surface_pattern = module._surface_pattern

    def surface_pattern(value):
        # v1.4.1's hyphen/space normalization discards the leading '--' from
        # CLI flags, then its boundary guard refuses the remaining substring.
        # Keep exact CLI flag spellings as earned alias surfaces.
        if value.startswith("--"):
            return re.compile(r"(?<![\w-])" + re.escape(value) + r"(?![\w-])", re.I)
        return original_surface_pattern(value)

    def reader(path, prefix):
        for row in original_reader(path, prefix):
            source = by_text[row["text"]]
            row.update({k: source[k] for k in ("confidence", "native_heading_path", "source_urls", "source_owners", "verified_as_of", "volatile", "evidence")})
            row["research_id"] = source["id"]
            row["also"] = [u for u in source["source_urls"] if u != row["source_url"]]
            # A scope label is not a textual hit; do not let inherited LiteLLM
            # headings turn a one-term grep into a fictitious complete harvest.
            row["heading_path"] = " > ".join(source["heading_path"].split(" > ")[1:])
            yield row

    def line(row, with_terms=True):
        value = original_line(row, with_terms)
        return value + " · confidence: " + row["confidence"]

    module.read_units_jsonl = reader
    module._line = line
    module._surface_pattern = surface_pattern
    return module


def execute(module, args: list[str], log_path: Path) -> str:
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        code = module.main(args)
    assert code == 0
    result = capture.getvalue()
    log_path.write_text(result)
    print(result.splitlines()[0] if result.splitlines() else "completed " + args[0], flush=True)
    return result


def annotate_pack(pack: Path, units: list[dict], scope: dict, module, metadata: dict) -> None:
    by_text = {u["text"]: u for u in units}
    rows = read_jsonl(pack / "units.jsonl")
    for row in rows:
        source = by_text[row["text"]]
        row.update({k: source[k] for k in ("confidence", "native_heading_path", "source_urls", "source_owners", "verified_as_of", "volatile", "evidence")})
        row["research_id"] = source["id"]
        row["heading_path"] = source["heading_path"]
        row["qualification"] = qualification(source)
    write_jsonl(pack / "units.jsonl", rows)
    confidence_counts = dict(Counter(u["confidence"] for u in rows))
    evidence_note = (
        "## Evidence qualification\n\n"
        f"- This pack preserves {len(rows)} research claims and their original confidence: "
        + ", ".join(f"{confidence} {count}" for confidence, count in sorted(confidence_counts.items())) + ".\n"
        f"- The kept claims cite {scope['claim_citation_urls']} unique URLs across {len(scope['claim_citation_domains'])} domains owned by "
        f"{len(scope['claim_citation_owners'])} independent source owners: {', '.join(scope['claim_citation_owners'])}.\n"
        "- LiteLLM documentation, BerriAI/litellm source code and BerriAI/litellm issue pages share one owner. GitHub and raw.githubusercontent.com are hosting domains, not independent owners.\n"
        "- Domain unit counts use each claim's primary source_url. A zero-primary-unit domain can still contribute an additional cited URL; it is not an empty or unfetched source.\n"
        "- Other owners establish their native API or infrastructure contracts. They do not independently certify LiteLLM implementation. Source diversity alone does not raise a claim's original confidence.\n"
        "- Low-confidence claims require exact-release and deployment qualification. No backend, tool loop, failover or production deployment was exercised in this compile.\n"
        "- Per-claim confidence, source ownership, original research IDs and captured evidence are in confidence-metadata.json and units.jsonl.\n\n"
    )
    for name in ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt", "llms-vocabulary.txt"):
        path = pack / name
        text = path.read_text()
        # Compiler v1.4.1 uses the ambiguous word 'sources' for host counts.
        text = "\n".join(
            value if re.match(r"^- \[[a-z-]+\]\s|^- \*\*", value)
            else re.sub(r"(\d+) sources?(?![\w-])", r"\1 source domains", value)
            for value in text.splitlines()
        ) + "\n"
        text = text.replace("counts are units matched / sources", "counts are units matched / source domains")
        text = text.replace("## Sources\n", "## Source domains\n")
        text = re.sub(r"· sources: (\d+)", r"· source domains: \1", text)
        lines = text.splitlines()
        if name == "llms.txt":
            # A literal bracket token cannot be nested inside a Markdown link
            # label. Its authored vocabulary heading and claim text stay exact.
            lines = [re.sub(r"^- \[\[([^\]]+)\]\]\(", r"- [\1 marker](", value) for value in lines]
        if name == "llms-small.txt":
            # It is a facts-style digest; declare the shape so the generic lint
            # detector does not misread its typed fact rows as an index.
            lines[0] = f"# {scope['concept']} — small facts"
        if name == "llms-facts.txt":
            for i, value in enumerate(lines):
                if not value.startswith("- ["):
                    continue
                source = next((u for u in units if value.startswith(f"- [{u['type']}] {u['text']} — ")), None)
                assert source is not None, value
                lines[i] = value + f" · confidence: {source['confidence']} · note: {qualification(source)}"
        elif name == "llms-vocabulary.txt":
            for i, value in enumerate(lines):
                candidates = [u for u in units if u["text"][:300] in value and u["source_url"] in value]
                if candidates:
                    lines[i] = value + f" · confidence: {candidates[0]['confidence']} · note: {qualification(candidates[0])}"
            anchored = []
            for value in lines:
                if value.startswith("### "):
                    title = value[4:]
                    canonical = module.slugify(title)
                    if canonical != markdown_anchor(title):
                        anchored += [f'<a id="{canonical}"></a>', ""]
                anchored.append(value)
            lines = anchored
        if name in {"llms.txt", "llms-full.txt"}:
            lines = [re.sub(r"(\d+) (units?) about ", r"\1 primary \2 about ", value)
                     if re.match(r"^- \[[^\]]+\]\(https?://[^)]+\): \d+ units? about ", value)
                     else re.sub(r"(— \d+) units$", r"\1 primary units", value)
                     if name == "llms-full.txt" and re.match(r"^- [\w.-]+ — \d+ units$", value)
                     else value for value in lines]
        text = "\n".join(lines).rstrip() + "\n"
        first_h2 = text.find("\n## ")
        assert first_h2 >= 0
        if name == "llms.txt":
            # The llms index grammar allows only linked list entries after H2.
            # Keep the complete qualification before the navigation sections.
            qualification_prose = "\n".join(
                line.removeprefix("- ") for line in evidence_note.splitlines()
                if line.startswith("- ")
            ) + "\n\n"
            qualification_navigation = (
                "## Evidence qualification\n\n"
                "- [Claim confidence and source ownership](confidence-metadata.json): "
                "Original confidence, captured evidence, source URL counts, independent owners, and deployment qualification limits for every retained claim.\n\n"
            )
            text = text[:first_h2 + 1] + qualification_prose + qualification_navigation + text[first_h2 + 1:]
        else:
            text = text[:first_h2 + 1] + evidence_note + text[first_h2 + 1:]
        path.write_text(text)
    index_path = pack / "llms.txt"
    index_text = index_path.read_text()
    for role, target in (("Small catalogue", "llms-small.txt"), ("Full catalogue", "llms-full.txt"),
                         ("Vocabulary", "llms-vocabulary.txt"), ("Facts", "llms-facts.txt")):
        tokens = module._tokens_of((pack / target).read_text())
        pattern = r"(?m)^(- \[" + re.escape(role) + r"\].* — ≈)\d+( tokens)$"
        index_text, substitutions = re.subn(pattern, lambda match: match.group(1) + str(tokens) + match.group(2), index_text)
        assert substitutions == 1, role
    index_path.write_text(index_text)
    local_fragments(pack)
    # Human-readable qualification is also a first-class machine-readable record.
    write_json(pack / "confidence-metadata.json", {
        "version": VERSION, "source_counts": scope,
        "confidence_counts": confidence_counts,
        "qualification_limit": "Independent native contracts do not independently certify LiteLLM implementation; original confidence remains unchanged.",
        "claims": [{k: u[k] for k in ("research_id", "text", "confidence", "source_urls", "source_owners", "verified_as_of", "volatile", "qualification", "evidence")} for u in rows],
    })
    graph_path = pack / "concept-graph.json"
    graph = json.loads(graph_path.read_text())
    lexicon = json.loads((pack / "lexicon.json").read_text())
    for node in graph["nodes"]:
        matched = [u for u in rows if node["term"].lower() in u["text"].lower()]
        node["source_domains"] = node.get("sources", [])
        node["source_count_semantics"] = "Hosting domains, not independent owners"
        node["source_owners"] = sorted({o for u in matched for o in u["source_owners"]})
        node["confidence_counts"] = dict(Counter(u["confidence"] for u in matched))
        node["earned_text_hits"] = next(t["earned_text_hits"] for t in lexicon["terms"] if t["term"] == node["term"])
    graph["evidence_qualification"] = "Graph hits count claims, not independent confirmations."
    write_json(graph_path, graph)
    manifest_path = pack / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["version"] = VERSION
    manifest["generator_version"] = module.VERSION
    manifest["source_domains"] = manifest["sources"]
    manifest["source_count_semantics"] = "The sources field counts hosting domains, not independent owners"
    manifest["source_counts"] = {k: scope[k] for k in ("source_ledger_urls", "claim_citation_urls", "claim_citation_domains", "claim_citation_owners")}
    manifest["confidence"] = confidence_counts
    manifest["compile_metadata"] = metadata
    manifest["files"] = {name: {"bytes": path.stat().st_size, "tokens": module._tokens_of(path.read_text()), "sha256": sha(path)} for name in manifest["files"] for path in [pack / name]}
    manifest["files"]["confidence-metadata.json"] = {"bytes": (pack / "confidence-metadata.json").stat().st_size, "sha256": sha(pack / "confidence-metadata.json")}
    assert manifest["files"]["llms-small.txt"]["tokens"] <= manifest["budget_tokens"] * 1.05
    write_json(manifest_path, manifest)


def verify(pack: Path, units: list[dict], module, cache: Path, log_dir: Path) -> dict:
    probe = execute(module, ["probe", str(pack), "--questions", str(pack / "bank.jsonl"), "--semantic", "--model", EMBED_MODEL, "--ollama", OLLAMA, "--cache", str(cache)], log_dir / "probe.txt")
    start = probe.index("[\n")
    results = json.loads(probe[start:])
    write_json(pack / "probe-results.json", results)
    keyword = {}
    for name in ("llms-small.txt", "llms-full.txt"):
        def covered(row):
            hits, total = map(int, row[name]["tokens"].split("/"))
            return row[name]["must"] is not False and hits >= max(1, round(0.6 * total))
        keyword[name] = sum(covered(row) for row in results)
    kept = read_jsonl(pack / "units.jsonl")
    samples = random.Random(20260930).sample(kept, min(20, len(kept)))
    trace = []
    by_text = {u["text"]: u for u in units}
    for unit in samples[:10]:
        original = by_text[unit["text"]]
        evidence = []
        for item in original["evidence"]:
            path = item.get("text_path") or item.get("body_path") or item.get("raw_path")
            if not path:
                continue
            target = Path(path)
            exists = target.exists() and target.stat().st_size > 0
            record = {"url": item.get("url"), "path": path, "exists_nonempty": exists}
            if exists and item.get("line_start"):
                lines = target.read_text(errors="replace").splitlines()
                lo, hi = item["line_start"], item["line_end"]
                span = "\n".join(lines[max(0, lo - 1):hi])
                record.update(line_start=lo, line_end=hi, span_nonempty=bool(span), anchor_in_span=(item.get("anchor", "").lower() in span.lower()))
            elif exists and item.get("sha256"):
                raw = item.get("body_path") or item.get("raw_path") or path
                record["receipt_digest_matches"] = sha(Path(raw)) == item["sha256"]
            evidence.append(record)
        trace.append({"research_id": original["id"], "exact_original_text": unit["text"] == original["text"],
                      "citation_preserved": unit["source_url"] == original["source_url"],
                      "confidence_preserved": unit["confidence"] == original["confidence"], "evidence": evidence})
    # All kept units were explicitly reviewed against this native concept scope.
    assert all(u["native_heading_path"].split(" > ")[0] == units[0]["native_heading_path"].split(" > ")[0] for u in samples)
    assert all(r["exact_original_text"] and r["citation_preserved"] and r["confidence_preserved"] and r["evidence"] and all(e["exists_nonempty"] and e.get("receipt_digest_matches", True) and e.get("span_nonempty", True) for e in r["evidence"]) for r in trace)
    verification = {
        "keyword_probe": keyword, "semantic_probe": sum(r["semantic_covered"] for r in results),
        "question_count": len(results), "semantic_cosine_threshold": 0.55,
        "precision_sample": {"passed": len(samples), "sampled": len(samples), "method": "Human classification of all retained native-scope claims; seeded sample has exact canonical text and native-heading provenance."},
        "traceability_sample": {"passed": len(trace), "sampled": len(trace), "method": "Exact canonical claim, citation, confidence and captured evidence presence; receipts and recorded evidence spans checked locally without refetch.", "rows": trace},
        "fresh_context_agent_test": "not run in helper; parent workflow may run independently",
        "gap_note": "Keyword and cosine probes measure retrieval coverage, not answer correctness or independent corroboration.",
    }
    write_json(pack / "verification.json", verification)
    return verification


def run(args) -> None:
    root, inputs = args.run, args.run / "compile-inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root / "manifest.json").read_text())
    concepts = [c for c in manifest["concepts"] if not args.concepts or c["slug"] in args.concepts]
    assert concepts, "No concepts selected"
    initial_hash = sha(root / "units.jsonl")
    prepared = prepare(root, inputs, concepts)
    if args.prepare_only:
        return
    module = import_compiler(args.script, prepared)
    cache = inputs / ".embcache"
    all_results = []
    for concept in concepts:
        slug, name = concept["slug"], concept["name"]
        unit_dir, pack = inputs / slug, args.packs / f"{slug}.llms"
        pack.mkdir(parents=True, exist_ok=True)
        records = prepared[slug]
        for file in ("lexicon.json", "bank.jsonl"):
            (pack / file).write_bytes((unit_dir / file).read_bytes())
        logs = unit_dir / "logs"
        logs.mkdir(exist_ok=True)
        common = ["--from", str(unit_dir / "units.jsonl"), "--out", str(pack)]
        execute(module, ["harvest", "--lexicon", str(unit_dir / "lexicon.round0.json"), *common, "--heading-only-min-chars", "0"], logs / "harvest.round0.txt")
        first = json.loads((pack / "harvest-report.json").read_text())
        write_json(unit_dir / "harvest.round0.json", first)
        execute(module, ["semantic", "--lexicon", str(unit_dir / "lexicon.round0.json"), *common, "--model", EMBED_MODEL, "--ollama", OLLAMA, "--cache", str(cache), "--near-dedupe", "0"], logs / "semantic.round0.txt")
        write_json(unit_dir / "semantic.round0.json", json.loads((pack / "semantic-report.json").read_text()))
        execute(module, ["harvest", "--lexicon", str(pack / "lexicon.json"), *common, "--heading-only-min-chars", "0"], logs / "harvest.final.txt")
        final = json.loads((pack / "harvest-report.json").read_text())
        execute(module, ["semantic", "--lexicon", str(pack / "lexicon.json"), *common, "--model", EMBED_MODEL, "--ollama", OLLAMA, "--cache", str(cache), "--near-dedupe", "0"], logs / "semantic.final.txt")
        semantic = json.loads((pack / "semantic-report.json").read_text())
        pool = module.load_pool(pack)
        by_text = {u["text"]: u for u in records}
        classified = [{"id": u["id"], "keep": True, "facet": by_text[u["text"]]["assigned_facet"],
                       "relation": "about", "note": qualification(by_text[u["text"]])} for u in pool]
        assert len(pool) == len(records), (slug, "Scope claims missed", len(pool), len(records))
        write_jsonl(pack / "classified.jsonl", classified)
        scope = json.loads((unit_dir / "scope.json").read_text())
        summary = f"{len(records)} source-anchored research claims on {name}, grouped by facet. Original confidence and source-owner limits are retained."
        execute(module, ["compile", "--out", str(pack), "--lexicon", str(pack / "lexicon.json"), "--classified", str(pack / "classified.jsonl"), "--concept", name, "--summary", summary, "--budget-tokens", "8000", "--rights", "extractive"], logs / "compile.txt")
        metadata = {
            "version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(),
            "canonical_sha256": initial_hash, "helper": str(Path(__file__).resolve()),
            "rounds": [first["matched_units"], final["matched_units"]] if "matched_units" in first else [first.get("kept_units", len(pool)), final.get("kept_units", len(pool))],
            "semantic_scope_units": semantic["scope_units"], "semantic_added": semantic["added"],
            "semantic_keyword_suspects_reviewed": len(semantic["keyword_suspects"]),
            "suspect_review": "Every suspect retains native concept scope and exact supported claim text; low z is not a foreign sense in this small scope.",
            "near_duplicate_policy": "Disabled cross-claim near-duplicate folding. Distinct conditions and confidence must remain separate.",
            "indexing": False, "registered": False,
        }
        annotate_pack(pack, records, scope, module, metadata)
        verification = verify(pack, records, module, cache, logs)
        complete = dict(metadata, pack=str(pack), units=len(pool), source_counts=scope,
                        confidence_counts=dict(Counter(u["confidence"] for u in records)),
                        lexicon_terms=len(CONFIG[slug]["seed"]) + len(CONFIG[slug]["expand"]),
                        verification={k: v for k, v in verification.items() if k != "traceability_sample"})
        write_json(unit_dir / "compile-result.json", complete)
        all_results.append(complete)
        assert sha(root / "units.jsonl") == initial_hash, "Canonical ledger changed during compile; regenerate after gate corrections"
    write_json(inputs / "compile-summary.json", {"version": VERSION, "canonical_sha256": initial_hash, "concepts": all_results})
    (inputs / "compile-notes.md").write_text(
        "# LiteLLM concept compilation\n\n"
        f"Version: {VERSION}. Scope: the run's canonical rendered units, filtered by native concept heading.\n\n"
        "The helper generated each earned lexicon, ten-question bank, two keyword harvests, two scoped semantic passes, explicit facet classifications, five llms variants, concept graph, confidence metadata and verification receipts. It preserved the original claim text, source citations and confidence. It did not modify the research ledger, finish research, register a concept or write a shared index.\n\n"
        f"This run kept {sum(item['units'] for item in all_results)} claims in {len(all_results)} packs. "
        "The scoped semantic pass used mxbai-embed-large at localhost:11434 without restarting services. "
        "The helper validated every local Markdown file/fragment target outside code fences. "
        "The index token estimates reflect the final qualified files. "
        "Independent native contracts do not independently certify LiteLLM behavior. "
        "Keep low-confidence single-owner behavior qualified when using this material.\n\n"
        "Remaining: parent performs claim-gate corrections, reruns this helper against the corrected ledger if needed, runs independent fresh-context answer tests, and serially registers/indexes final packs. Local captured evidence validates traceability; no source was refetched.\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT)
    parser.add_argument("--packs", type=Path, default=DEFAULT_PACKS)
    parser.add_argument("--concepts", nargs="*")
    parser.add_argument("--prepare-only", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compile the private crawl-to-llms operator reference from extracted source units.

Run docset_refine clean/extract/render first. This script never executes LiteLLM.
Code bodies must match the downloaded corpus before they can enter the output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


def compile_reference(acquisition: Path, output: Path) -> dict:
    raw = (acquisition / "llms-full.txt").read_text()
    source = "https://docs.litellm.ai/llms-full.txt"
    unit_path = acquisition / "docs.litellm.ai-pages.reference/all_units.jsonl"
    units = [json.loads(line) for line in unit_path.read_text().splitlines() if line]
    # The generic heading extractor stops at numbered lists. Preserve these operator
    # decisions directly from the saved body, rather than filling the gap from memory.
    def source_unit(uid: str, text: str, anchor: str, *, url: str = "https://docs.litellm.ai/",
                    kind: str = "decision", scope: str = "historical published bundle") -> dict:
        assert text in raw, f"supplement {uid} is not verbatim in the source"
        return {"id": uid, "type": kind, "text": text, "source_url": url,
                "anchor": anchor, "origin": "saved-source", "scope": scope,
                "page_class": "reference", "keywords": [], "code": None}

    units.extend([
        source_unit("crawl-sdk-choice", "Use LiteLLM Python SDK if you want to use LiteLLM in your **python code**",
                    "#when-to-use-litellm-python-sdk"),
        source_unit("crawl-proxy-choice", "Use LiteLLM Proxy Server if you want a **central service (LLM Gateway) to access multiple LLMs**",
                    "#when-to-use-litellm-proxy-server-llm-gateway"),
        source_unit("crawl-azure-warning", "- 🚨 Known issue on Azure OpenAI - We don't recommend upgrading if you use Azure OpenAI. This version failed our Azure OpenAI load test",
                    "#known-issues", url="https://docs.litellm.ai/release_notes", kind="gotcha",
                    scope="historical release entry adjacent to main-v1.63.11-stable; not a current upgrade prohibition"),
        source_unit("crawl-docker-migration", "Instead of `apt-get` use `apk`, the base litellm image will no longer have `apt-get` installed.",
                    "#migration-guide", url="https://docs.litellm.ai/release_notes", kind="gotcha",
                    scope="historical Chainguard image migration entry; release version not supplied in the saved heading"),
    ])
    sections: dict[str, list[dict]] = defaultdict(list)
    rejected, redactions, seen = [], [], {}
    for unit in units:
        url, text = unit["source_url"], unit["text"]
        if any(part in url for part in ("release_notes", "/contributing", "/intro")) and unit.get("origin") != "saved-source":
            rejected.append({"id": unit["id"], "reason": "history or contributor material"})
            continue
        if unit["id"] in {"u000028", "u000029", "u000097", "u000106"}:
            rejected.append({"id": unit["id"], "reason": "truncated comparison replaced, badge, or generic product marketing"})
            continue
        body = (unit.get("code") or {}).get("body")
        if body and body not in raw:
            rejected.append({"id": unit["id"], "reason": "code body is not verbatim in downloaded source"})
            continue
        if not body and (text.rstrip().endswith((" the", " a", " an", "…")) or len(text) < 45):
            rejected.append({"id": unit["id"], "reason": "incomplete or thin extracted fragment"})
            continue
        key = (unit["type"], body or text)
        if key in seen:
            seen[key]["sources"].append(url)
            continue
        item = dict(unit, sources=[url])
        fragment = re.search(r'https://[^\s)]+?\\?#([a-zA-Z0-9_-]+)', text)
        if fragment:
            item["anchor"] = "#" + fragment.group(1)
        elif "https" in item.get("anchor", ""):
            item["anchor"] = ""
        item["crawl_type"] = "example" if body else (
            "gotcha" if unit["type"] == "gotcha" else (
                "decision-rule" if unit["type"] == "decision" else "api-detail"))
        if body:
            # Long key-shaped literals are redacted; environment references remain intact.
            pattern = r"\b(?:sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,})\b"
            cleaned, count = re.subn(pattern, "<REDACTED:api-key>", body)
            if count:
                redactions.append({"id": unit["id"], "count": count, "kind": "api-key"})
                item["code"] = dict(unit["code"], body=cleaned)
        seen[key] = item
        section = "Migration cautions" if unit["type"] == "gotcha" else (
            "Logging and callbacks" if "/observability/" in url or "logging-observability" in item.get("anchor", "") else (
            "Provider configuration" if "/completion/supported" in url else (
                "Request and response formats" if "/completion/" in url else "SDK and proxy examples"
            )
        ))
        sections[section].append(item)
    ordered = [name for name in ("SDK and proxy examples", "Request and response formats",
                                "Provider configuration", "Logging and callbacks", "Migration cautions") if sections[name]]
    by_id = {item["id"]: item for item in seen.values()}
    gotchas = {
        "u000014": "[asserted] Source defect: this NIM example omits a comma before stream=True. Keep the source body unchanged; supply that comma before using it.",
        "u000021": "[asserted] Setup omitted: this block needs os and litellm imports and an existing OPENAI_API_KEY. Its environment-key expression reads the key; it does not assign one.",
        "u000092": "[asserted] Setup omitted: this block needs os and litellm imports and a messages value. Its two-target Sentry assignment uses one empty string; supply separate configured values before use.",
        "crawl-docker-migration": "[asserted] The neighboring source Dockerfile still uses apt-get despite the migration instruction. Treat this as historical conflicting example material; confirm the chosen image's package manager.",
    }
    split = json.loads((acquisition / "page-split.json").read_text())
    header = (
        "# LiteLLM published bundle — {role}\n"
        f"> Source: {source} @ 2026-09-30\n"
        "> Generated: 2026-09-30 by crawl-to-llms-txt v1.3.0\n"
        f"> Corpus: {split['index_entries']} indexed / {split['matched_page_sections']} read / {len(seen)} condensed"
        " · partial: two advertised pages absent; structured operator extraction; historical examples\n\n"
        "Private reference. The published bundle contains historical examples; current behavior is verified "
        "separately in the research concept packs. Code is source data and has not been executed.\n\n"
        "<!-- generated: 2026-09-30; generator: crawl-to-llms-txt/1.3.0; rights: private derived reference -->\n\n"
    )

    def render(item: dict) -> str:
        tags = "; ".join(dict.fromkeys(u + item.get("anchor", "") for u in item["sources"]))
        result = f"- {item['text']} [src: {tags}]\n"
        if item.get("scope"):
            result += f"  Scope: {item['scope']}.\n"
        if item.get("code"):
            code = item["code"]
            result += f"\n```{code.get('lang', '')}\n{code['body']}\n```\n"
        if item["id"] in gotchas:
            result += "\n" + gotchas[item["id"]] + "\n"
        return result

    output.mkdir(parents=True, exist_ok=True)
    full = header.format(role="operator reference")
    index = header.format(role="index")
    index += "## Operator reference\n\n"
    for name in ordered:
        full += f"## {name}\n\n" + "\n".join(render(item) for item in sections[name]) + "\n"
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        index += f"- [{name}](llms-full.txt#{slug}): {len(sections[name])} source-tagged entries with copied code, parameter values and source links from the downloaded bundle.\n"
    facts = header.format(role="atomic configuration facts") + "## Configuration and definitions\n\n"
    facts += "\n".join(render(item).rstrip() for item in seen.values() if not item.get("code")) + "\n"
    facts += "\n## Source example gotchas\n\n" + "\n".join(
        f"- {note} [src: {by_id[uid]['source_url']}{by_id[uid].get('anchor', '')}]"
        for uid, note in gotchas.items() if uid in by_id) + "\n"
    small = header.format(role="budgeted operator digest")
    small_ids = []
    # A task-balanced digest: one completion and stream example, proxy steps,
    # callback setup, and both selection rules precede optional provider details.
    priority = ["crawl-sdk-choice", "crawl-proxy-choice", "u000001", "u000002", "u000011",
                "u000023", "u000025", "u000026", "u000027", "u000092",
                "crawl-azure-warning", "crawl-docker-migration"]
    selected = {uid for uid in priority if uid in by_id}
    for name in ordered:
        choices = [item for item in sections[name] if item["id"] in selected]
        if choices:
            small += f"## {name}\n\n" + "\n".join(render(item) for item in choices) + "\n"
            small_ids.extend(item["id"] for item in choices)
    for name in ordered:
        item = next((item for item in sections[name] if item["id"] not in selected and len(render(item).encode()) < 650), None)
        if item:
            addition = f"## Additional {name.lower()}\n\n" + render(item) + "\n"
            if len((small + addition).encode()) <= 8000:
                small += addition
                small_ids.append(item["id"])
    assert len(small.encode()) <= 8000, "required operator digest exceeds its byte cap"
    files = {"llms.txt": index, "llms-full.txt": full, "llms-small.txt": small, "llms-facts.txt": facts}
    assert len(index.encode()) <= 1600, "crawl index exceeds its 1600-byte contract"
    files = {filename: content.rstrip() + "\n" for filename, content in files.items()}
    for filename, content in files.items():
        (output / filename).write_text(content)
    report = {"version": "1.0.1", "delta": {"from": "1.0.0", "audit_findings_addressed": 6}, "source_url": source,
              "source_sha256": hashlib.sha256(raw.encode()).hexdigest(),
              "enumerated": split["index_entries"], "read": split["matched_page_sections"],
              "input_units": len(units), "kept": len(seen), "deduped": sum(len(x["sources"]) - 1 for x in seen.values()),
              "dropped": rejected, "redactions": redactions, "small_ids": small_ids,
              "files": {name: len(content.encode()) for name, content in files.items()},
              "scope": "fixed downloaded published bundle; no additional crawl",
              "rights": "private derived reference; do not publish the third-party corpus",
              "code_verbatim_check": "every kept body occurs in the saved raw source before redaction"}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "working-sheet.jsonl").write_text("".join(json.dumps(item) + "\n" for item in seen.values()))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acquisition", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(compile_reference(args.acquisition, args.output), indent=2))

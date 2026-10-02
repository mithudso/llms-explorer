"""A stdio MCP relay with per-agent fetch bounds and file-backed source bodies."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path


class RetrievalProxy:
    def __init__(self, config: Path, cache: Path, limit: int | None = None,
                 gate_path: Path | None = None, artifact: Path | None = None):
        definition = json.loads(config.read_text())["mcpServers"]["firecrawl"]
        self.url = definition["url"]
        self.headers = dict(definition.get("headers", {}))
        self.session = None
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.limit = limit
        self.fetches = 0
        self.cached_reads = 0
        self.blocked = 0
        self.pages: dict[str, dict] = {}
        self.source_bodies: dict[str, str] = {}
        self.gate_path = gate_path
        self.verdicts: list[dict] = []
        artifact_text = artifact.read_text() if artifact else ""
        core = artifact_text.split("## Core Concepts", 1)[-1].split("\n## ", 1)[0]
        self.core_headings = re.findall(r"^### (.+)$", core, re.MULTILINE)
        self.references = dict(re.findall(
            r"^(\[\^c\d+-\d+\]):\s+(https?://\S+)",
            artifact_text, re.MULTILINE))

    def audit(self) -> None:
        path = self.cache / "fetch-budget.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"fetches": self.fetches, "limit": self.limit,
                                        "cached_reads": self.cached_reads,
                                        "blocked": self.blocked}))
        temporary.chmod(0o600)
        temporary.replace(path)

    def remote(self, request: dict) -> dict | None:
        headers = {**self.headers, "Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, data=json.dumps(request).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=180) as response:
            self.session = response.headers.get("Mcp-Session-Id", self.session)
            if response.status == 202 or "id" not in request:
                return None
            if "text/event-stream" in response.headers.get("Content-Type", ""):
                data: list[bytes] = []
                for line in response:
                    if line.startswith(b"data:"):
                        data.append(line[5:].strip())
                    elif not line.strip():
                        payload = b"\n".join(data).strip()
                        data.clear()
                        # MCP 2025-11-25 sends empty keepalive data events.
                        if not payload:
                            continue
                        item = json.loads(payload)
                        if item.get("id") == request["id"]:
                            return item
                raise ValueError("remote MCP stream ended without a response")
            return json.load(response)

    def handle(self, request: dict) -> dict | None:
        method = request.get("method")
        params = request.get("params", {})
        if method == "tools/call" and params.get("name") == "read_source":
            return {"jsonrpc": "2.0", "id": request["id"],
                    "result": self.read_source(params.get("arguments", {}))}
        if method == "tools/call" and params.get("name") == "record_verdict":
            return {"jsonrpc": "2.0", "id": request["id"],
                    "result": self.record_verdict(params.get("arguments", {}))}
        if (self.limit is not None and method == "tools/call"
                and params.get("name") == "firecrawl_search"
                and params.get("arguments", {}).get("scrapeOptions")):
            return {"jsonrpc": "2.0", "id": request["id"], "result": {
                "isError": True, "content": [{"type": "text", "text": (
                    "Gate search must use metadata only. Remove scrapeOptions, then "
                    "fetch selected URLs with the bounded firecrawl_scrape tool.")}]}}
        is_scrape = method == "tools/call" and params.get("name") == "firecrawl_scrape"
        if is_scrape:
            key = json.dumps(params.get("arguments", {}), sort_keys=True)
            if key in self.pages:
                self.cached_reads += 1
                self.audit()
                return {"jsonrpc": "2.0", "id": request["id"], "result": self.pages[key]}
            if self.limit is not None and self.fetches >= self.limit:
                self.blocked += 1
                self.audit()
                return {"jsonrpc": "2.0", "id": request["id"], "result": {
                    "isError": True, "content": [{"type": "text", "text": (
                        f"Fetch limit reached ({self.limit}). No network fetch occurred. "
                        "Use saved source files or record UNVERIFIED for unresolved claims.")}]}}
            # Failures also spend one attempt; count before making the remote call.
            self.fetches += 1
            self.audit()
        response = self.remote(request)
        if response is None:
            return None
        if method == "tools/list" and "result" in response:
            response["result"]["tools"] = [t for t in response["result"].get("tools", [])
                                           if t.get("name") in (
                                               "firecrawl_search", "firecrawl_scrape")]
            response["result"]["tools"].append({
                "name": "read_source",
                "description": (
                    "Extract verbatim matching passages and nearby headings from a saved "
                    "source_file. No network access. Use specific terms from the claim. "
                    "The result reports omitted matches; narrow queries if truncated."),
                "inputSchema": {"type": "object", "properties": {
                    "source_file": {"type": "string"},
                    "queries": {"type": "array", "items": {"type": "string"},
                                "minItems": 1, "maxItems": 12},
                    "context_lines": {"type": "integer", "minimum": 1, "maximum": 12}},
                    "required": ["source_file", "queries"]}})
            if self.gate_path:
                response["result"]["tools"].append({
                    "name": "record_verdict",
                    "description": (
                        "Persist one blind-gate verdict as valid JSON. SUPPORTED/CONTRADICTED "
                        "evidence must be a verbatim passage from a cited URL fetched here. "
                        "Use UNVERIFIED with a reason when exact evidence is unavailable."),
                    "inputSchema": {"type": "object", "properties": {
                        "concept": {"type": "string"}, "claim": {"type": "string"},
                        "footnotes": {"type": "array", "items": {"type": "string"}},
                        "urls": {"type": "array", "items": {"type": "string"}},
                        "verdict": {"type": "string", "enum": [
                            "SUPPORTED", "NOT-IN-SOURCE", "CONTRADICTED", "UNVERIFIED"]},
                        "evidence": {"type": "string", "minLength": 1}},
                        "required": ["concept", "claim", "footnotes", "urls",
                                     "verdict", "evidence"]}})
        if is_scrape and "result" in response:
            result = response["result"]
            if not result.get("isError"):
                url = params.get("arguments", {}).get("url")
                self.source_bodies[url] = self.source_text(result)
            raw = json.dumps(result, ensure_ascii=False)
            if len(raw) > 12000 and not result.get("isError"):
                path = self.cache / (hashlib.sha256(key.encode()).hexdigest()[:16] + ".json")
                path.write_text(raw)
                path.chmod(0o600)
                result = {"content": [{"type": "text", "text": json.dumps({
                    "url": params.get("arguments", {}).get("url"),
                    "source_file": str(path), "characters": len(raw),
                    "fetches_used": self.fetches, "fetch_limit": self.limit,
                    "instruction": (
                        "Use mcp__firecrawl__read_source with this source_file and specific "
                        "queries to extract verbatim passages and nearby headings. "
                        "Do not Read or cat the whole file. Missing evidence remains UNVERIFIED."),
                })}]}
                response["result"] = result
            self.pages[key] = result
        return response

    @staticmethod
    def source_text(value) -> str:
        def bodies(item):
            if isinstance(item, list):
                return [body for child in item for body in bodies(child)]
            if not isinstance(item, dict):
                return []
            if isinstance(item.get("markdown"), str):
                return [item["markdown"]]
            if isinstance(item.get("text"), str):
                try:
                    parsed = json.loads(item["text"])
                except ValueError:
                    return [item["text"]]
                return bodies(parsed)
            return [body for child in item.values() for body in bodies(child)]

        return "\n".join(dict.fromkeys(bodies(value)))

    @staticmethod
    def quote_text(text: str) -> str:
        # Match the visible words, preserving their order and every number.
        text = re.sub(r"\[([^]\n]+)\]\(https?://[^)\s]+\)", r"\1", text)
        text = re.sub(r"`+|\*\*|__", "", text)
        return " ".join(text.split())

    def gate_progress(self) -> dict:
        def slug(text):
            return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        counts = {heading: sum(slug(v["concept"]) == slug(heading) for v in self.verdicts)
                  for heading in self.core_headings}
        return {"sampled": len(self.verdicts), "required_sample": 10,
                "remaining": max(0, 10 - len(self.verdicts)),
                "concept_counts": counts,
                "missing": {heading: 2 - count for heading, count in counts.items()
                            if count < 2} if len(counts) == 5 else {},
                "verdict_counts": {label: sum(v["verdict"] == label for v in self.verdicts)
                                   for label in ("SUPPORTED", "NOT-IN-SOURCE",
                                                 "CONTRADICTED", "UNVERIFIED")}}

    def record_verdict(self, arguments: dict) -> dict:
        fields = ("concept", "claim", "footnotes", "urls", "verdict", "evidence")
        error = None
        if not self.gate_path:
            error = "This session has no configured gate output."
        elif any(not isinstance(arguments.get(k), str) or not arguments[k].strip()
                 for k in ("concept", "claim", "verdict", "evidence")):
            error = "concept, claim, verdict and evidence must be nonempty strings."
        elif arguments["verdict"] not in (
                "SUPPORTED", "NOT-IN-SOURCE", "CONTRADICTED", "UNVERIFIED"):
            error = "Use one of the four gate verdict labels."
        elif any(not isinstance(arguments.get(k), list) or not arguments[k]
                 or any(not isinstance(x, str) for x in arguments[k])
                 for k in ("footnotes", "urls")):
            error = "footnotes and urls must be nonempty string arrays."
        elif any(not re.fullmatch(r"\[\^c\d+-\d+\]", x) for x in arguments["footnotes"]):
            error = "Keep exact footnotes such as [^c1-2], including brackets."
        elif self.references and any(self.references.get(x) not in arguments["urls"]
                                     for x in arguments["footnotes"]):
            error = "Resolve every footnote to its exact URL in the artifact References."
        elif arguments["verdict"] in ("SUPPORTED", "CONTRADICTED"):
            quote = self.quote_text(arguments["evidence"])
            urls = arguments["urls"]
            if arguments["verdict"] == "SUPPORTED" and self.references:
                urls = [self.references[x] for x in arguments["footnotes"]]
            if len(quote) < 15 or not any(
                    quote in self.quote_text(self.source_bodies.get(url, ""))
                    for url in urls):
                error = ("Evidence must preserve the words of a passage "
                         "from a cited URL fetched here "
                         "(Markdown links and emphasis may be omitted). "
                         "Remove commentary/line numbers from the excerpt. Use read_source, "
                         "fetch the cited page, or record UNVERIFIED with a reason.")
        if error:
            return {"isError": True, "content": [{"type": "text", "text": json.dumps({
                "error": error, "progress": self.gate_progress(),
                "instruction": "This verdict was NOT saved. Repair it or record UNVERIFIED. "
                               "Do not stop until sampled=10 and missing is empty."})}]}
        verdict = {k: arguments[k] for k in fields}
        identity = (verdict["concept"], verdict["claim"])
        previous = next((i for i, v in enumerate(self.verdicts)
                         if (v["concept"], v["claim"]) == identity), None)
        if previous is None:
            self.verdicts.append(verdict)
        else:
            self.verdicts[previous] = verdict
        saved = {"sampled": len(self.verdicts), "verdicts": self.verdicts,
                 "notes": [f"Relay fetched {self.fetches} pages; limit {self.limit}. "
                           "Exact source excerpts are checked mechanically; their meaning "
                           "still requires independent review."]}
        temporary = self.gate_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n")
        temporary.chmod(0o600)
        temporary.replace(self.gate_path)
        return {"content": [{"type": "text", "text": json.dumps({
            "saved": True, **self.gate_progress(), "path": str(self.gate_path),
            "instruction": "Continue until sampled=10 and missing is empty. "
                           "Use actual verdict_counts for the final response."})}]}

    @staticmethod
    def schema_scopes(lines: list[str]) -> list[list[tuple[int, str, list[int]]]]:
        """Keep object ownership in API pages rendered as indented property lists."""
        stack: list[tuple[int, str, list[int]]] = []
        scopes = []
        for i, line in enumerate(lines):
            if line.startswith("#"):
                stack.clear()
            if re.fullmatch(r"\s*-\s*", line):
                indent = len(line) - len(line.lstrip())
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                following = [j for j in range(i + 1, min(len(lines), i + 12))
                             if lines[j].strip()][:2]
                if len(following) == 2:
                    label, kind = (lines[j].strip() for j in following)
                    if (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", label)
                            and re.fullmatch(r"object|array|string(?:Discriminator)?|boolean|"
                                             r"integer(?:\([^)]*\))?|number(?:\([^)]*\))?", kind)):
                        context = [i, *following]
                        # Keep the object's purpose, before its first child property.
                        for j in range(following[-1] + 1, min(len(lines), i + 28)):
                            if re.fullmatch(r"\s*-\s*", lines[j]):
                                break
                            if lines[j].strip() and not lines[j].lstrip().startswith("Hide "):
                                context.append(j)
                        stack.append((indent, label, context))
            scopes.append(list(stack))
        return scopes

    def read_source(self, arguments: dict) -> dict:
        path = Path(arguments["source_file"]).resolve()
        if not path.is_relative_to(self.cache.resolve()) or path.suffix != ".json":
            raise ValueError("source_file must be a saved relay source")
        queries = arguments["queries"]
        if (not isinstance(queries, list) or not 1 <= len(queries) <= 12
                or any(not isinstance(q, str) or len(q.strip()) < 3 for q in queries)):
            raise ValueError("provide one to twelve specific queries of at least three characters")

        text = self.source_text(json.loads(path.read_text()))
        lines = text.splitlines()
        context = max(1, min(12, arguments.get("context_lines", 5)))
        scopes = self.schema_scopes(lines)
        matches = [i for i, line in enumerate(lines)
                   if any(q.lower() in line.lower() for q in queries)]
        indices: set[int] = set()
        for i in matches:
            indices.update(range(max(0, i - context), min(len(lines), i + context + 1)))
            for _, _, ownership_lines in scopes[i]:
                indices.update(ownership_lines)
            # Preserve the enclosing Markdown headings, including distant API object paths.
            for level in range(1, 7):
                heading = next((j for j in range(i, -1, -1)
                                if lines[j].startswith("#" * level + " ")), None)
                if heading is not None:
                    indices.add(heading)
        excerpts, used = [], 0
        for i in sorted(indices):
            scope = ".".join(item[1] for item in scopes[i])
            owner = f" [{scope}]" if scope else ""
            line = f"{i + 1}{owner}: {lines[i]}"
            if used + len(line) > 10000:
                break
            excerpts.append(line)
            used += len(line)
        result = {"source_file": str(path), "queries": queries,
                  "total_matches": len(matches), "source_characters": len(text),
                  "truncated": len(excerpts) < len(indices), "excerpts": excerpts}
        return {"content": [{"type": "text", "text": json.dumps(result)}]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--gate-path", type=Path)
    parser.add_argument("--artifact", type=Path)
    args = parser.parse_args()
    proxy = RetrievalProxy(args.config, args.cache, args.limit, args.gate_path, args.artifact)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = proxy.handle(request)
        except Exception as exc:
            # URLs can contain credentials. Never echo exception text or request arguments.
            response = {"jsonrpc": "2.0", "id": locals().get("request", {}).get("id"),
                        "error": {"code": -32603,
                                  "message": f"Retrieval relay failed: {type(exc).__name__}"}}
        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

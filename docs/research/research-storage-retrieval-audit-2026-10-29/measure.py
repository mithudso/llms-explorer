#!/usr/bin/env python3
"""Read-only granularity and lexical-coverage census. Never loads an encoder."""
import argparse
import json
import re
import sqlite3
import statistics
from datetime import UTC, datetime
from pathlib import Path


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return {"count": 0}
    return {"count": len(values), "total": sum(values), "median": statistics.median(values),
            "p95": ordered[int((len(ordered) - 1) * .95)], "max": ordered[-1]}


def measure(repo, hub):
    result = {"version": "1.1.0", "delta": "1.0.0 to 1.1.0: distinguish syntactic suffix removal from semantic metadata; measure separator ambiguity.", "observed_at": datetime.now(UTC).isoformat(),
              "method": "Filesystem reads and SQLite mode=ro/query_only; no inference, fetch, reindex or mutations."}
    lines, payload, removed, missing_citation, files = [], [], [], 0, 0
    ambiguous, alternate_retained = 0, []
    for path in sorted((hub / "llms-concepts").glob("*/llms-facts*.txt")):
        files += 1
        for line in path.read_text(errors="replace").splitlines():
            if not line or line.startswith(("#", ">", "<!--")) or not (line.startswith("- ") or " :: " in line):
                continue
            body = line[2:] if line.startswith("- ") else line.split(" :: ", 1)[1]
            body = re.sub(r"^\[[a-z]+\]\s+", "", body)
            matches = list(re.finditer(r"\s+—\s+(?:https?://|file:|~/|/)", body))
            if matches:
                alternate_retained.append(len(body[:matches[-1].start()]))
                ambiguous += len(matches) > 1
                body = body[:matches[0].start()]
            else:
                missing_citation += 1
                alternate_retained.append(len(body))
            lines.append(len(line))
            payload.append(len(body))
            removed.append(len(line) - len(body))
    result["facts_lines"] = {"files": files, "characters": distribution(lines),
                             "retained_prefix_characters": distribution(payload), "removed_syntax_suffix_characters": distribution(removed),
                             "removed_fraction_first_separator": round(sum(removed) / max(1, sum(lines)), 4),
                             "removed_fraction_last_separator": round((sum(lines) - sum(alternate_retained)) / max(1, sum(lines)), 4),
                             "multiple_source_like_separators": ambiguous,
                             "interpretation": "Syntactic prefix/suffix split only. Embedded citations and compound legacy lines prevent interpreting removed text as pure metadata or retained text as validated atomic claims.",
                             "over_500_chars": sum(n > 500 for n in lines),
                             "over_1000_chars": sum(n > 1000 for n in lines),
                             "over_2000_chars": sum(n > 2000 for n in lines),
                             "without_dash_source": missing_citation}
    keyword = json.loads((repo / "site/public/search-keywords.json").read_text())["items"]
    by_slug = {item["slug"]: item for item in keyword}
    meta = json.loads((repo / "site/src/data/search-meta.json").read_text())
    sizes, embedding_sizes, absent, truncated, cases, facts_count = [], [], 0, 0, [], 0
    db_path = hub / "facts.db"
    connection = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) if db_path.is_file() else None
    if connection:
        connection.execute("PRAGMA query_only=ON")
    try:
        readers = sorted((repo / "site/src/data/concepts").glob("*.json"))
        for path in readers:
            pack = json.loads(path.read_text())
            facts = [f["text"] for facet in pack.get("facets", []) for f in facet.get("facts", [])]
            facts_count += len(facts)
            text = " ".join([pack["concept"], pack.get("summary", ""), *facts])
            sizes.append(len(text))
            embedding_text = ". ".join(value for value in [pack["concept"], pack.get("summary", ""), *facts] if value)
            embedding_sizes.append(len(embedding_text.encode("utf-16-le")) // 2)
            item = by_slug.get(pack["slug"])
            if not item:
                absent += 1
                continue
            indexed = (item["concept"] + " " + item.get("text", item.get("summary", ""))).lower()
            if len(text) > len(item.get("text", "")):
                truncated += 1
            # A literal token present only after the keyword prefix proves a
            # representational miss; it is not a relevance benchmark.
            if len(cases) < 6 and len(text) > 2500:
                late = sorted(set(re.findall(r"[a-z]{9,}", text[2500:].lower())))
                for token in late:
                    if token in indexed:
                        continue
                    hits = None
                    if connection:
                        hits = connection.execute("SELECT count(*) FROM facts WHERE facts MATCH ? AND origin='llms'",
                                                  ('"' + token + '"',)).fetchone()[0]
                    cases.append({"slug": pack["slug"], "late_token": token, "in_full_reader": True,
                                  "in_keyword_record": False, "private_claim_index_hits": hits,
                                  "reader_text_chars": len(text), "indexed_text_chars": len(item.get("text", ""))})
                    break
    finally:
        if connection:
            connection.close()
    result["website"] = {"reader_concepts": len(readers), "reader_facts": facts_count,
                          "keyword_records": len(keyword), "missing_keyword_records": absent,
                          "concepts_with_truncated_keyword_text": truncated,
                          "full_reader_text_characters": distribution(sizes),
                          "over_2000_embedding_input_cap": sum(n > 2000 for n in embedding_sizes),
                          "semantic_rows": meta["count"], "semantic_dimensions": meta["dim"],
                          "semantic_binary_bytes": (repo / "site/public/search-index.bin").stat().st_size,
                          "literal_late_token_probes": cases,
                          "probe_limit": "Literal representation coverage only; no semantic search or judged ranking evaluation."}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    args = parser.parse_args()
    print(json.dumps(measure(args.repo.resolve(), args.hub.resolve()), indent=2))

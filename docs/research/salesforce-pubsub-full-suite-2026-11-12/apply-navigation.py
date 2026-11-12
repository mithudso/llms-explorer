#!/usr/bin/env python3
"""Reapply navigation-only overrides after canonical pack compilation.

Requires llms-txt 0.1.0 installed in the chosen interpreter or available on
PYTHONPATH from an existing checkout. This helper never installs dependencies.
From the repository root:
  python3 docs/research/salesforce-pubsub-full-suite-2026-11-12/apply-navigation.py \
    --packs-root outputs/llms-concepts [--check]
Repeat --packs-root for another installation. All guards for all targets pass
before writing; changed facts, narrative, vocabulary or graph require review.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

try:
    from llms_txt import IndexEntry, render_index
    from llms_txt import __version__ as library_version
    from llms_txt.lint import parse_index
except ImportError as exc:
    raise SystemExit("llms-txt is required: select an interpreter with llms_txt "
                     "installed or set PYTHONPATH to its existing checkout") from exc


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: object) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode())


def authority(manifest: dict) -> str:
    result = copy.deepcopy(manifest)
    result.pop("navigation", None)
    result.get("files", {}).pop("llms.txt", None)
    return digest(result)


def structure(index: dict) -> str:
    return sha(json.dumps({"h1": index["h1"][0][1],
                          "entries": [{k: e[k] for k in ("name", "url", "section")}
                                      for e in index["entries"]]},
                         sort_keys=True, separators=(",", ":")).encode())


def plan(root: Path, item: dict, override_sha: str) -> list[tuple[Path, bytes]]:
    directory = item["directory"]
    if Path(directory).name != directory or not directory.endswith(".llms"):
        raise ValueError(f"invalid pack directory: {directory}")
    pack = root / directory
    protected = {"units.jsonl", "llms-facts.txt", "llms-full.txt", "llms-small.txt",
                 "llms-vocabulary.txt", "concept-graph.json"}
    if set(item["source_files_sha256"]) != protected:
        raise ValueError(f"incomplete source guards: {pack}")
    for name, expected in item["source_files_sha256"].items():
        if Path(name).name != name or sha((pack / name).read_bytes()) != expected:
            raise ValueError(f"changed source layer; review required: {pack / name}")
    manifest_path = pack / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if authority(manifest) != item["manifest_authority_sha256"]:
        raise ValueError(f"changed canonical manifest; review required: {manifest_path}")
    index = parse_index((pack / "llms.txt").read_text())
    if len(index["h1"]) != 1 or index["stray"] or index["fence_open"]:
        raise ValueError(f"unsupported index structure: {pack}")
    if structure(index) != item["entry_structure_sha256"]:
        raise ValueError(f"changed index links/title; review required: {pack}")
    units = [json.loads(line) for line in (pack / "units.jsonl").read_text().splitlines()
             if line.strip()]
    facets = item["facets"]
    if set(facets) != set(manifest["facets"]):
        raise ValueError(f"facet set changed: {pack}")
    notes = {}
    for facet, override in facets.items():
        rows = [row for row in units if row["section"] == facet]
        if len(rows) != manifest["facets"][facet]:
            raise ValueError(f"facet count changed: {pack} {facet}")
        by_id = {row["id"]: row for row in rows}
        if [e["term"] for e in override["term_evidence"]] != override["terms"]:
            raise ValueError(f"term evidence incomplete: {pack} {facet}")
        for binding in override["term_evidence"]:
            text = by_id[binding["unit_id"]]["text"]
            excerpt = text[binding["start"]:binding["end"]]
            if excerpt.casefold() != binding["term"].casefold():
                raise ValueError(f"term not bound to facet source: {pack} {facet}")
        count = len(rows)
        notes[facet] = "; ".join(override["terms"]) + f" — {count} unit" + ("s" if count != 1 else "")
    # Bind descriptions to explicit native targets, independent of JSON key order.
    # Keep every existing title, URL, section and non-facet note unchanged.
    facet_entries = [e for e in index["entries"] if e["section"] == "Facets"]
    if len(facet_entries) != len(facets):
        raise ValueError(f"facet navigation changed: {pack}")
    facet_by_url = {value["entry_url"]: facet for facet, value in facets.items()}
    if set(facet_by_url) != {entry["url"] for entry in facet_entries}:
        raise ValueError(f"facet targets changed: {pack}")
    if any(facets[facet_by_url[e["url"]]]["entry_name"] != e["name"]
           for e in facet_entries):
        raise ValueError(f"facet labels changed: {pack}")
    entries = [IndexEntry(e["name"], e["url"],
                          notes[facet_by_url[e["url"]]] if e["section"] == "Facets" else e["notes"],
                          e["section"], optional=e["section"] == "Optional")
               for e in index["entries"]]
    rendered = render_index(entries, title=index["h1"][0][1], summary=item["summary"],
                            generated=manifest["generated"])
    if structure(parse_index(rendered)) != item["entry_structure_sha256"]:
        raise ValueError(f"native rendering changed index structure: {pack}")
    # Keep manifest.summary and all canonical metadata as compiler authority.
    # The explicit navigation field owns only this index's editorial overrides.
    manifest["navigation"] = {
        "schema": "llms-navigation-overrides/v1",
        "ownership": "hand-maintained-with-explicit-regenerator",
        "summary": item["summary"],
        "facet_notes": notes,
        "override_file": "docs/research/salesforce-pubsub-full-suite-2026-11-12/navigation-overrides.json",
        "override_sha256": override_sha,
        "regenerator": "docs/research/salesforce-pubsub-full-suite-2026-11-12/apply-navigation.py --packs-root <pack-root>",
        "generator_api": ["llms_txt.lint.parse_index", "llms_txt.render_index"],
        "source_units_sha256": item["source_files_sha256"]["units.jsonl"],
        "canonical_compiler": "scripts/codex_dr_artifacts.py::compile_claims",
    }
    manifest["files"]["llms.txt"] = {"bytes": len(rendered.encode()),
                                      "tokens": max(1, len(rendered) // 4)}
    if authority(manifest) != item["manifest_authority_sha256"]:
        raise ValueError(f"navigation edit changed canonical manifest: {pack}")
    return [(pack / "llms.txt", rendered.encode()),
            (manifest_path, (json.dumps(manifest, indent=2) + "\n").encode())]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overrides", type=Path, default=Path(__file__).with_name("navigation-overrides.json"))
    parser.add_argument("--packs-root", action="append", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="verify exact regeneration without writing")
    args = parser.parse_args()
    raw = args.overrides.read_bytes()
    overrides = json.loads(raw)
    if overrides.get("schema") != "salesforce-navigation-overrides/v1":
        raise ValueError("unsupported navigation override schema")
    if library_version != overrides["generator_version"]:
        raise ValueError("llms-txt version changed; review navigation regeneration")
    plans = []
    for root in args.packs_root:
        for item in overrides["packs"]:
            plans.extend(plan(root, item, sha(raw)))
    changed = [path for path, data in plans if path.read_bytes() != data]
    if args.check and changed:
        raise SystemExit("navigation regeneration differs: " + ", ".join(str(p) for p in changed))
    if not args.check:
        for path, data in plans:
            if path.read_bytes() != data:
                path.write_bytes(data)
    print(json.dumps({"mode": "check" if args.check else "apply",
                      "packs": len(plans) // 2, "changed_files": len(changed),
                      "source_guards": "PASS", "canonical_manifest_parity": "PASS"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

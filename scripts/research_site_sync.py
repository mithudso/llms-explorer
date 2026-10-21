#!/usr/bin/env python3
"""Audit or refresh publishable concept research in the website checkout.

The default is read-only. --apply merges the hub tree and renders concept JSON,
tree JSON, context JSON and facts downloads together. Existing website-only
research stays intact. Source-library snapshots and source mirrors never enter
the website. --check exits 1 if generated content needs refreshing.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {path}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value, indent=1, sort_keys=False):
    return json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + "\n"


def nodes_at(path: Path) -> list[dict]:
    value = read_json(path)
    return value if isinstance(value, list) else value.get("nodes", [])


def merge_nodes(destination: list[dict], source: list[dict]) -> list[dict]:
    """Preserve destination placement and stable URLs; merge new evidence."""
    result = copy.deepcopy(destination)
    by_name = {node["concept"]: node for node in result}
    taken = {node.get("slug") for node in result}
    for incoming in source:
        name = incoming["concept"]
        if name not in by_name:
            node = copy.deepcopy(incoming)
            if node.get("slug") in taken:
                owner = next(item["concept"] for item in result if item.get("slug") == node.get("slug"))
                raise ValueError(f"concept slug collision: {node['slug']} ({owner!r} vs {name!r})")
            result.append(node)
            by_name[name] = node
            taken.add(node.get("slug"))
            continue
        node = by_name[name]
        for key in ("childConcepts", "aliases", "slugAliases"):
            if key in incoming:
                node[key] = list(dict.fromkeys([*(node.get(key) or []), *(incoming.get(key) or [])]))
        if "slugAliases" in node:
            node["slugAliases"] = [slug for slug in node["slugAliases"] if slug != node.get("slug")]
        if str(incoming.get("researchedAt") or "") >= str(node.get("researchedAt") or ""):
            for key in ("researchedAt", "sourcesCount", "conceptsCount", "summary", "cvs", "cvsDecision", "cvsScoredAt", "llmsFile"):
                if incoming.get(key) not in (None, ""):
                    node[key] = incoming[key]
    for node in result:
        parent = node.get("parentConcept")
        if parent and parent in by_name:
            children = by_name[parent].setdefault("childConcepts", [])
            if node["concept"] not in children:
                children.append(node["concept"])
    resolved_aliases = {alias.casefold() for node in result for alias in node.get("aliases", [])}
    for node in result:
        node["childConcepts"] = [child for child in node.get("childConcepts", [])
                                 if child in by_name or child.casefold() not in resolved_aliases]
    return result


def search_writes(repo: Path, packs: dict, redirects: dict) -> tuple[dict, dict]:
    """Keep frozen vectors row-aligned; give every pack keyword coverage."""
    writes = {}
    keyword = []
    for slug, pack in sorted(packs.items()):
        facts = [fact["text"] for facet in pack.get("facets", []) for fact in facet.get("facts", [])]
        keyword.append({"slug": slug, "concept": pack["concept"], "summary": pack.get("summary", ""),
                        "text": " ".join([pack["concept"], pack.get("summary", ""), *facts])[:2500]})
    writes[repo / "site/public/search-keywords.json"] = json_text({"items": keyword})
    meta_path = repo / "site/src/data/search-meta.json"
    binary_path = repo / "site/public/search-index.bin"
    indexed = set()
    if meta_path.is_file() and binary_path.is_file():
        meta, binary = read_json(meta_path), binary_path.read_bytes()
        width = meta["dim"] * 4
        if len(binary) != len(meta["items"]) * width or meta["count"] != len(meta["items"]):
            raise ValueError("Existing semantic metadata and vectors are not row-aligned")
        items, vectors = [], []
        for index, item in enumerate(meta["items"]):
            slug = redirects.get(item["slug"], item["slug"])
            if slug not in packs or slug in indexed:
                continue
            indexed.add(slug)
            items.append({**item, "slug": slug, "concept": packs[slug]["concept"]})
            vectors.append(binary[index * width:(index + 1) * width])
        writes[meta_path] = json_text({**meta, "count": len(items), "items": items})
        writes[binary_path] = b"".join(vectors)
    exclusions = {"version": "1.0.0", "items": [
        {"slug": slug, "concept": packs[slug]["concept"],
         "reason": "Semantic indexing and embeddings are paused; keyword search includes this concept."}
        for slug in sorted(set(packs) - indexed)]}
    writes[repo / "site/src/data/search-meta-exclusions.json"] = json_text(exclusions, indent=2)
    return writes, {"keyword_concepts": len(keyword), "existing_semantic_rows": len(indexed),
                    "deferred_semantic_concepts": len(exclusions["items"]), "new_embeddings": 0}


def publication_pack(pack: dict, scrub, terms: list[str]) -> dict:
    """Publish documentation placeholders while retaining private originals."""
    allowed = scrub.gate.allowlist()
    identity_rules = [(name, regex) for name, regex, _ in scrub.gate.COMPILED
                      if name in ("atlas object id", "email inside a path")]

    def clean(value):
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, dict):
            return {key: ("archived:private-reference" if key == "source" and isinstance(item, str)
                          and scrub._matches(item, terms) else clean(item))
                    for key, item in value.items()}
        if not isinstance(value, str):
            return value
        value, _ = scrub.scrub_home_paths(value)
        value, _ = scrub.scrub_addresses(value, terms)
        # JSON escapes a quote after an example email as a backslash. The
        # publication gate correctly treats that shape as a possible path.
        value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                       lambda match: match.group() if scrub.gate.RESERVED.search(match.group())
                       else "user@example.test", value)
        for name, regex in identity_rules:
            def replace(match, name=name):
                if any(item in match.group() for item in allowed) or scrub.gate.RESERVED.search(match.group()):
                    return match.group()
                return "<object-id>" if name == "atlas object id" else "/user@example.test/"
            value = regex.sub(replace, value)
        return value

    return clean(pack)


def plan(repo: Path, hub: Path, merge_tree: bool = True, current_run: str | None = None,
         withheld: tuple | list = ()) -> tuple[dict, dict[Path, str]]:
    sys.path.insert(0, str(repo / "scripts"))
    scrub = module("research_site_scrub", repo / "scripts/publish_scrub.py")
    concepts = module("research_site_concepts", repo / "site/tools/gen_concepts.py")
    tree = module("research_site_tree", repo / "site/tools/gen_tree.py")
    context = module("research_site_context", repo / "site/tools/gen_context.py")
    facts = module("research_site_facts", repo / "site/tools/gen_concept_facts.py")
    current_nodes = nodes_at(repo / "concept-tree/tree.json")
    hub_nodes = nodes_at(hub / "concept-tree/tree.json")
    tree_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in (repo / "concept-tree/tree.json", hub / "concept-tree/tree.json")}
    safe_hub, excluded, removed_refs = scrub.filter_tree(hub_nodes, scrub.gate.denylist())
    safe_repo, excluded_repo, _ = scrub.filter_tree(current_nodes, scrub.gate.denylist())
    merged = merge_nodes(safe_repo, safe_hub) if merge_tree else safe_repo
    baseline_errors = set(tree.ct.ConceptTree(current_nodes).validate())
    added_errors = set(tree.ct.ConceptTree(merged).validate()) - baseline_errors
    if added_errors:
        raise ValueError("concept tree merge adds problems: " + "; ".join(sorted(added_errors)))
    safe_names = {node["concept"] for node in safe_hub}
    excluded_names = set(excluded) | set(excluded_repo)
    recovery = module("research_site_recovery", repo / "scripts/recover_dr_packs.py")
    recovered_writes, recovered_packs, recovery_report = recovery.plan(repo, hub, safe_hub, module, scrub, current_run)
    site_packs = {path.stem: read_json(path) for path in (repo / "site/src/data/concepts").glob("*.json")}
    selected = {slug: pack for slug, pack in site_packs.items()
                if not scrub._matches(pack["concept"], scrub.gate.denylist())}
    excluded_pack_slugs = set(site_packs) - set(selected)
    classifications, stale, new, conflicts = {}, [], [], []
    owners = {node["slug"]: node for node in [*merged, *safe_hub]}
    title_normalizations = []
    inputs = {}
    for root in (repo / "outputs/llms-concepts", hub / "llms-concepts"):
        for path in sorted(root.glob("*.llms")):
            candidate = concepts.build_one(path)
            if candidate is None or not candidate.get("facets"):
                classifications[str(path.relative_to(root))] = "non-renderable"
                continue
            if candidate["concept"] in excluded_names or scrub._matches(candidate["concept"], scrub.gate.denylist()):
                classifications[path.name] = "excluded"
                continue
            slug = candidate["slug"]
            previous = selected.get(slug)
            if previous and previous["concept"].casefold() != candidate["concept"].casefold():
                owner = owners.get(slug)
                if owner and owner["concept"].casefold() in (previous["concept"].casefold(), candidate["concept"].casefold()):
                    title_normalizations.append({"slug": slug, "pack_title": candidate["concept"], "tree_concept": owner["concept"]})
                    candidate = {**candidate, "concept": owner["concept"]}
                else:
                    conflicts.append(slug)
                    continue
            # An older pack cannot replace a newer committed research result.
            if previous and str(candidate.get("generated") or "") < str(previous.get("generated") or ""):
                classifications[path.name] = "older-than-website"
                continue
            count_facts = lambda value: sum(len(facet.get("facts", [])) for facet in value.get("facets", []))
            if (previous and candidate.get("generated") == previous.get("generated")
                    and count_facts(candidate) < count_facts(previous)):
                classifications[path.name] = "same-date-richer-website"
                continue
            selected[slug] = candidate
            inputs[slug] = path
    identity_by_slug = {node["slug"]: node["concept"].casefold() for node in [*safe_hub, *merged]}
    existing_identities = {identity_by_slug.get(slug, pack["concept"].casefold()) for slug, pack in selected.items()}
    current_slugs = {row["slug"] for row in recovery_report["recovered_packs"] if row["run"] == current_run}
    for slug, pack in recovered_packs.items():
        identity = identity_by_slug.get(slug, pack["concept"].casefold())
        if slug in current_slugs or (slug not in selected and identity not in existing_identities):
            selected[slug] = pack
    if conflicts:
        raise ValueError("website pack identity conflicts: " + ", ".join(sorted(set(conflicts))))
    # A facts download without a node otherwise advertises a /tree/<slug>/
    # URL that Astro never builds. Register evidence-backed packs, or attach
    # an alternate pack slug to its existing named node without a duplicate.
    by_name = {node["concept"].casefold(): node for node in merged}
    by_slug = {node["slug"]: node for node in merged}
    hub_by_slug = {node["slug"]: node for node in safe_hub}
    aliases = {alias.casefold(): node for node in merged for alias in node.get("aliases", [])}
    registrations, pack_aliases = [], {}
    for slug, pack in list(selected.items()):
        if slug in by_slug:
            continue
        hub_owner = hub_by_slug.get(slug)
        node = (by_name.get(pack["concept"].casefold()) or aliases.get(pack["concept"].casefold())
                or (by_name.get(hub_owner["concept"].casefold()) if hub_owner else None))
        if node:
            canonical = node["slug"]
            previous = selected.get(canonical)
            count = lambda value: sum(len(facet.get("facts", [])) for facet in value.get("facets", []))
            if (previous is None or str(pack.get("generated") or "") > str(previous.get("generated") or "")
                    or (pack.get("generated") == previous.get("generated") and count(pack) > count(previous))):
                selected[canonical] = {**pack, "slug": canonical, "concept": node["concept"]}
            node["slugAliases"] = list(dict.fromkeys([*(node.get("slugAliases") or []), slug]))
            pack_aliases[slug] = canonical
            del selected[slug]
            continue
        parents = sorted(node["concept"] for node in merged if pack["concept"] in node.get("childConcepts", []))
        parent = parents[0] if parents else ("Global AI Hub Research Corpus" if "global ai hub research corpus" in by_name else None)
        node = {"concept": pack["concept"], "slug": slug, "skillId": None,
                "parentConcept": parent, "childConcepts": [], "aliases": [],
                "researchedAt": pack.get("generated") or None,
                "sourcesCount": len({fact.get("source") for facet in pack["facets"] for fact in facet["facts"]}),
                "conceptsCount": 1}
        merged.append(node)
        by_name[node["concept"].casefold()] = node
        by_slug[slug] = node
        registrations.append(slug)
        if parent:
            parent_node = by_name[parent.casefold()]
            parent_node["childConcepts"] = list(dict.fromkeys([*parent_node.get("childConcepts", []), node["concept"]]))
    added_errors = set(tree.ct.ConceptTree(merged).validate()) - baseline_errors
    if added_errors:
        raise ValueError("pack registration adds tree problems: " + "; ".join(sorted(added_errors)))
    selected = {slug: publication_pack(pack, scrub, [*scrub.gate.denylist(), *withheld]) for slug, pack in selected.items()}
    writes = dict(recovered_writes)
    for slug, pack in selected.items():
        if slug not in site_packs:
            new.append(slug)
        elif pack != site_packs[slug]:
            stale.append(slug)
        writes[repo / f"site/src/data/concepts/{slug}.json"] = json_text(pack, indent=2)
    # Generate against the complete planned snapshot before changing real files.
    with tempfile.TemporaryDirectory(prefix="research-site-plan-") as temporary:
        staged = Path(temporary)
        (staged / "concept-tree").mkdir()
        (staged / "concept-tree/tree.json").write_text(json_text(merged, indent=2))
        for name in ("RESEARCH_QUEUE.md", "cvs-scores.json", "skill-summaries.json"):
            source = repo / "concept-tree" / name
            if source.is_file():
                shutil.copy2(source, staged / "concept-tree" / name)
        # New Codex skills are local runtime artifacts. Vendor their summaries
        # so an isolated CI checkout reproduces the same generated tree.
        summary_path = repo / "concept-tree/skill-summaries.json"
        summaries = read_json(summary_path) if summary_path.is_file() else {}
        for node in merged:
            skill_id = node.get("skillId")
            if skill_id and (repo / ".agents/skills" / skill_id / "SKILL.md").is_file():
                summaries[skill_id] = tree.skill_summary(repo, skill_id, {})
        if summaries:
            summary_text = json_text(summaries, indent=2)
            (staged / "concept-tree/skill-summaries.json").write_text(summary_text)
            writes[summary_path] = summary_text
        for name in (".claude", ".agents"):
            if (repo / name).exists():
                (staged / name).symlink_to(repo / name, target_is_directory=True)
        staged_packs = staged / "packs"
        staged_packs.mkdir()
        for slug, pack in selected.items():
            (staged_packs / f"{slug}.json").write_text(json_text(pack, indent=2))
        tree_data = tree.build(staged, concepts_dir=staged_packs)
        staged_tree = staged / "tree.json"
        staged_tree.write_text(json_text(tree_data, sort_keys=True))
        context_data = context.build(None, staged_packs, staged_tree)
        search_changes, search_report = search_writes(repo, selected, tree_data.get("redirects", {}))
        writes.update(search_changes)
        writes[repo / "site/src/data/tree.json"] = json.dumps(tree_data, indent=1, sort_keys=True) + "\n"
        writes[repo / "site/src/data/context.json"] = json_text(context_data, sort_keys=True)
        for slug, pack in selected.items():
            writes[repo / f"site/public/downloads/concepts/{slug}.md"] = facts.render_pack(
                pack, tree_data["nodes"], facts.DEFAULT_SITE_URL, repo / "site/src/content/sources")
    if merged != current_nodes:
        writes[repo / "concept-tree/tree.json"] = json_text(merged, indent=2)
    # Pack-only research becomes discoverable in the runtime tree too. Keep
    # private hub nodes and each tree's independent placement and stable URLs.
    merged_hub = merge_nodes(hub_nodes, merged)
    if merged_hub != hub_nodes:
        writes[hub / "concept-tree/tree.json"] = json_text(merged_hub, indent=2)
    changes = {path: text for path, text in writes.items()
               if not path.is_file() or path.read_bytes() != (text if isinstance(text, bytes) else text.encode())}
    report = {"hub_nodes": len(hub_nodes), "repository_nodes_before": len(current_nodes),
              "repository_nodes_after": len(merged), "excluded_private_nodes": len(excluded),
              "excluded_child_references": removed_refs,
              "hub_only_publishable_nodes": sorted(safe_names - {node["concept"] for node in current_nodes}),
              "website_packs_before": len(site_packs), "website_packs_after": len(selected),
              "new_website_packs": sorted(new), "changed_website_packs": sorted(stale),
              "preserved_website_only_packs": len(set(site_packs) - set(inputs)),
              "registered_pack_nodes": registrations, "pack_slug_aliases": pack_aliases,
              "pack_title_normalizations": title_normalizations,
              "pack_classifications": classifications,
              "unfiled_website_packs": sorted(set(selected) - set(tree_data["nodes"])),
              "tree_validation_problems": sorted(baseline_errors),
              "website_totals": context_data["totals"],
              "search": search_report,
              "tree_input_hashes": tree_hashes, "dr_recovery": recovery_report,
              "changed_files": [str(path.relative_to(repo)) if path.is_relative_to(repo) else "hub/" + str(path.relative_to(hub)) for path in changes]}
    # Obsolete data copies would otherwise re-enter context.json on the next
    # CI generation. Their URLs redirect and their original bodies are backed up.
    for slug in set(pack_aliases) | excluded_pack_slugs:
        for path in (repo / f"site/src/data/concepts/{slug}.json",
                     repo / f"site/public/downloads/concepts/{slug}.md"):
            if path.exists():
                changes[path] = None
    report["changed_files"] = [str(path.relative_to(repo)) if path.is_relative_to(repo) else "hub/" + str(path.relative_to(hub)) for path in changes]
    return report, changes


def sync(repo: Path, hub: Path, apply: bool = False, merge_tree: bool = True, current_run: str | None = None) -> dict:
    # This serializes CFE, /dr, suite and batch writers' website refreshes.
    lock_path = repo / "tmp/research-site-sync.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        reference_cache = hub / "research/.site-public-references.json"
        withheld = [key for key, value in read_json(reference_cache).items() if not value["public"]] if reference_cache.is_file() else []
        for attempt in range(3):
            report, changes = plan(repo, hub, merge_tree, current_run, withheld)
            if not apply or all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
                                for path, digest in report["tree_input_hashes"].items()):
                break
        else:
            raise ValueError("concept trees kept changing during refresh; retry when the current writer finishes")
        if apply:
            verifier_path = repo / "scripts/public_research_references.py"
            if verifier_path.is_file():
                verifier = module("research_public_references", verifier_path)
                reference_writes, newly_withheld = verifier.resolve(repo, hub, changes)
                if set(newly_withheld) != set(withheld):
                    report, changes = plan(repo, hub, merge_tree, current_run, newly_withheld)
                changes.update(reference_writes)
            if not all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
                       for path, digest in report["tree_input_hashes"].items()):
                raise ValueError("A concept tree changed during reference verification; retry the refresh")
        report["changed_files"] = [str(path.relative_to(repo)) if path.is_relative_to(repo) else "hub/" + str(path.relative_to(hub)) for path in changes]
        report["applied"] = apply
        if apply and changes:
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
            backup = repo / "tmp/research-site-sync-backups" / stamp
            for path in changes:
                if path.exists():
                    saved = backup / (Path("repository") / path.relative_to(repo) if path.is_relative_to(repo)
                                      else Path("hub") / path.relative_to(hub))
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, saved)
            for path, text in changes.items():
                if text is None:
                    path.unlink(missing_ok=True)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_name(path.name + ".research-sync-tmp")
                if isinstance(text, bytes):
                    temporary.write_bytes(text)
                else:
                    temporary.write_text(text, encoding="utf-8")
                temporary.replace(path)
            report["backup"] = str(backup.relative_to(repo))
        return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-merge-tree", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--run", help="just-finished DR run whose claims may update its existing packs")
    args = parser.parse_args(argv)
    if args.apply and args.check:
        parser.error("--apply and --check are mutually exclusive")
    try:
        report = sync(args.repo.resolve(), args.hub.expanduser().resolve(), args.apply, not args.no_merge_tree, args.run)
    except (OSError, ValueError) as error:
        parser.exit(2, f"research site refresh failed: {error}\n")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json_text(report, indent=2))
    print(json.dumps({"applied": report["applied"], "hub_nodes": report["hub_nodes"],
                      "repository_nodes": report["repository_nodes_after"],
                      "website_packs": report["website_packs_after"], "facts": report["website_totals"]["facts"],
                      "changed_files": len(report["changed_files"]),
                      "recovered_dr_packs": len(report["dr_recovery"]["recovered_packs"]),
                      "unfiled": len(report["unfiled_website_packs"])}))
    return 1 if args.check and report["changed_files"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

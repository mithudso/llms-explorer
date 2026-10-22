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
        owner = next((node for node in result if node.get("slug") == incoming.get("slug")), None)
        if name not in by_name and owner:
            if owner["concept"].casefold() in {alias.casefold() for alias in incoming.get("aliases", [])}:
                old = owner["concept"]
                owner["concept"] = name
                owner["aliases"] = list(dict.fromkeys([*owner.get("aliases", []), old]))
                by_name.pop(old)
                by_name[name] = owner
            elif name.casefold() in {alias.casefold() for alias in owner.get("aliases", [])}:
                name = owner["concept"]
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
    canonical = {alias: node["concept"] for node in result for alias in node.get("aliases", [])
                 if alias not in by_name}
    for node in result:
        if node.get("parentConcept") in canonical:
            node["parentConcept"] = canonical[node["parentConcept"]]
        node["childConcepts"] = list(dict.fromkeys(canonical.get(child, child)
                                                   for child in node.get("childConcepts", [])))
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
            items.append({**item, "slug": slug, "concept": packs[slug]["concept"],
                          "summary": packs[slug].get("summary", "")})
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

    def clean(value):
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, dict):
            return {clean(key): ("archived:private-reference" if key == "source" and isinstance(item, str)
                          and scrub._matches(item, terms) else clean(item))
                    for key, item in value.items()}
        if not isinstance(value, str):
            return value
        return scrub.scrub_public_text(value, terms, allowed)

    return clean(pack)


def plan(repo: Path, hub: Path, merge_tree: bool = True, current_run: str | None = None,
         withheld: tuple | list = (), authoritative_slugs=()) -> tuple[dict, dict[Path, str]]:
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
    excluded_names = set()
    identities = [({node["concept"], *(node.get("aliases") or [])},
                   {slug for slug in [node.get("slug"), *(node.get("slugAliases") or [])] if slug})
                  for node in [*hub_nodes, *current_nodes]]
    # Follow private descendants across either tree until their different
    # parent/child placements no longer add another excluded identity.
    while True:
        safe_hub, excluded, removed_refs = scrub.filter_tree(hub_nodes, scrub.gate.denylist(), excluded_names)
        safe_repo, excluded_repo, _ = scrub.filter_tree(current_nodes, scrub.gate.denylist(), excluded_names)
        discovered = set(excluded) | set(excluded_repo)
        known = {name.casefold() for name in discovered | excluded_names}
        private_slugs = set()
        for names, slugs in identities:
            if known & {name.casefold() for name in names}:
                discovered.update(names)
                private_slugs.update(slugs)
        for names, slugs in identities:
            if slugs & private_slugs:
                discovered.update(names)
        if discovered <= excluded_names:
            break
        excluded_names.update(discovered)
    merged = merge_nodes(safe_repo, safe_hub) if merge_tree else safe_repo
    baseline_errors = set(tree.ct.ConceptTree(current_nodes).validate())
    added_errors = set(tree.ct.ConceptTree(merged).validate()) - baseline_errors
    if added_errors:
        raise ValueError("concept tree merge adds problems: " + "; ".join(sorted(added_errors)))
    safe_names = {node["concept"] for node in safe_hub}
    excluded_identities = {name.casefold() for name in excluded_names}
    excluded_slugs = {slug for names, slugs in identities for slug in slugs
                      if excluded_identities & {name.casefold() for name in names}}
    recovery = module("research_site_recovery", repo / "scripts/recover_dr_packs.py")
    recovered_writes, recovered_packs, recovery_report = recovery.plan(
        repo, hub, safe_hub, module, scrub, current_run, excluded_names, withheld,
        excluded_slugs=excluded_slugs)
    authoritative_slugs = set(authoritative_slugs) | set(recovery_report.get("current_run_slugs", [])) | {
        row["slug"] for row in recovery_report["recovered_packs"] if row["run"] == current_run}
    def private_pack(pack):
        return (pack["concept"].casefold() in excluded_identities or pack["slug"] in excluded_slugs
                or scrub._matches(pack["concept"] + " " + pack["slug"], scrub.gate.denylist()))
    site_packs = {path.stem: read_json(path) for path in (repo / "site/src/data/concepts").glob("*.json")}
    selected = {slug: pack for slug, pack in site_packs.items()
                if not private_pack(pack)}
    excluded_pack_slugs = set(site_packs) - set(selected)
    classifications, stale, new, conflicts = {}, [], [], []
    owners = {node["slug"]: node for node in [*merged, *safe_hub]}
    title_normalizations = []
    inputs, excluded_repository_packs = {}, []
    for root in (repo / "outputs/llms-concepts", hub / "llms-concepts"):
        for path in sorted(root.glob("*.llms")):
            if root == repo / "outputs/llms-concepts" and path.stem in excluded_slugs:
                excluded_repository_packs.append(path)
                classifications[path.name] = "excluded"
                continue
            candidate = concepts.build_one(path)
            if candidate is None or not candidate.get("facets"):
                classifications[str(path.relative_to(root))] = "non-renderable"
                continue
            if private_pack(candidate):
                classifications[path.name] = "excluded"
                if root == repo / "outputs/llms-concepts":
                    excluded_repository_packs.append(path)
                continue
            slug = candidate["slug"]
            previous = selected.get(slug)
            owner = owners.get(slug)
            compatible_owner = owner and owner["concept"].casefold() in (
                (previous["concept"].casefold(), candidate["concept"].casefold())
                if previous else (candidate["concept"].casefold(),))
            if previous and previous["concept"].casefold() != candidate["concept"].casefold() and not compatible_owner:
                conflicts.append(slug)
                continue
            if owner and candidate["concept"] != owner["concept"] and (
                    previous is None or compatible_owner):
                title_normalizations.append({"slug": slug, "pack_title": candidate["concept"], "tree_concept": owner["concept"]})
                candidate = {**candidate, "concept": owner["concept"]}
            # An older pack cannot replace a newer committed research result.
            if previous and str(candidate.get("generated") or "") < str(previous.get("generated") or ""):
                classifications[path.name] = "older-than-website"
                continue
            count_facts = lambda value: sum(len(facet.get("facts", [])) for facet in value.get("facets", []))
            if (previous and candidate.get("generated") == previous.get("generated")
                    and count_facts(candidate) < count_facts(previous) and slug not in authoritative_slugs):
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
            selected[slug] = {**selected[slug], "concept": by_slug[slug]["concept"]}
            continue
        hub_owner = hub_by_slug.get(slug)
        node = (by_name.get(pack["concept"].casefold()) or aliases.get(pack["concept"].casefold())
                or (by_name.get(hub_owner["concept"].casefold()) if hub_owner else None))
        if node:
            canonical = node["slug"]
            previous = selected.get(canonical)
            count = lambda value: sum(len(facet.get("facts", [])) for facet in value.get("facets", []))
            if (slug in authoritative_slugs or previous is None or str(pack.get("generated") or "") > str(previous.get("generated") or "")
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
    # Preserve private hub prose before creating the repository-bound copy.
    merged_hub = merge_nodes(hub_nodes, merged)
    for node in merged:
        if node.get("summary"):
            node["summary"] = scrub.scrub_public_text(str(node["summary"]),
                                                      [*scrub.gate.denylist(), *withheld])
    selected = {slug: publication_pack(pack, scrub, [*scrub.gate.denylist(), *withheld]) for slug, pack in selected.items()}
    writes = dict(recovered_writes)
    writes.update({path: None for path in excluded_repository_packs})
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
        summaries = {key: tree.publication_summary(value, [*scrub.gate.denylist(), *withheld])
                     for key, value in (read_json(summary_path) if summary_path.is_file() else {}).items()}
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
        download_texts = facts.download_texts(selected, tree_data["nodes"], tree_data.get("redirects", {}),
                                              facts.DEFAULT_SITE_URL, repo / "site/src/content/sources")
        for slug, text in download_texts.items():
            writes[repo / f"site/public/downloads/concepts/{slug}.md"] = text
        for path in (repo / "site/public/downloads/concepts").glob("*.md"):
            if path.stem not in download_texts:
                writes[path] = None
    if merged != current_nodes:
        writes[repo / "concept-tree/tree.json"] = json_text(merged, indent=2)
    # Pack-only research becomes discoverable in the runtime tree too. Keep
    # private hub nodes and each tree's independent placement and stable URLs.
    if merged_hub != hub_nodes:
        writes[hub / "concept-tree/tree.json"] = json_text(merged_hub, indent=2)
    changes = {path: text for path, text in writes.items()
               if (text is None and path.exists()) or
               (text is not None and (not path.is_file() or
                path.read_bytes() != (text if isinstance(text, bytes) else text.encode())))}
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
        paths = [repo / f"site/src/data/concepts/{slug}.json"]
        if slug in excluded_pack_slugs:
            paths.append(repo / f"site/public/downloads/concepts/{slug}.md")
        for path in paths:
            if path.exists():
                changes[path] = None
    report["changed_files"] = [str(path.relative_to(repo)) if path.is_relative_to(repo) else "hub/" + str(path.relative_to(hub)) for path in changes]
    return report, changes


def sync(repo: Path, hub: Path, apply: bool = False, merge_tree: bool = True,
         current_run: str | None = None, authoritative_slugs=()) -> dict:
    # This serializes CFE, /dr, suite and batch writers' website refreshes.
    lock_path = repo / "tmp/research-site-sync.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        reference_cache = hub / "research/.site-public-references.json"
        withheld = [key for key, value in read_json(reference_cache).items() if not value["public"]] if reference_cache.is_file() else []
        for attempt in range(3):
            report, changes = plan(repo, hub, merge_tree, current_run, withheld, authoritative_slugs)
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
                    report, changes = plan(repo, hub, merge_tree, current_run, newly_withheld, authoritative_slugs)
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
                    if path.is_dir():
                        shutil.copytree(path, saved, symlinks=True)
                    else:
                        shutil.copy2(path, saved)
            for path, text in changes.items():
                if text is None:
                    if path.is_dir() and not path.is_symlink():
                        shutil.rmtree(path)
                    else:
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

#!/usr/bin/env python3
"""Compile recorded DR claims and merge both local concept trees before finish."""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path

PACK_FILES = ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
              "llms-vocabulary.txt", "units.jsonl", "concept-graph.json", "manifest.json")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load DR artifact dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repository() -> Path:
    configured = os.environ.get("LLMS_EXPLORER_REPO")
    if configured:
        return Path(configured).expanduser().resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts/sync_codex_research_skills.py").is_file():
            return parent
    return Path.home() / "dev/llms-explorer"


def compile_claims(lca, out: Path, name: str, slug: str, docs: list[dict], status: str) -> None:
    """Use the existing compiler with trusted rows; no lossy text re-harvest."""
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc in docs:
        for claim in doc["claims"]:
            urls = claim["sources"]
            if not urls or any(not url.startswith(("https://", "http://")) for url in urls):
                raise ValueError(f"{doc['concept']}: llms claims require original HTTP source URLs")
            text = f"{claim['text']} ({claim['confidence']} confidence)"
            if claim.get("verified_as_of"):
                text += f" (verified as of {claim['verified_as_of']})"
            row = lca._unit(f"dr{len(rows) + 1:06d}", "statement", text, urls[0],
                            heading=f"{doc['concept']} > {claim.get('section', 'core')}",
                            keywords=[doc["concept"]], origin="dr", also=urls[1:])
            row.update(matched=[name], relations=["about"], relation="about", score=1.0,
                       facet=lca.heuristic_facet(row), keep=True)
            rows.append(row)
    compile_rows(lca, out, name, slug, rows,
                 {"summary": f"Source-anchored research for {name}. Run status: {status}.", "research_status": status})


def compile_rows(lca, out: Path, name: str, slug: str, rows: list[dict], metadata: dict) -> None:
    """Compile authored synthesis, preserving statements and research dates."""
    out.mkdir(parents=True, exist_ok=True)
    rows = [dict(row, matched=[name], relations=[row.get("relation", "about")],
                 facet=row.get("facet", row.get("section", "facts")), keep=True) for row in rows]
    (out / "pool.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    lexicon = {"concept": name, "slug": slug,
               "terms": [{"term": name, "relation": "self"}], "exclude": []}
    lexicon_path = out / "lexicon.json"
    lexicon_path.write_text(json.dumps(lexicon))
    with redirect_stdout(io.StringIO()):
        lca.main(["compile", "--out", str(out), "--concept", name,
                  "--lexicon", str(lexicon_path), "--keep-lead-ins",
                  "--rights", "quote", "--budget-tokens", str(metadata.get("budget_tokens", 8000)),
                  "--summary", metadata.get("summary", f"Source-anchored research for {name}.")])
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["kept_units"] != len(rows):
        raise ValueError(f"{name}: llms compilation lost claims ({len(rows)} -> {manifest['kept_units']})")
    full = (out / "llms-full.txt").read_text()
    for row in rows:
        if re.sub(r"\s+", " ", row["text"]).strip() not in full:
            raise ValueError(f"{name}: llms compilation clipped claim {row['id']}")
    # The compiler lists undefined terms twice: as unsourced bold entries and
    # in its explicit research-gap section. Keep the gap section, so a missing
    # definition never masquerades as a sourced vocabulary entry (lint C6).
    vocabulary_path = out / "llms-vocabulary.txt"
    vocabulary = "\n".join(line for line in vocabulary_path.read_text().splitlines()
                           if not (line.startswith("- **") and not re.search(r"https?://", line))) + "\n"
    vocabulary_path.write_text(vocabulary)
    manifest["files"]["llms-vocabulary.txt"] = {"bytes": len(vocabulary.encode()),
                                                 "tokens": lca._tokens_of(vocabulary)}
    generated = metadata.get("generated", manifest["generated"])
    for filename in PACK_FILES:
        if filename.endswith(".txt"):
            path = out / filename
            path.write_text(path.read_text().replace("· generated " + manifest["generated"], "· generated " + generated))
    graph = json.loads((out / "concept-graph.json").read_text())
    graph["generated"] = generated
    (out / "concept-graph.json").write_text(json.dumps(graph, indent=1, ensure_ascii=False) + "\n")
    manifest.update({key: value for key, value in metadata.items() if key not in manifest})
    manifest["generated"] = generated
    for filename in manifest["files"]:
        text = (out / filename).read_text()
        manifest["files"][filename] = {"bytes": len(text.encode()), "tokens": lca._tokens_of(text)}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    if any(not (out / filename).is_file() for filename in PACK_FILES):
        raise ValueError(f"{name}: llms compiler did not produce all required files")


def public_pack_files(repo: Path, hub: Path, files: dict, lca, withheld=()) -> dict:
    """Recompile a publication-safe copy; leave private inputs untouched."""
    scrub = load_module("codex_pack_scrub", repo / "scripts/publish_scrub.py")
    website = load_module("codex_pack_publication", repo / "scripts/research_site_sync.py")
    cache = hub / "research/.site-public-references.json"
    blocked = set(withheld)
    if cache.is_file():
        blocked.update(key for key, value in json.loads(cache.read_text()).items() if not value["public"])
    terms = [*scrub.gate.denylist(), *blocked]
    metadata = website.publication_pack(json.loads(files["manifest.json"]), scrub, terms)
    rows = [website.publication_pack(json.loads(line), scrub, terms)
            for line in files["units.jsonl"].splitlines() if line.strip()]
    if not rows or any(row.get("origin") != "dr" for row in rows):
        raise ValueError("Repository claim export requires authored DR units")
    with tempfile.TemporaryDirectory(prefix="public-dr-pack-") as temporary:
        out = Path(temporary)
        compile_rows(lca, out, metadata["concept"], metadata["slug"], rows, metadata)
        return {filename: (out / filename).read_text() for filename in PACK_FILES}


def finalize_artifacts(shared, manifest: dict, claims: dict[str, dict], status: str,
                       repo: Path | None = None) -> dict:
    """Back up and merge each tree independently; mirror packs in both roots.

    Callers hold the run lock. The global DR lock serializes this operation with
    other DR finish operations. Existing tree placement and slugs win.
    """
    if not claims:
        return {"ok": True, "skipped": "no recorded claims", "packs": [], "trees": []}
    repo = repo or repository()
    sys.path.insert(0, str(repo / "scripts"))
    lca = load_module("codex_dr_lca", repo / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py")
    sync = load_module("codex_dr_tree_sync", repo / "scripts/codex_research_assets/concept-family-explorer/scripts/sync_trees.py")
    scrub = load_module("codex_dr_publication_scrub", repo / "scripts/publish_scrub.py")
    ct = shared.concept_tree
    run = shared.run_dir(manifest["slug"])
    tree_paths = {"hub": shared.HUB_DIR / "concept-tree/tree.json",
                  "repository": repo / "concept-tree/tree.json"}
    topic = manifest["topic"]
    by_name = {doc["concept"]: doc for doc in claims.values()}
    cohort_parent = manifest.get("cohort_parent")
    documents = ({name: [doc] for name, doc in by_name.items()} if cohort_parent else
                 {topic: list(claims.values()),
                  **{name: [doc] for name, doc in by_name.items() if name != topic}})
    today = shared._today()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = run / "artifacts/backups" / stamp

    with shared.locked(shared.RESEARCH_DIR / ".global.lock"):
        planned, jobs = {}, {}
        for label, path in tree_paths.items():
            if not path.is_file():
                raise ValueError(f"DR artifact tree not found: {path}")
            before = ct.load_nodes(path)
            after = copy.deepcopy(before)
            existing = {node["concept"]: node for node in before}
            for name, docs in documents.items():
                children = [child for doc in docs for child in doc.get("child_concepts", [])]
                if name == topic:
                    children += [child for child in by_name if child != topic]
                # Keep each target's curated placement. Only new nodes receive
                # the run's proposed parent, and sync.upsert handles missing parents.
                parent = existing[name].get("parentConcept") if name in existing else (
                    cohort_parent or (manifest.get("parent_concept") if name == topic else topic))
                skill_id = manifest.get("skill_id") or manifest["slug"]
                if manifest.get("kind") == "spoke" and manifest.get("hub"):
                    skill_id = f"{manifest['hub']}/references/{skill_id}.md"
                sync.upsert(ct, after, {
                    "concept": name, "skillId": skill_id if ct.skill_paths(skill_id) else None,
                    "parentConcept": parent, "childConcepts": children,
                    "aliases": manifest.get("aliases", []) if name == topic else [],
                    "sourcesCount": len({url for doc in docs for claim in doc["claims"] for url in claim["sources"]}),
                    "conceptsCount": len(docs), "researchedAt": today,
                }, today)
            for node in after:
                if node["concept"] in documents:
                    slug = node["slug"]
                    if slug in jobs and jobs[slug] != node["concept"]:
                        raise ValueError(f"DR pack slug collision: {slug}")
                    jobs[slug] = node["concept"]
                    node["llmsFile"] = f"{slug}.llms/llms-facts.txt"
            # Preserve init --alias semantics for frontier placeholders in
            # both trees. A name with its own researched node stays intact.
            known_names = {node["concept"] for node in after}
            consumed = set(manifest.get("aliases", [])) - known_names
            for node in after:
                node["childConcepts"] = [child for child in node.get("childConcepts", [])
                                         if child not in consumed]
            new_problems = set(ct.ConceptTree(after).validate()) - set(ct.ConceptTree(before).validate())
            if len(after) < len(before) or new_problems:
                raise ValueError(f"DR tree merge refused for {path}: {sorted(new_problems)}")
            planned[label] = before, after

        private_names = set()
        if scrub._matches(" ".join(filter(None, (topic, cohort_parent, manifest.get("parent_concept")))), scrub.gate.denylist()):
            private_names.update(documents)
        while True:
            discovered = set()
            for _, after in planned.values():
                _, excluded, _ = scrub.filter_tree(after, scrub.gate.denylist(), private_names)
                discovered.update(excluded)
            if discovered <= private_names:
                break
            private_names.update(discovered)
        before, after = planned["repository"]
        public_after, _, _ = scrub.filter_tree(after, scrub.gate.denylist(), private_names)
        public_before, _, _ = scrub.filter_tree(before, scrub.gate.denylist(), private_names)
        problems = set(ct.ConceptTree(public_after).validate()) - set(ct.ConceptTree(before).validate())
        if len(public_after) < len(public_before) or problems:
            raise ValueError(f"DR publication tree merge refused: {sorted(problems)}")
        planned["repository"] = before, public_after

        destinations = [(label, root / f"{slug}.llms", slug, name)
                        for label, root in (("hub", shared.HUB_DIR / "llms-concepts"),
                                            ("repository", repo / "outputs/llms-concepts"))
                        for slug, name in jobs.items() if label == "hub" or name not in private_names]
        excluded_destinations = [("repository", repo / "outputs/llms-concepts" / f"{slug}.llms", slug, name)
                                 for slug, name in jobs.items() if name in private_names]
        # Check every destination before writing any packs or trees.
        for _, dest, _, name in [*destinations, *excluded_destinations]:
            if dest.exists():
                old_manifest = dest / "manifest.json"
                if not old_manifest.is_file() or json.loads(old_manifest.read_text()).get("concept") != name:
                    raise ValueError(f"refusing to replace another concept's pack: {dest}")
        staging = run / "artifacts"
        staging.mkdir(parents=True, exist_ok=True)
        pack_receipts = []
        with tempfile.TemporaryDirectory(prefix="compile-", dir=staging) as temporary:
            compiled = Path(temporary)
            for slug, name in jobs.items():
                compile_claims(lca, compiled / slug, name, slug, documents[name], status)
            originals = {slug: {filename: (compiled / slug / filename).read_text() for filename in PACK_FILES} for slug in jobs}
            verifier = repo / "scripts/public_research_references.py"
            reference_writes, withheld = {}, []
            if verifier.is_file():
                reference_writes, withheld = load_module("codex_pack_reference_check", verifier).resolve(
                    repo, shared.HUB_DIR, {dest / filename: originals[slug][filename]
                                          for label, dest, slug, _ in destinations if label == "repository"
                                          for filename in PACK_FILES})
            public = {slug: public_pack_files(repo, shared.HUB_DIR, originals[slug], lca, withheld)
                      for label, _, slug, _ in destinations if label == "repository"}
            for path, text in reference_writes.items():
                shared.atomic_write(path, text)
            for label, dest, slug, name in destinations:
                contents = originals[slug] if label == "hub" else public[slug]
                changed = [filename for filename in PACK_FILES if not (dest / filename).is_file()
                           or (dest / filename).read_text() != contents[filename]]
                if changed and dest.exists():
                    shutil.copytree(dest, backup / label / dest.name)
                for filename in changed:
                    shared.atomic_write(dest / filename, contents[filename])
                pack_receipts.append({"target": label, "concept": name, "path": str(dest),
                                      "claims": sum(len(doc["claims"]) for doc in documents[name]),
                                      "changed": changed})
        for label, dest, _, _ in excluded_destinations:
            if dest.exists():
                shutil.copytree(dest, backup / label / dest.name)
                shutil.rmtree(dest)
        tree_receipts = []
        for label, path in tree_paths.items():
            before, after = planned[label]
            if before != after:
                saved = backup / label / "tree.json"
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, saved)
                shared.atomic_write(path, json.dumps(after, indent=2, ensure_ascii=False) + "\n")
            tree_receipts.append({"target": label, "path": str(path),
                                  "before": len(before), "after": len(after), "changed": before != after})
        receipt = {"ok": True, "status": status, "packs": pack_receipts, "trees": tree_receipts,
                   "excluded_repository_concepts": sorted(private_names & set(documents)),
                   "backup": str(backup) if backup.exists() else None}
    website = load_module("codex_dr_website", repo / "scripts/research_site_sync.py")
    receipt["website"] = website.sync(repo, shared.HUB_DIR, apply=True, merge_tree=False)
    shared.atomic_write(run / "artifacts/receipt.json", json.dumps(receipt, indent=2) + "\n")
    return receipt

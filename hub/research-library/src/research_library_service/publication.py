"""Fixed owner-configured publication through the maintained independent gate.

The provider process has no database capability. Only this local worker can
promote the frozen revision after checking the canonical completion receipt.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
import threading
from datetime import UTC, datetime

from .canonical_bridge import atomic, clean_provider_environment, load_module
from .models import MANAGED_BY, Conflict, digest, source_id

CLAIM_FIELDS = {"text", "sources", "confidence", "verified_as_of", "volatile",
                "temporal", "evidence", "conflict"}
SOURCE_FIELDS = {"url", "title", "tier", "origin_id", "org", "derived_from", "version"}
PROVENANCE_FIELDS = SOURCE_FIELDS | {"fetched_at", "etag", "last_modified", "origin_annotation_sha256"}


def export_document(bridge, concept):
    """Build a claims document, without changing any immutable claim identity."""
    claims = [{**{k: v for k, v in claim.items() if k in CLAIM_FIELDS}, "section": "core"}
              for claim in concept.get("claims", []) if not claim.get("deleted")]
    if not claims:
        raise ValueError("Publication requires factual claims")
    sources = []
    urls = sorted({url for claim in claims for url in claim["sources"]})
    for url in urls:
        row = bridge.store.sources.find_one(bridge.store._owned({"_id": source_id(url)}))
        if not row or row.get("deleted"):
            raise ValueError("Publication source is missing or archived")
        metadata = row.get("metadata", {})
        sources.append({**{k: v for k, v in metadata.items() if k in SOURCE_FIELDS},
                        "url": url, "title": row.get("title") or metadata.get("title") or url,
                        "tier": row.get("tier") or metadata.get("tier", "docs")})
    children = [bridge.store.concept_get(cid)["name"] for cid in concept.get("children_ids", [])]
    document = {"concept": concept["name"], "slug": concept["slug"],
                "summary": concept.get("summary", ""), "claims": claims, "sources": sources,
                "disagreements": concept.get("disagreements", []),
                "open_questions": concept.get("open_questions", []),
                "child_concepts": children, "telemetry": concept.get("telemetry", {})}
    domain = concept.get("metadata", {}).get("research_domain")
    if domain is not None:
        document["research_domain"] = domain
    return document


def family_binding(bridge, concept):
    fields = ("children_ids", "related_ids", "adjacent_ids", "prerequisite_ids", "dependent_ids")
    return {"parent_id": concept.get("parent_id"),
            "parent_name": (bridge.store.concept_get(concept["parent_id"])["name"]
                            if concept.get("parent_id") else None),
            **{field: sorted(concept.get(field, [])) for field in fields}}


def archive_sources(bridge, document, directory):
    """Copy exact pinned bodies into the private, immutable provenance archive."""
    provenance = load_module(bridge.repo / "scripts/research_provenance.py",
                             "mongodb_publication_provenance")
    metadata = {}
    for claim in document["claims"]:
        spans = list(claim.get("evidence", []))
        for position in (claim.get("conflict") or {}).get("positions", []):
            spans.extend(position.get("evidence", []))
        for span in spans:
            sid, sha, url = span["source_id"], span["snapshot_sha256"], span["url"]
            if sid != source_id(url):
                raise ValueError("Publication evidence has a different source identity")
            if url in metadata and (metadata[url]["id"], metadata[url]["sha256"]) != (sid, sha):
                raise ValueError("Conflicting source versions require separate research revisions")
            body, snapshot = bridge.store._snapshot_text(sid, sha)
            raw = body.encode("utf-8")
            if digest(raw) != sha or body[span["start"]:span["end"]] != span["quote"]:
                raise ValueError("Publication snapshot or Unicode evidence has changed")
            path = bridge.hub / "research/.library/provenance/snapshots" / (sha + ".txt")
            provenance.immutable(path, raw)
            path.chmod(0o600)
            source = bridge.store.sources.find_one(bridge.store._owned({"_id": sid}))
            # Source metadata is remotely authored. In particular raw_path and
            # history are capabilities in the local archive API, never data we
            # may forward from a remote writer.
            row = {**{k: v for k, v in source.get("metadata", {}).items()
                       if k in PROVENANCE_FIELDS}, "id": sid, "url": source["url"],
                   "sha256": sha, "text_path": str(path),
                   "fetched_at": snapshot.get("fetched_at", source.get("updated_at"))}
            provenance.archive(bridge.hub / "research/.library", row)
            metadata[url] = row
    atomic(directory / "gate-sources.json", metadata)
    return metadata


def _paths(bridge, job_id):
    if not re.fullmatch(r"pub:[0-9a-f]{32}", job_id):
        raise ValueError("Invalid publication identity")
    return bridge.state / "jobs" / job_id[4:]


def _source_override(shared, directory):
    metadata = json.loads((directory / "gate-sources.json").read_text())
    original = shared.lib_find
    shared.lib_find = lambda url: metadata.get(url) or original(url)


def _call(shared, arguments):
    args = shared.build_parser().parse_args(arguments)
    result = getattr(shared, "cmd_" + args.cmd.replace("-", "_"))(args)
    if result not in (None, 0):
        raise ValueError("The maintained research operation did not pass")


def gate_job(bridge, job_id):
    """Independent semantic review. This process never loads Mongo credentials."""
    directory = _paths(bridge, job_id)
    job = json.loads((directory / "gate-request.json").read_text())
    shared = bridge._shared()
    _source_override(shared, directory)
    timeout = max(30, min(int(bridge.config.get("gate_timeout_seconds", 900)), 3600))
    _call(shared, ["gate", job["run_slug"], "--sample", "all", "--refetch-cap", "0",
                   "--agent-timeout", str(timeout), "--model", "gpt-6.1-sol",
                   "--effort", "medium"])
    shared.verify_current_gate(shared.load_manifest(job["run_slug"]))


def run_job(bridge, store, job_id):
    """Freeze → independent gate → canonical promotion → Mongo receipt/CAS."""
    directory = _paths(bridge, job_id)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    jobs = bridge._jobs(store)
    query = {"_id": job_id, "managed_by": MANAGED_BY}
    with (directory / "worker.lock").open("a") as lock:
        # A duplicate local worker cannot run the same publication twice.
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        job = jobs.find_one(query)
        if not job or job["status"] not in {"queued", "running"}:
            return
        private = json.loads((directory / "private.json").read_text())
        bridge.bind_store(store)
        stop, lost = threading.Event(), []

        def renew():
            store.lease_renew(private["concept_ids"], private["tokens"], private["owner"],
                              ttl_seconds=900, actor="trusted-publisher")

        def heartbeat():
            while not stop.wait(60):
                try:
                    renew()
                except Exception as error:
                    lost.append(type(error).__name__)
                    return

        def phase(name):
            if lost:
                raise Conflict("Publication lease heartbeat failed")
            renew()
            jobs.update_one(query, {"$set": {"status": "running", "phase": name,
                "updated_at": datetime.now(UTC).isoformat()}})

        thread = threading.Thread(target=heartbeat, daemon=True)
        try:
            phase("preflight")
            thread.start()
            concept = store.concept_get(job["concept_id"])
            if concept["revision"] != job["input_revision"] or digest(concept) != job["input_sha256"]:
                raise Conflict("Publication input revision changed")
            document = export_document(bridge, concept)
            family = family_binding(bridge, concept)
            shared = bridge._shared()
            def checkpoint():
                if lost:
                    raise Conflict("Publication lease heartbeat failed")
                renew()
                current = store.concept_get(concept["_id"])
                if (current["revision"] != job["input_revision"]
                        or export_document(bridge, current) != document
                        or family_binding(bridge, current) != family):
                    raise Conflict("Publication input or related source/family binding changed")
            shared._research_library_lease_checkpoint = checkpoint
            errors = shared.validate_claims(document)
            if errors:
                raise ValueError("The concept does not satisfy the canonical claims contract")
            archive_sources(bridge, document, directory)
            _source_override(shared, directory)
            run_slug = job["run_slug"]
            manifest_path = shared.run_dir(run_slug) / "manifest.json"
            if manifest_path.exists():
                existing = shared.load_manifest(run_slug)
                if existing.get("research_library_managed", {}).get("concept_id") != concept["_id"]:
                    raise Conflict("A different workflow already owns the publication run")
                if existing.get("status") in {"paused", "blocked", "budget_exhausted"}:
                    raise Conflict("The canonical publication run is held by an operator")
            _call(shared, ["init", concept["name"], "--slug", run_slug, "--depth", "standard",
                           "--refresh"])
            with shared.run_lock(run_slug):
                manifest = shared.load_manifest(run_slug)
                manifest["concepts"] = [{"name": concept["name"], "slug": concept["slug"],
                                          "status": "pending"}]
                manifest["research_library_managed"] = {"concept_id": concept["_id"], "job_id": job_id,
                                                        "family_sha256": digest(family)}
                manifest["cohort_completion_assessment"] = concept["scope_assessment"]
                manifest["aliases"] = concept.get("aliases", [])
                manifest["parent_concept"] = (store.concept_get(concept["parent_id"])["name"]
                    if concept.get("parent_id") else None)
                shared.save_manifest(manifest)
            atomic(directory / "claims.json", document)
            recorded = shared.record_claims(run_slug, str(directory / "claims.json"), concept["name"])
            if not recorded.get("ok"):
                raise ValueError("Canonical claims recording failed")
            _call(shared, ["render", run_slug, "--kind", "standalone", "--out",
                str(directory / "rendered/SKILL.md"), "--name", run_slug[:80],
                "--description", "Evidence-backed research on " + concept["name"][:300],
                "--keywords", "research,library,evidence,claims,sources,concepts,methodology,verification"])
            phase("independent-gate")
            atomic(directory / "gate-request.json", {"run_slug": run_slug})
            environment = clean_provider_environment(os.environ)
            environment.update(HUB_DIR=str(bridge.hub), LLMS_EXPLORER_REPO=str(bridge.repo))
            timeout = max(30, min(int(bridge.config.get("gate_timeout_seconds", 900)), 3600))
            # No shell, no remote-selected paths/commands, no provider DB access.
            completed = subprocess.run([sys.executable, "-m",
                "research_library_service.canonical_bridge", "gate-job", job_id,
                "--config", str(directory / "config.json")], env=environment,
                timeout=timeout * 2 + 180, check=False)
            if completed.returncode:
                raise ValueError("Independent semantic gate did not accept this revision")
            phase("canonical-promotion")
            checkpoint()
            shared.verify_current_gate(shared.load_manifest(run_slug))
            _call(shared, ["finish", run_slug, "--status", "COMPLETED",
                           "--stop-reason", "MongoDB library full-assertion publication"])
            proof = json.loads((shared.run_dir(run_slug) / "artifacts/receipt.json").read_text())
            canonical = proof["canonical_artifact"]
            receipt = {"artifact_path": canonical["path"], "artifact_sha256": canonical["sha256"],
                       "document_slug": concept["slug"]}
            phase("database-promotion")
            result = store.complete(concept["_id"], job["input_revision"],
                private["tokens"][concept["_id"]], receipt,
                actor="trusted-publisher", request_id=job_id + "-complete")
            jobs.update_one(query, {"$set": {"status": "completed", "phase": "completed",
                "updated_at": datetime.now(UTC).isoformat(), "result": {
                    "concept_id": result["_id"], "revision": result["revision"],
                    "state": result["state"], "artifact_sha256": canonical["sha256"]}}})
        except BaseException as error:
            # Detailed provider logs are private. Remote status exposes no body,
            # credentials, caller text, filesystem path or driver diagnostics.
            jobs.update_one(query, {"$set": {"status": "failed", "phase": "failed",
                "error_type": type(error).__name__, "updated_at": datetime.now(UTC).isoformat()}})
            raise
        finally:
            stop.set()
            if thread.is_alive():
                thread.join(timeout=2)
            try:
                store.lease_release(private["concept_ids"], private["tokens"], private["owner"],
                                    actor="trusted-publisher")
            except Exception:
                # An expired/replaced fence never authorizes release of its heir.
                pass

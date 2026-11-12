"""Trusted owner-local bridge to canonical research and legacy reservations."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from .models import MANAGED_BY, Conflict, digest


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("The maintained research adapter is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + "." + secrets.token_hex(6))
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False) + "\n")
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def key(value):
    return " ".join(value.split()).casefold()


def clean_provider_environment(environment):
    """The independent judge receives no MongoDB, server or lease credentials."""
    blocked = ("MONGODB_", "RESEARCH_LIBRARY_", "SKILL_", "CLOUDFLARE_", "VOYAGE_")
    return {k: v for k, v in environment.items()
            if not k.startswith(blocked) and k not in {"TUNNEL_TOKEN"}}


class CanonicalBridge:
    def __init__(self, config):
        self.config = copy.deepcopy(config)
        self.repo = Path(config.get("repo_root",
            os.environ.get("LLMS_EXPLORER_REPO", "~/dev/llms-explorer"))).expanduser().resolve()
        self.hub = Path(config.get("hub_root", "~/.global-ai-hub")).expanduser().resolve()
        self.llmsx = Path(config.get("llmsx_root", "~/.llmsx")).expanduser().resolve()
        self.state = Path(config.get("state_dir", "~/.local/share/research-library")).expanduser()
        self.store = None
        self._scanner = None
        self._claims = None

    def bind_store(self, store):
        self.store = store

    def claim_identity(self, slug, claim):
        if self._claims is None:
            self._claims = load_module(self.repo / "scripts/research_claims.py",
                                       "mongodb_canonical_claims")
        return self._claims.claim_identity(slug, claim)

    def _legacy_runs(self):
        if self.config.get("legacy_reservations", True) is False:
            return []
        if self._scanner is None:
            self._scanner = load_module(self.repo / "api/explorer_api/checkouts.py",
                                        "mongodb_legacy_reservations")
            self._scanner.hub_dir = lambda: self.hub
            self._scanner.llmsx_home = lambda: self.llmsx
            # New coordination is conservative: age alone does not prove that
            # another orchestrator has died or that its work may be resumed.
            self._scanner.DR_STALE_HOURS = 10**9
        runs = self._scanner.runs()
        seen = {(r["source"], r["name"]) for r in runs}
        for path in (self.hub / "research").glob("*/manifest.json"):
            manifest = json.loads(path.read_text())
            if not isinstance(manifest, dict):
                raise ValueError("Legacy research reservation metadata is invalid")
            if manifest.get("status") not in {"blocked", "budget_exhausted", "paused"}:
                continue
            slug = manifest.get("slug", path.parent.name)
            if ("dr", slug) in seen:
                continue
            pending = [c.get("name") for c in manifest.get("concepts", [])
                       if isinstance(c, dict) and c.get("status") not in {"done", "complete"}]
            if pending:
                runs.append({"source": "dr", "name": slug, "state": manifest["status"],
                             "pending": [manifest.get("topic"), *pending]})
        return runs

    def reservations(self, concept_ids, owner, run_id):
        if self.store is None:
            raise ValueError("Research reservation bridge is not bound")
        # Frontier enumeration may contain thousands of IDs. Fetch only names
        # and aliases in bounded batches; never issue one full-document read per
        # concept or carry private claim bodies into the reservation scan.
        wanted, requested, by_name = set(concept_ids), {}, {}
        ids = sorted(wanted)
        for offset in range(0, len(ids), 1000):
            for doc in self.store.concepts.find(self.store._owned({
                    "_id": {"$in": ids[offset:offset + 1000]}, "deleted": {"$ne": True}}),
                    {"_id": 1, "name": 1, "aliases": 1}):
                requested[doc["_id"]] = {key(n) for n in [doc["name"], *doc.get("aliases", [])]}
                for name in requested[doc["_id"]]:
                    by_name.setdefault(name, set()).add(doc["_id"])
        if set(requested) != wanted:
            raise KeyError("A reserved research concept is unavailable")
        holds = {}
        runs = self._legacy_runs()
        running = [r["name"] for r in runs if r["source"] == "dr" and r["state"] == "researching"]
        registered = {row["run_slug"]: row for row in self._jobs(self.store).find({
            "managed_by": MANAGED_BY, "run_slug": {"$in": running}},
            {"run_slug": 1, "concept_id": 1})} if running else {}
        for run in runs:
            # These fixed, service-owned runs use Mongo leases. Keep manual
            # pauses and all other filesystem runs as independent reservations.
            if run["source"] == "dr" and run["state"] == "researching":
                registration = registered.get(run["name"])
                path = self.hub / "research" / run["name"] / "manifest.json"
                manifest = json.loads(path.read_text()) if path.is_file() else {}
                if (registration and manifest.get("research_library_managed", {}).get(
                        "concept_id") == registration.get("concept_id")):
                    continue
            own = (run["source"] == "dr" and run["name"] == run_id
                   and owner in {"legacy:" + run_id, "publication:" + run_id})
            if own:
                continue
            for name in run.get("pending", []):
                if not isinstance(name, str):
                    continue
                for cid in by_name.get(key(name), ()):
                    holds[cid] = {"concept_id": cid, "source": run["source"],
                                  "owner": run["name"], "state": run["state"]}
        # A stopped ranked plan is not resumed by taking a new distributed lease.
        for stop in (self.hub / "research/.ranked").glob("*/STOP"):
            plan_path = stop.parent / "plan.json"
            if not plan_path.is_file():
                raise ValueError("A stopped research plan is missing its reservation inventory")
            plan = json.loads(plan_path.read_text())
            names = set()
            def visit(value):
                if isinstance(value, dict):
                    for name in ("concept", "name", "label", "original_label"):
                        if isinstance(value.get(name), str):
                            names.add(key(value[name]))
                    for child in value.values():
                        if isinstance(child, (dict, list)):
                            visit(child)
                elif isinstance(value, list):
                    for child in value:
                        visit(child)
            visit(plan)
            for name in names:
                for cid in by_name.get(name, ()):
                    holds[cid] = {"concept_id": cid, "source": "ranked-STOP",
                                  "owner": stop.parent.name, "state": "stopped"}
        return holds

    def coordinate(self, store, action, run_id, names=None, bundle=None,
                   ttl_seconds=900, actor="local-admin", request_id=""):
        if not actor.startswith("local-"):
            raise PermissionError("Legacy coordination is owner-local")
        if not isinstance(run_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,159}", run_id):
            raise ValueError("Invalid research run identity")
        owner = "legacy:" + run_id
        bundle = bundle or {}
        if bundle and bundle.get("owner") != owner:
            raise ValueError("Research lease bundle does not belong to this run")
        ids, tokens = bundle.get("concept_ids", []), bundle.get("tokens", {})
        if action == "release":
            return {"ok": True, **store.lease_release(ids, tokens, owner, actor=actor)}
        if action == "renew":
            return {"ok": True, "owner": owner, "concept_ids": ids,
                    **store.lease_renew(ids, tokens, owner, ttl_seconds, actor=actor)}
        if action != "acquire" or not isinstance(names, list) or not names or len(names) > 100:
            raise ValueError("Research coordination requires a bounded concept list")
        wanted = []
        for name in names:
            try:
                doc = store.resolve_concept(name)
            except KeyError:
                try:
                    doc = store.concept_create(name, actor=actor)
                except Conflict:
                    doc = store.resolve_concept(name)
            wanted.append(doc["_id"])
        wanted = sorted(set(wanted))
        retained = sorted(set(wanted) & set(ids))
        if retained:
            try:
                store.lease_renew(retained, tokens, owner, ttl_seconds, actor=actor)
            except Conflict:
                # Reclaim only through the same atomic reservation protocol;
                # a different active owner still wins.
                retained = []
        added = sorted(set(wanted) - set(retained))
        grants = store.lease_acquire(added, owner, ttl_seconds, run_id, actor=actor) if added else {}
        combined = {cid: tokens[cid] for cid in retained}
        combined.update(grants.get("tokens", {}))
        return {"ok": True, "owner": owner, "run_id": run_id,
                "concept_ids": wanted, "tokens": combined,
                "fences": grants.get("fences", {})}

    def _shared(self):
        adapter = load_module(self.repo / "scripts/codex_dr_run.py", "mongodb_dr_adapter")
        shared = adapter.load_shared(library_coordination=False)
        if Path(shared.HUB_DIR).resolve() != self.hub:
            raise ValueError("The canonical runtime hub differs from the trusted service configuration")
        # Imported frontier labels can exceed a filesystem component's limit.
        # Preserve every existing short/curated identity; bound newly generated
        # pack names before the canonical compiler allocates them.
        original_slugify = shared.slugify
        def bounded_slugify(value):
            slug = original_slugify(value)
            return (slug if len(slug) <= 160 else
                    slug[:147].rstrip("-") + "-" + digest(slug.encode())[:12])
        shared.slugify = bounded_slugify
        return shared

    def completion_verifier(self, concept, receipt):
        from .publication import pending_family
        if pending_family(concept):
            raise ValueError("Canonical family reconciliation is still pending")
        if not isinstance(receipt, dict):
            raise ValueError("A trusted canonical completion receipt is required")
        path = Path(receipt.get("artifact_path", "")).expanduser().resolve()
        research = (self.hub / "research").resolve()
        if (not path.is_relative_to(research) or path.parent.name != "canonical"
                or path.parent.parent.name != "artifacts"
                or not re.fullmatch(r"[0-9a-f]{64}\.json", path.name)):
            raise ValueError("Canonical artifact is outside the trusted research archive")
        if path.stat().st_size > 32 * 1024 * 1024:
            raise ValueError("Canonical artifact exceeds its byte bound")
        artifact_module = load_module(self.repo / "scripts/research_artifact.py",
                                      "mongodb_canonical_artifact")
        artifact = artifact_module.verify(json.loads(path.read_text()))
        if (artifact.get("status") != "COMPLETED"
                or artifact.get("assertion_contract_version", 0) < 4
                or artifact["artifact_sha256"] != receipt.get("artifact_sha256")
                or path.stem != artifact["artifact_sha256"]):
            raise ValueError("Completion requires a current full-assertion v4 artifact")
        slug = receipt.get("document_slug", concept["slug"])
        document = artifact["documents"].get(slug)
        if document is None or slug != concept["slug"]:
            raise ValueError("Canonical artifact does not bind this concept")
        current_ids = sorted(c["claim_id"] for c in concept.get("claims", [])
                             if not c.get("deleted"))
        accepted_ids = sorted(c["canonical_claim_id"] for c in document["claims"])
        if not current_ids or current_ids != accepted_ids:
            raise ValueError("Concept claims changed after canonical verification")
        # Claim IDs alone do not bind summaries, names, family or scope. A
        # supported old claim set cannot validate newly edited factual prose.
        from .publication import export_document, family_binding
        current = export_document(self, concept)
        for field in ("summary", "disagreements", "open_questions"):
            if current.get(field) != document.get(field):
                raise ValueError("Concept prose or source metadata changed after verification")
        if sorted(current["sources"], key=lambda row: row["url"]) != sorted(
                document["sources"], key=lambda row: row["url"]):
            raise ValueError("Concept source metadata changed after verification")
        if concept["name"] not in {document.get("concept"), document.get("recorded_concept_title")}:
            raise ValueError("Concept name changed after canonical verification")
        if sorted(current["child_concepts"]) != sorted(document.get("child_concepts", [])):
            raise ValueError("Concept family changed after canonical verification")
        if artifact.get("input_hashes", {}).get(slug) != digest(current):
            raise ValueError("Canonical input does not match this exact concept version")
        shared = self._shared()
        manifest = shared.load_manifest(artifact["run"])
        if manifest.get("exit_status") != "COMPLETED":
            raise ValueError("Canonical run has not completed")
        if manifest.get("cohort_completion_assessment") != concept.get("scope_assessment"):
            raise ValueError("Canonical commissioned scope does not match the current revision")
        if (manifest.get("parent_concept") != family_binding(self, concept)["parent_name"]
                or manifest.get("research_library_managed", {}).get("family_sha256") != digest(
                    family_binding(self, concept))):
            raise ValueError("Canonical family proof does not match this exact concept version")
        shared.verify_current_gate(manifest)
        gate = load_module(self.repo / "scripts/research_gate.py", "mongodb_completion_gate")
        gate.verify_completion_scope(manifest)
        proof = json.loads((shared.run_dir(artifact["run"]) / "artifacts/receipt.json").read_text())
        if (proof.get("ok") is not True
                or proof.get("canonical_artifact", {}).get("sha256") != artifact["artifact_sha256"]
                or not isinstance(proof.get("website"), dict)):
            raise ValueError("Canonical projection completion is missing or stale")
        if proof.get("website", {}).get("ok") is False:
            raise ValueError("Canonical website projection did not complete")
        return {"artifact_sha256": artifact["artifact_sha256"], "run_slug": artifact["run"],
                "gate_contract": 4, "packet_sha256": artifact["validation"]["packet_sha256"],
                "canonical_verified": True, "projections_refreshed": True}

    def _jobs(self, store):
        return store.database[store.prefix + "publications"]

    def publication_status(self, store, job_id):
        if not isinstance(job_id, str) or not re.fullmatch(r"pub:[0-9a-f]{32}", job_id):
            raise ValueError("Invalid publication job identity")
        row = self._jobs(store).find_one({"_id": job_id, "managed_by": MANAGED_BY})
        if row is None:
            raise KeyError("No such publication")
        if (row.get("status") in {"queued", "running"} and row.get("hostname") == socket.gethostname()
                and time.time() - row.get("started_epoch", time.time()) > 45):
            try:
                if not row.get("pid"):
                    raise ProcessLookupError
                os.kill(row["pid"], 0)
            except ProcessLookupError:
                # Observation only: the reader capability never writes jobs.
                row["status"], row["phase"] = "interrupted", "worker-exited"
        return {k: row[k] for k in ("_id", "concept_id", "input_revision", "status",
                "phase", "error_type", "created_at", "updated_at", "result") if k in row}

    def publish(self, store, concept_id, expected_revision, lease_token, owner,
                actor="local-admin", request_id=""):
        if self.config.get("publication_enabled") is not True:
            raise ValueError("Trusted publication is not enabled by the owner")
        document = store.concept_get(concept_id)
        request_id = request_id or secrets.token_hex(16)
        job_id = "pub:" + digest([actor, request_id])[:32]
        fingerprint = digest([actor, request_id, document["_id"], expected_revision, owner,
                              digest(lease_token.encode())])
        jobs = self._jobs(store)
        jobs.create_index([("managed_by", 1), ("status", 1)])
        jobs.create_index([("managed_by", 1), ("run_slug", 1)])
        prior = jobs.find_one({"_id": job_id})
        if prior and (prior.get("managed_by") != MANAGED_BY
                      or prior.get("request_sha256") != fingerprint):
            raise Conflict("Publication request identity conflicts with another operation")
        if prior and prior.get("status") != "preparing":
            return self.publication_status(store, job_id)
        if document["revision"] != expected_revision:
            raise Conflict("Concept revision changed before publication")
        from .publication import pending_family
        if pending_family(document):
            raise Conflict("Canonical family reconciliation is still pending")
        if not any(not c.get("deleted") for c in document.get("claims", [])) or document.get("deleted"):
            raise ValueError("Research publication requires active claims")
        if document.get("scope_assessment", {}).get("ready_for_full_scope_export") is not True:
            raise ValueError("A complete commissioned-scope assessment is required")
        held = store.queue.find_one(store._owned({"_id": document["_id"]}))
        if held and (held.get("stop") or held.get("status") in {"paused", "held", "stopped", "stop"}):
            raise Conflict("Publication cannot resume held or stopped work")
        # A stable private run preserves validated unchanged judgments across
        # versions. Registration prevents commandeering a pre-existing run.
        run_slug = "mongo-library-" + document["slug"][:70] + "-" + digest(document["_id"])[:8]
        now = datetime.now(UTC).isoformat()
        jobs.update_one({"_id": job_id, "managed_by": MANAGED_BY}, {"$setOnInsert": {
            "managed_by": MANAGED_BY, "request_sha256": fingerprint,
            "concept_id": document["_id"], "input_revision": expected_revision,
            "status": "preparing", "phase": "lease-handoff", "created_at": now,
            "input_sha256": digest(document),
            "run_slug": run_slug, "updated_at": now}}, upsert=True)
        saved = jobs.find_one({"_id": job_id})
        if (not saved or saved.get("managed_by") != MANAGED_BY
                or saved.get("request_sha256") != fingerprint):
            raise Conflict("Publication request identity conflicts with another operation")
        claimed = jobs.find_one_and_update({"_id": job_id, "managed_by": MANAGED_BY,
            "status": "preparing", "request_sha256": fingerprint}, {"$set": {
            "status": "queued", "phase": "lease-handoff",
            "hostname": socket.gethostname(), "started_epoch": time.time()}})
        if claimed is None:
            return self.publication_status(store, job_id)
        delegated = None
        try:
            delegated = store.lease_delegate([document["_id"]],
                {document["_id"]: lease_token}, owner, "publication:" + run_slug,
                actor="trusted-publisher", request_id=job_id + "-handoff")
            directory = self.state / "jobs" / job_id[4:]
            atomic(directory / "private.json", {"tokens": delegated["tokens"],
                   "owner": "publication:" + run_slug, "concept_ids": [document["_id"]]})
            atomic(directory / "config.json", self.config)
            log = directory / "worker.log"
            with log.open("ab") as stream:
                log.chmod(0o600)
                environment = dict(os.environ, HUB_DIR=str(self.hub), LLMS_EXPLORER_REPO=str(self.repo))
                process = subprocess.Popen([sys.executable, "-m", __name__, "run-job",
                    job_id, "--config", str(directory / "config.json")],
                    stdout=stream, stderr=stream, env=environment, start_new_session=True)
            jobs.update_one({"_id": job_id, "managed_by": MANAGED_BY},
                            {"$set": {"pid": process.pid, "phase": "starting"}})
        except Exception as error:
            jobs.update_one({"_id": job_id, "managed_by": MANAGED_BY}, {"$set": {
                "status": "failed", "phase": "startup-failed", "error_type": type(error).__name__,
                "updated_at": datetime.now(UTC).isoformat()}})
            if delegated:
                store.lease_release([document["_id"]], delegated["tokens"], "publication:" + run_slug,
                                    actor="trusted-publisher")
            raise
        return self.publication_status(store, job_id)


def make_bridge(config):
    bridge = CanonicalBridge(config)
    return {name: getattr(bridge, name) for name in (
        "bind_store", "claim_identity", "completion_verifier", "reservations",
        "coordinate", "publish", "publication_status")} | {
        "reservation_provider": bridge.reservations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run-job", "gate-job"])
    parser.add_argument("job_id")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    from .publication import gate_job, run_job
    bridge = CanonicalBridge(config)
    if args.action == "gate-job":
        gate_job(bridge, args.job_id)
    else:
        from .service import Service
        service = Service(config=config)
        bridge.bind_store(service.store)
        run_job(bridge, service.store, args.job_id)


if __name__ == "__main__":
    main()

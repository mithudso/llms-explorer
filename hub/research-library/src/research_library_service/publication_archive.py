"""Private Mongo archives for the fixed publisher's derived filesystem state.

Archiving records bytes and provenance. It never grants a research judgment,
changes the maintained gate, restores credentials, or republishes projections.
"""
from __future__ import annotations

import copy
import json
import os
import re
import secrets
import threading
from pathlib import PurePosixPath

from .models import MANAGED_BY, Conflict, digest
from .runs import MAX_ARTIFACT_BYTES, ResearchRunStore

SCHEMA = "publication-archive/v1"
MAX_FILES = 5000
PACK_FILES = ("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
              "llms-vocabulary.txt", "units.jsonl", "concept-graph.json", "manifest.json")
SAFE_COMPONENT = r"[A-Za-z0-9][A-Za-z0-9._-]{0,159}"
SHA = r"[0-9a-f]{64}"
ATTEMPT_JSON = ("packet", "preflight", "validation", "verdicts", "repair", "startup",
                "startup-recovery")
TELEMETRY_FIELDS = {"name", "model", "effort", "started", "finished", "transport",
                    "requested_max_turns", "max_turns_enforced", "timeout_seconds",
                    "cost_usd", "tokens", "seconds", "usage", "num_turns", "is_error",
                    "attempts", "counts", "resumed", "reused_tokens"}


class ArchiveIncomplete(Conflict):
    """The publisher cannot prove that its durable archive is complete."""


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def _relative(value):
    if (not isinstance(value, str) or "\\" in value or not value
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ArchiveIncomplete("Invalid publication archive relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value:
        raise ArchiveIncomplete("Invalid publication archive relative path")
    return path


def _allowed(location, relative):
    _relative(relative)
    if location == "job":
        return (relative in {"inputs.json", "claims.json", "gate-request.json", "gate-sources.json",
                             "archive-state.json", "rendered/SKILL.md"}
                or re.fullmatch(r"inputs/source-pins/" + SHA + r"\.txt", relative) is not None)
    if location == "canonical":
        return (re.fullmatch(SHA + r"\.json", relative) is not None
                or re.fullmatch(r"compiled/(hub|repository)/" + SAFE_COMPONENT + "/(" +
                                "|".join(re.escape(name) for name in PACK_FILES) + ")",
                                relative) is not None)
    if location != "run":
        return False
    return (relative in {"manifest.json", "draft.md", "sources.jsonl", "units.jsonl", "report.md",
                         "gate.json", "artifacts/receipt.json", "briefs/gate.md"}
            or re.fullmatch(r"claims/" + SAFE_COMPONENT + r"\.json", relative) is not None
            or re.fullmatch(r"gate/attempts/" + SAFE_COMPONENT + "/(" +
                            "|".join(ATTEMPT_JSON) + r")\.json", relative) is not None
            or re.fullmatch(r"gate/attempts/" + SAFE_COMPONENT + "/evidence/" + SHA + r"\.txt",
                            relative) is not None
            or re.fullmatch(r"gate/startup-recoveries/" + SHA + r"\.json", relative) is not None
            or re.fullmatch(r"agents/attempts/gate/" + SAFE_COMPONENT +
                            r"/(validated-summary\.json|worker\.json|brief\.md)", relative) is not None
            or re.fullmatch(r"checkpoints/workers/" + SHA + r"\.json", relative) is not None)


def _safe_path(root, relative):
    """Derive targets from owner configuration, never artifact-authored absolute paths."""
    relative = _relative(relative)
    root = root.expanduser().absolute()
    path = root
    # Check existing ancestors too: resolving a symlink would hide the capability.
    for ancestor in [*reversed(root.parents), root]:
        if ancestor.is_symlink():
            raise ArchiveIncomplete("Publication archive paths cannot contain symlinks")
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ArchiveIncomplete("Publication archive paths cannot contain symlinks")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ArchiveIncomplete("Publication archive path escapes its configured root")
    return path


def _write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + "." + secrets.token_hex(6))
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            os.chmod(temporary, 0o600)
            handle.write(body)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _diagnostics(value):
    """Keep structured gate failure bindings without copying provider error bodies."""
    if isinstance(value, dict):
        return {key: ("Provider diagnostics remain in the private local log" if item else item)
                if key in {"error", "errors", "result", "stderr", "stdout", "traceback"}
                else _diagnostics(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_diagnostics(item) for item in value]
    return value


def _telemetry(value):
    return _diagnostics({key: item for key, item in value.items() if key in TELEMETRY_FIELDS})


class PublicationArchive:
    def __init__(self, bridge, store, job):
        from .publication import _paths
        self.bridge, self.store, self.job = bridge, store, copy.deepcopy(job)
        self.directory = _paths(bridge, job["_id"])
        if not re.fullmatch(r"mongo-library-[a-z0-9-]+", job["run_slug"]):
            raise ArchiveIncomplete("Invalid trusted publication run identity")
        self.root = bridge.hub / "research" / job["run_slug"]
        self.jobs = bridge._jobs(store)
        self.runs = ResearchRunStore(store)
        self.lock, self.cached = threading.RLock(), {}
        self.compiled_records = []
        self.binding = {"publication_job_id": job["_id"], "concept_id": job["concept_id"],
                        "input_revision": job["input_revision"], "run_slug": job["run_slug"]}
        self.provenance = {"schema": SCHEMA, "publisher": "trusted-publisher", **self.binding}
        if job.get("archive_run_id"):
            self.run_id = job["archive_run_id"]
        else:
            result = self.runs.run_create("dr", "Canonical publication " + job["concept_id"],
                "Archive the fixed publisher's exact inputs, gate attempts and generated outputs.",
                "trusted-publisher", options={"purpose": "publication-archive"}, scope=self.binding,
                actor="trusted-publisher", request_id=job["_id"] + "-archive-run")
            # The secret run lease is deliberately never placed in a readable document.
            self.run_id = result["run"]["_id"]
            self.jobs.update_one({"_id": job["_id"], "managed_by": MANAGED_BY},
                                 {"$set": {"archive_run_id": self.run_id}})
        run = self.runs.run_get(self.run_id)
        if (run.get("owner") != "trusted-publisher" or run.get("mode") != "dr"
                or run.get("scope") != self.binding
                or run.get("options") != {"purpose": "publication-archive"}):
            raise ArchiveIncomplete("Publication archive run is not owned by this job")

    def _target(self, location, relative):
        if not _allowed(location, relative):
            raise ArchiveIncomplete("Publication archive file is not allowlisted")
        if (location == "run" and relative.startswith("claims/")
                and relative != "claims/" + self.job["concept_id"][2:] + ".json"):
            raise ArchiveIncomplete("Publication claim input belongs to another concept")
        root = {"job": self.directory, "run": self.root,
                "canonical": self.root / "artifacts/canonical"}[location]
        return _safe_path(root, relative)

    def _put(self, location, relative, body, *, kind="publication-file"):
        self._target(location, relative)
        sha = digest(body.encode("utf-8"))
        cache_key = (location, relative, sha)
        if cache_key in self.cached:
            return self.cached[cache_key]
        metadata = {"schema": SCHEMA, **self.binding, "location": location,
                    "relative_path": relative, "content_sha256": sha}
        saved = self.runs._archive_artifact(self.run_id,
            "publication-" + digest([location, relative]), kind, body,
            provenance=self.provenance, metadata=metadata, owner="trusted-publisher",
            actor="trusted-publisher", request_id=self.job["_id"] + "-archive-" +
            digest([location, relative, sha]))
        record = {"artifact_id": saved["artifact"]["_id"], "location": location,
                  "relative_path": relative, "content_sha256": sha}
        self.cached[cache_key] = record
        return record

    def inputs(self, document, family, scope):
        """Archive exact factual inputs and pinned bodies before any provider process."""
        _write(self._target("job", "inputs.json"), _json({"schema": SCHEMA, **self.binding,
            "document": document, "family": family, "scope_assessment": scope}))
        pins = set()
        for claim in document["claims"]:
            spans = list(claim.get("evidence", []))
            for position in (claim.get("conflict") or {}).get("positions", []):
                spans.extend(position.get("evidence", []))
            pins.update((span["source_id"], span["snapshot_sha256"]) for span in spans)
        for sid, sha in sorted(pins):
            body, _ = self.store._snapshot_text(sid, sha)
            if digest(body.encode("utf-8")) != sha:
                raise ArchiveIncomplete("Publication source pin checksum mismatch")
            _write(self._target("job", "inputs/source-pins/" + sha + ".txt"), body)
        self.capture("inputs")

    def _read_file(self, location, relative):
        path = self._target(location, relative)
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            raise ArchiveIncomplete("Publication archive file exceeds its byte limit")
        with path.open("rb") as handle:
            raw = handle.read(MAX_ARTIFACT_BYTES + 1)
        if len(raw) > MAX_ARTIFACT_BYTES:
            raise ArchiveIncomplete("Publication archive file exceeds its byte limit")
        body = raw.decode("utf-8")
        if relative.endswith(".json"):
            value = json.loads(body)
            if relative == "manifest.json" and location == "run":
                if (value.get("slug") != self.job["run_slug"]
                        or value.get("research_library_managed", {}).get("concept_id") !=
                        self.job["concept_id"]):
                    raise ArchiveIncomplete("Publication manifest belongs to another workflow")
                value = copy.deepcopy(value)
                value["agents"] = {key: _telemetry(item) for key, item in value.get("agents", {}).items()
                                   if isinstance(item, dict)}
                body = _json(_diagnostics(value))
            elif (relative.endswith(("/validated-summary.json", "/worker.json"))):
                body = _json(_telemetry(value))
            elif relative.startswith("checkpoints/workers/"):
                value = copy.deepcopy(value)
                if isinstance(value.get("summary"), dict):
                    value["summary"] = _telemetry(value["summary"])
                body = _json(_diagnostics(value))
            elif relative.endswith(("/validation.json", "/startup.json")):
                body = _json(_diagnostics(value))
        return body

    def _files(self):
        files = []
        for location, root in (("job", self.directory), ("run", self.root)):
            if not root.exists():
                continue
            # Enumerate only fixed subtrees. Private handoff/config/log files are never opened.
            patterns = (["inputs.json", "claims.json", "gate-request.json", "gate-sources.json",
                         "archive-state.json", "rendered/SKILL.md", "inputs/source-pins/*.txt"]
                        if location == "job" else
                        ["manifest.json", "draft.md", "sources.jsonl", "units.jsonl", "report.md",
                         "gate.json", "artifacts/receipt.json", "briefs/gate.md", "claims/*.json",
                         "gate/attempts/*/*.json", "gate/attempts/*/evidence/*.txt",
                         "gate/startup-recoveries/*.json", "agents/attempts/gate/*/validated-summary.json",
                         "agents/attempts/gate/*/worker.json", "agents/attempts/gate/*/brief.md",
                         "checkpoints/workers/*.json"])
            for pattern in patterns:
                for path in sorted(root.glob(pattern)):
                    relative = path.relative_to(root).as_posix()
                    if _allowed(location, relative):
                        files.append((location, relative))
        canonical = self.root / "artifacts/canonical"
        if canonical.exists():
            for path in sorted(canonical.glob("*.json")):
                if _allowed("canonical", path.name):
                    files.append(("canonical", path.name))
        if len(files) > MAX_FILES:
            raise ArchiveIncomplete("Publication archive exceeds its file count limit")
        return files

    def _compiled(self):
        """Read configured projection roots; ignore all paths supplied in receipts."""
        receipt_path = self._target("run", "artifacts/receipt.json")
        if not receipt_path.exists():
            return []
        receipt = json.loads(receipt_path.read_text())
        canonical = receipt.get("canonical_artifact", {})
        sha = canonical.get("sha256", "")
        if not re.fullmatch(SHA, sha):
            return []
        artifact = json.loads(self._read_file("canonical", sha + ".json"))
        from .canonical_bridge import load_module
        verifier = load_module(self.bridge.repo / "scripts/research_artifact.py",
                               "mongodb_archived_canonical_artifact")
        verifier.verify(artifact)
        inputs = json.loads(self._read_file("job", "inputs.json"))["document"]
        if (artifact.get("run") != self.job["run_slug"]
                or artifact.get("assertion_contract_version", 0) < 4
                or artifact.get("input_hashes", {}).get(inputs["slug"]) != digest(inputs)):
            raise ArchiveIncomplete("Compiled publication belongs to another run")
        records = []
        for pack in receipt.get("packs", []):
            label = pack.get("target")
            if label not in {"hub", "repository"}:
                raise ArchiveIncomplete("Invalid canonical projection target")
            base = (self.bridge.hub / "llms-concepts" if label == "hub" else
                    self.bridge.repo / "outputs/llms-concepts")
            tree_path = ((self.bridge.hub if label == "hub" else self.bridge.repo)
                         / "concept-tree/tree.json")
            nodes = json.loads(tree_path.read_text())
            if isinstance(nodes, dict):
                nodes = nodes.get("nodes", nodes.get("concepts", []))
            matches = [node for node in nodes if node.get("concept") == pack.get("concept")
                       and node.get("canonicalArtifactSha256") == sha]
            if len(matches) != 1:
                raise ArchiveIncomplete("Canonical projection owner is missing or ambiguous")
            slug = matches[0].get("slug", "")
            if not re.fullmatch(SAFE_COMPONENT, slug):
                raise ArchiveIncomplete("Invalid canonical projection slug")
            for filename in PACK_FILES:
                path = _safe_path(base, slug + ".llms/" + filename)
                if path.stat().st_size > MAX_ARTIFACT_BYTES:
                    raise ArchiveIncomplete("Compiled publication exceeds its byte limit")
                with path.open("rb") as handle:
                    raw = handle.read(MAX_ARTIFACT_BYTES + 1)
                if len(raw) > MAX_ARTIFACT_BYTES:
                    raise ArchiveIncomplete("Compiled publication exceeds its byte limit")
                records.append(self._put("canonical", f"compiled/{label}/{slug}/{filename}",
                                         raw.decode("utf-8"), kind="publication-compiled"))
        return records

    def capture(self, phase, *, compiled=False):
        """Publish a checksum-bound inventory only after every selected file is durable."""
        with self.lock:
            try:
                records = [self._put(location, relative, self._read_file(location, relative))
                           for location, relative in self._files()]
                if compiled:
                    self.compiled_records = self._compiled()
                records.extend(self.compiled_records)
                if len(records) > MAX_FILES:
                    raise ArchiveIncomplete("Publication archive exceeds its file count limit")
                index = {"schema": SCHEMA, **self.binding, "phase": phase, "files": records}
                saved = self.runs._archive_artifact(self.run_id, "publication-inventory",
                    "publication-inventory", _json(index), provenance=self.provenance,
                    metadata={"schema": SCHEMA, **self.binding}, owner="trusted-publisher",
                    actor="trusted-publisher", request_id=self.job["_id"] + "-inventory-" + digest(index))
                self.jobs.update_one({"_id": self.job["_id"], "managed_by": MANAGED_BY}, {"$set": {
                    "archive_status": "complete", "archive_phase": phase,
                    "archive_manifest_id": saved["artifact"]["_id"]}})
                return saved["artifact"]["_id"]
            except Exception as error:
                self.jobs.update_one({"_id": self.job["_id"], "managed_by": MANAGED_BY}, {"$set": {
                    "archive_status": "incomplete", "archive_error_type": type(error).__name__}})
                raise ArchiveIncomplete("Publication Mongo archive is incomplete") from error

    def state(self, state, input_sha256):
        with self.lock:
            _write(self._target("job", "archive-state.json"), _json({"schema": SCHEMA, **self.binding,
                   "gate_execution": state, "gate_input_sha256": input_sha256}))
            # Do not resolve dispatched/unknown execution before its gate files
            # are durable. A failed capture must preserve the paid-retry fence
            # even if every local scratch file is subsequently lost. Dispatch
            # itself still finishes both writes before the provider can start.
            self.capture("gate-" + state)
            self.jobs.update_one({"_id": self.job["_id"], "managed_by": MANAGED_BY}, {"$set": {
                "gate_execution": state, "gate_input_sha256": input_sha256}})

    def require_known_gate(self, input_sha256):
        if self.jobs.find_one({"managed_by": MANAGED_BY, "concept_id": self.job["concept_id"],
                "gate_input_sha256": input_sha256,
                "gate_execution": {"$in": ["dispatched", "unknown"]}}):
            raise Conflict("An earlier paid gate may have executed; recover its proof before retrying")

    def _read_artifact(self, aid):
        row, body = self.runs._artifact_text(aid)
        if (row.get("run_id") != self.run_id or row.get("trusted_provenance") != self.provenance
                or row.get("qualification") != {"status": "trusted-archive",
                                                  "authority": "trusted-publisher"}):
            raise ArchiveIncomplete("Only this publisher's trusted archive can restore scratch files")
        return row, body

    def restore(self):
        """Restore missing private scratch only; leave every existing projection untouched."""
        with self.lock:
            job = self.jobs.find_one({"_id": self.job["_id"], "managed_by": MANAGED_BY}) or {}
            aid = job.get("archive_manifest_id")
            if not aid:
                return []
            row, body = self._read_artifact(aid)
            if row.get("kind") != "publication-inventory":
                raise ArchiveIncomplete("Invalid trusted publication inventory")
            inventory = json.loads(body)
            if (inventory.get("schema") != SCHEMA
                    or any(inventory.get(key) != val for key, val in self.binding.items())
                    or not isinstance(inventory.get("files"), list)
                    or len(inventory["files"]) > MAX_FILES):
                raise ArchiveIncomplete("Publication inventory binding is invalid")
            pending, seen = [], set()
            # Verify the complete selected snapshot before writing any bytes.
            for record in inventory["files"]:
                location, relative = record["location"], record["relative_path"]
                target = self._target(location, relative)
                identity = (location, relative)
                if identity in seen:
                    raise ArchiveIncomplete("Duplicate publication archive file")
                seen.add(identity)
                artifact, text = self._read_artifact(record["artifact_id"])
                metadata = artifact.get("metadata", {})
                sha = digest(text.encode("utf-8"))
                if (metadata != {"schema": SCHEMA, **self.binding, "location": location,
                                 "relative_path": relative, "content_sha256": sha}
                        or sha != record.get("content_sha256")):
                    raise ArchiveIncomplete("Publication archive file checksum or binding changed")
                if location == "run" and relative == "manifest.json":
                    manifest = json.loads(text)
                    if (manifest.get("slug") != self.job["run_slug"]
                            or manifest.get("research_library_managed", {}).get("concept_id") !=
                            self.job["concept_id"]):
                        raise ArchiveIncomplete("Archived manifest has another publication owner")
                    if manifest.get("install_path"):
                        manifest["install_path"] = str(self._target("job", "rendered/SKILL.md"))
                    text = _json(manifest)
                if not target.exists():
                    pending.append((target, text))
            for target, text in pending:
                _write(target, text)
            self.compiled_records = [record for record in inventory["files"]
                if record["location"] == "canonical"
                and record["relative_path"].startswith("compiled/")]
            return [str(target) for target, _ in pending]

    def restore_previous(self):
        """Preserve same-concept gate reuse if a fresh job lost the shared run scratch."""
        if self._target("run", "manifest.json").exists():
            return
        rows = self.jobs.find({"managed_by": MANAGED_BY, "concept_id": self.job["concept_id"],
            "run_slug": self.job["run_slug"], "archive_manifest_id": {"$exists": True},
            "_id": {"$ne": self.job["_id"]}}).sort("created_at", -1)
        for previous in rows:
            PublicationArchive(self.bridge, self.store, previous).restore()
            if self._target("run", "manifest.json").exists():
                return


def restore_completion(bridge, concept, path):
    """A writer can recover only the configured run already named by its receipt."""
    rows = bridge._jobs(bridge.store).find({"managed_by": MANAGED_BY,
        "concept_id": concept["_id"], "run_slug": path.parent.parent.parent.name,
        "archive_manifest_id": {"$exists": True}}).sort("created_at", -1)
    for job in rows:
        archive = PublicationArchive(bridge, bridge.store, job)
        archive.restore()
        if path.is_file():
            return

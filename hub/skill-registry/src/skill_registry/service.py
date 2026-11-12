"""One local contract shared by CLI and MCP."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .bundles import MAX_ARCHIVE_BYTES, build_bundle, install_bundle
from .catalog import Catalog
from .client import Remote, token_from_environment
from .environment import load_environment
from .jobs import OPTIMIZERS, Jobs
from .util import atomic, read_bounded, validate_workspace


class Service:
    def __init__(self, state: Path | None = None, config: dict | None = None):
        load_environment()
        self.state = Path(state or os.environ.get("SKILL_REGISTRY_HOME", "~/.local/share/skill-registry")).expanduser()
        if config is None:
            path = Path(os.environ.get("SKILL_REGISTRY_CONFIG", "~/.config/skill-registry/config.json")).expanduser()
            config = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(config, dict):
            raise ValueError("Skill registry config must be a JSON object")
        self.config = config
        self.catalog = Catalog(self.state, config.get("roots"))
        self.jobs = Jobs(self.state)

    def mongo(self):
        """Open the separately authorized MongoDB distribution projection lazily."""
        from .mongo_store import MongoStore
        return MongoStore()

    def remote(self) -> Remote:
        return Remote(os.environ.get("SKILL_REGISTRY_URL", self.config.get("remote_url", "")),
                      token_from_environment(), self.state / "releases")

    def package(self, skill_id: str, namespace: str, name: str, version: str) -> dict:
        record = self.catalog.load(skill_id)
        manifest, data = build_bundle(Path(record["path"]).parent, namespace, name, version)
        path = self.state / "releases" / (manifest["release_sha256"] + ".zip")
        atomic(path, data)
        return {"manifest": manifest, "bundle": str(path), "published": False,
                "instruction": "Review the complete bundle before explicit private/team publication."}

    def cached_bundle(self, checksum: str) -> bytes:
        if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            raise ValueError("Expected a complete release SHA256")
        return read_bounded(self.state / "releases" / (checksum + ".zip"), MAX_ARCHIVE_BYTES)

    def install(self, checksum: str, destination: Path) -> dict:
        return install_bundle(self.cached_bundle(checksum), destination, checksum)

    def definition(self, kind: str) -> Path | None:
        if kind not in OPTIMIZERS:
            raise ValueError("Unsupported optimizer kind")
        name = OPTIMIZERS[kind]
        exact = self.catalog.resolve_exact(name)
        return Path(exact["path"]) if exact else None

    def submit(self, kind: str, *, skill_id: str = "", input_text: str | None = None,
               expected_sha256: str = "", timeout_seconds: int = 600, max_iterations: int = 3) -> dict:
        if skill_id:
            if kind != "skill" or input_text is not None:
                raise ValueError("skill_id is only for a skill job without input_text")
            skill = self.catalog.load(skill_id)
            target = Path(skill["path"])
        else:
            target = None
        return self.jobs.enqueue(kind, target=target, input_text=input_text,
                                 expected_sha256=expected_sha256, skill_id=skill_id,
                                 timeout_seconds=timeout_seconds, max_iterations=max_iterations,
                                 definition=self.definition(kind))

    def finish_external(self, job_id: str, worker: str, lease_token: str,
                        native_report: dict | None = None) -> dict:
        """Accept a manually executed local worker after independently checking bytes.

        This is useful for an agent operating through MCP. The service runs its
        structural check itself and marks native convergence as reported only.
        It cannot turn an agent's claim into independent native verification.
        """
        from .jobs import snapshot_identity
        record = self.jobs.get(job_id)
        base = self.state / "runs" / job_id
        validate_workspace(base, record["params"].get("workspace"))
        filename = record["params"]["filename"]
        if snapshot_identity(record["kind"], base / "original", filename,
                text_only=record["params"]["text_only"]) != record["input_sha256"]:
            raise ValueError("Original snapshot changed")
        check = self.jobs.structural_check(record)
        candidate = snapshot_identity(record["kind"], base / "candidate", filename,
                                      text_only=record["params"]["text_only"])
        return self.jobs.complete(job_id, worker, lease_token, {
            "schema": "optimization-result/v1", "input_sha256": record["input_sha256"],
            "candidate_sha256": candidate, "changed": candidate != record["input_sha256"],
            "executed": True, "checks": [check], "checks_passed": True,
            "converged": False, "published": False, "candidate_ready": True,
            "worker_report": native_report,
            "convergence": {"basis": "external worker report", "independently_verified": False},
        })

"""Existing-account hosted API client with exact release pins and offline cache."""

from __future__ import annotations

import base64
import ipaddress
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import __version__
from .bundles import MAX_ARCHIVE_BYTES, install_bundle, validate_bundle, validate_coordinates
from .util import atomic, canonical, read_bounded


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Registry redirects are refused to protect scoped credentials")


class Remote:
    def __init__(self, base_url: str, token: str, cache: Path):
        parts = urllib.parse.urlsplit(base_url)
        if parts.username or parts.password or parts.query or parts.fragment or not parts.hostname:
            raise ValueError("Registry URL must have a host and no credentials/query/fragment")
        loopback = parts.hostname == "localhost"
        try:
            loopback = loopback or ipaddress.ip_address(parts.hostname).is_loopback
        except ValueError:
            pass
        if parts.scheme != "https" and not (parts.scheme == "http" and loopback):
            raise ValueError("Use HTTPS for remote registries; HTTP is allowed only on loopback")
        if not isinstance(token, str) or not token or len(token) > 512 or any(c in token for c in "\r\n"):
            raise ValueError("A scoped API token is required")
        self.base = base_url.rstrip("/")
        self.token = token
        self.cache = Path(cache)
        self.opener = urllib.request.build_opener(_NoRedirect())

    def request(self, method: str, path: str, payload=None, *, binary=False):
        if not (path.startswith("/api/skill-registry/") or path == "/api/jobs"
                or path.startswith("/api/jobs/")) or path.startswith("//"):
            raise ValueError("Request must stay in the skill-registry API")
        req = urllib.request.Request(self.base + path, method=method,
                                     headers={"Authorization": "Bearer " + self.token,
                                              "Accept": "application/json",
                                              "User-Agent": "skill-registry/" + __version__})
        if payload is not None:
            req.data = canonical(payload)
            req.add_header("Content-Type", "application/json")
        try:
            with self.opener.open(req, timeout=60) as response:
                maximum = MAX_ARCHIVE_BYTES if binary else MAX_ARCHIVE_BYTES * 4 // 3 + 512 * 1024
                data = response.read(maximum + 1)
        except urllib.error.HTTPError as exc:
            # Never reflect request headers or a provider response body that
            # might contain private material into logs or an agent transcript.
            raise ValueError(f"Registry returned HTTP {exc.code}") from None
        if len(data) > maximum:
            raise ValueError("Registry response exceeds the client byte bound")
        return data if binary else json.loads(data)

    def search(self, query: str, top: int = 10):
        if type(top) is not int or not 1 <= top <= 20 or not isinstance(query, str) or len(query) > 2000:
            raise ValueError("Invalid remote search bounds")
        return self.request("GET", "/api/skill-registry/search?" + urllib.parse.urlencode({"query": query, "top": top}))

    def publish(self, bundle: bytes, *, visibility: str = "private"):
        validate_bundle(bundle)
        if visibility != "private":
            raise ValueError("This release supports private/team hosting; public publishing awaits moderation")
        return self.request("POST", "/api/skill-registry/releases",
                            {"bundle_base64": base64.b64encode(bundle).decode(), "visibility": visibility})

    def create_job(self, artifact_type: str, *, input_text: str | None = None,
                   release_ref: dict | None = None, input_sha256: str = "",
                   timeout_seconds: int = 600, max_iterations: int = 3):
        return self.request("POST", "/api/jobs", {
            "artifact_type": artifact_type, "input_text": input_text, "release_ref": release_ref,
            "input_sha256": input_sha256, "timeout_seconds": timeout_seconds,
            "max_iterations": max_iterations})

    @staticmethod
    def job_path(job_id: str) -> str:
        if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", job_id):
            raise ValueError("Invalid optimizer job ID")
        return "/api/jobs/" + job_id

    def job(self, job_id: str):
        return self.request("GET", self.job_path(job_id))

    def claim_job(self, job_id: str, worker: str, lease_seconds: int = 60):
        return self.request("POST", self.job_path(job_id) + "/claim",
                            {"worker": worker, "lease_seconds": lease_seconds})

    def heartbeat_job(self, job_id: str, worker: str, token: str, lease_seconds: int = 60):
        return self.request("POST", self.job_path(job_id) + "/heartbeat",
                            {"worker": worker, "lease_token": token, "lease_seconds": lease_seconds})

    def complete_job(self, job_id: str, body: dict):
        return self.request("POST", self.job_path(job_id) + "/complete", body)

    def cancel_job(self, job_id: str):
        return self.request("POST", self.job_path(job_id) + "/cancel", {})

    def fetch(self, namespace: str, name: str, version: str, expected_sha256: str) -> dict:
        validate_coordinates(namespace, name, version)
        location = "/api/skill-registry/releases/" + "/".join(urllib.parse.quote(v, safe="") for v in (namespace, name, version))
        data = self.request("GET", location + "/bundle.zip", binary=True)
        manifest, _ = validate_bundle(data)
        if (manifest["namespace"], manifest["name"], manifest["version"], manifest["release_sha256"]) != (
                namespace, name, version, expected_sha256):
            raise ValueError("Downloaded release does not match its exact requested pin")
        self.cache.mkdir(parents=True, exist_ok=True, mode=0o700)
        atomic(self.cache / (expected_sha256 + ".zip"), data)
        return {"manifest": manifest, "cache": str(self.cache / (expected_sha256 + ".zip")),
                "offline_available": True}

    def install_cached(self, checksum: str, destination: Path) -> dict:
        if len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            raise ValueError("Expected a full release SHA256")
        data = read_bounded(self.cache / (checksum + ".zip"), MAX_ARCHIVE_BYTES)
        return install_bundle(data, destination, checksum)


def token_from_environment() -> str:
    """Credentials stay in the existing account key system, not published bundles."""
    token = os.environ.get("SKILL_REGISTRY_TOKEN", "")
    path = os.environ.get("SKILL_REGISTRY_TOKEN_FILE")
    if path:
        credential = Path(path).expanduser()
        if credential.stat().st_mode & 0o077:
            raise ValueError("Registry token file must be private (mode 600)")
        token = credential.read_text().strip()
    return token

"""Owner-scoped optimizer broker over the platform's existing Job table.

The broker stores immutable inputs and worker attestations. It never executes
uploaded content, calls a model, or promotes a candidate into a skill release.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import datetime as dt
import hashlib
import logging
import secrets

from sqlalchemy import func, select

from skill_registry.bundles import MAX_ARCHIVE_BYTES, _metadata, release_hash, validate_bundle
from skill_registry.jobs import OPTIMIZERS, artifact_snapshot
from skill_registry.util import canonical, sha

from .models import Job, JobEvent, User

log = logging.getLogger(__name__)
ADAPTER = "skill-registry/v1"
ACTIVE = ("queued", "running", "held")


class BrokerError(ValueError):
    def __init__(self, status: int, detail: str):
        self.status, self.detail = status, detail
        super().__init__(detail)


def _now():
    return dt.datetime.now(dt.UTC)


def normalized_skill_hash(manifest):
    return release_hash(
        dict(manifest, namespace="local", name="optimization-input", version="0.0.0")
    )


def describe(row, *, include_input=False, lease_token=None):
    params = row.params
    result = {
        "id": row.id,
        "status": row.status,
        "kind": row.kind,
        "artifact_type": params["artifact_type"],
        "optimizer_id": params["optimizer_id"],
        "input_sha256": row.input_hash,
        "source_release_sha256": params.get("source_release_sha256"),
        "timeout_seconds": params["timeout_seconds"],
        "max_iterations": params["max_iterations"],
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "worker": row.worker,
        "attempts": row.attempts,
        "lease_expires": row.lease_expires.isoformat() if row.lease_expires else None,
        "execution_deadline": params.get("deadline"),
        "lease_expired": bool(
            row.status == "running" and row.lease_expires and row.lease_expires <= _now()
        ),
        "result": params.get("result"),
        "published": False,
    }
    if include_input:
        result["input_snapshot"] = params["input_snapshot"]
    if lease_token is not None:
        result["lease_token"] = lease_token
    return result


async def get(session, owner, job_id, *, lock=False):
    query = select(Job).where(
        Job.id == job_id,
        Job.user_id == owner,
        Job.kind == "optimize",
        Job.params["adapter"].astext == ADAPTER,
    )
    if lock:
        query = query.with_for_update()
    row = await session.scalar(query)
    if row is None:
        raise BrokerError(404, "no such optimizer job")
    return row


async def event(session, row, operation):
    sequence = await session.scalar(
        select(func.coalesce(func.max(JobEvent.seq), 0)).where(JobEvent.job_id == row.id)
    )
    session.add(
        JobEvent(
            job_id=row.id,
            seq=sequence + 1,
            kind="stage",
            payload={"operation": operation, "status": row.status},
        )
    )


async def create(session, owner, body, settings, *, source_release=None):
    kind = body["artifact_type"]
    if kind not in OPTIMIZERS:
        raise BrokerError(422, "unsupported optimizer artifact type")
    if source_release is not None:
        manifest, _ = await asyncio.to_thread(validate_bundle, source_release.bundle)
        if manifest["release_sha256"] != source_release.release_sha256:
            raise BrokerError(409, "source release identity is inconsistent")
        reference = body["release_ref"]
        if reference["release_sha256"] != source_release.release_sha256:
            raise BrokerError(409, "source release pin changed")
        input_hash = normalized_skill_hash(manifest)
        snapshot = {
            "format": "skill-release/v1",
            "bundle_base64": base64.b64encode(source_release.bundle).decode(),
            "manifest": manifest,
        }
        source_ref = "skill-release:" + source_release.id
    else:
        text = body.get("input_text")
        try:
            raw = text.encode("utf-8") if isinstance(text, str) else b""
        except UnicodeError as exc:
            raise BrokerError(422, "optimizer input must be valid UTF-8") from exc
        if not raw or len(raw) > settings.optimizer_max_text_bytes:
            raise BrokerError(422, "optimizer text input is missing or too large")
        try:
            _, _, input_hash = artifact_snapshot(kind, None, text)
        except (ValueError, UnicodeError) as exc:
            raise BrokerError(422, "invalid optimizer input") from exc
        snapshot = {"format": "text/v1", "text": text}
        source_ref = None
    expected = body.get("input_sha256")
    if expected and expected != input_hash:
        raise BrokerError(409, "optimizer input checksum mismatch")
    signature = sha(
        canonical(
            {
                "artifact_type": kind,
                "input_hash": input_hash,
                "timeout_seconds": body["timeout_seconds"],
                "max_iterations": body["max_iterations"],
                "source_ref": source_ref,
                "retry_of": body.get("retry_of"),
            }
        )
    )
    await session.scalar(select(User).where(User.id == owner).with_for_update())
    cutoff = _now() - dt.timedelta(days=1)
    same = await session.scalar(
        select(Job)
        .where(
            Job.user_id == owner,
            Job.created_at >= cutoff,
            Job.input_hash == input_hash,
            Job.params["request_sha256"].astext == signature,
        )
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    if same is not None:
        return same, False
    if body.get("retry_of"):
        previous = await get(session, owner, body["retry_of"], lock=True)
        if previous.status not in {"failed", "cancelled", "held"}:
            raise BrokerError(409, "only failed, cancelled or held jobs can be retried")
        if previous.input_hash != input_hash:
            raise BrokerError(409, "retry input must match the original request")
    active = await session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == owner, Job.status.in_(ACTIVE))
    )
    if active >= settings.optimizer_max_active_jobs:
        raise BrokerError(429, "optimizer active-job quota reached")
    daily = await session.scalar(
        select(func.count()).select_from(Job).where(Job.user_id == owner, Job.created_at >= cutoff)
    )
    if daily >= settings.optimizer_max_jobs_per_day:
        raise BrokerError(429, "optimizer daily-job quota reached")
    params = {
        "adapter": ADAPTER,
        "artifact_type": kind,
        "optimizer_id": OPTIMIZERS[kind],
        "timeout_seconds": body["timeout_seconds"],
        "max_iterations": body["max_iterations"],
        "request_sha256": signature,
        "input_snapshot": snapshot,
        "source_release_sha256": source_release.release_sha256 if source_release else None,
        "retry_of": body.get("retry_of"),
    }
    row = Job(
        user_id=owner,
        kind="optimize",
        input_ref=source_ref,
        input_hash=input_hash,
        params=params,
        status="queued",
    )
    session.add(row)
    await session.flush()
    await event(session, row, "queued")
    log.info("optimizer_job_created job_id=%s artifact_type=%s", row.id, kind)
    return row, True


async def claim(session, row, worker, lease_seconds):
    now = _now()
    if row.status == "running" and row.lease_expires and row.lease_expires <= now:
        row.status = "held"
        row.params = {
            **row.params,
            "lease_token_hash": None,
            "hold_reason": "worker lease expired; execution is uncertain",
        }
        await event(session, row, "lease-expired")
        return None
    if row.status != "queued":
        raise BrokerError(409, "optimizer job is not queued")
    token = secrets.token_urlsafe(32)
    row.status, row.worker = "running", worker
    row.started_at = row.last_heartbeat = now
    row.attempts += 1
    deadline = now + dt.timedelta(seconds=row.params["timeout_seconds"])
    row.lease_expires = min(deadline, now + dt.timedelta(seconds=lease_seconds))
    row.params = {
        **row.params,
        "lease_token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "deadline": deadline.isoformat(),
    }
    await event(session, row, "claimed")
    return token


def lease(row, worker, token):
    if (
        row.status != "running"
        or row.worker != worker
        or not row.lease_expires
        or row.lease_expires <= _now()
        or not secrets.compare_digest(
            row.params.get("lease_token_hash") or "", hashlib.sha256(token.encode()).hexdigest()
        )
    ):
        raise BrokerError(409, "optimizer worker lease is missing, expired or invalid")


async def heartbeat(session, row, worker, token, lease_seconds):
    lease(row, worker, token)
    now = _now()
    deadline = dt.datetime.fromisoformat(row.params["deadline"])
    row.last_heartbeat = now
    row.lease_expires = min(deadline, now + dt.timedelta(seconds=lease_seconds))
    return row


async def complete(session, row, body, settings):
    lease(row, body["worker"], body["lease_token"])
    if body["input_sha256"] != row.input_hash:
        raise BrokerError(409, "optimizer completion does not bind its requested input")
    candidate_text, candidate_bundle = (
        body.get("candidate_text"),
        body.get("candidate_bundle_base64"),
    )
    server_checks = []
    snapshot = row.params["input_snapshot"]
    result = {
        "schema": "optimization-result/v1",
        "input_sha256": row.input_hash,
        "worker_exit_code": body["exit_code"],
        "worker_execution_reported": True,
        "execution_independently_verified": False,
        "reported_checks": body["checks"],
        "worker_checks_reported_passed": bool(body["checks"])
        and all(check["exit_code"] == 0 for check in body["checks"]),
        "reported_convergence": body["convergence_status"],
        "converged": False,
        "published": False,
        "summary": body["summary"],
    }
    if body["exit_code"] == 0:
        if snapshot["format"] == "skill-release/v1":
            if candidate_text is not None or not candidate_bundle:
                raise BrokerError(422, "a released skill requires a complete candidate bundle")
            try:
                data = base64.b64decode(candidate_bundle, validate=True)
                if len(data) > MAX_ARCHIVE_BYTES:
                    raise ValueError("candidate too large")
                manifest, _ = await asyncio.to_thread(validate_bundle, data)
            except (ValueError, binascii.Error) as exc:
                raise BrokerError(422, "invalid optimizer candidate bundle") from exc
            source = snapshot["manifest"]
            if manifest["namespace"] != row.user_id or manifest["name"] != source["name"]:
                raise BrokerError(422, "candidate must preserve source namespace and skill name")
            candidate_hash = normalized_skill_hash(manifest)
            result["candidate_bundle_base64"] = candidate_bundle
            result["candidate_manifest"] = manifest
            server_checks.append({"name": "complete-bundle-identity", "exit_code": 0})
        else:
            try:
                raw = candidate_text.encode("utf-8") if candidate_text else b""
            except UnicodeError as exc:
                raise BrokerError(422, "candidate text must be valid UTF-8") from exc
            if (
                candidate_bundle is not None
                or not raw
                or len(raw) > settings.optimizer_max_text_bytes
            ):
                raise BrokerError(422, "a text artifact requires bounded candidate text")
            try:
                if row.params["artifact_type"] == "skill":
                    _metadata(candidate_text.encode())
                candidate_hash = artifact_snapshot(
                    row.params["artifact_type"], None, candidate_text
                )[2]
            except (ValueError, UnicodeError) as exc:
                raise BrokerError(422, "invalid optimizer candidate text") from exc
            result["candidate_text"] = candidate_text
            server_checks.append(
                {"name": "candidate-bytes-and-required-frontmatter", "exit_code": 0}
            )
        result.update(candidate_sha256=candidate_hash, changed=candidate_hash != row.input_hash)
    result["server_checks"] = server_checks
    result["server_checks_passed"] = bool(server_checks)
    row.status = "done" if body["exit_code"] == 0 else "failed"
    row.finished_at = _now()
    row.lease_expires = None
    row.params = {**row.params, "lease_token_hash": None, "result": result}
    await event(session, row, "completed")
    log.info("optimizer_job_completed job_id=%s status=%s", row.id, row.status)
    return row


async def cancel(session, row):
    if row.status in {"queued", "running", "held", "created"}:
        row.status, row.lease_expires, row.finished_at = "cancelled", None, _now()
        row.params = {**row.params, "lease_token_hash": None, "cancel_requested": True}
        await event(session, row, "cancelled")
        log.info("optimizer_job_cancelled job_id=%s", row.id)
    return row

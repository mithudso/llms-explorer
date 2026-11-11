"""Run an explicitly claimed hosted request on its owner's trusted local worker."""

from __future__ import annotations

import base64
import datetime as dt
import threading
import uuid

from .bundles import MAX_FILE_BYTES, build_bundle, install_bundle, release_hash, validate_bundle
from .util import atomic, canonical, read_bounded, sha, validate_workspace
from .worker import run_one


def run_remote(service, job_id: str, command: list[str], *, worker: str = "owner-local-worker",
               stop_event: threading.Event | None = None):
    stop_event = stop_event if stop_event is not None else threading.Event()
    if stop_event.is_set():
        return {"remote": {"id": job_id, "status": "not-claimed"}, "local_job_id": None}
    remote = service.remote()
    leased = remote.claim_job(job_id, worker)
    token = leased["lease_token"]
    binding = service.state / "remote-runs" / (job_id + "-" + uuid.uuid4().hex)
    binding.mkdir(parents=True, mode=0o700)
    atomic(binding / "binding.json", canonical({"job_id": job_id, "worker": worker,
        "lease_token": token, "remote_url": remote.base, "input_sha256": leased["input_sha256"]}))
    local = None
    stop = threading.Event()
    heartbeat_errors = []
    thread = None

    def report_cancelled():
        if local:
            service.jobs.cancel(local["id"])
        reported = remote.cancel_job(job_id)
        atomic(binding / "binding.json", canonical({"job_id": job_id,
            "local_job": local["id"] if local else None, "remote_url": remote.base,
            "reported": True, "status": reported["status"],
            "finished_at": dt.datetime.now(dt.UTC).isoformat()}))
        return {"remote": reported, "local_job_id": local["id"] if local else None,
                "cancelled": reported["status"] == "cancelled", "reported": True}

    try:
        if stop_event.is_set():
            return report_cancelled()
        snapshot = leased["input_snapshot"]
        definition = service.definition(leased["artifact_type"])
        arguments = {}
        if snapshot["format"] == "skill-release/v1":
            data = base64.b64decode(snapshot["bundle_base64"], validate=True)
            manifest, _ = validate_bundle(data)
            if manifest["release_sha256"] != leased["source_release_sha256"]:
                raise ValueError("Hosted source release pin differs from its snapshot")
            source = binding / "source"
            install_bundle(data, source, manifest["release_sha256"])
            arguments["target"] = source / "SKILL.md"
        elif snapshot["format"] == "text/v1":
            arguments["input_text"] = snapshot["text"]
        else:
            raise ValueError("Unsupported hosted input snapshot")
        # Reserve reporting time inside the server's absolute budget.
        remote.heartbeat_job(job_id, worker, token)
        remaining = leased["timeout_seconds"]
        if leased.get("execution_deadline"):
            remaining = (dt.datetime.fromisoformat(leased["execution_deadline"])
                         - dt.datetime.now(dt.UTC)).total_seconds()
        if remaining <= 1:
            raise ValueError("Hosted execution budget expired during preparation")
        timeout = max(1, int(remaining) - 10)
        if stop_event.is_set():
            return report_cancelled()
        local = service.jobs.enqueue(leased["artifact_type"], **arguments,
            expected_sha256=leased["input_sha256"], timeout_seconds=timeout,
            max_iterations=leased["max_iterations"], definition=definition)

        def heartbeat():
            while not stop.wait(10):
                try:
                    remote.heartbeat_job(job_id, worker, token)
                except (ValueError, OSError) as exc:
                    heartbeat_errors.append(type(exc).__name__)
                    service.jobs.cancel(local["id"])
                    return

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        completed = run_one(service.jobs, command, worker=worker, jid=local["id"],
                            check_commands=service.config.get("check_commands", []),
                            stop_event=stop_event)
        stop.set()
        thread.join(timeout=65)
        if stop_event.is_set() or completed is None or completed["status"] == "cancelled":
            return report_cancelled()
        result = completed["result"] or {}
        payload = {"worker": worker, "lease_token": token,
                   "input_sha256": leased["input_sha256"],
                   "exit_code": result.get("exit_code") if completed["status"] == "executed" else 1,
                   "checks": [{"name": c["name"], "exit_code": c["exit_code"]}
                              for c in result.get("checks", [])],
                   "convergence_status": result.get("convergence", {}).get("status", "UNREPORTED"),
                   "summary": "Owner-local worker completed; native convergence is a separate worker report."}
        if payload["exit_code"] == 0:
            workspace = service.jobs.state / "runs" / local["id"]
            canonical_workspace = validate_workspace(workspace, local["params"].get("workspace"))
            candidate = workspace / "candidate"
            if snapshot["format"] == "skill-release/v1":
                manifest = snapshot["manifest"]
                outgoing, data = build_bundle(candidate, manifest["namespace"], manifest["name"], manifest["version"])
                identity = release_hash(dict(outgoing, namespace="local", name="optimization-input", version="0.0.0"))
                if identity != result["candidate_sha256"]:
                    raise ValueError("Candidate changed after local verification")
                payload["candidate_bundle_base64"] = base64.b64encode(data).decode()
            else:
                path = candidate / local["params"]["filename"]
                if path.is_symlink() or not path.resolve().is_relative_to(canonical_workspace / "candidate"):
                    raise ValueError("Candidate escaped before remote reporting")
                outgoing = read_bounded(path, MAX_FILE_BYTES)
                identity = (sha(canonical({path.name: sha(outgoing)}))
                            if leased["artifact_type"] == "skill" else sha(outgoing))
                if identity != result["candidate_sha256"]:
                    raise ValueError("Candidate changed after local verification")
                payload["candidate_text"] = outgoing.decode("utf-8")
        reported = remote.complete_job(job_id, payload)
        atomic(binding / "binding.json", canonical({"job_id": job_id, "local_job": local["id"],
            "remote_url": remote.base, "reported": True, "status": reported["status"],
            "finished_at": dt.datetime.now(dt.UTC).isoformat()}))
        return {"remote": reported, "local_job_id": local["id"],
                "local_result": result, "heartbeat_errors": heartbeat_errors}
    except KeyboardInterrupt:
        stop_event.set()
        report_cancelled()
        raise
    except Exception as exc:
        try:
            if stop_event.is_set():
                return report_cancelled()
            else:
                status = remote.job(job_id)
                if status["status"] == "running":
                    status = remote.complete_job(job_id, {"worker": worker, "lease_token": token,
                        "input_sha256": leased["input_sha256"], "exit_code": 1,
                        "summary": "Owner-local worker could not complete: " + type(exc).__name__})
        except Exception:
            status = {"id": job_id, "status": "report-pending"}
        return {"remote": status, "local_job_id": local["id"] if local else None,
                "error_type": type(exc).__name__, "reported": status["status"] != "report-pending",
                "recovery": str(binding / "binding.json")}
    finally:
        stop.set()
        if thread:
            thread.join(timeout=65)

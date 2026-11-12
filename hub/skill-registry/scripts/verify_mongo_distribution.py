#!/usr/bin/env python3
"""Verify a real remote MCP deployment without a MongoDB URI or installed skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from skill_registry.environment import load_environment
from skill_registry.prompt_hook import _NoRedirect


def verify(url: str, token: str, name: str) -> dict:
    from skill_registry.prompt_hook import HTTPStore
    HTTPStore(url, token)  # Apply the same HTTPS and credential separation rules.
    protocol = "2025-06-18"
    sequence = 0
    timings = {}

    def request(method, params, *, authenticated=True):
        nonlocal sequence
        sequence += 1
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": protocol}
        if authenticated:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": sequence,
            "method": method, "params": params}).encode(), headers=headers)
        started = time.monotonic()
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=90) as response:
            assert response.headers.get("cache-control") == "no-store"
            body = response.read(4 * 1024 * 1024 + 1)
            assert len(body) <= 4 * 1024 * 1024
            value = json.loads(body)
        timings[method + ":" + str(sequence)] = round(time.monotonic() - started, 3)
        assert "error" not in value, value.get("error")
        return value["result"]

    def call(tool, arguments, *, expected_error=False):
        value = request("tools/call", {"name": tool, "arguments": arguments})
        if expected_error:
            assert value.get("isError") is True
            return
        assert not value.get("isError"), value.get("content")
        return value["structuredContent"]

    try:
        request("tools/list", {}, authenticated=False)
        raise AssertionError("Unauthenticated MCP request was accepted")
    except urllib.error.HTTPError as exc:
        assert exc.code == 401
    initialized = request("initialize", {"protocolVersion": protocol, "capabilities": {},
        "clientInfo": {"name": "independent-distribution-verifier", "version": "1"}})
    protocol = initialized["protocolVersion"]
    tools = request("tools/list", {})["tools"]
    assert {"skill_search", "skill_get", "skill_resource", "skills_status"} <= {
        tool["name"] for tool in tools}
    assert all(tool["annotations"]["readOnlyHint"] for tool in tools)
    status = call("skills_status", {})
    assert status["search_ready"]
    found = call("skill_search", {"query": name, "mode": "hybrid", "top": 5})
    assert found["semantic"] and not found["degraded"], found["diagnostics"]
    hit = next(hit for hit in found["hits"] if hit["name"] == name)
    pin = hit["release_sha256"]
    arguments = {"skill_id": hit["id"], "expected_sha256": pin}
    guide, offset = "", 0
    while True:
        page = call("skill_get", {**arguments, "offset": offset, "max_chars": 32000})
        guide += page["text"]
        if page["next_offset"] is None:
            break
        offset = page["next_offset"]
        assert len(guide) <= 2 * 1024 * 1024
    assert hashlib.sha256(guide.encode()).hexdigest() == hit["sha256"]
    resource = call("skill_resource", {**arguments, "path": "references/verification.txt"})
    resource_hash = hashlib.sha256(resource["text"].encode()).hexdigest()
    assert resource_hash == resource["resource_sha256"]
    call("skill_get", {**arguments, "expected_sha256": "0" * 64}, expected_error=True)
    call("skill_resource", {**arguments, "path": "../private.env"}, expected_error=True)
    return {"passed": True, "url": url, "skill": name, "id": hit["id"],
        "release_sha256": pin, "resource_sha256": resource_hash,
        "verification_text": resource["text"].strip(), "counts": status["counts"],
        "semantic": found["diagnostics"]["channels"]["semantic"],
        "lexical": found["diagnostics"]["channels"]["lexical"], "timings_seconds": timings,
        "local_skill_files_used": False, "mongodb_credentials_required": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--skill", default="remote-skill-distribution-check")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    load_environment(args.env_file)
    result = verify(os.environ["SKILL_MCP_URL"], os.environ["SKILL_MCP_TOKEN"], args.skill)
    serialized = json.dumps(result, indent=2) + "\n"
    if args.receipt:
        args.receipt.write_text(serialized)
        args.receipt.chmod(0o600)
    print(serialized, end="")


if __name__ == "__main__":
    main()

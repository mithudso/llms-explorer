#!/usr/bin/env python3
"""Validate, render and narrowly install the eleven workflow agent definitions."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tomllib

VERSION = "1.0.0"
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "agents/workflows/catalog.json"
EXPECTED_NAMES = frozenset(
    {
        "continuation-recovery",
        "live-acceptance-verifier",
        "local-model-qualification",
        "research-contract-auditor",
        "memory-health-reconciler",
        "agent-asset-parity-auditor",
        "distribution-release-closer",
        "textual-job-lifecycle-specialist",
        "guarded-artifact-writer",
        "userscript-interaction-verifier",
        "prompt-memory-workflow-miner",
    }
)
MODES = {
    "read-only",
    "execute-within-authorization",
    "proposal-unless-maintenance-authorized",
    "read-only-unless-targeted-repair-authorized",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def nonempty_strings(value, field):
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError(f"{field} must be a nonempty list of nonempty strings")


def load_catalog(path=DEFAULT_CATALOG):
    catalog = json.loads(Path(path).read_text())
    if not re.fullmatch(r"\d+\.\d+\.\d+", catalog.get("version", "")):
        raise ValueError("catalog version must be semantic")
    nonempty_strings(catalog.get("common_instructions"), "common_instructions")
    agents = catalog.get("agents")
    if not isinstance(agents, list) or len(agents) != len(EXPECTED_NAMES):
        raise ValueError("catalog must contain exactly eleven agents")
    names = [agent.get("name") for agent in agents]
    if len(set(names)) != len(names) or set(names) != EXPECTED_NAMES:
        raise ValueError("agent names must be unique and match the eleven approved names")
    for agent in agents:
        for field in ("title", "description"):
            if not isinstance(agent.get(field), str) or not agent[field].strip():
                raise ValueError(f"{agent['name']}: invalid {field}")
        if len(agent["description"]) > 1024 or "\n" in agent["description"]:
            raise ValueError(
                f"{agent['name']}: description must be one line, at most 1024 characters"
            )
        if agent.get("mode") not in MODES:
            raise ValueError(f"{agent['name']}: unsupported mode")
        for field in ("triggers", "exclusions", "reuse", "steps", "output_fields"):
            nonempty_strings(agent.get(field), f"{agent['name']}.{field}")
        cases = agent.get("cases", [])
        if len(cases) != 3 or {case.get("kind") for case in cases} != {
            "positive",
            "boundary",
            "near_miss",
        }:
            raise ValueError(f"{agent['name']}: require positive, boundary and near-miss cases")
        for case in cases:
            if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
                raise ValueError("case needs a prompt")
            if case["kind"] == "near_miss":
                if not isinstance(case.get("route"), str) or not case["route"].strip():
                    raise ValueError("near-miss case needs an existing route")
            else:
                nonempty_strings(case.get("must"), "case.must")
                nonempty_strings(case.get("must_not"), "case.must_not")
    return catalog


def body_for(catalog, agent):
    sections = [
        f"# {agent['title']}",
        f"Definition version: {catalog['version']}",
        f"Mode: {agent['mode']}",
        "## Shared execution contract",
        "\n\n".join(catalog["common_instructions"]),
        "## Use for",
        "\n".join(f"- {item}" for item in agent["triggers"]),
        "## Route elsewhere",
        "\n".join(f"- {item}" for item in agent["exclusions"]),
        "## Reuse existing capabilities",
        "\n".join(f"- {item}" for item in agent["reuse"]),
        "## Workflow",
        "\n\n".join(f"{i}. {item}" for i, item in enumerate(agent["steps"], 1)),
        "## Receipt details",
        "\n".join(f"- {item}" for item in agent["output_fields"]),
    ]
    return "\n\n".join(sections) + "\n"


def render(catalog):
    """Use the same three Codex fields as the installed Claude migration."""
    files = {}
    for agent in catalog["agents"]:
        body = body_for(catalog, agent)
        description = json.dumps(agent["description"], ensure_ascii=False)
        claude = (
            f"---\nname: {agent['name']}\ndescription: {description}\nmodel: inherit\n---\n\n{body}"
        )
        codex = (
            "\n".join(
                f"{key} = {json.dumps(value, ensure_ascii=False)}"
                for key, value in {
                    "name": agent["name"],
                    "description": agent["description"],
                    "developer_instructions": body.strip(),
                }.items()
            )
            + "\n"
        )
        parsed = tomllib.loads(codex)
        if parsed["developer_instructions"] != body.strip():
            raise ValueError("rendered Codex body differs from Claude source")
        files[f".claude/agents/{agent['name']}.md"] = claude.encode()
        files[f".codex/agents/{agent['name']}.toml"] = codex.encode()
    return files


def checked_target(root, relative):
    target = root / relative
    current = target
    while current != root:
        if current.is_symlink():
            raise ValueError(f"refusing symlink target or ancestor: {current}")
        current = current.parent
    return target


def plan_files(root, files):
    plan = []
    for relative, data in files.items():
        target = checked_target(root, relative)
        if target.exists() and (not target.is_file() or target.read_bytes() != data):
            raise ValueError(f"refusing to overwrite a different existing definition: {target}")
        plan.append((target, data, "unchanged" if target.exists() else "create"))
    return plan


def exclusive_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def apply_files(root, files):
    """Preflight the whole set; create-only writes cannot overwrite a racing writer."""
    plan = plan_files(root, files)
    created = []
    try:
        for target, data, state in plan:
            if state == "create":
                exclusive_write(target, data)
                created.append((target, data))
            elif target.read_bytes() != data:
                raise ValueError(f"definition changed after preflight: {target}")
        verify_files(root, files)
    except BaseException:
        for target, data in reversed(created):
            if target.is_file() and not target.is_symlink() and target.read_bytes() == data:
                target.unlink()
        raise
    return [
        {"path": str(target), "sha256": digest(data), "action": state}
        for target, data, state in plan
    ]


def verify_files(root, files):
    for relative, data in files.items():
        target = checked_target(root, relative)
        if not target.is_file() or target.read_bytes() != data:
            raise ValueError(f"installed definition missing or different: {target}")


def evaluate_responses(catalog, path):
    """Grade explicit human verdicts for real saved responses, never lexical self-checks."""
    responses = json.loads(Path(path).read_text())
    results = []
    for agent in catalog["agents"]:
        for case in agent["cases"]:
            key = f"{agent['name']}:{case['kind']}"
            response = responses.get(key)
            if not isinstance(response, dict) or not response.get("response"):
                raise ValueError(f"missing actual response: {key}")
            if response.get("verdict") not in {"pass", "fail"} or not response.get("reviewer"):
                raise ValueError(f"missing independent review verdict: {key}")
            if not response.get("evidence"):
                raise ValueError(f"missing review evidence: {key}")
            results.append(
                {"case": key, "verdict": response["verdict"], "reviewer": response["reviewer"]}
            )
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["list", "validate", "render", "install", "verify", "evaluate"]
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--home", type=Path, default=Path.home(), help="target home for install/verify"
    )
    parser.add_argument("--output", type=Path, help="required destination for render")
    parser.add_argument(
        "--apply", action="store_true", help="install definitions; otherwise preview only"
    )
    parser.add_argument(
        "--responses", type=Path, help="real saved responses and independent review verdicts"
    )
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        files = render(catalog)
        result = {
            "version": catalog["version"],
            "agent_count": len(catalog["agents"]),
            "definition_count": len(files),
            "behavioral_evaluation": "not_run",
        }
        if args.action == "list":
            result["agents"] = [
                {"name": a["name"], "mode": a["mode"], "description": a["description"]}
                for a in catalog["agents"]
            ]
        elif args.action in {"install", "render"}:
            if args.action == "render" and args.output is None:
                raise ValueError("render requires --output")
            root = (args.output if args.action == "render" else args.home).expanduser().resolve()
            apply = args.action == "render" or args.apply
            plan = (
                apply_files(root, files)
                if apply
                else [
                    {"path": str(p), "sha256": digest(data), "action": state}
                    for p, data, state in plan_files(root, files)
                ]
            )
            result.update(applied=apply, files=plan)
        elif args.action == "verify":
            verify_files(args.home.expanduser().resolve(), files)
            result["installed_parity"] = "pass"
        elif args.action == "evaluate":
            if args.responses is None:
                raise ValueError("evaluate requires --responses from actual agent executions")
            results = evaluate_responses(catalog, args.responses)
            result.update(behavioral_evaluation="reviewed", cases=results)
            if any(row["verdict"] == "fail" for row in results):
                print(json.dumps(result, indent=2))
                return 1
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""The judge can inspect exact response failures without changing paid evidence."""

import copy
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location(
    "response_check_gate",
    Path(__file__).resolve().parents[1] / "scripts/research_gate.py",
)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


@pytest.fixture
def case(tmp_path):
    root = tmp_path / "quotes ' Unicode café $HOME"
    root.mkdir()
    url = "https://example.org/parameters"
    text = "The numCandidates parameter has a documented limit of 10000 entries."
    source = root / "source.txt"
    source.write_text(text)
    span = {
        "url": url,
        "source_id": "src:one",
        "snapshot_sha256": gate.digest(text.encode()),
        "start": 0,
        "end": len(text),
        "quote": text,
        "extraction_status": "complete",
    }
    doc = {
        "concept": "Parameters",
        "claims": [
            {"text": text, "confidence": "low", "sources": [url], "evidence": [span]}
        ],
        "open_questions": ["How should a new workload choose its parameters?"],
        "sources": [{"url": url}],
    }
    manifest = {
        "slug": "test",
        "gate_contract_version": 4,
        "depth": "quick",
        "concepts": [{"name": "Parameters", "slug": "parameters", "status": "done"}],
    }

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    shared = SimpleNamespace(
        load_claims=lambda *args: {"parameters": doc},
        atomic_write=write,
        run_dir=lambda slug: root,
        source_id=lambda url: "src:one",
        lib_find=lambda url: {
            "url": url,
            "id": "src:one",
            "text_path": str(source),
            "sha256": gate.digest(source.read_bytes()),
        },
    )
    attempt = root / "attempt"
    packet = gate.prepare(shared, manifest, attempt, "all", 0)
    verdicts = []
    for claim in packet["claims"]:
        auxiliary = bool(claim.get("assertion_kind"))
        verdicts.append(
            {
                **{key: claim[key] for key in ("claim_id", "claim_sha256", "text")},
                "verdict": gate.NO_ASSERTION if auxiliary else "SUPPORTED",
                "rationale": "This is a pure workload question."
                if auxiliary
                else "The complete passage supports this exact parameter and its limit.",
                "evidence": [] if auxiliary else copy.deepcopy(claim["evidence"]),
            }
        )
    response = {
        "schema": gate.STRICT_SCHEMA,
        "packet_sha256": packet["packet_sha256"],
        "verdicts": verdicts,
        "conflict_reviewed_claim_ids": [row["claim_id"] for row in packet["claims"]],
        "conflicts": [],
    }
    return attempt, packet, response


def save(case):
    root, packet, response = case
    packet["packet_sha256"] = gate.digest(
        {k: v for k, v in packet.items() if k != "packet_sha256"}
    )
    response["packet_sha256"] = packet["packet_sha256"]
    (root / "packet.json").write_text(json.dumps(packet))
    path = root / "verdicts.json"
    path.write_text(json.dumps(response))
    return root, path, packet["packet_sha256"]


@pytest.mark.parametrize(
    "verdict", ["SUPPORTED", "UNVERIFIED", "NOT-IN-SOURCE", "CONTRADICTED"]
)
def test_valid_negative_is_valid_format_and_keeps_its_verdict(case, verdict, capsys):
    case[2]["verdicts"][0]["verdict"] = verdict
    if verdict != "SUPPORTED":
        case[2]["verdicts"][0]["evidence"] = []
    root, path, digest = save(case)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert (
        gate.response_check_main(
            [
                "check-response",
                "--root",
                str(root),
                "--response",
                str(path),
                "--packet-sha256",
                digest,
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["structurally_valid"]
    assert report["all_supported"] == (verdict == "SUPPORTED")
    assert report["counts"][verdict] == 1
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_aggregates_selected_literal_failures_and_preserves_inputs(case, monkeypatch):
    root, _packet, response = case
    # Both genuine selected quote fragments omit required literals.
    span = response["verdicts"][0]["evidence"][0]
    offset = span["quote"].index("parameter")
    span.update(start=offset, quote=span["quote"][offset:])
    question = response["verdicts"][1]
    question["verdict"] = "SUPPORTED"
    question["evidence"] = []
    args = save(case)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def no_write(*args, **kwargs):
        pytest.fail("checker attempted an input or state write")

    monkeypatch.setattr(Path, "write_text", no_write)
    monkeypatch.setattr(Path, "write_bytes", no_write)
    monkeypatch.setattr(subprocess, "run", no_write)
    report = gate.check_response(*args)
    assert not report["structurally_valid"]
    assert len(report["errors"]) == 2
    assert "numCandidates" in report["errors"][0]["error"]
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize(
    "failure",
    [
        "missing",
        "duplicate",
        "wrong-source",
        "uncited",
        "stale-hash",
        "wrong-quote",
        "changed-claim",
        "conflict-coverage",
        "unattributed",
        "packet",
        "parent-hash",
        "source",
    ],
)
def test_same_strict_rules_reject_invalid_responses(case, failure, capsys):
    root, packet, response = case
    span = response["verdicts"][0]["evidence"][0]
    if failure == "missing":
        response["verdicts"].pop()
    elif failure == "duplicate":
        response["verdicts"][1] = copy.deepcopy(response["verdicts"][0])
    elif failure == "wrong-source":
        span["source_id"] = "src:other"
    elif failure == "uncited":
        span["url"] = "https://other.example/uncited"
    elif failure == "stale-hash":
        span["snapshot_sha256"] = "0" * 64
    elif failure == "wrong-quote":
        span["quote"] += " fabricated"
    elif failure == "changed-claim":
        response["verdicts"][0]["text"] += " with no exceptions"
    elif failure == "conflict-coverage":
        response["conflict_reviewed_claim_ids"].pop()
    elif failure == "unattributed":
        response["conflicts"] = [
            {
                "claim_ids": [packet["claims"][0]["claim_id"]],
                "resolution": "attributed",
                "rationale": "The claim does not contain attributed-conflict metadata.",
            }
        ]
    root, path, digest = save(case)
    if failure == "packet":
        packet["coverage"]["total_claims"] += 1
        (root / "packet.json").write_text(json.dumps(packet))
    elif failure == "parent-hash":
        # Even a rehashed replacement packet differs from the parent's brief.
        packet["coverage"]["total_claims"] += 1
        save(case)
    elif failure == "source":
        source = root / next(iter(packet["sources"].values()))["file"]
        source.write_text(source.read_text() + " changed")
    assert (
        gate.response_check_main(
            [
                "check-response",
                "--root",
                str(root),
                "--response",
                str(path),
                "--packet-sha256",
                digest,
            ]
        )
        == 1
    )
    assert not json.loads(capsys.readouterr().out)["structurally_valid"]


def test_exact_reuse_is_combined_in_memory_and_cannot_be_resubmitted(case):
    root, packet, response = case
    packet["reused_verdicts"] = [response["verdicts"].pop(0)]
    args = save(case)
    before = (root / "verdicts.json").read_bytes()
    assert gate.check_response(*args)["all_supported"]
    assert (root / "verdicts.json").read_bytes() == before
    response["verdicts"].append(packet["reused_verdicts"][0])
    with pytest.raises(ValueError, match="missing or extra"):
        gate.check_response(*save(case))


def test_real_shell_safe_brief_command_and_no_bytecode_output(case):
    root, packet, _ = case
    save(case)
    text = gate.brief(packet, root)
    command = next(
        line for line in text.splitlines() if "check-response --root" in line
    )
    args = shlex.split(command)
    assert args[:2] == [sys.executable, "-B"]
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr or result.stdout
    assert json.loads(result.stdout)["all_supported"]
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}

# Shared optimizer acceptance evidence

Version: 1.0.0
Delta: initial executable verification contract.

## Purpose and limits

Use this contract for every optimizer that cites convergence-and-severity.md.
A verified acceptance claim needs current artifact bindings, completed successful
checks and an independent final review. Installed changes also need actual loaded
identity and an exercised installed entry point. The existing ship-it installation
rule remains authoritative.

The stdlib evidence_gate.py checks declared roles, file hashes and outcomes. It
cannot establish that a reviewer was independent, that a logged observation is
truthful, or that the declared files cover the entire product. The orchestrator
must collect actual tool outputs and independent review, define the complete
scoped artifact set, and preserve the underlying captures/logs. Never create a
self-authored statement as a substitute for an unexecuted check.

## Artifact binding

An acceptance JSON object has schema_version equal to 1 and an artifacts list.
Each artifact has a unique nonempty string id, path, and exact lowercase SHA-256.
Paths are absolute or relative to the JSON file. The checker reads each actual
file and rejects a stale declared hash. The combined artifact_sha256 is SHA-256
of the sorted (id, file-hash) pairs encoded with compact JSON. IDs remain stable
across source and installation locations, so equal contents can share a binding.
Include all source/configuration/data files that can affect the scoped result.

Compute the binding from actual files, without editing the supplied JSON:

```sh
python3 evidence_gate.py acceptance.json --fingerprint
```

Copy the returned artifact_sha256 into the acceptance object and its current
receipts. Recollect affected evidence after any artifact change. The validator
must not treat an unchanged capture file as proof that it belongs to changed code.

## Required evidence

| Field | Required content |
| --- | --- |
| checks | Nonempty list of actual EXECUTED checks, each completed successfully on the current binding |
| review | ISOLATED receipt, nonempty reviewer identity, verdict PASS, and current binding |
| correctness_findings | Explicit list of reproduced correctness-finding IDs, or an empty list when none apply |
| regressions | Exactly one before/after regression record for each correctness finding |
| installation | Explicit required boolean; true adds loaded-source and entry-point requirements |

Each receipt has kind, completed equal to true, artifact_sha256, and proof.
Proof has a path to a real capture/log and its exact sha256. Its contents must
come from the actual operation. EXPERT, SIMULATED and PARTICIPANT grades retain
their uses elsewhere; they cannot satisfy these different acceptance roles.

An EXECUTED receipt declares exactly one nonempty command or tool. A command
receipt includes its completed integer exit_code (0 for success; a Boolean is
invalid). A tool receipt records actual success equal to true; do not invent a
process exit code for a tool that did not return one. Preserve nonzero command
status through pipelines and log capture.

The independent reviewer receives the final artifact and criteria without prior
verdicts. A label saying ISOLATED is not itself proof of isolation. Preserve the
separate review output as proof and record the reviewer identity.

## Regression records

For each reproduced correctness bug, preserve baseline_artifacts in the same
artifact-list shape as artifacts. The baseline files are the actual pre-repair
snapshots. Baseline and final lists must use the same stable artifact IDs.
Their fingerprints must differ because file bytes changed; renaming an ID cannot
serve as evidence of repair. The multiset of file hashes must change too, so
swapping labels among unchanged files does not pass. For a layout-only repair,
include an actual deployment/source manifest as a stable artifact whose bytes
record the changed layout. A regression row contains finding_id, test (path/sha256), before and
after receipts. Both receipts are EXECUTED command results, use the same command
and test_sha256, and point to preserved logs. Before binds to the baseline and
exits nonzero. After binds to the final artifact and exits zero. The test's actual
bytes must match the shared test hash, so changing the test cannot manufacture a
before/after success claim.

If a finding is a subjective design judgment rather than a reproduced correctness
bug, apply the domain's review/re-render checks; do not invent a regression-test
failure. If required reproduction or regression execution is unavailable, disclose
the gap and retain an unverified outcome instead of claiming verified completion.

## Installed changes

Set installation.required to true for a changed installed or deployed surface.
Provide identity (actual process/build/version), loaded_artifact_sha256 equal to
the reviewed binding, observation (OBSERVED current receipt), and entrypoint
(EXECUTED current receipt). The entry point must be the installed command or
running interaction the task requires. A source-tree test cannot fill this slot.
A source-only artifact sets required to false explicitly; it does not silently
omit installation applicability.

## Gate result and integration

```sh
python3 evidence_gate.py acceptance.json
python3 -m unittest test_evidence_gate
```

Exit 0 means the declared evidence is structurally consistent and current. Exit 1
means a failed evidence requirement. Exit 2 means an unreadable/malformed input.
None of these results replaces the optimizer's own scope, severity, iteration or
intent checks. All required gates must pass before verified completion.

PDO CLEAN and NO_CHANGE manifests carry this object in acceptance, plus example_plan. Its
selfcheck invokes the shared checker, retaining the existing eight-check output
shape. A missing shared helper prevents CLEAN certification. Historical non-clean
manifests remain readable; they gain no verified-completion claim retroactively.

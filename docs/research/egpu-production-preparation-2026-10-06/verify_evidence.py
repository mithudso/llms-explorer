#!/usr/bin/env python3
"""Verify saved preparation evidence without loading any runtime or model."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    mapping = json.loads((root / "SOURCE-MAP.json").read_text())
    for entry in mapping["files"]:
        path = root / entry["snapshot"]
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("Snapshot must be a regular file in this evidence directory")
        raw = path.read_bytes()
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise ValueError("Snapshot differs: " + str(path))
    feasibility = json.loads(
        (root / "evidence" / "TASK620-CAPTURE-PRODUCTION-FEASIBILITY.json").read_text()
    )
    assert feasibility["source_feasible_same_binary_capture_disabled"] is True
    assert feasibility["same_live_owner_can_disable_capture_via_existing_HTTP"] is False
    assert feasibility["normal_selected_token_EOS_gate_source_feasible"] is True
    assert feasibility["max_pairs"] == 64
    assert all(value == 0 for value in feasibility["reviewer_actions"].values())
    assert feasibility["full_qualification"] is False
    final_review = json.loads(
        (root / "evidence" / "TASK620-PRODUCTION-FINAL-SEAL-REVIEW.json").read_text()
    )
    assert final_review["final_root_authorities_readback_passed"] is True
    assert final_review["pure_actual_request_schema_prefix_passed"] is True
    assert all(value == 0 for value in final_review["reviewer_actions"].values())
    assert final_review["full_qualification"] is False
    static = json.loads(
        (root / "source" / "production" / "static-inputs" / "INDEPENDENT-REVIEW.json").read_text()
    )
    request = json.loads(
        (root / "source" / "production" / "capture-response-preparation" / "PREPARATION.json").read_text()
    )
    assert static["passed"] is True and static["seal_pending"] is False
    assert static["candidate_numerics_verified"] is False
    assert static["coding_verified"] is False and static["standard_research_verified"] is False
    assert static["actual_peak_verified"] is False and static["full_qualification"] is False
    assert request["capture_enabled"] is False and request["maximum_GPU_requests"] == 2
    assert request["source_review_sha256"] == hashlib.sha256(
        (root / "source" / "production" / "static-inputs" / "INDEPENDENT-REVIEW.json").read_bytes()
    ).hexdigest()
    assert request["production_mode_numerical_acceptance"] is False
    assert request["model_requests"] == 0 and request["GPU_initializations"] == 0
    assert request["full_qualification"] is False
    downstream = json.loads(
        (root / "source" / "INDEPENDENT-DOWNSTREAM-REVIEW.json").read_text()
    )
    downstream_review = json.loads(
        (root / "evidence" / "TASK620-DOWNSTREAM-FINAL-SEAL-REVIEW.json").read_text()
    )
    assert downstream["passed"] is True and downstream["seal_pending"] is False
    assert downstream["actual_session_identity"] is None
    assert downstream["actual_numerical_acceptance"] is False
    assert downstream["coding_verified"] is False and downstream["standard_research_verified"] is False
    assert downstream["full_qualification"] is False
    assert downstream["registry_status"] == "REGISTRY-UNAVAILABLE"
    assert len(downstream["runtime_alias_bindings"]) == 10
    assert downstream_review["final_source_authority_readback_passed"] is True
    assert downstream_review["actual_pure_source_review_prefix_passed"] is True
    assert downstream_review["actual_session_identity"] is None
    assert all(value == 0 for value in downstream_review["reviewer_actions"].values())
    assert downstream_review["full_qualification"] is False
    print(json.dumps({
        "saved_evidence_integrity": True,
        "snapshot_count": len(mapping["files"]),
        "capture_disabled_mode_source_feasible": True,
        "production_source_and_final_authority_admission": True,
        "scoped_downstream_source_and_final_authority_admission": True,
        "new_physical_numerical_pass_proven": False,
        "full_qualification": False,
    }, indent=2))


if __name__ == "__main__":
    main()

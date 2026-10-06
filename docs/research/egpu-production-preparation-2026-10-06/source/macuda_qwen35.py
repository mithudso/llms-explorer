#!/usr/bin/env python3
"""CPU-only Qwen3.5 static admission prototype; never authorizes a GPU launch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import struct
import time
from pathlib import Path

VERSION = "1.0.1"
DELTA = "Check regular-file metadata before fdopen, prevent FIFO blocking, and reject late native aliases/assignment overrides in isolated CPU-only preflight."
ALIAS = "qwen3.5:9b-q4-k-m"
GENERATION_PROFILE = "qwen35-9b-nonthinking"
MODEL_SHA = "d784ce9eda1a5a7b51e8f705a9e6310844bf4f173654d115823c775fdea56d43"
MODEL_BYTES = 6169341984
TEMPLATE_SHA = "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715"
GIB = 1024**3
FORMATS = {
    0: "B",
    1: "b",
    2: "H",
    3: "h",
    4: "I",
    5: "i",
    6: "f",
    7: "?",
    10: "Q",
    11: "q",
    12: "d",
}
QUANT = {0: (1, 4), 8: (32, 34), 12: (256, 144), 13: (256, 176), 14: (256, 210)}


def positive(value: object, name: str, maximum: int = 10**9) -> int:
    if type(value) is not int or not 0 < value <= maximum:
        raise ValueError(f"Invalid {name}: positive bounded integer required.")
    return value


def read_inventory(path: Path, verify_sha: bool = True) -> dict:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as error:
        if path.is_symlink():
            raise ValueError(
                "The independent GGUF must be a regular non-symlink file."
            ) from error
        raise
    try:
        before = os.fstat(descriptor)
    except BaseException:
        os.close(descriptor)
        raise
    if not stat.S_ISREG(before.st_mode):
        os.close(descriptor)
        raise ValueError("The independent GGUF must be a regular non-symlink file.")
    try:
        stream = os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise
    with stream:
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("The independent GGUF must be a regular non-symlink file.")
        if before.st_size != MODEL_BYTES:
            raise ValueError("Complete GGUF byte length differs from its reviewed pin.")
        if type(verify_sha) is not bool:
            raise ValueError("Hash verification mode must be Boolean.")
        if verify_sha:
            actual_sha = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual_sha != MODEL_SHA:
                raise ValueError("Complete GGUF SHA256 differs from its reviewed pin.")
        stream.seek(0)

        def read(size: int) -> bytes:
            if size < 0 or stream.tell() + size > before.st_size:
                raise ValueError("Truncated GGUF metadata/tensor inventory.")
            value = stream.read(size)
            if len(value) != size:
                raise ValueError("Truncated GGUF metadata/tensor inventory.")
            return value

        def number(fmt: str) -> int | float:
            return struct.unpack("<" + fmt, read(struct.calcsize(fmt)))[0]

        def string(keep: bool) -> str | None:
            size = number("Q")
            if size > 16 * 1024**2 or stream.tell() + size > before.st_size:
                raise ValueError("Unbounded GGUF string.")
            if keep:
                return read(size).decode("utf-8")
            stream.seek(size, 1)
            return None

        def value(kind: int, keep: bool, depth: int = 0) -> object:
            if depth > 2:
                raise ValueError("Unbounded nested GGUF array.")
            if kind == 8:
                return string(keep)
            if kind == 9:
                subtype, count = number("I"), number("Q")
                if count > 1000000:
                    raise ValueError("Unbounded GGUF array.")
                if not keep and subtype in FORMATS:
                    size = struct.calcsize(FORMATS[subtype]) * count
                    if stream.tell() + size > before.st_size:
                        raise ValueError("Truncated GGUF array.")
                    stream.seek(size, 1)
                    return None
                rows = [value(subtype, keep, depth + 1) for _ in range(count)]
                return rows if keep else None
            if kind not in FORMATS:
                raise ValueError("Unreviewed GGUF metadata type.")
            item = number(FORMATS[kind])
            return item if keep else None

        if read(4) != b"GGUF" or number("I") != 3:
            raise ValueError("Expected reviewed GGUFv3.")
        tensor_count = positive(number("Q"), "tensor count", 100000)
        metadata_count = positive(number("Q"), "metadata count", 10000)
        metadata = {}
        seen_keys = set()
        for _ in range(metadata_count):
            key = string(True)
            if not key or key in seen_keys:
                raise ValueError("Missing/duplicate GGUF metadata key.")
            seen_keys.add(key)
            keep = not key.startswith("tokenizer.ggml.") or key in {
                "tokenizer.ggml.model",
                "tokenizer.ggml.pre",
                "tokenizer.ggml.add_bos_token",
            }
            item = value(number("I"), keep)
            if keep:
                metadata[key] = item
        template = metadata.pop("tokenizer.chat_template")
        template_sha = hashlib.sha256(template.encode()).hexdigest()
        if template_sha != TEMPLATE_SHA:
            raise ValueError(
                "Actual GGUF tool template differs from its reviewed SHA256."
            )
        rows = []
        names = set()
        for _ in range(tensor_count):
            name = string(True)
            if not name or name in names:
                raise ValueError("Missing/duplicate GGUF tensor name.")
            names.add(name)
            dims = positive(number("I"), "tensor dimensions", 4)
            shape = [positive(number("Q"), "tensor dimension") for _ in range(dims)]
            kind, offset = number("I"), number("Q")
            if kind not in QUANT:
                raise ValueError("Unreviewed GGUF tensor quantization type.")
            block, width = QUANT[kind]
            if shape[0] % block:
                raise ValueError("Invalid GGUF quantization row shape.")
            logical = math.prod(shape) // block * width
            rows.append(
                {
                    "name": name,
                    "shape": shape,
                    "type_id": kind,
                    "relative_offset": offset,
                    "logical_bytes": logical,
                }
            )
        alignment = metadata.get("general.alignment", 32)
        positive(alignment, "GGUF alignment", 4096)
        if alignment & (alignment - 1):
            raise ValueError("GGUF alignment must be a power of two.")
        data_offset = (stream.tell() + alignment - 1) // alignment * alignment
        spans = []
        for row in rows:
            start = data_offset + row["relative_offset"]
            end = start + row["logical_bytes"]
            if start < data_offset or end > before.st_size or start % alignment:
                raise ValueError("Invalid GGUF tensor data bounds/alignment.")
            spans.append((start, end))
        if any(a[1] > b[0] for a, b in zip(sorted(spans), sorted(spans)[1:])):
            raise ValueError("Overlapping GGUF tensor payloads.")
        after = os.fstat(stream.fileno())
    named = path.lstat()
    initial_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    for info in (after, named):
        if not stat.S_ISREG(info.st_mode) or initial_identity != (
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        ):
            raise ValueError("GGUF changed during offline inventory.")
    return {
        "metadata": metadata,
        "tensors": rows,
        "template": template,
        "template_sha256": template_sha,
        "file_bytes": before.st_size,
        "file_sha256": MODEL_SHA if verify_sha else None,
        "complete_hash_verified": verify_sha,
        "data_offset": data_offset,
    }


def static_plan(
    inventory: dict,
    context: int = 32768,
    batch: int = 256,
    ubatch: int = 256,
    n_seq: int = 1,
    rollback: int = 0,
    mtp: bool = False,
) -> dict:
    m = inventory["metadata"]
    if m.get("general.architecture") != "qwen35" or mtp is not False:
        raise ValueError(
            "Only the reviewed qwen35 trunk with explicit MTP disabled is planned."
        )
    if any(
        type(value) is not int for value in (context, batch, ubatch, n_seq, rollback)
    ) or (context, batch, ubatch, n_seq, rollback) != (32768, 256, 256, 1, 0):
        raise ValueError(
            "The draft pins context32768, batch256, ubatch256, one sequence and no rollback snapshots."
        )
    dims = {
        suffix: positive(m.get("qwen35." + suffix), suffix)
        for suffix in [
            "block_count",
            "nextn_predict_layers",
            "full_attention_interval",
            "embedding_length",
            "feed_forward_length",
            "attention.head_count",
            "attention.head_count_kv",
            "attention.key_length",
            "attention.value_length",
            "ssm.conv_kernel",
            "ssm.state_size",
            "ssm.group_count",
            "ssm.time_step_rank",
            "ssm.inner_size",
            "context_length",
        ]
    }
    if (
        dims["block_count"] != 33
        or dims["nextn_predict_layers"] != 1
        or dims["full_attention_interval"] != 4
    ):
        raise ValueError(
            "Stored/trunk/MTP topology differs from the reviewed33/32/1 plan."
        )
    if (
        context > dims["context_length"]
        or dims["ssm.state_size"] != 128
        or dims["ssm.conv_kernel"] != 4
    ):
        raise ValueError(
            "Context or GDN/convolution kernel shape differs from the reviewed plan."
        )
    if m.get("qwen35.attention.recurrent_layers") is not None:
        raise ValueError(
            "Explicit recurrent-layer arrays require an independent new review."
        )
    expected_dimensions = {
        "embedding_length": 4096,
        "feed_forward_length": 12288,
        "attention.head_count": 16,
        "attention.head_count_kv": 4,
        "attention.key_length": 256,
        "attention.value_length": 256,
        "ssm.group_count": 16,
        "ssm.time_step_rank": 32,
        "ssm.inner_size": 4096,
    }
    if any(dims[key] != expected for key, expected in expected_dimensions.items()):
        raise ValueError(
            "Hybrid dimensions differ from the complete reviewed model inventory."
        )
    trunk = 32
    full = [i for i in range(trunk) if (i + 1) % dims["full_attention_interval"] == 0]
    recurrent = [i for i in range(trunk) if i not in full]
    by_layer = {i: [] for i in range(33)}
    globals_ = []
    for row in inventory["tensors"]:
        match = re.fullmatch(r"blk\.(\d+)\..+", row["name"])
        if match:
            index = int(match[1])
            if index not in by_layer:
                raise ValueError("GGUF contains an unexpected stored block.")
            by_layer[index].append(row)
        else:
            globals_.append(row["name"])
    if len(inventory["tensors"]) != 442 or sorted(globals_) != [
        "output.weight",
        "output_norm.weight",
        "token_embd.weight",
    ]:
        raise ValueError(
            "Complete text-only tensor inventory differs from442 expected rows."
        )
    for index, rows in by_layer.items():
        if len(rows) != (15 if index == 32 else 14 if index in recurrent else 11):
            raise ValueError("Missing/extra trunk or MTP tensor rows.")
    expected_shapes = {
        "output.weight": [4096, 248320],
        "output_norm.weight": [4096],
        "token_embd.weight": [4096, 248320],
    }
    shared = {
        "attn_norm.weight": [4096],
        "post_attention_norm.weight": [4096],
        "ffn_gate.weight": [4096, 12288],
        "ffn_up.weight": [4096, 12288],
        "ffn_down.weight": [12288, 4096],
    }
    linear = {
        "attn_gate.weight": [4096, 4096],
        "attn_qkv.weight": [4096, 8192],
        "ssm_a": [32],
        "ssm_alpha.weight": [4096, 32],
        "ssm_beta.weight": [4096, 32],
        "ssm_conv1d.weight": [4, 8192],
        "ssm_dt.bias": [32],
        "ssm_norm.weight": [128],
        "ssm_out.weight": [4096, 4096],
    }
    dense = {
        "attn_q.weight": [4096, 8192],
        "attn_k.weight": [4096, 1024],
        "attn_v.weight": [4096, 1024],
        "attn_q_norm.weight": [256],
        "attn_k_norm.weight": [256],
        "attn_output.weight": [4096, 4096],
    }
    nextn = {
        "nextn.eh_proj.weight": [8192, 4096],
        "nextn.enorm.weight": [4096],
        "nextn.hnorm.weight": [4096],
        "nextn.shared_head_norm.weight": [4096],
    }
    for index in range(33):
        block = (
            shared
            | (linear if index in recurrent else dense)
            | (nextn if index == 32 else {})
        )
        expected_shapes.update(
            {f"blk.{index}.{name}": shape for name, shape in block.items()}
        )
    actual_shapes = {row["name"]: row["shape"] for row in inventory["tensors"]}
    if actual_shapes != expected_shapes:
        raise ValueError(
            "Tensor names/shapes differ from the independently expected hybrid/MTP inventory."
        )
    channels = (
        dims["ssm.inner_size"] + 2 * dims["ssm.group_count"] * dims["ssm.state_size"]
    )
    if channels % 128 or dims["ssm.time_step_rank"] % dims["ssm.group_count"]:
        raise ValueError("Unsupported convolution channels/GDN grouped-head shape.")
    kv = (
        len(full)
        * context
        * dims["attention.head_count_kv"]
        * (dims["attention.key_length"] + dims["attention.value_length"])
        * 2
    )
    conv_elements = (dims["ssm.conv_kernel"] - 1) * channels
    recurrent_elements = dims["ssm.state_size"] * dims["ssm.inner_size"]
    state = (
        len(recurrent)
        * (conv_elements + recurrent_elements)
        * 4
        * n_seq
        * (1 + rollback)
    )
    attention_scores = ubatch * context * dims["attention.head_count"] * 4
    qkv_work = ubatch * channels * 4
    ffn_work = ubatch * dims["feed_forward_length"] * 4
    # This allowance is policy, not a proven graph allocator upper bound.
    workspace_allowance, allocator_allowance, driver_reserve, safety = (
        2 * GIB,
        GIB // 4,
        2 * GIB,
        GIB,
    )
    subtotal = (
        inventory["file_bytes"]
        + kv
        + state
        + workspace_allowance
        + allocator_allowance
        + driver_reserve
        + safety
    )
    return {
        "version": VERSION,
        "delta": DELTA,
        "context": context,
        "batch": batch,
        "ubatch": ubatch,
        "n_seq": n_seq,
        "rollback_snapshots": rollback,
        "mtp_enabled": False,
        "stored_blocks": 33,
        "active_trunk_blocks": trunk,
        "mtp_excluded_blocks": [32],
        "mtp_stored_logical_bytes": sum(row["logical_bytes"] for row in by_layer[32]),
        "full_attention_blocks": full,
        "recurrent_blocks": recurrent,
        "inventory_tensors": 442,
        "packed_file_weight_reserve_bytes": inventory["file_bytes"],
        "f16_full_attention_kv_bytes": kv,
        "f32_recurrent_state_bytes": state,
        "single_attention_score_tensor_bytes_without_flash": attention_scores,
        "single_conv_qkv_tensor_bytes": qkv_work,
        "single_ffn_tensor_bytes": ffn_work,
        "all256token_float32_logits_bytes": batch * 248320 * 4,
        "policy_compute_workspace_allowance_bytes": workspace_allowance,
        "policy_allocator_allowance_bytes": allocator_allowance,
        "policy_driver_firmware_reserve_bytes": driver_reserve,
        "policy_safety_reserve_bytes": safety,
        "planned_total_bytes": subtotal,
        "planned_remaining_of16gib_bytes": 16 * GIB - subtotal,
        "policy_budget_has_headroom": subtotal <= 16 * GIB,
        "workspace_upper_bound_proven": False,
        "admitted_for_runtime": False,
        "residency_supported_by_maintained_validator": False,
        "physical_gpu_execution_proven": False,
        "numerical_or_coding_quality_proven": False,
        "required_controls": [
            "--spec-type none and cleared all LLAMA_ARG_*",
            "--parallel1 --ctx-size32768 --batch-size256 --ubatch-size256 --flash-attn on --fit off",
            "independent hybrid tensor inventory/residency support with explicit skipped MTP",
            "actual private KV/recurrent/compute placement and allocation receipt",
            "bounded physical hybrid-operator/numerical checks before coding and standard /dr",
        ],
        "provenance_review": {
            "general_name": m.get("general.name"),
            "base_model_name": m.get("general.base_model.0.name"),
            "base_model_repo_url": m.get("general.base_model.0.repo_url"),
            "upstream_post_trained_model_identity_verified_by_parent": True,
            "upstream_readme_url": "https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/README.md",
            "upstream_base_lineage_matches": True,
            "special_base_lineage_discrepancy": False,
            "verification_scope": "Parent reviewed the official README's Base lineage and explicit post-trained note. This offline task performed no network request.",
            "claim_limit": "Matching Base lineage is normal upstream metadata. Artifact structure and post-trained identity do not prove numerical correctness or agent quality.",
        },
    }


DESCRIPTOR_SHA = "166abc252421a343fd16349c335f50c59503929d6746bf7354a95ea4a95e868d"
TYPE_NAMES = {0: "f32", 8: "q8_0", 12: "q4_K", 13: "q5_K", 14: "q6_K"}
PROFILE = {
    "context_n_ctx": 32768,
    "context_n_batch": 256,
    "context_n_ubatch": 256,
    "context_n_seq_max": 1,
    "recurrent_rollback_snapshots": 0,
    "model_n_layer": 32,
    "model_nextn_predict_layers": 1,
    "flash_attention_enabled": True,
    "fused_gdn_ar_enabled": True,
    "fused_gdn_ch_enabled": True,
    "auto_fused_gdn_enabled": False,
}
LAUNCH_OPTIONS = {
    "--ctx-size": "32768",
    "--batch-size": "256",
    "--ubatch-size": "256",
    "--parallel": "1",
    "--flash-attn": "on",
    "--fit": "off",
    "--spec-type": "none",
    "--cache-type-k": "f16",
    "--cache-type-v": "f16",
    "--log-verbosity": "5",
    "-ngl": "99",
    "--reasoning": "off",
}


def expected_inventory(independent: dict) -> dict:
    """Bind all442 descriptors and split427 active /15 explicitly skipped rows."""
    if (
        independent.get("complete_hash_verified") is not True
        or independent.get("file_sha256") != MODEL_SHA
        or type(independent.get("file_bytes")) is not int
        or independent["file_bytes"] != MODEL_BYTES
        or independent.get("template_sha256") != TEMPLATE_SHA
    ):
        raise ValueError("Complete pinned independent GGUF identity is required.")
    plan = static_plan(independent)
    rows = independent.get("tensors")
    if not isinstance(rows, list):
        raise TypeError("Complete descriptor rows are required.")
    normalized = json.dumps(
        sorted(rows, key=lambda row: row["name"]),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    if hashlib.sha256(normalized).hexdigest() != DESCRIPTOR_SHA:
        raise ValueError("Exact reviewed GGUF tensor descriptor manifest differs.")
    active, skipped = [], []
    for row in rows:
        shape = row["shape"] + [1] * (4 - len(row["shape"]))
        if len(shape) != 4 or any(type(n) is not int or n < 1 for n in shape):
            raise ValueError("Invalid tensor dimensions.")
        block, width = QUANT[row["type_id"]]
        if shape[0] % block:
            raise ValueError("Invalid quantized tensor row.")
        stride = [width, width * shape[0] // block]
        stride.extend([stride[1] * shape[1], stride[1] * shape[1] * shape[2]])
        logical_bytes = math.prod(shape) // block * width
        if logical_bytes != row["logical_bytes"]:
            raise ValueError("Descriptor byte size differs from its type/shape.")
        name = row["name"]
        item = {
            "name": name,
            "source_name": name,
            "derived_name": False,
            "semantic_role": "input_embedding"
            if name == "token_embd.weight"
            else "output_weight"
            if name == "output.weight"
            else "model_tensor",
            "shape": shape,
            "type_id": row["type_id"],
            "type_name": TYPE_NAMES[row["type_id"]],
            "logical_bytes": logical_bytes,
            "strides_bytes": stride,
            "data_offset": row["relative_offset"],
        }
        (skipped if name.startswith("blk.32.") else active).append(item)
    if len(active) != 427 or len(skipped) != 15:
        raise ValueError("Exact active/skipped tensor counts differ.")
    return {
        "version": VERSION,
        "model_sha256": MODEL_SHA,
        "architecture": "qwen35",
        "model_n_layer": 32,
        "model_nextn_predict_layers": 1,
        "stored_block_count": 33,
        "native_context": independent["metadata"]["qwen35.context_length"],
        "tensor_count": 442,
        "runtime_tensor_count": 427,
        "tied_output_expected": False,
        "tensors": active + skipped,
        "expected_live_tensors": active,
        "expected_skipped_mtp_tensors": skipped,
        "descriptor_sha256": DESCRIPTOR_SHA,
        "hybrid_memory_plan": plan,
        "admitted_for_runtime": False,
    }


def validate_context_receipt(
    proof: dict, state: dict, boot_id: str, *, now: float | None = None
) -> dict:
    """Check a prospective inspector contract; no current backend emits this."""
    expected_identity = {
        "TINYNV_WITNESS_SESSION": state.get("witness", {}).get("session"),
        "TINYNV_WITNESS_BOOT_ID": boot_id,
        "TINYNV_WITNESS_MODEL_SHA256": MODEL_SHA,
        "TINYNV_WITNESS_BUILD_SHA256": state.get("binary_sha256"),
    }
    if (
        not isinstance(boot_id, str)
        or not re.fullmatch(r"\d+:\d+", boot_id)
        or type(state.get("pid")) is not int
        or state["pid"] < 1
        or state.get("boot_id") != boot_id
        or state.get("context") != 32768
        or type(state.get("context")) is not int
        or state.get("model_sha256") != MODEL_SHA
        or not isinstance(expected_identity["TINYNV_WITNESS_SESSION"], str)
        or not re.fullmatch(
            r"[a-f0-9]{32}", expected_identity["TINYNV_WITNESS_SESSION"]
        )
        or not isinstance(expected_identity["TINYNV_WITNESS_BUILD_SHA256"], str)
        or not re.fullmatch(
            r"[a-f0-9]{64}", expected_identity["TINYNV_WITNESS_BUILD_SHA256"]
        )
    ):
        raise ValueError("Invalid prospective hybrid owner identity/profile.")
    if (
        proof.get("schema_version") != "1.0.0"
        or proof.get("evidence_kind") != "host_hybrid_context_metadata_only"
        or proof.get("native_identity") != expected_identity
        or type(proof.get("pid")) is not int
        or proof["pid"] != state["pid"]
        or proof.get("metadata_valid") is not True
        or proof.get("violations") != []
        or proof.get("native_identity_env_present") is not True
        or any(
            proof.get(k) is not False
            for k in [
                "gpu_execution_verified",
                "physical_vram_residency_verified",
                "kv_cache_residency_verified",
                "workspace_upper_bound_proven",
            ]
        )
    ):
        raise ValueError("Stale or overstated prospective hybrid context receipt.")
    stamp = proof.get("recorded_unix_seconds")
    if (
        type(stamp) is not int
        or stamp < int(boot_id.split(":")[0])
        or stamp > (time.time() if now is None else now) + 5
    ):
        raise ValueError("Prospective context timestamp is outside the owned boot.")
    for key, value in PROFILE.items():
        if proof.get(key) != value or type(proof.get(key)) is not type(value):
            raise ValueError("Unreviewed actual hybrid context field: " + key)
    return {
        "version": VERSION,
        "hybrid_context_metadata_consistent": True,
        "actual_model_buffer_metadata_verified": False,
        "gpu_execution_verified": False,
        "physical_vram_residency_verified": False,
        "kv_cache_residency_verified": False,
        "workspace_upper_bound_proven": False,
        "admitted_for_runtime": False,
        "claim_limit": "Future reviewed host-context getter metadata only. Must be combined with independent all-row model-buffer, private-file/build/command/fault/ownership evidence and separate native allocation/execution qualification. No present inspector support or physical proof is inferred.",
    }


def validate_reviewed_launch(argv: list, reviewed_argv: list, child_env: dict) -> dict:
    """Check typed argv and overrides; caller still must bind actual PID argv."""
    if (
        not isinstance(argv, list)
        or not argv
        or argv != reviewed_argv
        or any(not isinstance(item, str) or not item for item in argv)
    ):
        raise ValueError("Hybrid launch must match the complete reviewed argv.")
    for option, value in LAUNCH_OPTIONS.items():
        if argv.count(option) != 1:
            raise ValueError(
                "Missing or duplicate reviewed hybrid launch option: " + option
            )
        at = argv.index(option)
        if at + 1 == len(argv) or argv[at + 1] != value:
            raise ValueError("Unreviewed hybrid launch option value: " + option)
    passthrough = {"--model", "--alias", "--host", "--port", "--device"}
    switches = {"--jinja", "--no-warmup"}
    seen = set()
    at = 1
    while at < len(argv):
        option = argv[at]
        if option in seen:
            raise ValueError("Duplicate native argument: " + option)
        seen.add(option)
        if option in switches:
            at += 1
            continue
        if option not in LAUNCH_OPTIONS and option not in passthrough:
            raise ValueError("Unreviewed alias, assignment or native option: " + option)
        if at + 1 == len(argv) or argv[at + 1].startswith("-"):
            raise ValueError("Missing or ambiguous native argument value: " + option)
        value = argv[at + 1]
        if option == "--model" and not Path(value).is_absolute():
            raise ValueError("Hybrid model path must be absolute.")
        if option == "--alias" and value != ALIAS:
            raise ValueError("Hybrid alias differs from its model identity.")
        if option == "--host" and value != "127.0.0.1":
            raise ValueError("Hybrid server must remain on loopback.")
        if option == "--device" and value != "CUDA0":
            raise ValueError("Hybrid model device must be CUDA0.")
        if option == "--port" and (not value.isdigit() or not 1 <= int(value) <= 65535):
            raise ValueError("Invalid hybrid loopback port.")
        at += 2
    if any(key.startswith("LLAMA_ARG_") for key in child_env) or child_env.get(
        "TINYNV_FMC_REINIT"
    ):
        raise ValueError(
            "Inherited model overrides or unqualified warm handoff are refused."
        )
    return {
        "reviewed_hybrid_launch_profile_consistent": True,
        "mtp_explicitly_disabled_in_reviewed_command": True,
        "silent_fit_adjustment_disabled_in_reviewed_command": True,
        "actual_owned_pid_command_verified": False,
        "admitted_for_runtime": False,
    }


def candidate_profile(model: Path) -> dict:
    """Read the exact artifact on CPU; this cannot qualify physical execution."""
    inventory = read_inventory(model, verify_sha=True)
    expected = expected_inventory(inventory)
    return {
        "version": VERSION,
        "delta": DELTA,
        "runtime": "macuda-qwen35-cpu-preflight",
        "model": str(model.resolve()),
        "model_sha256": MODEL_SHA,
        "alias": ALIAS,
        "required_generation_profile": GENERATION_PROFILE,
        "cpu_candidate_profile_verified": True,
        "admitted_for_runtime": False,
        "context": 32768,
        "batch": 256,
        "ubatch": 256,
        "parallel": 1,
        "recurrent_rollback_snapshots": 0,
        "speculative_type": "none",
        "fit_enabled": False,
        "template_sha256": TEMPLATE_SHA,
        "required_gateway_extra_body": {
            "chat_template_kwargs": {"enable_thinking": False}
        },
        "expected_gguf_inventory": expected,
        "memory_admission": expected["hybrid_memory_plan"],
        "remaining_runtime_gates": [
            "early maintained route integration and exact alias/profile binding",
            "new reviewed host-only hybrid context/model-buffer inspector",
            "same-owner fault/boot/private-file/build/argv/socket/lock validation",
            "reviewed cold-card transition and native allocation/operator/numerical controls",
            "actual full coding-tool and unchanged standard research acceptance",
        ],
    }


def native_command(profile: dict, binary: Path, port: int = 8000) -> list[str]:
    """Construct a diagnostic argv for later owner review; never execute it."""
    if (
        profile.get("cpu_candidate_profile_verified") is not True
        or profile.get("admitted_for_runtime") is not False
        or profile.get("model_sha256") != MODEL_SHA
        or profile.get("alias") != ALIAS
        or not isinstance(profile.get("model"), str)
        or not Path(profile["model"]).is_absolute()
        or not binary.is_absolute()
        or type(port) is not int
        or not 1 <= port <= 65535
    ):
        raise ValueError(
            "Exact CPU candidate profile, absolute binary and valid port are required."
        )
    argv = [
        str(binary),
        "--model",
        profile["model"],
        "--alias",
        ALIAS,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--device",
        "CUDA0",
    ]
    for option, value in LAUNCH_OPTIONS.items():
        argv.extend([option, value])
    argv.extend(["--jinja", "--no-warmup"])
    validate_reviewed_launch(argv, list(argv), {})
    return argv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exact hybrid CPU preflight; never launches native code or admits a runtime."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument(
        "--native-binary",
        type=Path,
        default=Path("/Users/mitch/dev/macuda/cuda-shim/build/bin/llama-server-null"),
    )
    args = parser.parse_args()
    profile = candidate_profile(args.model)
    profile["draft_native_argv"] = native_command(profile, args.native_binary)
    output = args.output_directory
    if not output.is_absolute():
        raise ValueError(
            "CPU preflight output must be an absolute exclusive directory."
        )
    output.mkdir(mode=0o700, exist_ok=False)
    inventory = output / "inventory.json"
    with inventory.open("x") as stream:
        json.dump(profile["expected_gguf_inventory"], stream, indent=2)
        stream.write("\n")
    inventory.chmod(0o600)
    receipt = output / "receipt.json"
    with receipt.open("x") as stream:
        json.dump(profile, stream, indent=2)
        stream.write("\n")
    receipt.chmod(0o600)
    print(
        json.dumps(
            {
                "version": VERSION,
                "receipt": str(receipt),
                "cpu_candidate_profile_verified": True,
                "admitted_for_runtime": False,
                "model_calls": 0,
                "gpu_actions": 0,
                "backend_initialized": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Bind host-only live model-buffer metadata to an independently read GGUF.

This module never loads a native library, contacts an API or opens a GPU device.
CUDA buffer metadata is not proof of physical pages, KV placement or execution.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import struct
import time
from itertools import pairwise
from pathlib import Path

import macuda_qwen35 as qwen35
from macuda_safe_runtime import require_healthy_boot

VERSION = "1.0.1"
DELTA = "Require exact9B active/skipped inventory and same-receipt hybrid context proof; preserve qwen3 policy."
METHOD = "live-host-model-buffer-inventory"
LOG_METHOD = "native-log-discovery-and-full-layer-count"
QWEN35_EXPECTED_ROWS_SHA256 = (
    "0577fbc07bc13618f928f8fe9b0aae6bbf469124d2ae8bd7172bcb56af595a65"
)
TYPE_LAYOUT = {
    0: ("f32", 1, 4),
    1: ("f16", 1, 2),
    8: ("q8_0", 32, 34),
    12: ("q4_K", 256, 144),
    13: ("q5_K", 256, 176),
    14: ("q6_K", 256, 210),
}
META_FORMATS = {
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


def integer(value, label: str, *, minimum=0, maximum=2**63 - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise RuntimeError(f"Invalid residency integer: {label}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gguf_inventory(path: Path, expected_sha256: str) -> dict:
    """Read bounded GGUF metadata/tensor descriptors, not native tensor memory."""
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise RuntimeError("A reviewed GGUF SHA256 is required for residency.")
    if expected_sha256 == qwen35.MODEL_SHA:
        # Fresh same-descriptor hash/parse; never authorize this branch from an
        # arbitrary prior JSON Boolean or a scalar dense-KV estimate.
        return qwen35.expected_inventory(qwen35.read_inventory(path))
    with path.open("rb") as stream:
        initial = os.fstat(stream.fileno())
        if not stat.S_ISREG(initial.st_mode):
            raise RuntimeError("Residency GGUF must be a regular model file.")
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise RuntimeError("Residency GGUF differs from the reviewed model SHA256.")
        stream.seek(0)
        size = initial.st_size

        def read(length):
            if length < 0 or stream.tell() + length > size:
                raise RuntimeError("Truncated or unbounded GGUF residency inventory.")
            value = stream.read(length)
            if len(value) != length:
                raise RuntimeError("Truncated GGUF residency inventory.")
            return value

        def number(fmt):
            return struct.unpack("<" + fmt, read(struct.calcsize(fmt)))[0]

        def skip(length):
            if length < 0 or stream.tell() + length > size:
                raise RuntimeError("Truncated or unbounded GGUF metadata.")
            stream.seek(length, 1)

        def string(keep=True):
            length = number("Q")
            if length > 16 * 1024**2:
                raise RuntimeError("Unbounded GGUF string in residency inventory.")
            if keep:
                return read(length).decode("utf-8")
            skip(length)
            return None

        def value(kind, keep=True, depth=0):
            if depth > 4:
                raise RuntimeError("Unbounded nested GGUF metadata.")
            if kind == 8:
                return string(keep)
            if kind == 9:
                subtype, count = number("I"), number("Q")
                if count > size:
                    raise RuntimeError("Unbounded GGUF metadata array.")
                if subtype in META_FORMATS:
                    skip(struct.calcsize(META_FORMATS[subtype]) * count)
                else:
                    for _ in range(count):
                        value(subtype, False, depth + 1)
                return None
            if kind not in META_FORMATS:
                raise RuntimeError(f"Unsupported GGUF metadata type {kind}.")
            return number(META_FORMATS[kind])

        if read(4) != b"GGUF" or number("I") not in (2, 3):
            raise RuntimeError("Unsupported GGUF residency inventory format.")
        tensor_count = integer(
            number("Q"), "GGUF tensor count", minimum=1, maximum=100000
        )
        metadata_count = integer(number("Q"), "GGUF metadata count", maximum=100000)
        metadata = {}
        seen_metadata = set()
        for _ in range(metadata_count):
            key = string()
            if key in seen_metadata:
                raise RuntimeError("Duplicate GGUF residency metadata key.")
            seen_metadata.add(key)
            keep = key in {"general.architecture", "general.alignment"} or key.endswith(
                (".block_count", ".context_length")
            )
            item = value(number("I"), keep)
            if keep:
                metadata[key] = item
        architecture = metadata.get("general.architecture")
        if architecture != "qwen3":
            raise RuntimeError(
                "Live residency inventory currently qualifies qwen3 only."
            )
        layers = integer(
            metadata.get("qwen3.block_count"), "GGUF layers", minimum=1, maximum=10000
        )
        capacity = integer(
            metadata.get("qwen3.context_length"), "GGUF context", minimum=1
        )
        alignment = integer(
            metadata.get("general.alignment", 32),
            "GGUF alignment",
            minimum=1,
            maximum=4096,
        )
        if alignment & (alignment - 1):
            raise RuntimeError("GGUF alignment must be a power of two.")
        tensors = []
        names = set()
        for _ in range(tensor_count):
            name = string()
            if not name or name in names:
                raise RuntimeError("Missing or duplicate GGUF tensor name.")
            names.add(name)
            dimensions = integer(number("I"), "GGUF dimensions", minimum=1, maximum=4)
            shape = [
                integer(number("Q"), "GGUF shape", minimum=1) for _ in range(dimensions)
            ]
            shape += [1] * (4 - dimensions)
            type_id, offset = number("I"), number("Q")
            if type_id not in TYPE_LAYOUT:
                raise RuntimeError(f"Unreviewed GGUF tensor type {type_id}: {name}")
            type_name, block, width = TYPE_LAYOUT[type_id]
            if shape[0] % block:
                raise RuntimeError(f"Invalid quantized GGUF row shape: {name}")
            strides = [width, width * shape[0] // block]
            strides.extend((strides[1] * shape[1], strides[1] * shape[1] * shape[2]))
            logical_bytes = math.prod(shape) // block * width
            tensors.append(
                {
                    "name": name,
                    "shape": shape,
                    "type_id": type_id,
                    "type_name": type_name,
                    "logical_bytes": logical_bytes,
                    "strides_bytes": strides,
                    "data_offset": offset,
                }
            )
        data_start = (stream.tell() + alignment - 1) // alignment * alignment
        spans = []
        for row in tensors:
            offset, length = row["data_offset"], row["logical_bytes"]
            if offset % alignment or data_start + offset + length > size:
                raise RuntimeError(f"Invalid GGUF tensor data bounds: {row['name']}")
            spans.append((offset, offset + length))
        spans.sort()
        if any(left[1] > right[0] for left, right in pairwise(spans)):
            raise RuntimeError("Overlapping GGUF tensor data in residency inventory.")
        final = os.fstat(stream.fileno())
        if (initial.st_size, initial.st_mtime_ns, initial.st_ctime_ns) != (
            final.st_size,
            final.st_mtime_ns,
            final.st_ctime_ns,
        ):
            raise RuntimeError("GGUF changed during residency inventory validation.")
    blocks = {
        int(match[1])
        for name in names
        if (match := re.fullmatch(r"blk\.(\d+)\..+", name))
    }
    if (
        blocks != set(range(layers))
        or not {"token_embd.weight", "output_norm.weight"} <= names
    ):
        raise RuntimeError(
            "GGUF lacks complete transformer/output residency inventory."
        )
    live_tensors = []
    for row in tensors:
        live_tensors.append(
            {
                **row,
                "source_name": row["name"],
                "derived_name": False,
                "semantic_role": "input_embedding"
                if row["name"] == "token_embd.weight"
                else "output_weight"
                if row["name"] == "output.weight"
                else "model_tensor",
            }
        )
    tied_output = "output.weight" not in names
    if tied_output:
        embedding = next(row for row in tensors if row["name"] == "token_embd.weight")
        live_tensors.append(
            {
                **embedding,
                "name": "output.weight",
                "source_name": "token_embd.weight",
                "derived_name": True,
                "semantic_role": "tied_output",
            }
        )
    return {
        "model_sha256": expected_sha256,
        "architecture": architecture,
        "model_n_layer": layers,
        "native_context": capacity,
        "tensor_count": tensor_count,
        "tensors": tensors,
        "runtime_tensor_count": len(live_tensors),
        "tied_output_expected": tied_output,
        "expected_live_tensors": live_tensors,
    }


def validate_receipt(proof: dict, state: dict, boot_id: str, inventory: dict) -> dict:
    """Validate every row and summary; trust no helper's aggregate success flag."""
    configured = state.get("witness", {})
    identity = {
        "TINYNV_WITNESS_SESSION": configured.get("session"),
        "TINYNV_WITNESS_BOOT_ID": boot_id,
        "TINYNV_WITNESS_MODEL_SHA256": state.get("model_sha256"),
        "TINYNV_WITNESS_BUILD_SHA256": state.get("binary_sha256"),
    }
    hybrid = (
        inventory.get("architecture") == "qwen35"
        or inventory.get("model_sha256") == qwen35.MODEL_SHA
        or state.get("model_sha256") == qwen35.MODEL_SHA
    )
    expected_version = "1.0.3" if hybrid else "1.0.2"
    context_evidence = None
    if hybrid:
        expected_rows = {
            "active": inventory.get("expected_live_tensors"),
            "skipped": inventory.get("expected_skipped_mtp_tensors"),
        }
        row_digest = hashlib.sha256(
            json.dumps(expected_rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if (
            inventory.get("architecture") != "qwen35"
            or inventory.get("model_sha256") != qwen35.MODEL_SHA
            or inventory.get("model_n_layer") != 32
            or inventory.get("model_nextn_predict_layers") != 1
            or inventory.get("stored_block_count") != 33
            or inventory.get("native_context") != 262144
            or inventory.get("runtime_tensor_count") != 427
            or inventory.get("tensor_count") != 442
            or inventory.get("descriptor_sha256") != qwen35.DESCRIPTOR_SHA
            or row_digest != QWEN35_EXPECTED_ROWS_SHA256
        ):
            raise RuntimeError("Unreviewed hybrid expected inventory.")
        context_proof = proof.get("hybrid_context")
        if not isinstance(context_proof, dict):
            raise RuntimeError(
                "The9B live proof lacks same-receipt hybrid context metadata."
            )
        try:
            context_evidence = qwen35.validate_context_receipt(
                context_proof, state, boot_id
            )
        except (ValueError, TypeError) as error:
            raise RuntimeError(
                "Invalid live hybrid context metadata: " + str(error)
            ) from error
        if (
            context_proof.get("recorded_unix_seconds")
            != proof.get("recorded_unix_seconds")
            or context_proof.get("native_identity") != proof.get("native_identity")
            or context_proof.get("pid") != proof.get("pid")
        ):
            raise RuntimeError(
                "Hybrid context and tensor rows belong to different receipt identities/times."
            )
    if (
        proof.get("schema_version") != expected_version
        or proof.get("inspector_version") != expected_version
        or proof.get("evidence_kind") != "host_model_buffer_metadata_only"
        or type(proof.get("pid")) is not int
        or proof.get("pid") != state.get("pid")
        or state.get("boot_id") != boot_id
        or proof.get("native_identity") != identity
        or any(not isinstance(item, str) or not item for item in identity.values())
        or proof.get("native_identity_env_present") is not True
        or proof.get("metadata_valid") is not True
        or proof.get("violations") != []
        or any(
            proof.get(key) is not False
            for key in (
                "gpu_execution_verified",
                "physical_vram_residency_verified",
                "model_file_identity_bound",
                "kv_cache_residency_verified",
            )
        )
    ):
        raise RuntimeError(
            "Live residency receipt has stale identity or an invalid metadata-only scope."
        )
    seconds = integer(proof.get("recorded_unix_seconds"), "recorded time", minimum=1)
    integer(
        proof.get("recorded_nanoseconds"), "recorded nanoseconds", maximum=999999999
    )
    if (
        not re.fullmatch(r"\d+:\d+", boot_id)
        or seconds < int(boot_id.split(":")[0])
        or seconds > time.time() + 5
    ):
        raise RuntimeError("Live residency timestamp does not belong to this boot.")
    context = integer(state.get("context"), "configured context", minimum=1)
    if (
        type(proof.get("context_n_ctx")) is not int
        or proof["context_n_ctx"] != context
        or context > inventory["native_context"]
        or type(proof.get("model_n_layer")) is not int
        or proof["model_n_layer"] != inventory["model_n_layer"]
        or inventory.get("model_sha256") != state.get("model_sha256")
    ):
        raise RuntimeError(
            "Live residency context/layers/model differ from the independent GGUF."
        )
    rows, buffers = proof.get("tensors"), proof.get("buffers")
    if not isinstance(rows, list) or not isinstance(buffers, list):
        raise TypeError("Live residency requires complete tensor and buffer rows.")
    expected = {row["name"]: row for row in inventory["expected_live_tensors"]}
    actual = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("name"), str)
            or row["name"] in actual
        ):
            raise RuntimeError("Duplicate or invalid live residency tensor row.")
        actual[row["name"]] = row
    if (
        set(actual) != set(expected)
        or proof.get("tensor_count") != len(expected)
        or type(proof.get("tensor_count")) is not int
    ):
        raise RuntimeError(
            "Live residency omitted/added tensors from the complete GGUF inventory."
        )
    by_buffer = {}
    for buffer in buffers:
        if not isinstance(buffer, dict):
            raise TypeError("Invalid live residency buffer row.")
        key = integer(buffer.get("buffer_id"), "buffer ID")
        if key in by_buffer:
            raise RuntimeError("Duplicate live residency buffer ID.")
        integer(buffer.get("allocated_bytes"), "buffer allocation", minimum=1)
        if (
            type(buffer.get("host")) is not bool
            or type(buffer.get("non_host_cuda_named")) is not bool
        ):
            raise RuntimeError("Invalid live residency buffer classification.")
        cuda = (
            buffer.get("buffer_type") == "CUDA0"
            and buffer.get("device_name") == "CUDA0"
            and buffer["host"] is False
        )
        if buffer["non_host_cuda_named"] is not cuda:
            raise RuntimeError("Conflicting live residency CUDA buffer classification.")
        by_buffer[key] = buffer
    if (
        set(by_buffer) != set(range(len(buffers)))
        or proof.get("unique_buffer_count") != len(buffers)
        or type(proof.get("unique_buffer_count")) is not int
    ):
        raise RuntimeError("Invalid complete live residency buffer inventory.")
    layer_counts = [0] * inventory["model_n_layer"]
    output_count = 0
    host_names, cuda_names = [], []
    logical_total, usage = 0, dict.fromkeys(by_buffer, 0)
    for name, row in actual.items():
        want = expected[name]
        for key in ("shape", "type_id", "type_name", "logical_bytes", "strides_bytes"):
            if row.get(key) != want[key] or (
                key in {"type_id", "logical_bytes"} and type(row.get(key)) is not int
            ):
                raise RuntimeError(
                    f"Live residency tensor shape/type/bytes differ from GGUF: {name}"
                )
        for key in ("source_name", "semantic_role", "derived_name"):
            if row.get(key) != want[key] or type(row.get(key)) is not type(want[key]):
                raise RuntimeError(
                    f"Live residency tensor has an unreviewed derived role: {name}"
                )
        if any(
            type(value) is not int
            for key in ("shape", "strides_bytes")
            for value in row[key]
        ):
            raise RuntimeError(f"Invalid live residency tensor dimensions: {name}")
        key = integer(row.get("buffer_id"), "tensor buffer ID")
        buffer = by_buffer.get(key)
        if (
            buffer is None
            or row.get("allocated_metadata") is not True
            or row.get("view") is not False
        ):
            raise RuntimeError(
                f"Live residency tensor is unallocated, a view or lacks a buffer: {name}"
            )
        if any(
            row.get(field) != buffer.get(field) or type(row.get(field)) is not bool
            for field in ("host", "non_host_cuda_named")
        ) or any(
            row.get(field) != buffer.get(field)
            for field in ("buffer_type", "device_name")
        ):
            raise RuntimeError(
                f"Live residency tensor and buffer classifications differ: {name}"
            )
        match = re.fullmatch(r"blk\.(\d+)\..+", name)
        layer = int(match[1]) if match else None
        output = name.startswith(("output.", "output_norm."))
        if (
            row.get("layer_index") != layer
            or (layer is not None and type(row.get("layer_index")) is not int)
            or row.get("output_group") is not output
        ):
            raise RuntimeError(
                f"Invalid live residency layer/output assignment: {name}"
            )
        if name == "token_embd.weight" and row["host"] is True:
            host_names.append(name)
        elif row["non_host_cuda_named"] is True:
            cuda_names.append(name)
        else:
            raise RuntimeError(
                f"Transformer/output tensor lacks a non-host CUDA0 buffer: {name}"
            )
        if layer is not None:
            if not 0 <= layer < len(layer_counts):
                raise RuntimeError("Invalid live residency layer index.")
            layer_counts[layer] += 1
        output_count += int(output)
        usage[key] += row["logical_bytes"]
        logical_total += row["logical_bytes"]
    if any(
        not used or used > by_buffer[key]["allocated_bytes"]
        for key, used in usage.items()
    ):
        raise RuntimeError(
            "Live residency buffer bytes do not cover all assigned tensors."
        )

    def counts(count):
        return {
            "gpu_tensor_count": count,
            "host_tensor_count": 0,
            "other_tensor_count": 0,
            "unallocated_tensor_count": 0,
            "all_tensors_in_non_host_cuda_named_buffers": count > 0,
        }

    layers = [
        {"layer_index": index, "counts": counts(count)}
        for index, count in enumerate(layer_counts)
    ]
    summaries = {
        "layers": layers,
        "output_group": counts(output_count),
        "logical_tensor_bytes": logical_total,
        "cuda_tensor_count": len(cuda_names),
        "host_tensor_count": len(host_names),
        "other_tensor_count": 0,
        "unallocated_tensor_count": 0,
        "unique_host_buffer_bytes": sum(
            row["allocated_bytes"] for row in buffers if row["host"]
        ),
        "unique_cuda_buffer_bytes": sum(
            row["allocated_bytes"] for row in buffers if row["non_host_cuda_named"]
        ),
        "unique_other_buffer_bytes": 0,
        "all_repeating_layer_tensors_in_non_host_cuda_named_buffers": True,
        "all_output_group_tensors_in_non_host_cuda_named_buffers": True,
        "distinct_output_weight_present": not inventory["tied_output_expected"],
        "tied_output_present": inventory["tied_output_expected"],
        "model_output_pointer_bound": True,
        "model_input_embedding_pointer_bound": True,
        "active_output_tensor_name": "output.weight",
        "active_output_source_name": "token_embd.weight"
        if inventory["tied_output_expected"]
        else "output.weight",
    }
    if any(
        proof.get(key) != value or type(proof.get(key)) is not type(value)
        for key, value in summaries.items()
    ):
        raise RuntimeError(
            "Live residency aggregate summaries disagree with complete tensor rows."
        )
    return {
        "method": METHOD,
        "model_file_identity_bound": True,
        "transformer_output_cuda_buffer_metadata_verified": True,
        "physical_vram_residency_verified": False,
        "gpu_execution_verified": False,
        "kv_cache_residency_verified": False,
        "host_embedding_tensors": host_names,
        "tensor_count": len(expected),
        "layer_count": len(layer_counts),
        "gguf_tensor_count": inventory["tensor_count"],
        "tied_output_expected": inventory["tied_output_expected"],
        **(
            {
                "hybrid_context_evidence": context_evidence,
                "skipped_mtp_tensor_count": 15,
                "stored_layer_count": 33,
                "active_trunk_layer_count": 32,
            }
            if hybrid
            else {}
        ),
        "claim_limit": "All independently inventoried transformer/output model tensors have existing non-host CUDA0 buffer metadata. CPU embedding lookup is permitted. This does not inspect physical pages, KV/compute buffers or tensor contents, and does not establish GPU execution or numerical correctness.",
    }


def proof_path(state: dict, state_directory: Path) -> Path:
    session = state.get("witness", {}).get("session", "")
    if not isinstance(session, str) or not re.fullmatch(r"[a-f0-9]{32}", session):
        raise RuntimeError("Live residency requires a valid owned witness session.")
    return state_directory / "witness" / f"residency-{session}.json"


def validate_live_residency(state: dict, boot_id: str, state_directory: Path) -> dict:
    if require_healthy_boot(override_state=state_directory) != boot_id:
        raise RuntimeError("Host boot changed before live residency validation.")
    path = proof_path(state, state_directory)
    parent = path.parent.lstat()
    if (
        not stat.S_ISDIR(parent.st_mode)
        or parent.st_uid != os.getuid()
        or parent.st_mode & 0o077
    ):
        raise RuntimeError(
            "Live residency directory must be private, owned and not a symlink."
        )
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
            or info.st_size > 8 * 1024**2
        ):
            raise RuntimeError(
                "Live residency must be a private single-link regular JSON file."
            )
        raw = stream.read(8 * 1024**2 + 1)
        final = os.fstat(stream.fileno())
        named = path.lstat()
        fields = (
            "st_dev",
            "st_ino",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
            "st_mode",
            "st_uid",
            "st_nlink",
        )
        if len(raw) > 8 * 1024**2 or any(
            getattr(info, field) != getattr(final, field)
            or getattr(final, field) != getattr(named, field)
            for field in fields
        ):
            raise RuntimeError("Live residency private file changed during validation.")
    proof = json.loads(raw)
    if not isinstance(proof, dict):
        raise TypeError("Live residency JSON must contain an object.")
    inventory = gguf_inventory(Path(state["model"]), state["model_sha256"])
    result = validate_receipt(proof, state, boot_id, inventory)
    return {
        **result,
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_proof": proof,
        "raw_proof_json": raw.decode("utf-8"),
        "expected_gguf_inventory": inventory,
    }

#!/usr/bin/env python3
"""v1.0.3: render a root-reviewed cold-first 27B experiment; never execute it."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
import types
import os
from pathlib import Path
import re
import stat

VERSION = "1.1.0"
DELTA = "Bind targeted F32 diagnostic, strict timestamp framing, and exclude both consumed candidate boots; original floors remain."
ROOT = Path(__file__).absolute().parent
MODEL_SHA = "17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688"
MODEL_BYTES = 9605378560
MODEL_PATH = "/Users/mitch/.cache/claude-egpu/models/Qwen_Qwen3.6-27B-IQ2_XXS.gguf"
ALIAS = "qwen3.6:27b-iq2-xxs"
PROFILE = "qwen36-27b-iq2-reasoning-1024"
TEMPLATE_SHA = "e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259"
BINARY = "/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-small-prefill-global-scratch-build-v121/gpu-server-capture-small-prefill-global-scratch"
BINARY_SHA = None  # Actual candidate hash is supplied by the final reviewed build authority.
OLD_BOOTS = {"1790879561:56304", "1790920214:266510", "1791036657:431274", "1791115301:4730", "1791136050:203826", "1791188232:752319", "1791277640:498901"}
RESERVES = {"workspace": 2147483648, "allocator": 268435456, "driver": 2147483648, "safety": 1073741824}
ROLES = {"allocation_policy", "allocation_review", "build_abi", "cold_admission", "source_review", "root_activation"}
JSON_LIMIT = 16 * 1024 * 1024

class Refusal(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise Refusal(message)

def exact(value, expected, message):
    require(type(value) is type(expected) and value == expected, message)

def unconsumed_boot(value):
    return (type(value) is str and
            re.fullmatch(r"(?:0|[1-9][0-9]*):(?:0|[1-9][0-9]*)", value) is not None and
            value not in OLD_BOOTS)


def digest_shape(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "Exact lowercase SHA256 required")
    return value

def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key refused")
        result[key] = value
    return result

def parse_json(data):
    def invalid_constant(_value):
        raise Refusal("Nonfinite JSON refused")
    try:
        value = json.loads(data, object_pairs_hook=unique_pairs, parse_constant=invalid_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise Refusal("Invalid or excessively nested JSON") from error
    require(type(value) is dict, "JSON object root required")
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        require(depth <= 64, "Excessive JSON nesting refused")
        if type(item) is float:
            require(math.isfinite(item), "Nonfinite JSON number refused")
        elif type(item) is dict:
            pending.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            pending.extend((child, depth + 1) for child in item)
    return value

def absolute_path(value):
    require(type(value) is str and value and Path(value).is_absolute(), "Absolute path required")
    p = Path(value)
    require(str(p) == value and p.resolve(strict=True) == p, "Canonical nonsymlink path required")
    return p

def file_identity(s):
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

SOURCE_BINDINGS = {}
EXTERNAL_ROOTS = ("/Applications/", "/Library/", "/System/", "/usr/", "/bin/", "/sbin/", "/opt/homebrew/")
BUILD_ALIASES = {
    '/Users/mitch/dev/macuda/cuda-shim/build/libggml-cuda.a': '/Users/mitch/dev/macuda/cuda-shim/build/libggml-cuda.sm_120a.a',
    '/Users/mitch/dev/macuda/cuda-shim/libtinycudart/copy1d.cubin': '/Users/mitch/dev/macuda/cuda-shim/libtinycudart/copy1d.sm_120.cubin',
    '/Users/mitch/dev/macuda/cuda-shim/libtinycudart/copy2d.cubin': '/Users/mitch/dev/macuda/cuda-shim/libtinycudart/copy2d.sm_120.cubin',
}

def external_input(value):
    return type(value) is str and (value.startswith(EXTERNAL_ROOTS) or value in BUILD_ALIASES)

def metadata(s):
    return {"uid": s.st_uid, "gid": s.st_gid, "mode": stat.S_IMODE(s.st_mode), "bytes": s.st_size,
            "device": s.st_dev, "inode": s.st_ino, "mtime_ns": s.st_mtime_ns, "ctime_ns": s.st_ctime_ns}

def alias_chain(value):
    """Observe each symlink traversed, including links in resolved targets."""
    pending = list(Path(value).parts[1:]); current = Path('/'); links = []
    for _ in range(256):
        if not pending: return str(current), links
        part = pending.pop(0)
        if part == '.': continue
        if part == '..': current = current.parent; continue
        current = current / part
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode):
            text = os.readlink(current)
            links.append({"path": str(current), "target": text, "metadata": metadata(info)})
            target = Path(text)
            pending = list(target.parts[1:] if target.is_absolute() else target.parts) + pending
            current = Path('/') if target.is_absolute() else current.parent
    raise Refusal("Excessive system alias chain")

def configure_source_bindings(review):
    global SOURCE_BINDINGS
    bindings = review.get('external_source_bindings')
    require(type(bindings) is dict, 'Exact reviewed external source metadata required')
    pins = review['source_pins']
    require(set(bindings) == {p for p in pins if external_input(p)}, 'Complete external source bindings required')
    for name, binding in bindings.items():
        require(type(binding) is dict and set(binding) == {'canonical', 'sha256', 'metadata', 'aliases'},
                'Exact external binding schema required')
        require(binding['sha256'] == pins[name], 'External metadata/source hash differs')
        require(type(binding['canonical']) is str and
                (binding['canonical'] == BUILD_ALIASES[name] if name in BUILD_ALIASES else binding['canonical'].startswith(EXTERNAL_ROOTS)),
                'Trusted exact canonical source target required')
        require(type(binding['metadata']) is dict and binding['metadata'].get('uid') in (0, os.getuid()), 'Trusted external owner required')
        require(type(binding['metadata'].get('mode')) is int and not binding['metadata']['mode'] & 0o022,
                'External target cannot be group/other writable')
        require(type(binding['aliases']) is list, 'Exact external alias chain required')
    SOURCE_BINDINGS = bindings

def bound_input(value, expected, *, private=False):
    digest_shape(expected)
    if external_input(value):
        require(not private, 'External input cannot replace a private authority')
        require(value in SOURCE_BINDINGS, 'Unreviewed external input refused')
        binding = SOURCE_BINDINGS[value]
        require(binding['sha256'] == expected, 'External expected hash differs from reviewed binding')
        canonical, aliases = alias_chain(value)
        require(canonical == binding['canonical'] and aliases == binding['aliases'], 'External alias retargeted or metadata changed')
        p = Path(canonical)
        require(p.resolve(strict=True) == p, 'Canonical external target required')
        info = p.lstat()
        require(stat.S_ISREG(info.st_mode) and metadata(info) == binding['metadata'], 'External target owner/type/size/mode/identity changed')
        require(info.st_uid in (0, os.getuid()) and not info.st_mode & 0o022, 'Untrusted external target permissions')
        return p, binding
    p = absolute_path(value)
    info = p.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid() and not info.st_mode & 0o022, 'Private owned regular source required')
    strict = private or (('-v111/' in value or '-v124/' in value or value.startswith('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125/production/')) and value.endswith('.py'))
    if strict: require(stat.S_IMODE(info.st_mode) == 0o600, 'Private0600 proof/helper required')
    return p, None

def source_identity(value, expected):
    p, binding = bound_input(value, expected)
    info = p.lstat()
    return {"target": str(p), "metadata": metadata(info), "aliases": binding['aliases'] if binding else []}

def verified_file(value, expected, *, private=False, limit=None, prefix_bytes=0):
    p, binding = bound_input(value, expected, private=private)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size > 0, "Nonempty regular file required")
        if binding: require(metadata(before) == binding['metadata'], 'External open target differs from reviewed metadata')
        else: require(before.st_uid == os.getuid(), "File owner differs")
        if private: require(stat.S_IMODE(before.st_mode) == 0o600, "Private0600 proof required")
        if limit is not None: require(before.st_size <= limit, "Bounded JSON/source size exceeded")
        sha, chunks, prefix = hashlib.sha256(), [], bytearray()
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk: break
            sha.update(chunk)
            if limit is not None: chunks.append(chunk)
            if len(prefix) < prefix_bytes: prefix.extend(chunk[:prefix_bytes - len(prefix)])
        after = os.fstat(stream.fileno())
    named = p.lstat()
    require(stat.S_ISREG(named.st_mode) and metadata(before) == metadata(after) == metadata(named), "File changed while hashing")
    again, again_binding = bound_input(value, expected, private=private)
    require(again == p and again_binding == binding, 'Input alias or authority changed during read')
    require(sha.hexdigest() == expected, "Pinned file SHA differs")
    return {"bytes": before.st_size, "data": b"".join(chunks), "prefix": bytes(prefix)}

def load_proof(binding):
    require(type(binding) is dict and set(binding) == {"path", "sha256"}, "Exact proof path/SHA binding required")
    return parse_json(verified_file(binding["path"], binding["sha256"], private=True, limit=JSON_LIMIT)["data"])

def verify_pins(pins):
    require(type(pins) is dict and pins, "Nonempty exact source pins required")
    for name, expected in pins.items(): verified_file(name, expected)

def verify_command(argv, pins, env=None):
    import shutil
    require(type(argv) in (list, tuple) and argv and type(argv[0]) is str, 'Exact argv required')
    name = argv[0]
    resolved = name if Path(name).is_absolute() else shutil.which(name, path=(env or os.environ).get('PATH'))
    require(type(resolved) is str and resolved in pins, 'Unreviewed command executable refused: ' + str(name))
    verified_file(resolved, pins[resolved])
    return [resolved, *argv[1:]]

def guard_subprocess(module, pins):
    """Recheck the exact command file and aliases immediately before each spawn."""
    require(not hasattr(module, '_v111_bound_popen'), 'Command guard already installed')
    original = module.Popen
    def guarded(args, *positional, **kwargs):
        require(not kwargs.get('shell') and kwargs.get('executable') is None, 'Alternate shell/executable refused')
        argv = verify_command(args, pins, kwargs.get('env'))
        before = source_identity(argv[0], pins[argv[0]])
        process = original(argv, *positional, **kwargs)
        # Preserve a started child if post-spawn identity fails; never kill or retry it.
        try:
            require(source_identity(argv[0], pins[argv[0]]) == before, 'Command changed while spawning')
        except Exception:
            module._v111_started_child_on_refusal.append({'pid': process.pid, 'argv': argv, 'preserved': True})
            raise
        return process
    module._v111_bound_popen = original
    module._v111_started_child_on_refusal = []
    module.Popen = guarded

def verify_source_plan(plan):
    require(type(plan) is dict, "Source plan object required")
    pins = plan.get("source_pins")
    require(type(pins) is dict, "Source pin object required")
    for name in ("experimental_27b.py", "header_parser.py", "parse_guarded_memory_snapshots.py", "parse_framed.py", "original_parser.py", "expected-inventory.json"):
        require(str(ROOT / name) in pins, "Required source pin missing: " + name)
        digest_shape(pins[str(ROOT / name)])
    verify_pins(pins)
    return pins

def verified_source_module(name, path, pins):
    path = str(path)
    require(type(pins) is dict and path in pins, "Executed helper source pin missing")
    data = verified_file(path, pins[path], limit=1024 * 1024)["data"]
    module = types.ModuleType(name)
    module.__file__ = path
    exec(compile(data, path, "exec"), module.__dict__)
    return module

def identity(binary_sha=None):
    return {"model_sha256": MODEL_SHA, "model_bytes": MODEL_BYTES, "alias": ALIAS, "template_sha256": TEMPLATE_SHA, "context": 32768, "generation_profile": PROFILE, "binary_sha256": binary_sha, "publisher_revision":"4612927928b49982f8319dc3e2e6f62b9b73b192", "header_sha256":"84e75736205b467760b828bfef02fc88fd4edf4f47f4d4767341b412124eb1ec", "descriptor_sha256":"03ed563b55aa54f1ec6cd2b6c7911964a2e0795a33d6291b0ac21afd15e2b09e"}

def same_identity(proof, binary_sha):
    exact(proof.get("identity"), identity(binary_sha), "Proof model/template/context/profile/binary identity differs")
    require(type(proof["identity"]["context"]) is int and type(proof["identity"]["model_bytes"]) is int, "Boolean integer identity refused")

def final_review(review):
    exact(review.get("passed"), True, "Independent review has not passed")
    exact(review.get("seal_pending"), False, "Independent review seal remains pending")
    require(type(review.get("source_pins")) is dict and review["source_pins"], "Independent review source pins required")
    configure_source_bindings(review)

def fresh_actual(proof, now):
    exact(proof.get("actual"), True, "Fixture proof cannot admit an actual experiment")
    value = proof.get("observed_at")
    require(type(value) is str, "Actual observation timestamp required")
    try: when = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error: raise Refusal("Malformed observation timestamp") from error
    require(when.tzinfo is not None and 0 <= (now - when).total_seconds() <= 300, "Fresh actual observation<=300seconds required")

def bind_candidate_build(build, review, bindings):
    """Only the exact final root build and independently pinned ABI body can bind the new path."""
    require(type(build) is dict and type(build.get("identity")) is dict, "Final root candidate build is pending")
    candidate_sha = digest_shape(build["identity"].get("binary_sha256"))
    exact(build.get("binary_path"), BINARY, "Candidate binary path differs")
    exact(build.get("compiled"), True, "Final candidate build is not compiled")
    exact(build.get("seal_pending"), False, "Final candidate build seal is pending")
    final_review(review)
    require(type(build.get("source_pins")) is dict, "Final candidate build source/library pins required")
    exact(build["source_pins"].get(BINARY), candidate_sha, "Candidate binary is not bound by the final build")
    exact(review["source_pins"].get(BINARY), candidate_sha, "Independent review does not bind the actual new binary")
    exact(review["source_pins"].get(bindings["build_abi"]["path"]), bindings["build_abi"]["sha256"], "Independent review does not bind exact final build/ABI body")
    return candidate_sha

def experimental_admission(proofs, bindings, plan, now):
    """Pure boundary checks; compiled execution/numerics/quality remain first-trial outcomes."""
    require(type(proofs) is dict and set(proofs) == ROLES and set(bindings) == ROLES, "All six reviewed admission roles required")
    policy, policy_review = proofs["allocation_policy"], proofs["allocation_review"]
    build, cold = proofs["build_abi"], proofs["cold_admission"]
    review, activation = proofs["source_review"], proofs["root_activation"]
    binary_sha = bind_candidate_build(build, review, bindings)
    for p in (policy, build, cold, activation): same_identity(p, binary_sha)
    exact(policy.get("schema"), "qwen35-27b-bounded-allocation-policy-v1", "Reviewed allocation policy schema required")
    exact(policy.get("verdict"), "ALLOW_BOUNDED_COLD_FIRST_EXPERIMENT", "Final allocation policy does not permit the bounded experiment")
    exact(policy.get("final"), True, "Allocation policy is not final")
    exact(policy.get("reserves"), RESERVES, "Original reserves cannot change")
    require(all(type(v) is int for v in policy["reserves"].values()), "Boolean reserve bytes refused")
    exact(policy.get("placement_policy"), "CPU_INPUT_EMBEDDING_DEFAULT_ONLY", "Explicit reviewed embedding policy required")
    exact(policy.get("input_embedding_bytes"), 417177600, "Exact input embedding size required")
    exact(policy.get("charged_bound_bytes"), 16667408384, "Reviewed experimental charge differs")
    require(type(policy["input_embedding_bytes"]) is int and type(policy["charged_bound_bytes"]) is int, "Boolean policy byte fields refused")
    exact(policy.get("fresh_pool_measurement_required"), True, "Historical9B pool cannot admit a new pool")
    require(type(policy.get("memory_domain")) is str and policy["memory_domain"], "Reviewed memory domain required")
    final_review(policy_review)
    exact(policy_review["source_pins"].get(bindings["allocation_policy"]["path"]), bindings["allocation_policy"]["sha256"], "Independent policy review does not bind this policy")
    final_review(review)
    for name, digest in plan["source_pins"].items():
        exact(review["source_pins"].get(name), digest, "Independent source review does not bind every planned source")
    exact(build.get("schema"), "qwen35-27b-build-abi-admission-v1", "Exact build/ABI admission required")
    exact(build.get("static_build_verified"), True, "Static build not verified")
    exact(build.get("host_abi_source_reviewed"), True, "Current host/library/header ABI review required")
    exact(build.get("same_process_preload_capacity_refusal_source_reviewed"), True, "A reviewed same-process capacity refusal before model load is missing")
    exact(build.get("preload_envelope_bytes"), 16667408384, "Exact reviewed preload envelope required")
    exact(build.get("preused_driver_allowance_bytes"), 2147483648, "Original driver allowance must cover reconciled pre-used bytes")
    require(type(build["preload_envelope_bytes"]) is int and type(build["preused_driver_allowance_bytes"]) is int, "Boolean capacity policy refused")
    exact(build.get("candidate_runtime_compatibility"), "UNMEASURED_FIRST_TRIAL_OUTCOME", "Do not fabricate runtime compatibility before first trial")
    require(type(build.get("source_pins")) is dict and build["source_pins"].get(BINARY) == binary_sha, "Exact snapshot build/source/library bindings required")
    exact(review["source_pins"].get(bindings["build_abi"]["path"]), bindings["build_abi"]["sha256"], "Independent source review must bind the exact build/ABI admission body")
    for name, digest in build["source_pins"].items(): exact(review["source_pins"].get(name), digest, "Build/ABI source omitted from independent review")
    fresh_actual(cold, now)
    exact(cold.get("schema"), "qwen35-27b-cold-no-owner-admission-v1", "New cold-owner admission required")
    exact(cold.get("passed"), True, "Cold root admission has not passed")
    boot = cold.get("boot_id")
    require(unconsumed_boot(boot), "Old/malformed boot cannot admit a cold experiment")
    exact(cold.get("cold_recovery_verified"), True, "Fresh cold recovery unverified")
    exact(cold.get("owners"), [], "Any existing native/transport/gateway owner refuses cold launch")
    exact(cold.get("fault_clear"), True, "Fault latch not clear")
    exact(cold.get("listeners"), [], "Any existing inference listener refuses cold launch")
    exact(cold.get("exclusive_root_trial_reserved"), True, "Exclusive one-shot root trial reservation required")
    require(type(cold.get("source_pins")) is dict and cold["source_pins"], "Cold passive evidence hashes required")
    fresh_actual(activation, now)
    exact(activation.get("schema"), "qwen35-27b-root-activation-v1", "Explicit root activation required")
    exact(activation.get("root_authorized"), True, "Root activation absent")
    exact(activation.get("mode"), "EXPERIMENT_ONLY", "Production/fullqualification launch refused")
    exact(activation.get("boot_id"), boot, "Root activation boot differs")
    exact(activation.get("one_native_start_only"), True, "Exactly one separately owned start required")
    exact(activation.get("automatic_retry"), False, "Automatic retries refused")
    expected = {k: bindings[k] for k in ROLES if k != "root_activation"}
    exact(activation.get("bindings"), expected, "Root activation does not bind every exact admission proof")
    return {"experimental_argv_review_ready": True, "physical_launch_ready": False, "production_ready": False, "full_qualification": False, "boot_id": boot, "binary_sha256":binary_sha, "compiled_operator_verified": False, "actual_peak_verified": False, "candidate_numerics_verified": False, "actual_placement_verified": False, "quality_verified": False}

def build_launch_argv(admission, model):
    require(admission.get("experimental_argv_review_ready") is True, "Experimental admission refused")
    exact(model, MODEL_PATH, "The new guard requires its exact absolute model path")
    p = absolute_path(model)
    require(p.name == "Qwen_Qwen3.6-27B-IQ2_XXS.gguf", "Exact complete artifact filename required")
    return [BINARY, "--model", str(p), "--alias", ALIAS, "--host", "127.0.0.1", "--port", "8000", "--device", "CUDA0", "--ctx-size", "32768", "--batch-size", "256", "--ubatch-size", "256", "--parallel", "1", "--flash-attn", "on", "--fit", "off", "--spec-type", "none", "--cache-type-k", "f16", "--cache-type-v", "f16", "--log-verbosity", "5", "-ngl", "99", "--reasoning", "off", "--jinja", "--no-warmup"]

def validate_preload_guard_records(text):
    """Execute the exact frozen CPU parser bytes; no CUDA query or peak/fit inference."""
    path = str(ROOT / "parse_framed.py")
    parser = verified_source_module("framed27b_memory", path,
        {path: "77cd928d800d12109a7cc76dea08e8f5c08a70f6e35fc231a705a659e3278a09"})
    return parser.parse_memory_log(text)

def first_trial_quality_admission(outcomes, expected_owner, policy, evidence_pins):
    """Mechanical proof admission only; does not accept semantic research or quality."""
    exact(outcomes.get("schema"), "qwen35-27b-first-trial-outcomes-v1", "First-trial outcome schema required")
    require(type(expected_owner) is dict, "Actual owner tuple required")
    binary_sha = digest_shape(expected_owner.get("binary_sha256"))
    same_identity(outcomes, binary_sha)
    exact(outcomes.get("actual"), True, "Fixture outcomes cannot admit quality")
    exact(outcomes.get("owner"), expected_owner, "Outcome owner differs")
    require(type(expected_owner) is dict, "Actual owner tuple required")
    for field in ("native_pid", "transport_pid", "native_uid", "transport_uid"):
        require(type(expected_owner.get(field)) is int and expected_owner[field] > 0, "Actual nonboolean owner PID/UID required")
    require(unconsumed_boot(expected_owner.get("boot_id")), "Old/malformed owner boot refused")
    for field in ("native_birth", "transport_birth"):
        require(type(expected_owner.get(field)) is str and expected_owner[field], "Actual owner birth required")
    exact(outcomes["identity"]["binary_sha256"], binary_sha, "Actual outcome binary differs")
    exact(expected_owner.get("model_sha256"), MODEL_SHA, "Actual outcome model differs")
    for field in ("compiled_operator_numerics_passed", "strict_cpu_embedding_reference_passed", "active_cuda_loaded_verified", "actual_peak_with_reserves_passed", "original_pre_post_memory_parser_passed", "strict_preload_guard_parser_passed", "same_process_preload_capacity_guard_passed", "preused_within_full_driver_allowance"):
        exact(outcomes.get(field), True, "First-trial required outcome missing: " + field)
    exact(outcomes.get("mtp_enabled"), False, "MTP must remain disabled")
    exact(outcomes.get("tensor_buffer_overrides"), [], "Tensor overrides are outside this experiment")
    placement = outcomes.get("placement")
    require(type(placement) is dict, "Actual placement inventory required")
    for field, expected in {"cpu_input_embedding_bytes": 417177600, "active_tensor_count": 851, "mtp_skipped_tensor_count": 15, "trunk_blocks": 64, "cuda_active_tensor_count": 850}.items(): exact(placement.get(field), expected, "Exact actual placement differs: " + field); require(type(placement[field]) is int, "Boolean placement count refused")
    records = outcomes.get("memory_records")
    require(type(records) is list and len(records) == 2, "Actual pre-load/post-load snapshots required")
    for record, stage in zip(records, ("pre_load", "post_load")):
        exact(record.get("stage"), stage, "Memory stage differs")
        exact(record.get("cuda_success"), True, "Memory query failed")
        require(type(record.get("free_bytes")) is int and type(record.get("total_bytes")) is int and 0 <= record["free_bytes"] <= record["total_bytes"] and record["total_bytes"] > 0, "Invalid or boolean memory bytes")
        exact(record.get("memory_domain"), policy["memory_domain"], "Memory domain differs from reviewed policy")
        require(type(record.get("raw_path")) is str, "Raw snapshot path required")
        digest_shape(record.get("raw_sha256")); exact(evidence_pins.get(record["raw_path"]), record["raw_sha256"], "Raw memory record hash missing")
    exact(records[0]["total_bytes"], records[1]["total_bytes"], "Actual pre/post total changed")
    guard = outcomes.get("pre_load_guard")
    require(type(guard) is dict and guard.get("accepted") is True and type(guard.get("required_pool_bytes")) is int and guard["required_pool_bytes"] == 16667408384 and type(guard.get("driver_allowance_bytes")) is int and guard["driver_allowance_bytes"] == 2147483648, "Actual accepted same-process preload guard required")
    require(type(outcomes.get("evidence_pins")) is dict and outcomes["evidence_pins"] == evidence_pins and len(evidence_pins) >= 4, "All actual raw numerical/placement/peak/memory evidence pins required")
    return {"mechanical_first_trial_outcomes_ready_for_independent_quality_review": True, "coding2of2_verified": False, "standard_dr_verified": False, "full_quality_verified": False, "full_qualification": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--admission", required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    plan = parse_json(verified_file(args.plan, args.plan_sha256, private=True, limit=JSON_LIMIT)["data"])
    require(plan.get("schema") == "qwen35-27b-cold-first-source-plan-v1", "Exact source plan required")
    verify_source_plan(plan)
    require(not any(k.startswith("LLAMA_ARG_") for k in os.environ) and not os.environ.get("TINYNV_FMC_REINIT"), "Native environment overrides or warm reinitialization refused")
    packet = parse_json(verified_file(args.admission, args.admission_sha256, private=True, limit=JSON_LIMIT)["data"])
    exact(packet.get("schema"), "qwen35-27b-experimental-admission-packet-v1", "Exact admission packet required")
    bindings = packet.get("bindings")
    require(type(bindings) is dict and set(bindings) == ROLES, "Final allocation/ABI/cold/review/root admission is pending")
    proofs = {role: load_proof(binding) for role, binding in bindings.items()}
    exact(proofs["source_review"].get("source_pins", {}).get(args.plan), args.plan_sha256, "Independent source review does not bind the exact plan")
    admitted = experimental_admission(proofs, bindings, plan, dt.datetime.now(dt.timezone.utc))
    verify_pins(proofs["allocation_review"]["source_pins"])
    verify_pins(proofs["source_review"]["source_pins"])
    verify_pins(proofs["build_abi"]["source_pins"])
    verify_pins(proofs["cold_admission"]["source_pins"])
    full = verified_file(args.model, MODEL_SHA, prefix_bytes=16 * 1024 * 1024)
    exact(full["bytes"], MODEL_BYTES, "Complete publisher artifact size differs")
    header = verified_source_module("exact27b_header", ROOT / "header_parser.py", plan["source_pins"])
    inventory = header.parse_header(full["prefix"])
    header.validate_inventory(inventory)
    expected = parse_json(verified_file(str(ROOT / "expected-inventory.json"), plan["source_pins"][str(ROOT / "expected-inventory.json")], limit=JSON_LIMIT)["data"])
    exact(inventory, expected, "Complete artifact header differs from reviewed prefix")
    argv = build_launch_argv(admitted, args.model)
    verify_pins(plan["source_pins"])
    for binding in bindings.values(): load_proof(binding)
    fresh_actual(proofs["cold_admission"], dt.datetime.now(dt.timezone.utc))
    fresh_actual(proofs["root_activation"], dt.datetime.now(dt.timezone.utc))
    verified_file(BINARY, admitted["binary_sha256"])
    print(json.dumps({"version": VERSION, **admitted, "native_argv": argv, "required_environment": {"LLMSX_MEMORY_SNAPSHOT": "1", "LLMSX_27B_CAPACITY_GUARD": "1"}, "generation_controls": plan["generation_controls"], "mode": "EXPERIMENT_ONLY", "executed": False, "actual_operations": 0, "notice": "Render only. A separately reviewed root one-shot cold launcher must recheck actual owners/fault/build/policy immediately before its sole start. Post-load operator/placement/memory/numerics and original coding/research/fullquality remain pending."}, indent=2))

if __name__ == "__main__":
    try: main()
    except (Refusal, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"version": VERSION, "refused": True, "physical_launch_ready": False, "production_ready": False, "full_qualification": False, "actual_operations": 0, "error": str(error)}))
        raise SystemExit(2)

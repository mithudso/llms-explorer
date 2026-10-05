"""v1.0.3. Candidate controls with current compiled-build fixture fields; no model operations."""
import copy
import datetime as dt
import importlib.util
from pathlib import Path
import socket
import subprocess
import unittest
from unittest import mock

ROOT = Path(__file__).absolute().parent

def denied(*_args, **_kwargs):
    raise AssertionError("Real process/network/exec operation forbidden in source controls")

for name in ("Popen", "run", "call", "check_call", "check_output"):
    setattr(subprocess, name, denied)
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
socket.getaddrinfo = denied
import os
os.system = denied
os.execv = denied
os.execve = denied
os.posix_spawn = denied
os.posix_spawnp = denied
spec = importlib.util.spec_from_file_location("experimental27b", ROOT / "experimental_27b.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

class BoundaryControls(unittest.TestCase):
    def fixture(self):
        now = dt.datetime(2030, 1, 1, tzinfo=dt.timezone.utc)
        bindings = {r: {"path": "/FIXTURE/" + r + ".json", "sha256": "a" * 64} for r in e.ROLES}
        ident = e.identity("d" * 64)
        pins = {"/FIXTURE/source.py": "b" * 64}
        review = {"passed": True, "seal_pending": False, "source_pins": {**pins, e.BINARY: "d" * 64, bindings["build_abi"]["path"]:bindings["build_abi"]["sha256"]}}
        policy = {"identity": ident, "schema": "qwen35-27b-bounded-allocation-policy-v1", "verdict": "ALLOW_BOUNDED_COLD_FIRST_EXPERIMENT", "final": True, "reserves": e.RESERVES.copy(), "placement_policy": "CPU_INPUT_EMBEDDING_DEFAULT_ONLY", "input_embedding_bytes": 417177600, "charged_bound_bytes": 16667408384, "fresh_pool_measurement_required": True, "memory_domain": "FIXTURE_ONLY_NOT_ACTUAL"}
        cold = {"identity": ident, "actual": True, "observed_at": now.isoformat(), "schema": "qwen35-27b-cold-no-owner-admission-v1", "passed":True,"boot_id": "9000000000:1", "cold_recovery_verified": True, "owners": [], "fault_clear": True, "listeners": [], "exclusive_root_trial_reserved": True, "source_pins": pins}
        proofs = {"allocation_policy": policy, "allocation_review": {"passed": True, "seal_pending": False, "source_pins": {bindings["allocation_policy"]["path"]: bindings["allocation_policy"]["sha256"]}}, "build_abi": {"identity": ident, "schema": "qwen35-27b-build-abi-admission-v1", "static_build_verified": True, "binary_path": e.BINARY, "compiled": True, "seal_pending": False, "host_abi_source_reviewed": True, "same_process_preload_capacity_refusal_source_reviewed": True, "preload_envelope_bytes":16667408384,"preused_driver_allowance_bytes":2147483648,"candidate_runtime_compatibility": "UNMEASURED_FIRST_TRIAL_OUTCOME", "source_pins": {e.BINARY: "d" * 64}, "independent_review": bindings["source_review"]}, "cold_admission": cold, "source_review": review, "root_activation": {"identity": ident, "actual": True, "observed_at": now.isoformat(), "schema": "qwen35-27b-root-activation-v1", "root_authorized": True, "mode": "EXPERIMENT_ONLY", "boot_id": cold["boot_id"], "one_native_start_only": True, "automatic_retry": False, "bindings": {r: bindings[r] for r in e.ROLES if r != "root_activation"}}}
        return proofs, bindings, {"source_pins": pins}, now

    def test_fixture_only_render_ready_never_physical_or_quality(self):
        result = e.experimental_admission(*self.fixture())
        self.assertTrue(result["experimental_argv_review_ready"])
        for key in ("physical_launch_ready", "production_ready", "full_qualification", "candidate_numerics_verified", "actual_peak_verified", "compiled_operator_verified"):
            self.assertIs(result[key], False)

    def test_missing_policy_and_pending_or_unbound_reviews_refuse(self):
        for change in ("policy", "pending", "source", "policy_binding", "abi", "preload"):
            p,b,plan,now=self.fixture()
            if change=="policy": p.pop("allocation_policy")
            if change=="pending": p["source_review"]["seal_pending"]=True
            if change=="source": p["source_review"]["source_pins"]={"/wrong": "b"*64}
            if change=="policy_binding": p["allocation_review"]["source_pins"][b["allocation_policy"]["path"]]="c"*64
            if change=="abi": p["build_abi"]["host_abi_source_reviewed"]=False
            if change=="preload": p["build_abi"]["same_process_preload_capacity_refusal_source_reviewed"]=False
            with self.subTest(change=change), self.assertRaises(e.Refusal): e.experimental_admission(p,b,plan,now)

    def test_old_boot_live_owner_fault_or_stale_actual_refuses(self):
        for change in ("old", "owner", "listener", "fault", "stale", "fixture"):
            p,b,plan,now=self.fixture(); c=p["cold_admission"]
            if change=="old": c["boot_id"]="1790920214:266510"
            if change=="owner": c["owners"]=[{"pid":21735}]
            if change=="listener": c["listeners"]=[8000]
            if change=="fault": c["fault_clear"]=False
            if change=="stale": c["observed_at"]=(now-dt.timedelta(seconds=301)).isoformat()
            if change=="fixture": c["actual"]=False
            with self.subTest(change=change), self.assertRaises(e.Refusal): e.experimental_admission(p,b,plan,now)

    def test_bool_context_bytes_and_changed_policy_or_production_refuse(self):
        for change in ("context", "model_bytes", "reserve", "embedding", "policy_bytes", "production", "retry", "activation_binding"):
            p,b,plan,now=self.fixture()
            if change in ("context", "model_bytes"):
                for key in ("allocation_policy", "build_abi", "cold_admission", "root_activation"):
                    p[key]["identity"]=dict(p[key]["identity"]); p[key]["identity"][change]=True
            if change=="reserve": p["allocation_policy"]["reserves"]["allocator"]=True
            if change=="embedding": p["allocation_policy"]["input_embedding_bytes"]=True
            if change=="policy_bytes": p["allocation_policy"]["charged_bound_bytes"]+=1
            if change=="production": p["root_activation"]["mode"]="PRODUCTION"
            if change=="retry": p["root_activation"]["automatic_retry"]=True
            if change=="activation_binding": p["root_activation"]["bindings"]={}
            with self.subTest(change=change), self.assertRaises(e.Refusal): e.experimental_admission(p,b,plan,now)

    def test_duplicate_nested_nonfinite_json_refuses(self):
        for raw in ('{"x":1,"x":2}', '{"outer":{"x":1,"x":2}}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(e.Refusal): e.parse_json(raw)

    def test_argv_only_exact_controls_and_no_execution(self):
        result=e.experimental_admission(*self.fixture())
        with mock.patch.object(e,"absolute_path",return_value=Path(e.MODEL_PATH)):
            argv=e.build_launch_argv(result,e.MODEL_PATH)
        self.assertEqual(argv[0], e.BINARY)
        for option,value in (("--ctx-size","32768"),("-ngl","99"),("--spec-type","none"),("--fit","off"),("--reasoning","off"),("--parallel","1"),("--device","CUDA0")):
            self.assertEqual(argv[argv.index(option)+1],value)
        self.assertNotIn("--tensor-buffer-type",argv)
        with self.assertRaises(e.Refusal): e.build_launch_argv({},"/FIXTURE/model")

    def test_quality_outcomes_missing_or_bool_pid_refuse(self):
        with self.assertRaises(e.Refusal): e.first_trial_quality_admission({}, {"native_pid":True}, {}, {})
        p,b,plan,now=self.fixture()
        owner={"native_pid":True,"transport_pid":4,"native_uid":501,"transport_uid":501,"binary_sha256":"d"*64,"model_sha256":e.MODEL_SHA,"boot_id":"9000000000:1","native_birth":"fixture","transport_birth":"fixture"}
        outcomes={"schema":"qwen35-27b-first-trial-outcomes-v1","identity":e.identity("d"*64),"actual":True,"owner":owner}
        with self.assertRaisesRegex(e.Refusal,"Actual nonboolean owner PID/UID required"):
            e.first_trial_quality_admission(outcomes,owner,p["allocation_policy"],{})


class NewCandidateIdentityControls(unittest.TestCase):
    fixture = BoundaryControls.fixture
    def test_current_live_boot_refuses(self):
        p,b,plan,now=self.fixture()
        p["cold_admission"]["boot_id"]="1791036657:431274"
        with self.assertRaisesRegex(e.Refusal,"Old/malformed boot"):
            e.experimental_admission(p,b,plan,now)

    def test_old_model_alias_or_header_identity_refuses(self):
        for key,value in [("model_sha256","5ccd27a1ab2c909b1c0c3ccaeefde21d0c5c5f277eca2b607b813c18ad4a687e"),("alias","qwen3.5:27b-iq2-xxs"),("header_sha256","7b08249f9039dec3df0941e846b273290ffdc086137dbec2266b8d83d70ff6d5")]:
            p,b,plan,now=self.fixture();p=copy.deepcopy(p)
            p["allocation_policy"]["identity"][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(e.Refusal,"Proof model/template/context/profile/binary identity differs"):
                e.experimental_admission(p,b,plan,now)

class ReviewedGuardRegressionControls(unittest.TestCase):
    def test_all_required_sources_must_be_pinned_before_any_source_import(self):
        pins={str(e.ROOT/n):"a"*64 for n in ("experimental_27b.py","header_parser.py","parse_guarded_memory_snapshots.py","parse_framed.py","original_parser.py","expected-inventory.json")}
        for name in list(pins):
            broken=dict(pins);broken.pop(name)
            with self.subTest(name=name),mock.patch.object(e,"verify_pins") as verify,self.assertRaisesRegex(e.Refusal,"Required source pin missing"):
                e.verify_source_plan({"source_pins":broken})
            verify.assert_not_called()
        with mock.patch.object(e,"verify_pins") as verify:
            self.assertEqual(e.verify_source_plan({"source_pins":pins}),pins)
        verify.assert_called_once_with(pins)

    def test_helper_executes_only_verified_returned_bytes(self):
        path=str(e.ROOT/"header_parser.py")
        with self.assertRaisesRegex(e.Refusal,"Executed helper source pin missing"):
            e.verified_source_module("fixture",path,{})
        with mock.patch.object(e,"verified_file",return_value={"data":b"value=42\n"}) as read:
            module=e.verified_source_module("fixture",path,{path:"a"*64})
        self.assertEqual(module.value,42)
        read.assert_called_once_with(path,"a"*64,limit=1024*1024)
        self.assertEqual(module.__file__,path)

    def test_object_roots_and_deep_nesting_refuse_cleanly(self):
        for raw in ('[]','null','42','"text"','{"x":'+'['*1100+'0'+']'*1100+'}', '{"x":'+'['*65+'0'+']'*65+'}'):
            with self.subTest(raw=raw[:40]),self.assertRaises(e.Refusal):e.parse_json(raw)
        self.assertEqual(e.parse_json('{"x":[0,{"a":1}]}'),{"x":[0,{"a":1}]})

if __name__ == "__main__": unittest.main()

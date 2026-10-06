#!/usr/bin/env python3
"""One root-authorized cold-first 27B startup; no qualification or retry."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import shlex
import stat
import subprocess
import sys
import time
import types
import urllib.error
import urllib.request

VERSION = "1.1.0"
DELTA = "Bounded capture successor also limits readiness metadata with an absolute startup/read deadline and refuses redirects."
ROOT = Path("/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125/production/startup-preparation")
RENDERER = Path("/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125/production/renderer-preparation/experimental_27b.py")
SERVICE_DIR = Path("/Users/mitch/dev/worktrees/skills-egpu-full-qualification/rtx5080-egpu-harness/scripts")
CANONICAL_HARNESS = "/Users/mitch/dev/skills/ai-llm-model-layer/references/rtx5080-egpu-harness"
RUNTIME = Path("/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125/production/cold-runtime")
DRIVER = Path("/Applications/TinyGPU.app/Contents/MacOS/TinyGPU")
OVERRIDE_PREFIXES = ("TINYNV_", "TINYCUDART_", "TINYCUBLAS_", "LLAMA_ARG_", "MACUDA_", "EGPU_", "LLMSX_", "CUDA_", "GGML_")
OVERRIDE_NAMES = {"TINY_PORT", "TINYGRAD_DIR", "TINYGRAD_PYTHON", "OLLAMA_PROXY_PORT", "LITELLM_PORT", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "PYTHONPATH"}

CLOUD_CHECKER = None
CLOUD_PROFILES = {}
CLOUD_HELPER = Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-client-guard-v104/cloud_client_guard.py')

class Refusal(RuntimeError): pass

def require(value, message):
    if not value: raise Refusal(message)

def private_write(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")

def read_bound(path, expected=None, limit=16*1024*1024):
    p=Path(path)
    require(p.is_absolute() and p.resolve()==p,"Canonical nonsymlink file required")
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as handle:
        before=os.fstat(handle.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid(),"Regular owned file required")
        require(before.st_size<=limit,"Bounded input exceeded")
        data=handle.read(limit+1)
        after=os.fstat(handle.fileno())
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and p.lstat().st_ino==before.st_ino,"File changed")
    digest=hashlib.sha256(data).hexdigest()
    if expected is not None: require(type(expected) is str and re.fullmatch(r"[a-f0-9]{64}",expected) and digest==expected,"Bound file SHA differs")
    return {"data":data,"sha256":digest}

def source_module(name, filename, data):
    module = types.ModuleType(name)
    module.__file__ = str(filename)
    sys.modules[name] = module
    exec(compile(data, str(filename), "exec"), module.__dict__)
    return module

PRODUCT_MODULES = ("egpu_service", "macuda_qwen35", "macuda_safe_runtime", "macuda_residency", "macuda_service")

def load_product_modules(renderer, pins):
    require(not any(name in sys.modules for name in PRODUCT_MODULES), "Preloaded product module refused")
    bodies = {}
    for name in PRODUCT_MODULES:
        filename = str(SERVICE_DIR / (name + ".py"))
        require(filename in pins, "Required product source pin missing: " + name)
        bodies[name] = renderer.verified_file(filename, pins[filename], limit=1024*1024)["data"]
    for name in PRODUCT_MODULES:
        source_module(name, SERVICE_DIR / (name + ".py"), bodies[name])
    return sys.modules["macuda_service"]

def pin_identities(pins, renderer):
    result = {}
    for filename in pins:
        result[filename] = renderer.source_identity(filename, pins[filename])
    return result

def verify_pin_identities(pins, renderer, expected):
    require(pin_identities(pins, renderer) == expected, "Pinned source identity changed during startup polling")

def refuse_overrides(env):
    unexpected = sorted(k for k in env if k.startswith(OVERRIDE_PREFIXES) or k in OVERRIDE_NAMES)
    require(not unexpected, "Inherited runtime/model/GPU overrides refused: " + ",".join(unexpected))

def birth_uid(pid):
    require(type(pid) is int and pid>0,"Invalid owner PID")
    value=subprocess.run(["/bin/ps","-p",str(pid),"-o","lstart=,uid=,command="],check=True,text=True,capture_output=True).stdout.strip()
    require(value,"Retained process identity missing")
    return value

def worker_absence():
    listing = subprocess.run(["/bin/ps", "-axo", "pid=,comm=,command="], check=True, text=True, capture_output=True).stdout
    for row in listing.splitlines():
        pieces = row.strip().split(None, 2)
        if len(pieces) != 3 or not pieces[0].isdigit() or int(pieces[0]) == os.getpid(): continue
        name = Path(pieces[1]).name
        cloud = CLOUD_CHECKER.classify(int(pieces[0])) if name == "claude" and CLOUD_CHECKER else {"cloud_only": False}
        if name == "claude": CLOUD_PROFILES[int(pieces[0])] = cloud
        require((name != "claude" or cloud.get("cloud_only") is True) and not re.search(r"(?:^|/)egpu_research_agent\.py(?:\s|$)|(?:^|/)claude_qwen35\.py(?:\s|$)|(?:^|\s)-m\s+litellm(?:\s|$)", pieces[2]), "Existing worker/gateway refuses cold startup")

def capture_owner_absence(allowed_pid=None):
    listing=subprocess.run(["/bin/ps","-axo","pid=,comm=,command="],check=True,text=True,capture_output=True,timeout=15).stdout
    for row in listing.splitlines():
        parts=row.strip().split(None,2)
        if len(parts)!=3 or not parts[0].isdigit():continue
        pid=int(parts[0]);name=Path(parts[1]).name
        require(not name.startswith("gpu-server-capture") or pid==allowed_pid,"Other capture executable refuses startup: PID"+str(pid))

class NoReadinessRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise Refusal("Readiness redirect refused")

def readiness_metadata(startup_deadline,clock=time.monotonic):
    deadline=min(startup_deadline,clock()+2)
    require(deadline>clock(),"Absolute startup deadline exceeded before readiness")
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoReadinessRedirect())
    try:
        with opener.open("http://127.0.0.1:8000/v1/models",timeout=max(0.001,deadline-clock())) as response:
            require(response.status==200,"Unexpected readiness status")
            chunks=[];size=0
            while response.fp is not None:
                remaining=deadline-clock();require(remaining>0,"Absolute readiness body deadline exceeded")
                response.fp.raw._sock.settimeout(remaining)
                chunk=response.read1(min(65536,1024**2+1-size));size+=len(chunk)
                require(size<=1024**2,"Readiness metadata exceeds bound")
                if not chunk:break
                chunks.append(chunk)
            return json.loads(b"".join(chunks))
    except urllib.error.HTTPError as error:
        error.close()
        if error.code==503:return None
        raise Refusal("Unexpected readiness HTTP status: "+str(error.code)) from error
    except urllib.error.URLError as error:
        if isinstance(error.reason,ConnectionRefusedError):return None
        raise Refusal("Readiness connection failed: "+str(error.reason)) from error

def verify_runtime_library_aliases(config):
    expected = {
        "/opt/homebrew/opt/openssl@3/lib/libssl.3.dylib": "/opt/homebrew/Cellar/openssl@3/3.6.5/lib/libssl.3.dylib",
        "/opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib": "/opt/homebrew/Cellar/openssl@3/3.6.5/lib/libcrypto.3.dylib",
    }
    bindings = config.get("runtime_library_aliases")
    require(type(bindings) is dict and set(bindings) == set(expected), "Exact OpenSSL runtime aliases required")
    for alias, canonical in expected.items():
        binding = bindings[alias]
        require(type(binding) is dict and set(binding) == {"path", "sha256"} and binding["path"] == canonical,
                "Exact OpenSSL canonical runtime binding required")
        require(type(binding["sha256"]) is str and re.fullmatch(r"[a-f0-9]{64}", binding["sha256"]), "Exact runtime library SHA required")
        require(Path(alias).resolve(strict=True) == Path(canonical), "Runtime library alias retargeted: " + alias)
        read_bound(canonical, binding["sha256"])


def recheck_cold(service, admitted, pins, renderer, stale_faults, config):
    verify_runtime_library_aliases(config)
    renderer.verify_pins(pins)
    renderer.verify_pins(stale_faults)
    require(service.common.boot_identifier() == admitted["boot_id"], "Current boot differs from actual cold admission")
    service.reject_faults(admitted["boot_id"])
    service.reject_other_owners()
    capture_owner_absence()
    require(not service.driver_servers(), "Existing transport refuses cold startup")
    require(not service.listener_pids(8000), "Port8000 must be free before startup")
    worker_absence()

def dynamic_authority(document, bindings, admitted, renderer, now):
    """Root-owned actual authority D; independent STATIC review S remains distinct."""
    require(type(document) is dict and document.get("schema")=="qwen35-27b-root-dynamic-startup-authority-v1", "Exact root dynamic authority required")
    renderer.fresh_actual(document, now)
    require(document.get("authority")=="root" and document.get("root_authorized") is True, "Root-owned dynamic authority absent")
    require(type(document.get("issuer_uid")) is int and document["issuer_uid"]==os.getuid(), "Root authority UID differs")
    require(document.get("mode")=="EXPERIMENT_ONLY" and document.get("boot_id")==admitted["boot_id"], "Dynamic authority mode/currentboot differs")
    require(document.get("one_native_start_only") is True and document.get("automatic_retry") is False, "Dynamic authority must permit one start without retry")
    require(type(document.get("bindings")) is dict and document["bindings"]==bindings, "Dynamic authority must bind exact P/config/S/sourceplan")
    require(set(bindings)=={"admission","config","static_review","source_plan"}, "Exact one-way authority binding roles required")
    for item in bindings.values():
        require(type(item) is dict and set(item)=={"path","sha256"}, "Exact authority path/SHA required")
        renderer.verified_file(item["path"], item["sha256"], private=True, limit=renderer.JSON_LIMIT)
    return {"root_owned":True,"independent":False,"boot_id":admitted["boot_id"],"bindings":bindings}

def load_placement_proof(proof, log_sha, owner):
    """Post-load mechanical admission only; no prior CPU embedding or peak inference."""
    require(type(proof) is dict and proof.get("actual") is True, "Actual post-load placement evidence missing")
    require(proof.get("native_owner") == owner and proof.get("native_log_sha256") == log_sha, "Placement owner/log differs")
    require(proof.get("input_tensor") == {"name": "token_embd.weight", "backend": "CPU", "bytes": 417177600}, "Exact actual CPU input embedding required")
    for key, value in {"active_tensor_count":851,"cuda_tensor_count":850,"trunk_layers":64,"skipped_mtp_tensor_count":15}.items():
        require(type(proof.get(key)) is int and proof[key] == value, "Actual placement geometry differs: " + key)
    require(proof.get("all_trunk_output_cache_state_cuda0") is True and proof.get("mtp_enabled") is False and proof.get("tensor_overrides") == [], "Actual CUDA trunk/output/cache/state or MTP placement differs")
    require(type(proof.get("source_pins")) is dict and proof["source_pins"], "Raw placement witness bindings missing")
    return True

def diagnostic_environment(packet):
    expected = {"GGML_CUDA_CUBLAS_COMPUTE_TYPE": "f32", "TINYCUBLAS_TC": "0"}
    require(packet.get("diagnostic_environment") == expected, "Exact diagnostic scalar-F32 environment required")
    return expected.copy()

def start_once(service, renderer, admitted, argv, config, pins, stale_faults, activation_sha, dynamic_sha, persist=private_write, clock=time.monotonic, sleep=time.sleep):
    result = {"version": VERSION, "mode":"EXPERIMENT_ONLY", "passed":False, "transport_start_attempts":0,"native_start_attempts":0,"automatic_retry":False,"production_ready":False,"full_qualification":False,"candidate_numerics_verified":False,"actual_peak_verified":False,"actual_placement_verified":False,"coding_verified":False,"standard_research_verified":False,"errors":[],"boot_id":admitted["boot_id"]}
    started = clock()
    qualified = {"model_sha256":renderer.MODEL_SHA,"build":{"binary_sha256":admitted["binary_sha256"]}}
    try:
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        require(resource.getrlimit(resource.RLIMIT_CORE)==(0,0),"Diagnostic core limit differs")
        require(shutil.disk_usage(RUNTIME).free>=2*1024**3,"Bounded diagnostic disk floor unavailable")
        result["diagnostic_RLIMIT_CORE"]=[0,0]
        recheck_cold(service, admitted, pins, renderer, stale_faults, config)
        unchanged_pins = pin_identities(pins, renderer)
        persist(RUNTIME / "ACTIVATION-CONSUMED.json", {"activation_sha256":activation_sha,"dynamic_authority_sha256":dynamic_sha,"boot_id":admitted["boot_id"],"one_native_start_only":True})
        with service.exclusive_owner() as (descriptor, owner_lock):
            recheck_cold(service, admitted, pins, renderer, stale_faults, config)
            result["transport_start_attempts"] = 1
            driver = service.ensure_driver(config, admitted["boot_id"])
            result["driver"] = driver
            result["driver_birth_uid_command"] = birth_uid(driver["pid"])
            service.verify_driver_identity(config, admitted["boot_id"], driver)
            witness = service.new_witness_configuration(qualified, admitted["boot_id"])
            service.verify_witness_configuration(witness, qualified, admitted["boot_id"])
            env = service.native_environment(witness, descriptor, config["socket"])
            env.update(LLMSX_MEMORY_SNAPSHOT="1",LLMSX_27B_CAPACITY_GUARD="1")
            env.update(diagnostic_environment(config))
            require("LLMSX_PRECISION_CAPTURE_DIR" not in os.environ and "LLMSX_PRECISION_CAPTURE_DIR" not in env,"Capture environment key must be absent for production mode")
            result["capture_scheduler_arm"] = False
            result["capture_environment_absent"] = True
            result["diagnostic_environment"] = diagnostic_environment(config)
            result["witness"], result["owner_lock"] = witness, owner_lock
            verify_runtime_library_aliases(config)
            result["native_start_attempts"] = 1
            pid = service.launch_runtime(argv, env, RUNTIME / "native.log", descriptor, boot_id=admitted["boot_id"],model_sha256=renderer.MODEL_SHA,binary_sha256=admitted["binary_sha256"],owner_lock=owner_lock,driver=driver,witness=witness)
            require(type(pid) is int and pid > 0, "Invalid new native PID")
            result["native_pid"], result["native_argv"] = pid, argv
            result["native_birth_uid_command"] = birth_uid(pid)
        deadline = clock() + 600
        while True:
            verify_pin_identities(pins, renderer, unchanged_pins)
            renderer.verify_pins(stale_faults)
            require(birth_uid(pid)==result["native_birth_uid_command"] and birth_uid(driver["pid"])==result["driver_birth_uid_command"],"Retained owner birth/UID/command changed")
            require(service.common.boot_identifier() == admitted["boot_id"], "Boot changed during sole startup")
            service.reject_faults(admitted["boot_id"])
            service.reject_other_owners(allowed_pid=pid)
            capture_owner_absence(allowed_pid=pid)
            service.verify_owned_lock(result)
            service.verify_driver_identity(config, admitted["boot_id"], driver)
            service.verify_witness_configuration(witness, qualified, admitted["boot_id"])
            require(service.common.process_matches(pid,shlex.join(argv),exact=True), "Sole native exited or command changed; no retry")
            if service.require_listener(8000,pid,pending=True):
                data=readiness_metadata(deadline,clock=clock)
                if data is not None:
                    require(type(data) is dict, "Model readiness metadata is malformed")
                    items=data.get("data")
                    if items:
                        require(type(items) is list and all(type(item) is dict for item in items), "Model alias list is malformed")
                        require({item.get("id") for item in items}=={renderer.ALIAS}, "Ready listener serves wrong model alias")
                        result["model_ready_metadata"]=data
                        break
            require(clock() < deadline, "Sole native startup timed out; retained for root inspection")
            sleep(0.2)
        require(birth_uid(pid)==result["native_birth_uid_command"] and birth_uid(driver["pid"])==result["driver_birth_uid_command"],"Owner changed after model readiness metadata")
        require(service.common.boot_identifier()==admitted["boot_id"],"Boot changed after model readiness metadata")
        service.reject_faults(admitted["boot_id"])
        service.reject_other_owners(allowed_pid=pid)
        capture_owner_absence(allowed_pid=pid)
        service.verify_owned_lock(result)
        service.verify_driver_identity(config,admitted["boot_id"],driver)
        service.verify_witness_configuration(witness,qualified,admitted["boot_id"])
        service.require_listener(8000,pid)
        verify_runtime_library_aliases(config)
        raw = read_bound(RUNTIME / "native.log")
        text = raw["data"].decode("utf8", errors="strict")
        stages = renderer.validate_preload_guard_records(text)
        require(stages.get("successful_pre_post_association") is True and stages.get("same_process_preload_guard_association") is True, "Actual pre-load guard/post-load records did not pass")
        result.update(passed=True, listening=True, guard_stages=stages,native_log_sha256=raw["sha256"],actual_placement_verified=False,notice="Loaded bounded experiment only. Actual CPU token_embd/allCUDA trunk/output/cache/state witness, operators, peak and numerical controls must pass before quality. No inference or quality is emitted by this starter.")
    except Exception as error:
        result["errors"].append(type(error).__name__ + ": " + str(error))
        result["passed"] = False
        if result["native_start_attempts"]:
            try:
                result["fault_retention_attempted"]=True
                service.retain_fault(RUNTIME / "native.log", admitted["boot_id"])
                failed_log=read_bound(RUNTIME / "native.log")
                recognized=service.macuda_fault(failed_log["data"].decode("utf8",errors="replace"))
                result["failed_native_log_sha256"]=failed_log["sha256"]
                result["recognized_native_fault"]=recognized
                result["recognized_fault_retention_attempted"]=recognized is not None
            except Exception as retention_error:
                result["fault_retention_error"]=type(retention_error).__name__+": "+str(retention_error)
    finally:
        result["cloud_client_observations"] = dict(CLOUD_PROFILES)
        result["elapsed_seconds"] = clock()-started
        try:
            renderer.verify_pins(pins)
            renderer.verify_pins(stale_faults)
            result["sources_still_match"] = True
        except Exception as error:
            result["sources_still_match"] = False
            result["passed"] = False
            result["errors"].append(type(error).__name__+": "+str(error))
        persist(RUNTIME / "RESULT.json", result)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for item in ("plan-sha256","review","review-sha256","config","config-sha256","admission","admission-sha256","dynamic-authority","dynamic-authority-sha256"):
        parser.add_argument("--"+item, required=True)
    parser.add_argument("--root-activate-once", action="store_true", required=True)
    args = parser.parse_args()
    refuse_overrides(os.environ)
    renderer_bytes = read_bound(RENDERER, "3cedb4efa602242eef405c4c179c372e8be29871f8a50e6a0c9ba45422512157")["data"]
    renderer = types.ModuleType("reviewed27b_renderer")
    renderer.__file__ = str(RENDERER)
    exec(compile(renderer_bytes, str(RENDERER), "exec"), renderer.__dict__)
    plan = renderer.parse_json(renderer.verified_file(str(ROOT/"SOURCE-PLAN.json"),args.plan_sha256,private=True,limit=renderer.JSON_LIMIT)["data"])
    review = renderer.load_proof({"path":args.review,"sha256":args.review_sha256})
    renderer.final_review(review)
    renderer.verify_source_plan({"source_pins":plan["source_pins"]})
    for p,d in {**plan["source_pins"],str(ROOT/"SOURCE-PLAN.json"):args.plan_sha256}.items():
        require(review["source_pins"].get(p) == d,"Independent startup review omitted an exact source")
    renderer.verify_pins(review["source_pins"])
    renderer.guard_subprocess(subprocess, review["source_pins"])
    global CLOUD_CHECKER
    CLOUD_CHECKER = renderer.verified_source_module("reviewed_cloud_client_guard", CLOUD_HELPER, review["source_pins"])
    config_packet = renderer.load_proof({"path":args.config,"sha256":args.config_sha256})
    require(config_packet.get("schema")=="qwen35-27b-root-startup-config-v1", "Exact root startup config required")
    require(config_packet.get("runtime_directory")==str(RUNTIME),"Exact fresh private receiver required")
    stale_faults=config_packet.get("preserved_stale_faults")
    require(type(stale_faults) is dict and stale_faults,"Preserved stale fault hashes required")
    require(all(Path(name)!=Path.home()/".cache/claude-egpu/gpu-fault.json" for name in stale_faults), "Bind immutable stale-fault copies, not the mutable shared pointer")
    for name,digest in stale_faults.items():
        require(review["source_pins"].get(name)==digest,"Static review must bind immutable preserved stale fault copies")
    renderer.verify_pins(stale_faults)
    require(config_packet.get("driver_path")==str(DRIVER) and review["source_pins"].get(str(DRIVER))==config_packet.get("driver_sha256"),"Exact reviewed transport artifact required")
    packet=renderer.load_proof({"path":args.admission,"sha256":args.admission_sha256})
    require(packet.get("schema")=="qwen35-27b-experimental-admission-packet-v1","Exact admission packet required")
    bindings=packet.get("bindings",{})
    proofs={role:renderer.load_proof(binding) for role,binding in bindings.items()}
    original_plan=renderer.parse_json(renderer.verified_file(str(RENDERER.parent/"SOURCE-PLAN.json"),plan["source_pins"][str(RENDERER.parent/"SOURCE-PLAN.json")],private=True,limit=renderer.JSON_LIMIT)["data"])
    admitted=renderer.experimental_admission(proofs,bindings,original_plan,dt.datetime.now(dt.timezone.utc))
    for role in ("allocation_review","source_review","build_abi","cold_admission"): renderer.verify_pins(proofs[role]["source_pins"])
    require(review["source_pins"].get(args.config)==args.config_sha256,"Independent STATIC review must bind exact static root config")
    authority_binding={"path":args.dynamic_authority,"sha256":args.dynamic_authority_sha256}
    authority=renderer.load_proof(authority_binding)
    authority_bindings={"admission":{"path":args.admission,"sha256":args.admission_sha256},"config":{"path":args.config,"sha256":args.config_sha256},"static_review":{"path":args.review,"sha256":args.review_sha256},"source_plan":{"path":str(ROOT/"SOURCE-PLAN.json"),"sha256":args.plan_sha256}}
    dynamic_authority(authority,authority_bindings,admitted,renderer,dt.datetime.now(dt.timezone.utc))
    model=renderer.verified_file(renderer.MODEL_PATH,renderer.MODEL_SHA,prefix_bytes=16*1024*1024)
    require(model["bytes"]==renderer.MODEL_BYTES,"Incomplete publisher artifact")
    header=renderer.verified_source_module("reviewed27b_header",RENDERER.parent/"header_parser.py",plan["source_pins"])
    inventory=header.parse_header(model["prefix"])
    header.validate_inventory(inventory)
    expected=renderer.parse_json(renderer.verified_file(str(RENDERER.parent/"expected-inventory.json"),plan["source_pins"][str(RENDERER.parent/"expected-inventory.json")],limit=renderer.JSON_LIMIT)["data"])
    require(inventory==expected,"Complete artifact header differs")
    argv=renderer.build_launch_argv(admitted,renderer.MODEL_PATH)
    renderer.fresh_actual(proofs["cold_admission"],dt.datetime.now(dt.timezone.utc))
    renderer.fresh_actual(proofs["root_activation"],dt.datetime.now(dt.timezone.utc))
    authority=renderer.load_proof(authority_binding)
    dynamic_authority(authority,authority_bindings,admitted,renderer,dt.datetime.now(dt.timezone.utc))
    require(not RUNTIME.exists() and not RUNTIME.is_symlink(),"Runtime receiver already exists; no replay")
    os.umask(0o077)
    RUNTIME.mkdir(mode=0o700)
    state=RUNTIME/"state"
    state.mkdir(mode=0o700)
    socket_path=RUNTIME/"driver.sock"
    os.environ.update(EGPU_STATE_DIR=str(state),EGPU_HARNESS_DIR=CANONICAL_HARNESS,EGPU_MAX_CONTEXT="32768",TINY_PORT="8000",PYTHONDONTWRITEBYTECODE="1")
    require(not any(n in sys.modules for n in ("macuda_service","egpu_service","macuda_safe_runtime","macuda_residency","macuda_qwen35")),"Preloaded product module refused")
    service=load_product_modules(renderer, {**plan["source_pins"], **review["source_pins"]})
    for name in ("macuda_service","egpu_service","macuda_safe_runtime","macuda_residency","macuda_qwen35"):
        require(Path(sys.modules[name].__file__).resolve()==SERVICE_DIR/(name+".py"),"Foreign product module refused")
    require(service.common.STATE==state and service.common.ROOT==Path(CANONICAL_HARNESS),"Private state/canonical harness differs")
    require(proofs["build_abi"].get("runtime_library_aliases") == config_packet.get("runtime_library_aliases"), "Build/config runtime library aliases differ")
    config={"driver_binary":DRIVER,"driver_sha256":config_packet["driver_sha256"],"socket":socket_path,"driver_timeout":30,"diagnostic_environment":diagnostic_environment(config_packet),"runtime_library_aliases":config_packet.get("runtime_library_aliases")}
    pins={**plan["source_pins"],**review["source_pins"]}
    result=start_once(service,renderer,admitted,argv,config,pins,stale_faults,bindings["root_activation"]["sha256"],args.dynamic_authority_sha256)
    print(json.dumps(result,indent=2))
    return 0 if result["passed"] else 2

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"version":VERSION,"refused":True,"cloud_client_observations":CLOUD_PROFILES,"error":type(error).__name__+": "+str(error),"production_ready":False,"full_qualification":False}))
        raise SystemExit(2)

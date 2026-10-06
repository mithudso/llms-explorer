#!/opt/homebrew/bin/python3
"""Source-only capture-off successor of reviewed v124; never run a native file."""
from pathlib import Path
import hashlib, json, os, copy

ROOT=Path(__file__).absolute().parent
BASE=ROOT.parent
PROD=ROOT/'production'
OLD=BASE/'qwen36-27b-iq2-static-inputs-v124'
PARTS=('static-inputs','renderer-preparation','startup-preparation','cold-root-operation','capture-response-preparation')
MAP={f'qwen36-27b-iq2-{p}-v124':f'{ROOT.name}/production/{p}' for p in PARTS+('cold-runtime','capture-inference')}

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def text(s):
    for a,b in MAP.items():s=s.replace(a,b)
    return s.replace('guard_v124','guard_v125')

def mapped(v):
    if isinstance(v,dict):return {text(k):mapped(x) for k,x in v.items()}
    if isinstance(v,list):return [mapped(x) for x in v]
    return text(v) if isinstance(v,str) else v

def put(p,v):
    raw=v if isinstance(v,bytes) else (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)

def main():
    assert sha(OLD/'INDEPENDENT-REVIEW.json')=='84fdf276096e24c00651c92a1ffcd082bfec6691dd6278bf7c9a4ac63acbc511'
    assert not PROD.exists()
    PROD.mkdir(mode=0o700)
    for p in PARTS:(PROD/p).mkdir(mode=0o700)
    for part in PARTS:
        old=BASE/f'qwen36-27b-iq2-{part}-v124'; new=PROD/part
        names={'static-inputs':['ROOT-CONFIG.json','ALLOCATION-POLICY.json','BUILD-PROVENANCE.json','BUILD-ABI.json'],
               'renderer-preparation':['experimental_27b.py','header_parser.py','original_parser.py','parse_framed.py','parse_guarded_memory_snapshots.py','expected-inventory.json'],
               'startup-preparation':['start_once.py'],
               'cold-root-operation':['run_actual_cold_once.py'],
               'capture-response-preparation':['guard_v124.py']}[part]
        for name in names:
            raw=(old/name).read_bytes()
            value=mapped(json.loads(raw)) if name.endswith('.json') else text(raw.decode()).encode()
            if name=='experimental_27b.py':
                value=value.decode().replace("('-v111/' in value or '-v124/' in value)","('-v111/' in value or '-v124/' in value or value.startswith(str(ROOT / 'production') + '/'))").encode()
            if name=='start_once.py':
                value=value.decode()
                a='            env["LLMSX_PRECISION_CAPTURE_DIR"] = str(RUNTIME / "captures")\n            result["capture_directory"] = str(RUNTIME / "captures")\n            result["capture_scheduler_arm"] = True\n'
                b='            require("LLMSX_PRECISION_CAPTURE_DIR" not in os.environ and "LLMSX_PRECISION_CAPTURE_DIR" not in env,"Capture environment key must be absent for production mode")\n            result["capture_scheduler_arm"] = False\n            result["capture_environment_absent"] = True\n'
                assert value.count(a)==1;value=value.replace(a,b)
                a='    (RUNTIME / "captures").mkdir(mode=0o700)\n';assert value.count(a)==1;value=value.replace(a,'')
                value=value.replace(sha(BASE/'qwen36-27b-iq2-renderer-preparation-v124/experimental_27b.py'),sha(PROD/'renderer-preparation/experimental_27b.py'))
                value=value.encode()
            if name=='guard_v124.py':
                value=value.decode()
                a='    require(startup["native_argv"][0] == str(BINARY), "Diagnostic binary path differs")\n'
                assert value.count(a)==1
                value=value.replace(a,a+'    require(startup.get("capture_scheduler_arm") is False and startup.get("capture_environment_absent") is True,"Capture-disabled startup required")\n')
                value=value.encode()
            if name=='run_actual_cold_once.py':
                value=value.decode();a='    os.umask(0o077)\n'
                assert value.count(a)==1
                value=value.replace(a,a+'    require("LLMSX_PRECISION_CAPTURE_DIR" not in os.environ,"Capture environment key must be absent before cold receiver consumption")\n')
                value=value.encode()
            put(new/('guard_v125.py' if name=='guard_v124.py' else name),value)
    # Keep historical build identity; bind only the new runtime source paths.
    abi_path=PROD/'static-inputs/BUILD-ABI.json'
    abi=json.loads(abi_path.read_bytes())
    abi['current_host_provenance']['sha256']=sha(PROD/'static-inputs/BUILD-PROVENANCE.json')
    abi['source_pins'][str(PROD/'static-inputs/BUILD-PROVENANCE.json')]=sha(PROD/'static-inputs/BUILD-PROVENANCE.json')
    abi_path.write_text(json.dumps(abi,indent=2,sort_keys=True)+'\n');abi_path.chmod(0o600)
    for part in ('renderer-preparation','startup-preparation'):
        plan=mapped(json.loads((BASE/f'qwen36-27b-iq2-{part}-v124/SOURCE-PLAN.json').read_bytes()))
        plan['version']='1.2.2';plan['task']='TASK-620'
        plan['delta']='Capture-off production startup, fresh nested private receivers; identical native binary and resource/numerical controls.'
        for p in plan['source_pins']:plan['source_pins'][p]=sha(p)
        put(PROD/part/'SOURCE-PLAN.json',plan)
    draft=mapped(json.loads((OLD/'INDEPENDENT-REVIEW.json').read_bytes()))
    draft.update(version='1.2.2',passed=False,seal_pending=True,independent_review_pending=True,physical_launch_ready=False,cold_admission_issued=False)
    draft['issuer']='author-source-draft-only';draft.pop('sealed_at',None)
    draft['delta']='Capture-off successor for original native numerical pair then same-owner downstream work. No operation or acceptance.'
    draft['independent_audit']=None
    draft['source_draft']=None
    draft['build_provenance']['sha256']=sha(PROD/'static-inputs/BUILD-PROVENANCE.json')
    # Tests are historical evidence, not newly consumed source inputs.
    draft['source_pins']={p:d for p,d in draft['source_pins'].items() if not (str(PROD) in p and not Path(p).exists())}
    for p in draft['source_pins']:
        if str(PROD) in p:draft['source_pins'][p]=sha(p)
    draft['source_pin_count']=len(draft['source_pins'])
    put(PROD/'static-inputs/REVIEW-DRAFT.json',draft)
    prep=mapped(json.loads((BASE/'qwen36-27b-iq2-capture-response-preparation-v124/PREPARATION.json').read_bytes()))
    prep.update(version='1.0.1',source_review_sha256=None,independent_review_pending=True,seal_pending=True)
    prep['pins']={str(PROD/'capture-response-preparation/guard_v125.py'):sha(PROD/'capture-response-preparation/guard_v125.py')}
    prep['scope']='Exactly two native cache-off64-token requests with immutable current-OS CPU111 reference/all21/EOS/ATOL.05; no raw captures.'
    prep.pop('original_CUDA_responses',None)
    put(PROD/'capture-response-preparation/PREPARATION-DRAFT.json',prep)
    print(json.dumps({'production_source_root':str(PROD),'runtime_receiver_absent':not (PROD/'cold-runtime').exists(),'inference_receiver_absent':not (PROD/'capture-inference').exists(),'root_authorities_created':False,'native_invocations':0},indent=2))

if __name__=='__main__':main()

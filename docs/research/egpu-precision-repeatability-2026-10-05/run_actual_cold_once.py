#!/usr/bin/env python3
"""v1.0.3: one explicitly confirmed, independently reviewed actual cold operation."""
from pathlib import Path
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
import re
import resource
import shutil
import stat
import subprocess
import time
import types

VERSION='1.0.12'
ROOT=Path(__file__).absolute().parent
BASE=Path('/Users/mitch/.cache/claude-egpu/experiments')
STARTER=BASE/'qwen36-27b-iq2-startup-preparation-v110/start_once.py'
PLAN=STARTER.parent/'SOURCE-PLAN.json'
RENDERER=BASE/'qwen36-27b-iq2-renderer-preparation-v110/experimental_27b.py'
STATIC=BASE/'qwen36-27b-iq2-static-inputs-v110'
S=STATIC/'INDEPENDENT-REVIEW.json'
CONFIG=STATIC/'ROOT-CONFIG.json'
RUNTIME=BASE/'qwen36-27b-iq2-cold-runtime-v110'
LOCK=Path('/Users/mitch/.cache/claude-egpu/nv-runtime.lock')
LIVE_PORTS=(8000,14013,14135,14137)
OUTPUTS=('OPERATION-CONSUMED.json','STATIC-VERIFIED.json','ACTUAL-COLD-EVIDENCE.json','COLD-ADMISSION.json','ROOT-ACTIVATION.json','ADMISSION-P.json','ROOT-DYNAMIC-D.json','STARTUP-COMMAND.json','STARTUP-CHILD.json','STARTUP.stdout','STARTUP.stderr','OPERATION-RESULT.json','MEMORY.md','SHA256-MANIFEST.json','SEAL.json')
STARTER_TIMEOUT=750
CHILD_BOOTSTRAP="import sys; data=sys.stdin.buffer.read(); sys.argv=sys.argv[1:]; exec(compile(data,sys.argv[0],'exec'),{'__name__':'__main__','__file__':sys.argv[0],'__package__':None,'__spec__':None})"

CLOUD_CHECKER=None
CLOUD_PROFILES={}
CLOUD_HELPER=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-client-guard-v104/cloud_client_guard.py')

class Refusal(RuntimeError):pass

def require(value,message):
    if not value:raise Refusal(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()

def put(name,value):
    path=ROOT/name
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as out:json.dump(value,out,indent=2,sort_keys=True);out.write('\n')
    return path

def bound(path):return {'path':str(path),'sha256':sha(path)}

def verified_bytes(path,expected):
    require(type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected),'Exact lowercase static review SHA required')
    require(path.is_absolute() and path.resolve(strict=True)==path,'Canonical nonsymlink input required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and stat.S_IMODE(before.st_mode)==0o600,'Private owned regular review required')
        require(0<before.st_size<=16*1024**2,'Bounded nonempty review required')
        data=stream.read(16*1024**2+1);after=os.fstat(stream.fileno())
    fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    require(fields(before)==fields(after)==fields(path.lstat()),'Review changed during read')
    require(hashlib.sha256(data).hexdigest()==expected,'Independent review hash differs')
    return data

def initial_read(path,expected):
    value=parse_json_object(verified_bytes(path,expected))
    return value

def parse_json_object(data):
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'Duplicate review JSON key refused')
            result[key]=value
        return result
    def constant(_value):raise Refusal('Nonfinite review JSON refused')
    try:value=json.loads(data,object_pairs_hook=unique,parse_constant=constant)
    except (ValueError,RecursionError) as error:raise Refusal('Invalid independent review JSON') from error
    require(type(value) is dict,'Independent review object required')
    pending=[(value,0)]
    while pending:
        item,depth=pending.pop()
        require(depth<=64,'Excessive review JSON nesting refused')
        if type(item) is float:require(math.isfinite(item),'Nonfinite review number refused')
        elif type(item) is dict:pending.extend((x,depth+1) for x in item.values())
        elif type(item) is list:pending.extend((x,depth+1) for x in item)
    return value

def minimal_final_review(review):
    require(review.get('passed') is True and review.get('seal_pending') is False,'Independent final review has not passed')
    pins=review.get('source_pins')
    require(type(pins) is dict and bool(pins),'Independent reviewed source pins required')
    require(all(type(p) is str and Path(p).is_absolute() and type(d) is str and re.fullmatch('[0-9a-f]{64}',d) for p,d in pins.items()),'Exact reviewed source bindings required')
    return pins

def source_child_command(args):
    return ['/opt/homebrew/bin/python3','-B','-c',CHILD_BOOTSTRAP,str(STARTER),*args]

def wait_child_once(process,starter_bytes):
    try:
        process.communicate(input=starter_bytes,timeout=STARTER_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {'exit_code':None,'parent_wait_timed_out':True,'startup_child_may_be_active':process.poll() is None,'startup_child_pid':process.pid,'automatic_child_kill':False}
    return {'exit_code':process.returncode,'parent_wait_timed_out':False,'startup_child_may_be_active':False,'startup_child_pid':process.pid,'automatic_child_kill':False}

def private_capture(path):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    return os.fdopen(fd,'wb')

def launch_starter_once(argv,env,starter_bytes,result,out,err):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    require(resource.getrlimit(resource.RLIMIT_CORE)==(0,0),'Diagnostic core limit differs')
    require(shutil.disk_usage(ROOT).free>=2*1024**3,'Bounded diagnostic disk floor unavailable')
    result['diagnostic_RLIMIT_CORE']=[0,0]
    process=subprocess.Popen(argv,cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=out,stderr=err)
    result.update(startup_child_pid=process.pid,startup_child_may_be_active=True,automatic_child_kill=False)
    put('STARTUP-CHILD.json',{'pid':process.pid,'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'command':argv,'preserve_on_parent_timeout':True})
    result.update(wait_child_once(process,starter_bytes))

def passive(argv,allow_one=False):
    proc=subprocess.run(argv,text=True,capture_output=True,check=False,timeout=15)
    require(proc.returncode==0 or (allow_one and proc.returncode==1 and not proc.stderr.strip()),'Passive observation failed: '+str(argv))
    return {'argv':argv,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}

def owners(text):
    found=[]
    for row in text.splitlines():
        fields=row.strip().split(None,2)
        if len(fields)!=3 or not fields[0].isdigit() or int(fields[0])==os.getpid():continue
        name=Path(fields[1]).name;command=fields[2]
        native=name.startswith(('llama-server','llama-cli','gpu-server-capture','nv_shim_','tinynv-','tinynv_')) or (name.lower().startswith('python') and re.search(r'(?:^|\s)-m\s+tinygrad\.llm(?:\s|$)',command))
        driver=name=='TinyGPU' and re.search(r'(?:^|\s)server(?:\s|$)',command)
        cloud={}
        if name=='claude':
            cloud=CLOUD_CHECKER.classify(int(fields[0])) if CLOUD_CHECKER else {'cloud_only':False}
            CLOUD_PROFILES[int(fields[0])]=cloud
        worker=(name=='claude' and cloud.get('cloud_only') is not True) or re.search(r'(?:^|/)egpu_research_agent\.py(?:\s|$)|(?:^|/)claude_qwen35\.py(?:\s|$)|(?:^|\s)-m\s+litellm(?:\s|$)',command)
        if native or driver or worker:found.append({'pid':int(fields[0]),'name':name,'native':bool(native),'driver':bool(driver),'worker':bool(worker)})
    return found

def execute(args):
    require(args.cold_recovery_confirmed,'Explicit user-confirmed full host shutdown and enclosure cold recovery required')
    require(os.getuid()==501,'Run as mitch UID501; root refers to agent authority, not sudo')
    require(not (ROOT/'OPERATION-CONSUMED.json').exists() and not (ROOT/'SEAL.json').exists(),'Consumed receiver; no repeat')
    require(not any((ROOT/name).exists() or (ROOT/name).is_symlink() for name in OUTPUTS),'Pre-existing future operation output refuses cold attempt')
    require(not RUNTIME.exists() and not RUNTIME.is_symlink(),'Future runtime must remain absent')
    put('OPERATION-CONSUMED.json',{'version':VERSION,'explicit_cold_confirmation':True,'automatic_retry':False,'at':dt.datetime.now(dt.timezone.utc).isoformat()})
    result={'version':VERSION,'passed':False,'actual_startup_commands':0,'automatic_retry':False,'full_qualification':False,'errors':[]}
    try:
        review=initial_read(S,args.static_review_sha256)
        pins=minimal_final_review(review)
        required=[Path(__file__).absolute(),STARTER,PLAN,RENDERER,CONFIG,STATIC/'BUILD-ABI.json',STATIC/'ALLOCATION-POLICY.json']
        require(all(str(p) in pins for p in required),'Independent review omitted a required operation/source/config/policy')
        renderer_data=verified_bytes(RENDERER,pins[str(RENDERER)])
        r=types.ModuleType('frozen_candidate_renderer');r.__file__=str(RENDERER)
        exec(compile(renderer_data,str(RENDERER),'exec'),r.__dict__)
        r.final_review(review)
        review=r.load_proof({'path':str(S),'sha256':args.static_review_sha256})
        r.verify_pins(review['source_pins'])
        starter_bytes=r.verified_file(str(STARTER),pins[str(STARTER)],private=True,limit=1024*1024)['data']
        global CLOUD_CHECKER
        require(str(CLOUD_HELPER) in pins,'Reviewed cloud classifier missing')
        helper_bytes=verified_bytes(CLOUD_HELPER,pins[str(CLOUD_HELPER)])
        CLOUD_CHECKER=types.ModuleType('reviewed_cloud_client_guard');CLOUD_CHECKER.__file__=str(CLOUD_HELPER)
        exec(compile(helper_bytes,str(CLOUD_HELPER),'exec'),CLOUD_CHECKER.__dict__)
        require(review['source_pins'].get(r.MODEL_PATH)==r.MODEL_SHA,'Reviewed complete model binding missing')
        cfg=r.load_proof(bound(CONFIG));r.verify_pins(cfg['preserved_stale_faults'])
        identity=r.load_proof(bound(STATIC/'BUILD-ABI.json'))['identity']
        require(identity==r.identity(identity.get('binary_sha256')),'New candidate build identity differs')
        r.verify_source_plan(r.load_proof(bound(RENDERER.parent/'SOURCE-PLAN.json')))
        put('STATIC-VERIFIED.json',{'verified_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_review':{'path':str(S),'sha256':args.static_review_sha256},'source_pins':review['source_pins'],'source_plan':bound(PLAN),'config':bound(CONFIG),'fullmodel_verified':True,'all_pins_current':True})
        boot=passive(['/usr/sbin/sysctl','-n','kern.boottime'])
        match=re.search(r'sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)',boot['stdout'])
        bootid=f'{match[1]}:{match[2]}' if match else None
        require(type(bootid) is str and bootid not in r.OLD_BOOTS,'Old or malformed boot cannot admit the candidate')
        require(bootid not in {'1791115301:4730','1791136050:203826','1791188232:752319'},'Boot already used by candidate trial; fresh user-confirmed cold recovery required')
        proc=passive(['/bin/ps','-axo','pid=,comm=,command='])
        found=owners(proc['stdout']);require(not found,'Existing recognized owner or worker')
        evidence={'boot':boot,'owner_observation':{'argv':proc['argv'],'exit_code':proc['exit_code'],'recognized_owners':found,'excluded_default_cloud_clients':CLOUD_PROFILES,'unrelated_command_bytes_not_retained':True},'user_recovery_confirmation':'explicit --cold-recovery-confirmed after user reports full host shutdown and enclosure recovery','root_uid':os.getuid()}
        for port in LIVE_PORTS:
            obs=passive(['/usr/sbin/lsof','-nP',f'-iTCP:{port}','-sTCP:LISTEN','-Fp'],allow_one=True)
            require(not re.search(r'^p\d+',obs['stdout'],re.M),'Existing inference listener')
            evidence[f'listener_{port}']=obs
        fault=Path('/Users/mitch/.cache/claude-egpu/gpu-fault.json')
        if fault.exists():
            marker=r.parse_json(r.verified_file(str(fault),sha(fault),private=True,limit=r.JSON_LIMIT)['data'])
            require(type(marker.get('boot_id')) is str and re.fullmatch(r'\d+:\d+',marker['boot_id']),'Fault marker boot missing')
            require(marker['boot_id']!=bootid,'Current-boot fault latch')
            evidence['fault']={'path':str(fault),'sha256':sha(fault),'boot_id':marker['boot_id'],'current_boot_fault':False,'preserved_original_untouched':True}
        else:evidence['fault']={'path':str(fault),'absent':True,'current_boot_fault':False}
        fd=os.open(LOCK,os.O_RDWR|os.O_NOFOLLOW)
        try:
            info=os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and not info.st_mode&0o077,'Private owned owner lock required')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            require(not owners(passive(['/bin/ps','-axo','pid=,comm=,command='])['stdout']),'Owner appeared during lock observation')
            evidence['owner_lock']={'path':str(LOCK),'device':info.st_dev,'inode':info.st_ino,'exclusive_acquired':True,'released_for_reviewed_starter_shared_lock_reacquisition':True}
        finally:os.close(fd)
        when=dt.datetime.now(dt.timezone.utc).isoformat();evidence['observed_at']=when
        passive_path=put('ACTUAL-COLD-EVIDENCE.json',evidence)
        cold=put('COLD-ADMISSION.json',{'schema':'qwen35-27b-cold-no-owner-admission-v1','identity':identity,'passed':True,'actual':True,'observed_at':when,'boot_id':bootid,'cold_recovery_verified':True,'owners':[],'listeners':[],'fault_clear':True,'exclusive_root_trial_reserved':True,'source_pins':{str(passive_path):sha(passive_path)}})
        bindings={'allocation_policy':bound(STATIC/'ALLOCATION-POLICY.json'),'allocation_review':bound(S),'build_abi':bound(STATIC/'BUILD-ABI.json'),'cold_admission':bound(cold),'source_review':bound(S)}
        activation=put('ROOT-ACTIVATION.json',{'schema':'qwen35-27b-root-activation-v1','identity':identity,'actual':True,'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'root_authorized':True,'mode':'EXPERIMENT_ONLY','boot_id':bootid,'one_native_start_only':True,'automatic_retry':False,'bindings':bindings})
        packet=put('ADMISSION-P.json',{'schema':'qwen35-27b-experimental-admission-packet-v1','bindings':{**bindings,'root_activation':bound(activation)}})
        dynamic=put('ROOT-DYNAMIC-D.json',{'schema':'qwen35-27b-root-dynamic-startup-authority-v1','actual':True,'authority':'root','independent':False,'root_authorized':True,'issuer_uid':os.getuid(),'mode':'EXPERIMENT_ONLY','boot_id':bootid,'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'one_native_start_only':True,'automatic_retry':False,'bindings':{'admission':bound(packet),'config':bound(CONFIG),'static_review':bound(S),'source_plan':bound(PLAN)}})
        argv=source_child_command(['--plan-sha256',sha(PLAN),'--review',str(S),'--review-sha256',args.static_review_sha256,'--config',str(CONFIG),'--config-sha256',sha(CONFIG),'--admission',str(packet),'--admission-sha256',sha(packet),'--dynamic-authority',str(dynamic),'--dynamic-authority-sha256',sha(dynamic),'--root-activate-once'])
        env={'HOME':'/Users/mitch','USER':'mitch','LOGNAME':'mitch','PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','LANG':'en_US.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
        put('STARTUP-COMMAND.json',{'argv':argv,'environment':env,'cwd':str(ROOT),'one_actual_attempt':True,'verified_starter_bytes_sha256':hashlib.sha256(starter_bytes).hexdigest(),'executes_verified_bytes_not_source_path':True,'parent_wait_timeout_seconds':STARTER_TIMEOUT})
        start=time.monotonic();result['actual_startup_commands']=1
        with private_capture(ROOT/'STARTUP.stdout') as out,private_capture(ROOT/'STARTUP.stderr') as err:
            launch_starter_once(argv,env,starter_bytes,result,out,err)
        result.update(elapsed_seconds=time.monotonic()-start,boot_id=bootid,passed=result['exit_code']==0 and result['parent_wait_timed_out'] is False)
        if (RUNTIME/'RESULT.json').is_file():
            actual=r.load_proof(bound(RUNTIME/'RESULT.json'))
            result['actual_runtime_result']=actual
            result['actual_runtime_result_sha256']=sha(RUNTIME/'RESULT.json')
    except Exception as error:
        result['errors'].append(type(error).__name__+': '+str(error))
        terminal(result)
        return 2
    terminal(result)
    return 0 if result['passed'] else 2

def terminal(result):
    put('OPERATION-RESULT.json',result)
    put('MEMORY.md',{'version':VERSION,'delta':'Actual operation terminal; no retries or resets.','outcome':result,'remaining':'First inference/numerical/peak/coding/standard DR all require their own new evidence.'})
    pending={'STARTUP.stdout','STARTUP.stderr'} if result.get('startup_child_may_be_active') is True else set()
    put('SHA256-MANIFEST.json',{'version':VERSION,'parent_terminal':True,'mutable_pending_paths':[str(ROOT/name) for name in sorted(pending)],'files':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(ROOT.iterdir()) if p.is_file() and p.name not in {'SHA256-MANIFEST.json','SEAL.json'}|pending}})
    put('SEAL.json',{'version':VERSION,'manifest':bound(ROOT/'SHA256-MANIFEST.json'),'full_qualification':False})
    print(json.dumps(result,indent=2),flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cold-recovery-confirmed',action='store_true',required=True)
    parser.add_argument('--static-review-sha256',required=True)
    args=parser.parse_args()
    os.umask(0o077)
    return execute(args)

if __name__=='__main__':raise SystemExit(main())

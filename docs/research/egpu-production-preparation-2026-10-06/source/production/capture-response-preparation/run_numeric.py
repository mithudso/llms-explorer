#!/opt/homebrew/bin/python3
"""Two original native numerical requests on capture-disabled c1fb; no lifecycle."""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, os, stat, types, time, urllib.request, urllib.error

ROOT=Path(__file__).absolute().parent
GUARD_SHA='cf92f2f5e2e6b089a228951077afc63b121881951f343556e96d4bd9229a6696'
CPU=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cpu-capture-controls-v111')
CPU_MANIFEST_SHA='c1357b03f9a504d7bddde19b247e1f649cb707c95d6aaa9f4f4c0c5691619a53'

def held_private(path,expected):
    if path.resolve(strict=True)!=path:raise ValueError('Canonical private source required')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno())
        if not stat.S_ISREG(a.st_mode) or a.st_uid!=501 or stat.S_IMODE(a.st_mode)!=0o600 or not 0<a.st_size<=16*1024**2:raise ValueError('Private bounded source metadata differs')
        raw=f.read(16*1024**2+1);b=os.fstat(f.fileno())
    fields=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    if fields(a)!=fields(b) or fields(a)!=fields(path.lstat()) or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Source changed during held read')
    return raw

def load_guard():
    path=ROOT/'guard_v125.py';raw=held_private(path,GUARD_SHA)
    m=types.ModuleType('held_production_numeric_guard');m.__file__=str(path)
    exec(compile(raw,str(path),'exec'),m.__dict__)
    return m

def exchange(path,data=None):
    g.require(path in ('/health','/slots','/v1/models','/v1/chat/completions','/apply-template','/tokenize'),'Endpoint outside bounded diagnostic')
    deadline=time.monotonic()+(600 if path=='/v1/chat/completions' else 10)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),g.NoRedirect())
    req=urllib.request.Request('http://127.0.0.1:8000'+path,data=data,headers={'Content-Type':'application/json'})
    def bounded_body(response):
        chunks=[];size=0
        while response.fp is not None:
            remaining=deadline-time.monotonic();g.require(remaining>0,'Absolute HTTP deadline exceeded')
            response.fp.raw._sock.settimeout(remaining)
            chunk=response.read1(min(65536,8*1024**2+1-size));size+=len(chunk)
            if size>8*1024**2:
                raise g.HTTPFailure(response.status,b''.join(chunks)+chunk[:8*1024**2-(size-len(chunk))],{},True)
            if not chunk:break
            chunks.append(chunk)
        return b''.join(chunks)
    try:
        with opener.open(req,timeout=max(0.001,deadline-time.monotonic())) as response:
            g.require(response.status==200,'Native request unsuccessful')
            return bounded_body(response)
    except urllib.error.HTTPError as error:
        with error:raw=bounded_body(error)
        headers={key:str(error.headers[key])[:512] for key in ('Content-Type','Content-Length') if error.headers.get(key)}
        raise g.HTTPFailure(error.code,raw,headers) from error


def evidence_snapshot(name,startup,save):
    native=g.read(g.RUNTIME/'native.log',limit=64*1024**2,allow_empty=True)
    save(name+'-native.log',native)
    witness_path=Path(startup['witness']['path'])
    g.require(witness_path==g.RUNTIME/'state'/'witness'/(startup['witness']['session']+'.json'),'Witness path differs')
    raw=g.read(witness_path);w=g.parse(raw)
    expected={'pid':startup['native_pid'],'session':startup['witness']['session'],'boot_id':startup['boot_id'],'model_sha256':startup['witness']['model_sha256'],'build_sha256':startup['witness']['build_sha256']}
    g.require(all(w.get(k)==v for k,v in expected.items()) and w.get('physical_device') is True,'Completed witness identity differs')
    for k in ('valid_kernel_stamps','compute_completed','copy_completed','compute_submitted','copy_submitted','publication_sequence'):
        g.require(type(w.get(k)) is int and w[k]>=0,'Witness counter malformed: '+k)
    g.require(w['compute_completed']<=w['compute_submitted'] and w['copy_completed']<=w['copy_submitted'],'Completed witness counter exceeds submitted')
    save(name+'-WITNESS.json',raw)
    save(name+'-EVIDENCE.json',{'observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'native_log_sha256':g.digest(native),'witness_sha256':g.digest(raw),'binding':expected,'completed_operation_counts':{k:w[k] for k in ('valid_kernel_stamps','compute_completed','copy_completed','compute_submitted','copy_submitted','publication_sequence')},'limit':'Cumulative bound physical counters around the exact requests. These are not per-tensor error attribution or peak evidence.'})
    return w

def main(preparation_sha):
    global g
    g=load_guard();g.exchange=exchange;os.umask(0o077)
    prep=g.parse(g.read(ROOT/'PREPARATION.json',preparation_sha))
    g.require(prep.get('seal_pending') is False and prep.get('independent_review_pending') is False,'Final request preparation required')
    g.require(prep['pins'].get(str(Path(__file__).absolute()))==g.digest(g.read(Path(__file__).absolute())),'Numeric helper source differs')
    g.STATIC_SHA=prep['source_review_sha256']
    OUT=g.OUTPUT
    g.require(not OUT.exists() and not OUT.is_symlink(),'Fresh numeric receiver required')
    manifest=g.parse(g.read(CPU/'SHA256-MANIFEST.json',CPU_MANIFEST_SHA))
    def cpu(name):
        p=CPU/name;g.require(str(p) in manifest,'Missing bound CPU input')
        return g.read(p,manifest[str(p)],limit=16*1024**2)
    cpu_result=g.parse(cpu('RESULT.json'))
    g.require(cpu_result['control_complete'] is True and cpu_result['errors']==[],'CPU reference is not accepted')
    startup,cloud,reference,admission=g.verify_admission(preparation_sha)
    g.require(startup.get('capture_scheduler_arm') is False and startup.get('capture_environment_absent') is True,'Capture-off owner required')
    g.require('LLMSX_PRECISION_CAPTURE_DIR' not in os.environ,'Capture environment key must be absent')
    owner=g.owner(startup,cloud)
    def save(name,value):
        raw=value if isinstance(value,bytes) else (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        fd=os.open(OUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw)
    request=cpu('REQUEST.json');g.require(request==reference['REQUEST.json'],'Original request changed')
    parsed=g.parse(request)
    rendered=g.exchange('/apply-template',json.dumps({'messages':parsed['messages'],'chat_template_kwargs':parsed['chat_template_kwargs']}).encode())
    g.require(rendered==cpu('RENDERED.json'),'CPU/native rendered prompt differs')
    tokens=g.exchange('/tokenize',json.dumps({'content':g.parse(rendered)['prompt'],'add_special':True,'parse_special':True}).encode())
    g.require(g.parse(tokens)['tokens']==g.parse(cpu('TOKENIZED.json'))['tokens'],'Original64-token/BOS mapping differs')
    OUT.mkdir(mode=0o700)
    save('CONSUMED.json',{'at':dt.datetime.now(dt.timezone.utc).isoformat(),'maximum_GPU_requests':2,'GPU_starts':0,'resets':0,'automatic_retry':False})
    save('PREPARATION.json',g.read(ROOT/'PREPARATION.json',preparation_sha));save('OWNER-BEFORE.json',owner)
    save('REQUEST.json',request);save('RENDERED.json',rendered);save('TOKENIZED.json',tokens)
    for n,raw in admission.items():save('admission-'+n,raw)
    result={'version':'1.0.0','scope':'Native selected probability original comparison; capture disabled','GPU_requests':0,'GPU_starts':0,'resets':0,'errors':[],'capture_enabled':False,'original_atol':0.05,'full_qualification':False,'actual_peak_verified':False,'coding_verified':False,'standard_dr_verified':False};responses=[]
    try:
        for i in range(2):
            before=g.owner(startup,cloud);save(f'{i}-OWNER-BEFORE.json',before)
            witness_before=evidence_snapshot(f'{i}-BEFORE',startup,save)
            result['GPU_requests']+=1;stamp=time.monotonic()
            raw=g.exchange('/v1/chat/completions',request);save(f'{i}-RESPONSE.json',raw)
            response=g.parse(raw);responses.append(response)
            g.require(response['timings']['cache_n']==0 and response['timings']['prompt_n']==64,'Cached or altered native prompt')
            rows=response['choices'][0]['logprobs']['content']
            g.require(len(rows)==21 and rows[-1]['id']==248046 and rows[-1]['token']=='' and rows[-1]['bytes']==[],'Original all21/finalEOS semantics differ')
            comparison=g.compare_response(g.parse(cpu(f'{i}-RESPONSE.json')),response)
            save(f'{i}-COMPARISON.json',comparison)
            result.setdefault('CPU_CUDA_original_gate',[]).append(comparison)
            result.setdefault('performance',[]).append({'wall_seconds':time.monotonic()-stamp,'timings':response['timings']})
            after=g.owner(startup,cloud);save(f'{i}-OWNER-AFTER.json',after)
            witness_after=evidence_snapshot(f'{i}-AFTER',startup,save)
            fields=('valid_kernel_stamps','compute_completed','copy_completed','publication_sequence')
            g.require(all(witness_after[k]>=witness_before[k] for k in fields),'Physical completion counter regressed')
            g.require(witness_after['valid_kernel_stamps']>witness_before['valid_kernel_stamps'] and witness_after['compute_completed']>witness_before['compute_completed'],'No completed physical compute attributable to uncached response')
            result.setdefault('completed_witness_deltas',[]).append({k:witness_after[k]-witness_before[k] for k in fields})
        result['CUDA_self_comparison']=g.compare_response(*responses)
        result['numerical_passed']=all(x['comparison_passed'] for x in result['CPU_CUDA_original_gate']) and result['CUDA_self_comparison']['comparison_passed']
        result['owner_preserved']=True
    except Exception as e:
        result['errors'].append(type(e).__name__+': '+str(e));result['numerical_passed']=False
        if isinstance(e,g.HTTPFailure):save('HTTP-ERROR-BODY.bin',e.raw)
    finally:
        result['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save('RESULT.json',result)
        save('SHA256-MANIFEST.json',{str(p):g.digest(g.read(p,limit=64*1024**2)) for p in OUT.iterdir() if p.is_file()})
        print(json.dumps(result,indent=2),flush=True)
    return 0 if result['numerical_passed'] and not result['errors'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--preparation-sha256',required=True);a=p.parse_args()
    if not a.execute:raise SystemExit('Explicit root execution required')
    raise SystemExit(main(a.preparation_sha256))

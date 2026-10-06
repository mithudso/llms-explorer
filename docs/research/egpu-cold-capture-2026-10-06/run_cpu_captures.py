#!/usr/bin/env python3
"""Two CPU-only callback controls; no native RTX startup or completion."""
import array
import datetime as dt
import heapq
import json
import math
import os
import resource
import shutil
from pathlib import Path
import subprocess
import time
import urllib.request
import types
import hashlib
import re
import sys
import guard_v111 as guard

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(4*1024**2),b""):h.update(block)
    return h.hexdigest()

def headroom():
    raw=subprocess.check_output(["/usr/bin/vm_stat"],text=True)
    page=int(re.search(r"page size of (\d+) bytes",raw).group(1))
    spare=sum(int(re.search(r"^"+re.escape(k)+r":\s+(\d+)\.",raw,re.M).group(1)) for k in ["Pages free","Pages inactive","Pages speculative"])*page
    assert spare>=15399416320,"Original CPU planning floor unavailable"
    return {"spare_pages_bytes":spare,"required_bytes":15399416320,"compressed_or_swap_counted":False}

repeat=types.SimpleNamespace(sha=sha,headroom=headroom,load_guard=lambda:guard,CPU=Path("/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cpu-reference-v100"))

ROOT=Path(__file__).resolve().parent
OUT=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cpu-capture-controls-v111')
BUILD_ROOT=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-precision-capture-v103')
def save(n,v):
    raw=v if isinstance(v,bytes) else (json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
    with (OUT/n).open('xb') as f:f.write(raw)
def exchange(path,data=None):
    guard=repeat.load_guard()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),guard.NoRedirect())
    req=urllib.request.Request('http://127.0.0.1:14128'+path,data=data,headers={'Content-Type':'application/json'})
    deadline=time.monotonic()+(300 if path=='/v1/chat/completions' else 5)
    with opener.open(req,timeout=max(0.001,deadline-time.monotonic())) as response:
        assert response.status==200
        chunks=[];size=0
        while True:
            remaining=deadline-time.monotonic();assert remaining>0,'Absolute HTTP deadline exceeded'
            if response.fp is None:break
            response.fp.raw._sock.settimeout(remaining)
            chunk=response.read1(min(65536,8*1024**2+1-size));size+=len(chunk)
            assert size<=8*1024**2,'HTTP response bound exceeded'
            if not chunk:break
            chunks.append(chunk)
        return b''.join(chunks)
def cpu_owner(proc,birth=None):
    assert proc.poll() is None
    current=subprocess.check_output(['/bin/ps','-p',str(proc.pid),'-o','lstart=,uid=,command='],text=True).strip()
    if birth is not None:assert current==birth
    listeners=subprocess.check_output(['/usr/sbin/lsof','-nP','-iTCP:14128','-sTCP:LISTEN','-Fp'],text=True).splitlines()
    assert set(s for s in listeners if s.startswith('p'))=={'p'+str(proc.pid)}
    meta=json.loads(exchange('/v1/models'));assert meta['data'][0]['id']=='qwen3.6:27b-iq2-xxs'
    m=meta['data'][0]['meta'];assert m['n_ctx']==32768 and m['n_vocab']==248320 and m['n_embd']==5120 and m['n_params']==27320697856
    slot=json.loads(exchange('/slots'));assert len(slot)==1 and slot[0]['n_ctx']==32768 and not slot[0]['is_processing']
    return {'pid':proc.pid,'birth_uid_command':current,'models':meta,'slots':slot,'listener_records':listeners}
def captures():
    outputs=sorted((OUT/'captures').glob('*-result_output.f32'))
    norms=sorted((OUT/'captures').glob('*-result_norm.f32'))
    assert len(outputs)==len(norms)
    assert [p.name[:4] for p in outputs]==[p.name[:4] for p in norms]
    return len(outputs)
def vector(path,elements):
    raw=path.read_bytes();assert len(raw)==elements*4
    data=array.array('f');data.frombytes(raw);assert len(data)==elements and all(math.isfinite(v) for v in data)
    return data
def summarize(index,token,emitted):
    logits=vector(OUT/'captures'/f'{index:04}-result_output.f32',248320)
    vector(OUT/'captures'/f'{index:04}-result_norm.f32',5120)
    maximum=max(logits);logz=maximum+math.log(math.fsum(math.exp(float(v)-maximum) for v in logits))
    raw_probability=float(logits[token])-logz
    top=heapq.nlargest(2,range(len(logits)),key=lambda i:logits[i])
    return {'pair':index,'selected_token_id':token,'selected_logit':float(logits[token]),'float64_log_normalizer':logz,'selected_logprob_float64':raw_probability,'emitted_logprob':emitted,'absolute_probability_processing_delta':abs(raw_probability-emitted),'argmax_id':top[0],'argmax_matches_selected':top[0]==token,'top_two_margin':float(logits[top[0]])-float(logits[top[1]]),'norm_sha256':repeat.sha(OUT/'captures'/f'{index:04}-result_norm.f32'),'logits_sha256':repeat.sha(OUT/'captures'/f'{index:04}-result_output.f32')}
def main():
    os.umask(0o077);assert not OUT.exists()
    assert sha(BUILD_ROOT/'BUILD-READY.json')=='c9e0e9a555747a2be0e3faad88e5878ed3b4385e4174b718ab5f1e0b42d3da45'
    ready=json.loads((BUILD_ROOT/'BUILD-READY.json').read_bytes());binary=Path(ready['CPU_binary']);assert repeat.sha(binary)==ready['CPU_sha256']=='d9157045bcb70bbc9777035b6e3eeecb55135dbc70291208167df0179a138936'
    preparation=json.loads((ROOT/'CPU-PREPARATION.json').read_bytes())
    for name,expected in preparation['pins'].items():assert sha(Path(name))==expected,name
    assert preparation['maximum_requests']==2 and preparation['GPU_actions']==0
    guard=repeat.load_guard();request=guard.read(repeat.CPU/'REQUEST.json',guard.REFERENCE_PINS['REQUEST.json'])
    guard.verify_large(guard.MODEL,'17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688',9605378560)
    original_manifest=json.loads((BUILD_ROOT/'cpu-capture-controls/SHA256-MANIFEST.json').read_bytes())
    assert sha(BUILD_ROOT/'cpu-capture-controls/SHA256-MANIFEST.json')=='4684d5ad8b6edb8b812e530ad2f93a5866928405c641dc9a34f37437bcfca377'
    for name,expected in original_manifest.items():assert sha(Path(name))==expected,name
    reference={'REQUEST.json':request}
    assert request==(BUILD_ROOT/'cpu-capture-controls/REQUEST.json').read_bytes()
    GPU_owner_before={'GPU_actions':0,'scope':'CPU-only current-OS reference. No GPU owner was initialized or queried.'}
    command_path=repeat.CPU/'COMMAND.json';assert repeat.sha(command_path)=='684b910cf4de56315859a467a9658d485608b750e2657cac0656c12adfc4a3f4'
    memory=repeat.headroom();assert subprocess.run(['/usr/sbin/lsof','-nP','-iTCP:14128','-sTCP:LISTEN','-Fp'],capture_output=True).returncode==1
    assert shutil.disk_usage(ROOT).free>=2*1024**3,'Original disk reserve for this bounded capture is unavailable'
    symbols=subprocess.check_output(['/usr/bin/nm','-g',str(binary)],text=True);deps=subprocess.check_output(['/usr/bin/otool','-L',str(binary)],text=True)
    assert not any(s in symbols or s in deps for s in ['tinynv','tinycudart','ggml_backend_cuda','cudaLaunch','cudaMem','ggml_backend_metal'])
    OUT.mkdir(mode=0o700);(OUT/'captures').mkdir(mode=0o700)
    save('REQUEST.json',request)
    save('MODEL-ADMISSION.json',{'capture_helper_sha256':repeat.sha(Path(__file__).resolve()),'model_stat_after_verified_hash_before_spawn':list((lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns))(guard.MODEL.stat())),'version':'1.0.0','fresh_model_sha256_verified':True,'model_sha256':'17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688','model_bytes':9605378560,'same_retained_GPU_owner_observed_only':GPU_owner_before,'GPU_actions':0})
    argv=json.loads(command_path.read_bytes())['argv'];argv[0]=str(binary);argv[argv.index('--port')+1]='14128'
    save('PREFLIGHT.json',{'at':dt.datetime.now(dt.timezone.utc).isoformat(),'CPU_binary_sha256':repeat.sha(binary),'CPU_only_symbols_and_dependencies':True,'original_command_sha256':repeat.sha(command_path),'original_request_sha256':repeat.sha(repeat.CPU/'REQUEST.json'),'headroom':memory,'capture_limit_bytes':64*(993280+20480+8192),'maximum_single_capture_allocation_bytes':1986560,'capture_scheduler_changed':True,'GPU_actions':0})
    save('COMMAND.json',{'argv':argv,'env_addition':{'LLMSX_PRECISION_CAPTURE_DIR':str(OUT/'captures')},'CPU_starts':1,'request_maximum':2,'no_retry':True})
    save('CONSUMED.json',{'at':dt.datetime.now(dt.timezone.utc).isoformat(),'CPU_starts':1,'GPU_starts':0,'request_maximum':2})
    process=None;result={'version':'1.0.1','CPU_requests':0,'GPU_requests':0,'errors':[],'capture_arm':True,'full_qualification':False};responses=[];ranges=[];summaries=[]
    try:
        env={k:os.environ[k] for k in ['HOME','USER','LOGNAME','PATH','LANG'] if k in os.environ};env['LLMSX_PRECISION_CAPTURE_DIR']=str(OUT/'captures')
        def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        with (OUT/'CPU.log').open('xb') as log: process=subprocess.Popen(argv,stdout=log,stderr=log,env=env,preexec_fn=no_core)
        start=time.monotonic()
        while True:
            assert process.poll() is None,'CPU capture server exited before ready'
            assert time.monotonic()-start<120,'CPU capture load timeout'
            try:
                first_owner=cpu_owner(process);break
            except (OSError,subprocess.CalledProcessError):pass
            time.sleep(0.2)
        save('CPU-OWNER-START.json',first_owner);birth=first_owner['birth_uid_command']
        parsed=json.loads(request)
        rendered=exchange('/apply-template',json.dumps({'messages':parsed['messages'],'chat_template_kwargs':parsed['chat_template_kwargs']}).encode())
        save('RENDERED.json',rendered);prompt=json.loads(rendered)['prompt']
        tokenized=exchange('/tokenize',json.dumps({'content':prompt,'add_special':True,'parse_special':True}).encode())
        save('TOKENIZED.json',tokenized);tokens=json.loads(tokenized)['tokens'];assert len(tokens)==64
        save('TOKEN-BINDING.json',{'version':'1.0.0','tokens':tokens,'token_count':64,'request_sha256':repeat.sha(OUT/'REQUEST.json'),'rendered_response_sha256':repeat.sha(OUT/'RENDERED.json'),'tokenized_response_sha256':repeat.sha(OUT/'TOKENIZED.json'),'tokenize_settings':{'add_special':True,'parse_special':True},'historical_token_array_saved':False,'historical_limit':'Original reference saved request and prompt_n64 but no rendered/token array. This new same-model/template/source CPU reference supplies the exact token/BOS sequence for future CUDA capture comparison.','template_sha256':'e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259','model_sha256':'17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688'})
        for i in range(2):
            save(f'{i}-OWNER-BEFORE.json',cpu_owner(process,birth));begin=captures();samples_before=len(list((OUT/'captures').glob('sample-*.json')));start=time.monotonic();result['CPU_requests']+=1
            raw=exchange('/v1/chat/completions',request);wall=time.monotonic()-start
            save(f'{i}-RESPONSE.json',raw);response=json.loads(raw);responses.append(response)
            assert response['timings']['cache_n']==0 and response['timings']['prompt_n']==64
            end=captures();assert end>begin
            sample_files=sorted((OUT/'captures').glob('sample-*.json'))[samples_before:]
            samples=[json.loads(p.read_bytes()) for p in sample_files]
            assert len(samples)==len(response['choices'][0]['logprobs']['content']),'Per-request sampler count differs from emitted token count'
            pair_ids=[p['pair'] for p in samples]
            assert len(samples)==21 and pair_ids==list(range(begin,end)) and end-begin==21
            assert all(v['sample']==samples_before+n and v['raw_logits_bitwise_match'] is True and v['output_row']==0 and v['pre_sampler'] is True and type(v['batch_token_index']) is int and 0<=v['batch_token_index']<256 for n,v in enumerate(samples))
            last=response['choices'][0]['logprobs']['content'][-1];assert last['id']==248046 and last['token']=='' and last['bytes']==[]
            item={'request_index':i,'before_pair_count':begin,'after_pair_count':end,'first_output_pair':begin,'first_sample_index':samples_before,'extra_sampling_evaluations':'Any capture/sample count beyond emitted content is preserved separately; final EOS sampling is not assumed from count alone.','capture_pair_count':end-begin,'emitted_tokens':len(response['choices'][0]['logprobs']['content']),'wall_seconds':wall,'timings':response['timings'],'mapping':'The first new completed norm/output pair after this request starts supplies its first generated token. Pair count is observed rather than inferred from emitted token count.'};ranges.append(item);save(f'{i}-CAPTURE-RANGE.json',item)
            sample=json.loads((OUT/'captures'/f'sample-{samples_before:04}.json').read_bytes());assert sample['pair']==begin and sample['raw_logits_bitwise_match'] and sample['output_row']==0
            first=response['choices'][0]['logprobs']['content'][0];summaries.append(summarize(sample['pair'],first['id'],first['logprob']))
            save(f'{i}-OWNER-AFTER.json',cpu_owner(process,birth))
        result['request_ranges']=ranges;result['first_token_summaries']=summaries
        result['capture_CPU_self_compare']=guard.compare_response(*responses)
        result['capture_vs_original_CPU']=[guard.compare_response(json.loads((BUILD_ROOT/'cpu-capture-controls'/f'{i}-RESPONSE.json').read_bytes()),response) for i,response in enumerate(responses)]
        result['raw_first_norm_equal']=summaries[0]['norm_sha256']==summaries[1]['norm_sha256'];result['raw_first_logits_equal']=summaries[0]['logits_sha256']==summaries[1]['logits_sha256']
        for f in (OUT/'captures').glob('*.f32'):vector(f,5120 if f.name.endswith('result_norm.f32') else 248320)
        result['capture_total_bytes']=sum(p.stat().st_size for p in (OUT/'captures').iterdir());assert result['capture_total_bytes']<=65404928;result['control_complete']=True
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc));result['control_complete']=False
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=30)
            except subprocess.TimeoutExpired:result['errors'].append('Owned CPU child did not terminate within30seconds; no repeated signal');result['control_complete']=False
        if process:result['CPU_exit_code']=process.returncode
        save('RESULT.json',result);save('SHA256-MANIFEST.json',{str(p):repeat.sha(p) for p in OUT.rglob('*') if p.is_file()})
    print(json.dumps({k:v for k,v in result.items() if k not in ('capture_CPU_self_compare','capture_vs_original_CPU')},indent=2))
    return 0 if result['control_complete'] else 2
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true',required=True);p.parse_args();raise SystemExit(main())

#!/usr/bin/env python3
"""Exactly two newly bound CUDA capture requests after v110 cold admission."""
import array
import argparse
import datetime as dt
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import urllib.request
import urllib.error
import guard_v110 as g

CPU=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-precision-capture-v103/cpu-capture-controls')
CPU_MANIFEST_SHA='4684d5ad8b6edb8b812e530ad2f93a5866928405c641dc9a34f37437bcfca377'
ROOT=Path(__file__).resolve().parent
OUT=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-capture-inference-v110')
CAPTURES=g.RUNTIME/'captures'
CPU_PINS=None

def read_cpu(path):
    g.require(CPU_PINS is not None and str(path) in CPU_PINS,'CPU reference missing from exact manifest')
    return g.read(path,CPU_PINS[str(path)],limit=16*1024**2)

def save(n,v):
    raw=v if isinstance(v,bytes) else (json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
    fd=os.open(OUT/n,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)

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


def vector(path,expected):
    raw=read_cpu(path) if path.is_relative_to(CPU) else g.read(path,limit=993280)
    g.require(len(raw)==expected*4,'Capture vector size differs')
    values=array.array('f');values.frombytes(raw)
    g.require(len(values)==expected and all(math.isfinite(v) for v in values),'Capture vector nonfinite or wrong shape')
    return values

def inventory():
    pairs=sorted(CAPTURES.glob('*-result_output.f32'));norms=sorted(CAPTURES.glob('*-result_norm.f32'))
    g.require([p.name[:4] for p in pairs]==[p.name[:4] for p in norms],'Capture pairs disagree')
    g.require(len(pairs)<=64 and [p.name[:4] for p in pairs]==[f'{i:04}' for i in range(len(pairs))],'Capture pair index range differs')
    samples=sorted(CAPTURES.glob('sample-*.json'))
    g.require(len(samples)<=64 and [p.name for p in samples]==[f'sample-{i:04}.json' for i in range(len(samples))],'Sample index range differs')
    return len(pairs),len(samples)

def evidence_snapshot(name,startup):
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

def analyze(pair,cpu_pair,selected,emitted):
    left=vector(CPU/'captures'/f'{cpu_pair:04}-result_output.f32',248320)
    right=vector(CAPTURES/f'{pair:04}-result_output.f32',248320)
    a=vector(CPU/'captures'/f'{cpu_pair:04}-result_norm.f32',5120)
    b=vector(CAPTURES/f'{pair:04}-result_norm.f32',5120)
    def logsoftmax(values):
        maximum=max(values);z=maximum+math.log(math.fsum(math.exp(float(v)-maximum) for v in values));return float(values[selected])-z,z
    clp,cz=logsoftmax(left);glp,gz=logsoftmax(right)
    differences=sorted(abs(float(x)-float(y)) for x,y in zip(left,right,strict=True))
    analysis_host_bytes=sum(sys.getsizeof(v) for v in (left,right,a,b,differences))+sum(sys.getsizeof(v) for v in differences)
    g.require(analysis_host_bytes<=32*1024**2,'Logical analysis buffers exceed declared bound')
    top=heapq.nlargest(2,range(len(right)),key=lambda i:right[i])
    return {'pair':pair,'CPU_pair':cpu_pair,'selected_token_id':selected,'CPU_selected_raw_logit':float(left[selected]),'CUDA_selected_raw_logit':float(right[selected]),'CPU_float64_log_normalizer':cz,'CUDA_float64_log_normalizer':gz,'CPU_selected_logprob_float64':clp,'CUDA_selected_logprob_float64':glp,'CUDA_emitted_logprob':emitted,'CUDA_probability_processing_delta':abs(glp-emitted),'absolute_shared_normalization_delta':abs(clp-glp),'full_logits_max_abs_error':differences[-1],'full_logits_p50_abs_error':differences[len(differences)//2],'full_logits_p99_abs_error':differences[math.ceil(0.99*len(differences))-1],'normalized_hidden_max_abs_error':max(abs(float(x)-float(y)) for x,y in zip(a,b,strict=True)),'normalized_hidden_bitwise_equal':g.digest(read_cpu(CPU/'captures'/f'{cpu_pair:04}-result_norm.f32'))==g.digest(g.read(CAPTURES/f'{pair:04}-result_norm.f32')),'CUDA_argmax_id':top[0],'CUDA_top_two_margin':float(right[top[0]])-float(right[top[1]]),'analysis_logical_buffers_bytes':analysis_host_bytes,'analysis_host_bound_bytes':32*1024**2,'analysis_bound_excludes_Python_interpreter_and_sort_allocator_overhead':True,'normalization_is_diagnostic_not_true_reference':True}

def main(preparation_sha):
    global CPU_PINS
    os.umask(0o077);g.require(not OUT.exists(),'Fresh capture receiver required')
    prep=g.parse(g.read(ROOT/'PREPARATION.json',preparation_sha));g.STATIC_SHA=prep['source_review_sha256']
    g.exchange=exchange  # All owner metadata exchanges share the absolute HTTP deadline.
    g.require(prep['pins'].get(str(Path(__file__).resolve()))==g.digest(g.read(Path(__file__).resolve())),'Capture helper differs from bound preparation')
    g.require(prep['pins'].get(str(ROOT/'guard_v110.py'))==g.digest(g.read(ROOT/'guard_v110.py')),'Capture guard differs from bound preparation')
    manifest=g.parse(g.read(CPU/'SHA256-MANIFEST.json',CPU_MANIFEST_SHA))
    for path,expected in manifest.items():g.read(Path(path),expected,limit=16*1024**2)
    CPU_PINS=manifest
    cpu_result=g.parse(read_cpu(CPU/'RESULT.json'));g.require(cpu_result['control_complete'] and not cpu_result['errors'],'CPU capture control incomplete')
    startup,cloud,reference,admission_captures=g.verify_admission(preparation_sha)
    owner=g.owner(startup,cloud)
    g.require(startup.get('capture_directory')==str(CAPTURES) and startup.get('capture_scheduler_arm') is True,'New startup did not enable bounded capture')
    g.require(CAPTURES.resolve(strict=True)==CAPTURES and CAPTURES.is_dir() and not CAPTURES.stat().st_mode&0o077,'Private capture receiver differs')
    g.require(shutil.disk_usage(CAPTURES).free>=2*1024**3,'Bounded capture disk floor unavailable')
    parsed=g.parse(reference['REQUEST.json'])
    rendered=exchange('/apply-template',json.dumps({'messages':parsed['messages'],'chat_template_kwargs':parsed['chat_template_kwargs']}).encode())
    g.require(rendered==read_cpu(CPU/'RENDERED.json'),'CUDA rendered prompt differs from exact CPU reference')
    tokens=exchange('/tokenize',json.dumps({'content':g.parse(rendered)['prompt'],'add_special':True,'parse_special':True}).encode())
    g.require(g.parse(tokens)['tokens']==g.parse(read_cpu(CPU/'TOKENIZED.json'))['tokens'],'Exact token/BOS sequence differs')
    OUT.mkdir(mode=0o700)
    save('CONSUMED.json',{'at':dt.datetime.now(dt.timezone.utc).isoformat(),'maximum_GPU_requests':2,'GPU_starts':0,'resets':0,'automatic_retry':False})
    save('OWNER-BEFORE.json',owner);save('RENDERED.json',rendered);save('TOKENIZED.json',tokens);save('REQUEST.json',reference['REQUEST.json'])
    result={'version':'1.0.1','GPU_requests':0,'GPU_starts':0,'resets':0,'errors':[],'full_qualification':False,'actual_peak_verified':False,'original_atol':0.05,'capture_arm':True};responses=[];ranges=[];diagnostics=[]
    try:
        for name,raw in admission_captures.items():save('admission-'+name,raw)
        save('PREPARATION.json',g.read(ROOT/'PREPARATION.json',preparation_sha))
        for i in range(2):
            save(f'{i}-OWNER-BEFORE.json',g.owner(startup,cloud));begin,sample_begin=inventory()
            g.require(shutil.disk_usage(CAPTURES).free>=2*1024**3,'Bounded capture disk floor unavailable')
            witness_before=evidence_snapshot(f'{i}-BEFORE',startup)
            result['GPU_requests']+=1;started=time.monotonic();raw=exchange('/v1/chat/completions',reference['REQUEST.json']);wall=time.monotonic()-started
            save(f'{i}-RESPONSE.json',raw);response=g.parse(raw);responses.append(response)
            g.require(response['timings']['cache_n']==0 and response['timings']['prompt_n']==64,'Cached or changed request')
            end,sample_end=inventory();entries=[g.parse(g.read(CAPTURES/f'sample-{n:04}.json')) for n in range(sample_begin,sample_end)]
            g.require(len(entries)==len(response['choices'][0]['logprobs']['content'])==21,'Sampler/output count differs')
            ids=[e['pair'] for e in entries];g.require(ids==list(range(begin,end)) and end-begin==21,'Sample pair range differs')
            g.require(all(e['sample']==sample_begin+n and type(e['batch_token_index']) is int and 0<=e['batch_token_index']<256 and e['output_row']==0 and e['raw_logits_bitwise_match'] is True and e['pre_sampler'] is True for n,e in enumerate(entries)),'Sampled row not exact captured row')
            g.require(response['choices'][0]['logprobs']['content'][-1]['id']==248046 and response['choices'][0]['logprobs']['content'][-1]['token']=='' and response['choices'][0]['logprobs']['content'][-1]['bytes']==[],'Original final EOS semantics differ')
            item={'request_index':i,'first_pair':begin,'after_pairs':end,'sample_before':sample_begin,'sample_after':sample_end,'wall_seconds':wall,'timings':response['timings']};ranges.append(item);save(f'{i}-CAPTURE-RANGE.json',item)
            first=response['choices'][0]['logprobs']['content'][0]
            diagnostics.append(analyze(begin,cpu_result['request_ranges'][i]['first_output_pair'],first['id'],first['logprob']))
            save(f'{i}-OWNER-AFTER.json',g.owner(startup,cloud))
            witness_after=evidence_snapshot(f'{i}-AFTER',startup)
            g.require(all(witness_after[k]>=witness_before[k] for k in ('valid_kernel_stamps','compute_completed','copy_completed','publication_sequence')),'Completed physical witness counter regressed')
            result.setdefault('completed_witness_deltas',[]).append({k:witness_after[k]-witness_before[k] for k in ('valid_kernel_stamps','compute_completed','copy_completed','publication_sequence')})
        result['request_ranges']=ranges;result['raw_first_token_diagnostics']=diagnostics
        result['CUDA_self_comparison']=g.compare_response(*responses)
        result['CPU_CUDA_original_gate']=[g.compare_response(g.parse(read_cpu(CPU/f'{i}-RESPONSE.json')),response) for i,response in enumerate(responses)]
        result['capture_vs_original_CUDA']=[g.compare_response(g.parse(g.read(Path(prep['original_CUDA_responses'][i]['path']),prep['original_CUDA_responses'][i]['sha256'])),response) for i,response in enumerate(responses)]
        result['raw_CUDA_self']={}
        for kind,elements in (('result_norm',5120),('result_output',248320)):
            paths=[CAPTURES/f"{r['first_pair']:04}-{kind}.f32" for r in ranges]
            values=[vector(p,elements) for p in paths]
            result['raw_CUDA_self'][kind]={'bitwise_equal':g.digest(g.read(paths[0]))==g.digest(g.read(paths[1])),'maximum_absolute_difference':max(abs(float(a)-float(b)) for a,b in zip(*values,strict=True))}
        pair_count,_=inventory()
        for p in range(pair_count):
            for kind,shape,expected,op in (('result_norm',[5120,1,1,1],20480,'GET_ROWS'),('result_output',[248320,1,1,1],993280,'MUL_MAT')):
                metadata=g.parse(g.read(CAPTURES/f'{p:04}-{kind}.json'))
                g.require(metadata['pair']==p and metadata['dtype']=='F32' and metadata['shape']==shape and metadata['bytes']==expected and metadata['op']==op and metadata['finite'] is True and metadata['contiguous'] is True and metadata['pre_sampler'] is True,'Vector metadata differs')
                vector(CAPTURES/f'{p:04}-{kind}.f32',shape[0])
        result['capture_total_bytes']=sum(p.stat().st_size for p in CAPTURES.iterdir());g.require(result['capture_total_bytes']<=65404928,'Capture total exceeds declared bound')
        save('CAPTURE-SHA256-MANIFEST.json',{str(p):g.digest(g.read(p)) for p in CAPTURES.iterdir() if p.is_file()})
        result['diagnostic_complete']=True
    except g.HTTPFailure as exc:
        save('HTTP-ERROR-RESPONSE.json',exc.raw);save('HTTP-ERROR.json',{'status':exc.status,'headers':exc.headers,'truncated':exc.truncated})
        result['errors'].append(str(exc));result['diagnostic_complete']=False
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc));result['diagnostic_complete']=False
    try:save('OWNER-AFTER.json',g.owner(startup,cloud));result['same_owner_retained']=True
    except Exception as exc:result['errors'].append(str(exc));result['same_owner_retained']=False
    try:
        save('TERMINAL-native.log',g.read(g.RUNTIME/'native.log',limit=64*1024**2,allow_empty=True))
        if not (OUT/'CAPTURE-SHA256-MANIFEST.json').exists():save('CAPTURE-SHA256-MANIFEST.json',{str(p):g.digest(g.read(p)) for p in CAPTURES.iterdir() if p.is_file()})
    except Exception as exc:result['errors'].append('Terminal evidence: '+str(exc))
    save('RESULT.json',result);save('SHA256-MANIFEST.json',{str(p):g.digest(g.read(p,allow_empty=True,limit=64*1024**2)) for p in OUT.iterdir() if p.is_file()})
    print(json.dumps(result,indent=2));return 0 if result['diagnostic_complete'] and not result['errors'] else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true',required=True);parser.add_argument('--preparation-sha256',required=True);args=parser.parse_args()
    try:raise SystemExit(main(args.preparation_sha256))
    except Exception as error:
        print(json.dumps({'refused':True,'receiver_exists':OUT.exists(),'full_qualification':False,'error':type(error).__name__+': '+str(error)}));raise SystemExit(2)

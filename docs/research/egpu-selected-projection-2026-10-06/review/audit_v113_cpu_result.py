#!/usr/bin/env python3
"""Inspect one actual bounded CPU graph result; never execute the helper."""
import datetime as dt
import hashlib
import json
import math
import os
import struct
from pathlib import Path
from audit_v112_cpu_source import read, bounded

ROOT=Path(__file__).absolute().parent
PROPOSAL=ROOT.parent/'qwen36-27b-iq2-explicit-cpu-repack-proposal-v113'
OUT=ROOT.parent/'qwen36-27b-iq2-explicit-cpu-repack-control-v113'

def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def bits(v):return struct.unpack('<I',struct.pack('<f',v))[0]

def dequant_q5k(raw):
 """Independent transcription of the canonical 176-byte Q5_K block grammar."""
 assert len(raw)==3520
 values=[]
 for block in range(20):
  q=raw[block*176:(block+1)*176]
  d,dmin=struct.unpack_from('<ee',q);scales=q[4:16];high=q[16:48];low=q[48:176]
  def sm(index):
   if index<4:return scales[index]&63,scales[index+4]&63
   return (scales[index+4]&15)|((scales[index-4]>>6)<<4),(scales[index+4]>>4)|((scales[index]>>6)<<4)
  for group in range(4):
   s1,m1=sm(2*group);s2,m2=sm(2*group+1)
   d1,mn1,d2,mn2=map(f32,(d*s1,dmin*m1,d*s2,dmin*m2))
   for lane in range(32):values.append(f32(f32(d1*((low[group*32+lane]&15)+(16 if high[lane]&(1<<(2*group)) else 0)))-mn1))
   for lane in range(32):values.append(f32(f32(d2*((low[group*32+lane]>>4)+(16 if high[lane]&(2<<(2*group)) else 0)))-mn2))
 assert len(values)==5120 and all(math.isfinite(v) for v in values)
 return values

def compensated_dot(a,b):
 total=correction=0.0
 for x,y in zip(a,b):
  adjusted=x*y-correction;updated=total+adjusted;correction=(updated-total)-adjusted;total=updated
 return total

def main():
 os.umask(0o077);at=dt.datetime.now(dt.timezone.utc).isoformat()
 result_raw,result_sha=read(OUT/'EXECUTION-RESULT.json');result=json.loads(result_raw)
 rows_raw,rows_sha=read(OUT/'GRAPH-RESULT.json');rows=json.loads(rows_raw)
 assert json.loads(read(OUT/'EXECUTE.stdout')[0])==rows
 stderr=read(OUT/'EXECUTE.stderr')[0].decode()
 assert stderr=='repack: repack tensor selected_output_weight_8_rows with q5_K_8x8\n'*3
 command=json.loads(read(PROPOSAL/'CPU-GRAPH-COMMAND.json','806345d88b90f780770bd7285b006157d0660b98bc72dec67e018f14ef307a93')[0])
 freeze=json.loads(read(PROPOSAL/'FREEZE.json','e23b46fdd2f333fa1ffc37f937eba0a0dedba79d4ce722599fc30b1ac7ca4f2e')[0])
 for p,h in freeze['source_pins'].items():read(Path(p),h)
 actual=json.loads(read(OUT/'EXECUTE-COMMAND.json')[0]);assert actual['argv']==command['execute_argv'] and actual['environment']==command['environment'] and actual['removed_environment_keys']==command['inherited_environment_remove'] and actual['timeout_seconds']==30
 build=json.loads(read(OUT/'BUILD-READY.json','5b05ff72464e5e5d57de3a989261e176b2163a72d17522bd67ada42f43d8d717')[0])
 read(Path(build['executable']['path']),build['executable']['sha256'],build['executable']['metadata'])
 consumed=json.loads(read(OUT/'CONSUMED-EXECUTE.json')[0])
 assert consumed['attempts']==1 and consumed['helper_executable_sha256']==build['executable']['sha256']
 assert consumed['command_sha256']=='806345d88b90f780770bd7285b006157d0660b98bc72dec67e018f14ef307a93'
 assert consumed['build_sha256']=='5b05ff72464e5e5d57de3a989261e176b2163a72d17522bd67ada42f43d8d717'
 assert consumed['artifact_review_sha256']==read(ROOT/'CPU-V113-BUILD-REVIEW.json')[1]
 authority=consumed['root_authority'];read(Path(authority['path']),authority['sha256'],authority['metadata'])
 process=json.loads(read(OUT/'EXECUTION-PROCESS.json')[0]);assert process['pid']==result['PID'] and process['CPU_only'] is True
 assert result['attempts']==result['helper_executions']==result['compilation_attempts']==1 and result['exit_code']==0 and result['retries']==0 and result['timed_out'] is False
 assert result['bounded_CPU_graph_calls']==rows['bounded_CPU_graph_calls']==6
 for name in ('GPU_initializations','GPU_requests','resets','model_inference_requests'):assert result[name]==0
 assert result['CPU_oracle_all_selected_bitwise'] is True and result['residual_interpretation_allowed'] is True
 assert rows['CPU_backend'] is True and rows['weight_buffer']=='CPU_REPACK' and rows['actual_trait']==command['required_runtime_trait']
 assert rows['actual_NEON'] is True and rows['actual_i8mm'] is True
 assert (rows['graph_input_columns'],rows['weight_rows'],rows['threads'])==(1,8,8)
 assert rows['graph_arena_bytes']==rows['graph_work_limit_bytes']==1048576 and rows['graph_work_bytes']==6352 and rows['logical_limit_bytes']==33554432
 assert 6352==5120//256*292+64*8
 assert (rows['model_row_bytes_read'],rows['norm_bytes_read'],rows['recorded_logit_bytes_read'])==(84480,40960,24)
 assert rows['CPU_oracle_all_selected_bitwise'] is True and rows['interpret_shared_route_residuals'] is True
 assert [r['token'] for r in rows['rows']]==[4754,90,71093]
 data=command['runtime_data'];norms=[]
 for j in range(2):
  raw=bounded(Path(data[j+1]['path']),data[j+1]['metadata'],0,20480)
  assert hashlib.sha256(raw).hexdigest()==command['norm_sha256'][j]
  norms.append(struct.unpack('<5120f',raw));assert all(math.isfinite(v) for v in norms[-1])
 comparisons=[]
 for row,g in zip(rows['rows'],command['model']['selected_eight_row_groups']):
  assert row['group_start']==g['start'] and row['selected_lane']==g['selected_lane']
  assert all(math.isfinite(v) for v in row.values() if type(v) is float)
  raw=bounded(Path(data[0]['path']),data[0]['metadata'],g['offset'],g['bytes']);assert hashlib.sha256(raw).hexdigest()==g['sha256']
  lane=row['selected_lane'];selected=raw[lane*3520:(lane+1)*3520]
  original=next(s for s in command['model']['selected_rows'] if s['token']==row['token']);assert hashlib.sha256(selected).hexdigest()==original['sha256']
  for j,name in enumerate(('CPU','CUDA')):
   raw=bounded(Path(data[j+3]['path']),data[j+3]['metadata'],row['token']*4,4)
   assert struct.unpack('<f',raw)[0]==row['recorded_'+name+'_logit']
  assert bits(row['explicit_graph_CPU_norm'])==bits(row['recorded_CPU_logit']) and row['CPU_oracle_bits_equal'] is True
  weights=dequant_q5k(selected);math_cpu=compensated_dot(weights,norms[0]);math_gpu=compensated_dot(weights,norms[1])
  assert math_cpu==row['dequantized_F32_dot_CPU_norm_f64'] and math_gpu==row['dequantized_F32_dot_CUDA_norm_f64']
  hidden=row['explicit_graph_CUDA_norm']-row['explicit_graph_CPU_norm']
  output=row['recorded_CUDA_logit']-row['explicit_graph_CUDA_norm']
  total=row['recorded_CUDA_logit']-row['recorded_CPU_logit']
  assert hidden==row['shared_explicit_graph_hidden_contribution'] and output==row['recorded_CUDA_minus_explicit_graph_CUDA_norm'] and hidden+output==total
  comparisons.append({'token':row['token'],'recorded_CPU_bits':bits(row['recorded_CPU_logit']),'graph_CPU_bits':bits(row['explicit_graph_CPU_norm']),'CPU_oracle_bitwise':True,'same_explicit_projection_hidden_delta':hidden,'same_CUDA_norm_projection_residual':output,'recorded_CUDA_minus_CPU_logit':total,'math_dot_CPU_f64':math_cpu,'math_dot_CUDA_f64':math_gpu,'math_dot_delta_f64':math_gpu-math_cpu,'actual_CUDA_minus_math_control_f64':row['recorded_CUDA_logit']-math_gpu})
 source=Path('/Users/mitch/dev/macuda/llama.cpp/ggml/src/ggml-quants.c');_,source_sha=read(source)
 evidence=[{'source':str(OUT/name),'sha256':read(OUT/name)[1],'observed_at':at,'supported_claim':claim} for name,claim in [('EXECUTION-RESULT.json','Exactlyone helper terminal exit0 and six bounded CPU graph calls without retry/GPU actions'),('GRAPH-RESULT.json','Actual runtime features, exact buffer/trait, workspace and allthree selected bitwise oracle'),('EXECUTE.stdout','Exact helper stdout binds graph result'),('EXECUTE.stderr','Three explicit Q5_K8x8 weight group repacks'),('EXECUTE-COMMAND.json','Exact bound argv/environment/sandbox/remove-list and30s timeout'),('CONSUMED-EXECUTE.json','Actual consumed one-execution bindings')]]
 evidence.append({'source':str(source)+':1731','sha256':source_sha,'observed_at':at,'supported_claim':'Primary Q5_K layout/dequant grammar for independent Python F32 decode and compensated float64 dot, not invented historical archive provenance'})
 receipt={'agent':'/root/cold_capture_review','definition_version':'1.0.0','status':'complete','observed_at':at,'actual_helper_terminal_review_complete':True,'CPU_bitwise_oracle_passed':True,'selected_shared_route_arithmetic_verified':True,'residual_interpretation_scope':'Only the three selected logits of sample0/pair1; unique historical operator unproven','evidence':evidence,'changes':['Only designated read-only result script/report'],'remaining':['Full-vocabulary normalization and original0.05 all21 CPU/CUDA gate remains failed','Source-level per-tensor GPU route and proposed fix still unverified','Original physical peak/full coding/stability/standardDR qualification remains unmet'],
 'details':{'surface':'One actual explicit bounded CPU_REPACK graph execution','acceptance_condition':'Exact three selected recorded CPU raw F32 logits reproduced bitwise, exact feature/trait/workspace, independently checked arithmetic','source_revision':'e23b46fdd2f333fa1ffc37f937eba0a0dedba79d4ce722599fc30b1ac7ca4f2e','loaded_revision':build['executable']['sha256'],'process_or_origin':{'PID':result['PID'],'terminal_exit':0,'seconds':result['seconds']},'configuration_identity':command['required_runtime_trait'],'observations':{'selected_rows':comparisons,'graph_workspace_bytes':6352,'graph_calls':6,'one_column':True,'eight_rows':True,'CPU_NEON_i8mm':True,'consumed_record':consumed},'mismatches':[],'unverified_checks':['Selected reproduction does not uniquely identify historical operator','No entire vocabulary normalizer or all21 numerical gate/fix conclusion','No model inference or GPU route modification occurred','Ephemeral0.130s helper loaded-image handles were not sampled independently; binary/source/command/output identity checked after execution','Logical arena/workspace limit is not RSS or physical eGPU peak']},'reviewer_actions':{'helper_reruns':0,'compiles':0,'GPU_actions':0,'model_requests':0,'resets':0},'v112_rejected_oracle':'Unchanged FAIL +3,-1,+2ULP; no v112 residual interpretation','full_qualification':False}
 target=ROOT/'CPU-V113-ORACLE-REVIEW.json'
 with target.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
 print(json.dumps({'review':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'oracle_passed':True,'workspace':6352,'rows':comparisons,'reviewer_reruns':0}))

if __name__=='__main__':main()

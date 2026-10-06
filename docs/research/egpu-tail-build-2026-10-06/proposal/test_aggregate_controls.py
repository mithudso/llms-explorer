#!/usr/bin/env python3
"""Offline source/adversarial model controls; no compiled C++/CUDA evidence."""
from pathlib import Path
import hashlib,json,datetime,threading,concurrent.futures
P=Path(__file__).resolve().parent
LIMIT=2147483648;CTX=268435456
reports=[]
def test(name,fn):
 fn();reports.append(dict(name=name,passed=True))
def require(c):assert c
# This selective directive consumer removes only our added macro blocks. Existing
# directives remain verbatim and nested original directives retain their ordering.
def disabled_source(text):
 out=[];stack=[];active=True
 for line in text.splitlines(True):
  s=line.strip()
  if s.startswith(('#if ','#if\t','#ifdef ','#ifndef ')):
   ours='LLMSX_QWEN36_' in s
   stack.append([active,ours,False])
   if ours:active=False
   elif active:out.append(line)
  elif s.startswith('#else'):
   prev,ours,seen=stack[-1]
   if ours:active=prev and not active;stack[-1][2]=True
   elif active:out.append(line)
  elif s.startswith('#endif'):
   prev,ours,_=stack.pop()
   if not ours and active:out.append(line)
   active=prev
  elif active:out.append(line)
 assert not stack
 return ''.join(out)

a=(P/'ggml-cuda.cu.proposed').read_text();b=(P/'ggml-cuda.cu.before').read_text()
test('macro-off exact original cuda source bytes',lambda:require(disabled_source(a)==b))
m=(P/'mmvq.cu.proposed').read_text();mb=(P/'mmvq.cu.before').read_text()
test('macro-off exact original MMVQ source bytes',lambda:require(disabled_source(m)==mb))
test('common header unchanged exact accepted SHA',lambda:require(hashlib.sha256((P/'common.cuh.UNCHANGED').read_bytes()).hexdigest()=='a210a71f965419ab55cce071b900df118c2520c1566ea5e068d8be07805644a2'))
# Actual source order binds the modeled failed-allocation refusal before the old
# OOM retry block. Full kernel compilation/route acceptance remains pending.
pool=a[a.index('struct ggml_cuda_pool_leg'):a.index('struct ggml_cuda_pool_vmm')]
test('legacy allocation error releases before abort and old sync/retry',lambda:require(pool.index('if (err != cudaSuccess)')<pool.index('llmsx_scratch::release(look_ahead_size)')<pool.index('LLMSX aggregate scratch allocation refused')<pool.index('cudaDeviceSynchronize()')))
test('reserve before actual allocation',lambda:require(pool.index('llmsx_scratch::reserve(look_ahead_size)')<pool.index('ggml_cuda_device_malloc(&ptr')))
test('zero/over-cap guard before cache lookup',lambda:require(pool.index('size == 0 || size > llmsx_scratch::limit')<pool.index('size_t best_diff')))
test('cached free release after successful cudaFree',lambda:require(pool.index('CUDA_CHECK(cudaFree(b.ptr))')<pool.index('llmsx_scratch::release(b.size)')))
test('pool overflow free release after successful cudaFree',lambda:require(pool.index('CUDA_CHECK(cudaFree(ptr))')<pool.index('llmsx_scratch::release(size)')))
ctx=a[a.index('ggml_backend_cuda_context::~ggml_backend_cuda_context'):a.index('// cuda buffer')]
test('context cuBLAS prepaid capacity releases after workspace free loop',lambda:require(ctx.index('cudaFree(cublas_workspaces[i][j])')<ctx.index('llmsx_scratch::release(llmsx_scratch::cublas_per_context)')))
class Refusal(Exception):pass
class Ledger:
 def __init__(self):self.n=0;self.high=0;self.lock=threading.Lock()
 def reserve(self,n):
  with self.lock:
   if n==0 or self.n>LIMIT or n>LIMIT-self.n:raise Refusal()
   self.n+=n;self.high=max(self.high,self.n)
 def release(self,n):
  with self.lock:
   if n==0 or n>self.n:raise Refusal()
   self.n-=n
class Pool:
 def __init__(self,l):self.l=l;self.cached=[];self.checked=[];self.calls=0;self.sync=0;self.evict=0
 def alloc(self,n,fail=False):
  if n<=0 or n>LIMIT:raise Refusal()
  for i,size in enumerate(self.cached):
   if size>=n:self.cached.pop(i);self.checked.append(size);return size
  size=int(1.05*n)
  if size>(1<<64)-1-255:raise Refusal()
  size=256*((size+255)//256);self.l.reserve(size);self.calls+=1
  if fail:self.l.release(size);raise Refusal()
  self.checked.append(size);return size
 def cache(self,size):self.checked.remove(size);self.cached.append(size)
 def free(self,size,success=True):
  if not success:raise Refusal()
  if size in self.cached:self.cached.remove(size)
  else:self.checked.remove(size)
  self.l.release(size)
def refused(fn):
 try:fn()
 except Refusal:return
 raise AssertionError('negative control unexpectedly admitted')
for value in [0,LIMIT+1,(1<<64)-1]:
 test('allocation reject invalid request '+str(value),lambda value=value:refused(lambda:Pool(Ledger()).alloc(value)))
for value in [0,LIMIT+1,(1<<64)-1]:
 test('reservation reject invalid request '+str(value),lambda value=value:refused(lambda:Ledger().reserve(value)))
def reuse():
 l=Ledger();p=Pool(l);size=p.alloc(4096);before=l.n;p.cache(size);require(l.n==before);p.alloc(4096);require(l.n==before and p.calls==1);p.free(size);require(l.n==0)
test('cache/checkout reuse preserves reservation until physical free',reuse)
def oom():
 l=Ledger();p=Pool(l);size=p.alloc(1024);p.cache(size);before=l.n;refused(lambda:p.alloc(4096,True));require(l.n==before and len(p.cached)==1 and p.calls==2 and p.sync==p.evict==0)
test('failed fresh allocation releases exactly once without sync/evict/retry',oom)
def freefail():
 l=Ledger();p=Pool(l);size=p.alloc(1024);refused(lambda:p.free(size,False));require(l.n==size and size in p.checked)
test('failed cudaFree keeps conservative owned reservation',freefail)
def multipl():
 l=Ledger();l.reserve(CTX);pools=[Pool(l) for _ in range(8)];owned=[]
 for p in pools[:5]:owned.append((p,p.alloc(356515840)))
 refused(lambda:pools[5].alloc(356515840));require(l.n<=LIMIT)
 for p,size in owned:p.free(size)
 l.release(CTX);require(l.n==0)
test('eight-pool shared cap refuses accumulated matrices across pools',multipl)
def multictx():
 l=Ledger()
 for _ in range(8):l.reserve(CTX)
 require(l.n==LIMIT);refused(lambda:l.reserve(CTX));refused(lambda:Pool(l).alloc(1))
 for _ in range(8):l.release(CTX)
 require(l.n==0)
test('multiple context prepaid cuBLAS capacity shares original2GiB',multictx)
def underflow():
 l=Ledger();refused(lambda:l.release(1));l.reserve(7);refused(lambda:l.release(8));require(l.n==7);refused(lambda:l.release(0));l.release(7)
test('zero/underflow/double-release rejected without counter wrap',underflow)
def concurrency():
 l=Ledger();barrier=threading.Barrier(16)
 def worker(i):
  barrier.wait()
  try:l.reserve(CTX);return True
  except Refusal:return False
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as x:r=list(x.map(worker,range(16)))
 require(sum(r)==8 and l.n==LIMIT and l.high==LIMIT)
 for ok in r:
  if ok:l.release(CTX)
 require(l.n==0)
test('sixteen concurrent contenders eight admitted no oversubscription model',concurrency)
def stalecas():
 # A source compare_exchange_weak updates expected after a lost race; the next
 # subtraction bound must refuse the second stale contender.
 old=LIMIT-CTX;first=old+CTX;expected_after_failed_CAS=first
 require(CTX>LIMIT-expected_after_failed_CAS)
test('stale CAS contender must re-evaluate latest bound model',stalecas)
# Original Q5_K/all-one-column selectors are preserved; new guard targets only
# the independently reviewed three quant types and2..8columns.
for ty in ['Q2_K','Q4_K','IQ2_XXS','Q5_K','Q6_K','Q8_0']:
 for n in [1,2,4,8,9]:
  predicted_refusal=ty in ['Q2_K','Q4_K','IQ2_XXS'] and 1<n<=8
  test('selector preserved target '+ty+' columns '+str(n),lambda ty=ty,n=n,predicted_refusal=predicted_refusal:require(predicted_refusal==(ty in ['Q2_K','Q4_K','IQ2_XXS'] and n in [2,4,8])))
report=dict(version='1.0.0',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Offline actual source-order/macro-off predicates plus separately labeled adversarial Python arithmetic/concurrency/allocator models; no compiled C++ or GPU correctness evidence.',passed=True,count=len(reports),controls=reports,source_sha256=hashlib.sha256(a.encode()).hexdigest(),ledger_sha256=hashlib.sha256((P/'llmsx_aggregate_scratch.hpp').read_bytes()).hexdigest(),compiles=0,GPU_initializations=0,GPU_requests=0,resets=0)
output=P/'OFFLINE-CONTROLS.json'
with output.open('x') as f:json.dump(report,f,indent=2)
output.chmod(0o600)
print(json.dumps({k:v for k,v in report.items() if k!='controls'},indent=2))

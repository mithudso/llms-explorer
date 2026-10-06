#!/usr/bin/env python3
"""Focused actual consuming guards in tiny owned fixtures; no host/model build."""
from pathlib import Path
import datetime,hashlib,json,os,uuid
P=Path(__file__).resolve().parent
def load(path,raw,name):
 namespace={'__name__':name,'__file__':str(path)};exec(compile(raw,str(path),'exec'),namespace);return namespace
w=load(P/'run_reviewed_host_build_once.py',(P/'run_reviewed_host_build_once.py').read_bytes(),'v120_consumer_control')
source=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-aggregate-scratch-host-proposal-v117');sf=json.loads((source/'FREEZE.json').read_bytes());name=source/'materialize_reviewed_host_inputs.py'
m=load(name,w['private_bytes'](name,'770acb382441fe100591efdaf7ddd8a4cc63d2e82db057948bffe9f6d0dc8a9f',expected_metadata=sf['source_input_metadata'][str(name)]),'held_v117_fixture_validator')
F=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006')/('v120-dependent-fixtures-'+str(uuid.uuid4()));F.mkdir(mode=0o700)
def file(name,data):
 p=F/name;fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(data)
 return p
def record(path):return dict(path=str(path),sha256=w['sha'](path.read_bytes()),metadata=w['metadata'](path.stat()))
reports=[]
def passed(name,fn):assert fn();reports.append(dict(name=name,passed=True))
def refused(name,fn,text):
 try:fn()
 except RuntimeError as error:
  assert text in str(error),(name,str(error));reports.append(dict(name=name,passed=True,actual_refusal=str(error)));return
 raise AssertionError('Actual consumer admitted mismatch: '+name)
a=file('authority.json',b'{"bound":true}\n');r=record(a)
passed('actual private read accepts frozen metadata',lambda:w['private_bytes'](a,r['sha256'],expected_metadata=r['metadata'])==a.read_bytes())
refused('actual private read refuses frozen inode mismatch',lambda:w['private_bytes'](a,r['sha256'],expected_metadata={**r['metadata'],'inode':r['metadata']['inode']+1}),'Frozen private input metadata')
cuda=file('ggml-cuda.cu',b'accepted frozen CUDA source\n');fat=file('ggml-cuda.fatbin',b'accepted historical device payload\n');cr=record(cuda);fr=record(fat)
fake_source=F/'source';frozen={'source_pins':{str(fake_source/'ggml-cuda.cu.proposed'):cr['sha256']}};command={'archive':{'members':{'ggml-cuda.o':{'nv_fatbin_sha256':fr['sha256']}}}};materialization={'members':{'ggml-cuda.o':{'source':cr,'fatbin':fr}}}
passed('generated inputs use immutable expected hashes',lambda:w['generated_inputs'](m,fake_source,F,frozen,command,materialization,'ggml-cuda'))
poison={'members':{'ggml-cuda.o':{'source':{**cr,'sha256':'0'*64},'fatbin':fr}}}
refused('mutable source record hash cannot replace frozen hash',lambda:w['generated_inputs'](m,fake_source,F,frozen,command,poison,'ggml-cuda'),'immutable expected hash')
poison={'members':{'ggml-cuda.o':{'source':cr,'fatbin':{**fr,'sha256':'0'*64}}}}
refused('mutable fatbin record hash cannot replace accepted hash',lambda:w['generated_inputs'](m,fake_source,F,frozen,command,poison,'ggml-cuda'),'immutable expected hash')
cuda.write_bytes(b'changed CUDA source\n');updated={**cr,'metadata':w['metadata'](cuda.stat())};changed={'members':{'ggml-cuda.o':{'source':updated,'fatbin':fr}}}
refused('actual changed generated source refuses content mismatch',lambda:w['generated_inputs'](m,fake_source,F,frozen,command,changed,'ggml-cuda'),'hash/size')
archive=file('accepted-copy.a',b'accepted original archive fixture\n');ar=record(archive)
passed('same descriptor archive consumer accepts fixed identity',lambda:w['bound_archive'](m,archive,ar['sha256'],ar['metadata']))
archive.write_bytes(b'changed copied archive fixture\n')
refused('pre-ar copied archive consumer refuses changed bytes',lambda:w['bound_archive'](m,archive,ar['sha256'],w['metadata'](archive.stat())),'full hash drift')
obj=file('ggml-cuda.o',b'accepted compiled object fixture\n');objr=record(obj);obj.write_bytes(b'changed compiled object fixture\n')
refused('pre-ar built object consumer refuses changed bytes',lambda:w['built_object'](m,{**objr,'metadata':w['metadata'](obj.stat())}),'hash/size')
replacement=file('accepted-replacement.a',b'accepted replacement archive fixture\n');rr=record(replacement);replacement.write_bytes(b'changed replacement archive fixture\n')
refused('before-after-link replacement archive consumer refuses changed bytes',lambda:w['bound_archive'](m,replacement,rr['sha256'],w['metadata'](replacement.stat())),'full hash drift')
report=dict(version='1.0.0',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,count=len(reports),controls=reports,scope='Actual focused private/generated-source/fatbin/copied-archive/built-object/replacement-archive consuming functions in tiny owned fixtures. Main wrapper, materializer main, compiler, ar, linker and GPU were never invoked.',wrapper_sha256=hashlib.sha256((P/'run_reviewed_host_build_once.py').read_bytes()).hexdigest(),fixture_directory=str(F),native_materializations=0,host_compiles=0,links=0,GPU_actions=0)
with (P/'DEPENDENT-CONSUMER-CONTROLS.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
(P/'DEPENDENT-CONSUMER-CONTROLS.json').chmod(0o600)
print(json.dumps(dict(passed=True,count=len(reports),report=str(P/'DEPENDENT-CONSUMER-CONTROLS.json'))))

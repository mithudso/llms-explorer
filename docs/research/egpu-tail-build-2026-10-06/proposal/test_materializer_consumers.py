#!/usr/bin/env python3
"""Actual consuming-function controls in isolated fixtures; never invoke main/GPU."""
from pathlib import Path
import importlib.util,json,hashlib,datetime,os,stat,uuid
P=Path(__file__).resolve().parent
CONTEXT=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006')
F=CONTEXT/('v117-materializer-fixtures-'+str(uuid.uuid4()));F.mkdir(mode=0o700)
spec=importlib.util.spec_from_file_location('v117_materializer_control',P/'materialize_reviewed_host_inputs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
reports=[]
def control(name,fn):fn();reports.append(dict(name=name,passed=True))
def check(x):assert x
def rejected(fn,text=None):
 try:fn()
 except RuntimeError as e:
  if text:check(text in str(e))
  return
 raise AssertionError('Actual consumer admitted refused control')
def file(name,raw,mode=0o600):
 p=F/name;fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode)
 with os.fdopen(fd,'wb') as f:f.write(raw)
 return p
valid=file('authority.json',b'{"exact":true}\n');expected=m.sha(valid.read_bytes());metadata=m.meta(valid.stat())
control('valid private read binds exact bytes and metadata before JSON',lambda:check(m.read_private(valid,expected,metadata)[0]==b'{"exact":true}\n'))
control('hash mismatch refused',lambda:rejected(lambda:m.read_private(valid,'0'*64),'hash'))
wrong=file('world-readable.json',b'{}\n',0o644)
control('private wrong mode refused',lambda:rejected(lambda:m.read_private(wrong,m.sha(wrong.read_bytes())),'UID501/0600'))
control('system owner rejected as private authority',lambda:rejected(lambda:m.read_private('/usr/bin/sandbox-exec','0'*64),'UID501/0600'))
link=F/'private-link.json';link.symlink_to(valid)
control('private symlink refused',lambda:rejected(lambda:m.read_private(link,expected),'Canonical'))
control('frozen metadata wrong owner binding refused',lambda:rejected(lambda:m.read_private(valid,expected,{**metadata,'uid':502}),'Named metadata'))
control('private size limit before read refused',lambda:rejected(lambda:m.read_private(valid,expected,max_bytes=2),'read bound'))
# Deterministic named-file retarget during actual os.read after the descriptor opens.
race=file('race-authority.json',b'{"race":true}\n');raceh=m.sha(race.read_bytes());realread=m.os.read;changed=False
replacement=file('replacement.json',race.read_bytes())
def race_read(fd,n):
 global changed
 raw=realread(fd,n)
 if raw and not changed:changed=True;race.rename(F/'race-original-preserved.json');replacement.rename(race)
 return raw
m.os.read=race_read
try:control('named-file retarget during opened read refused',lambda:rejected(lambda:m.read_private(race,raceh),'Private descriptor changed during read'))
finally:m.os.read=realread
# Actual complete historical20-pin source consumer, no main/materialization.
old=P.parent/'qwen36-27b-iq2-aggregate-scratch-host-proposal-v114/FREEZE.json'
oldraw,_=m.read_private(old,'cdc31fbae309c274ac4c075b60c222b2b6d2436efa0d0efe94188963e684a901');historical=json.loads(oldraw)
control('actual whole historical20-pin private consuming closure',lambda:check(len(m.verified_sources(historical))==20))
# Stage exact held bytes after their source names change: output must retain the
# admitted bytes, never reread the new name/content. Only tiny fixture bytes.
originalP=m.P;m.P=F
try:
 source=file('ggml-cuda.cu.proposed',b'held CUDA source\n');source2=file('mmvq.cu.proposed',b'held MMVQ source\n')
 freeze={'source_pins':{str(p):m.sha(p.read_bytes()) for p in [source,source2]},'source_input_metadata':{str(p):m.meta(p.stat()) for p in [source,source2]}}
 held=m.verified_sources(freeze);source.write_bytes(b'unverified changed source\n');source2.write_bytes(b'unverified changed source2\n')
 out=F/'held-staging';out.mkdir(mode=0o700);record=m.stage_sources(out,held)
 control('actual stage consumes held verified CUDA bytes after path mutation',lambda:check((out/'ggml-cuda.cu').read_bytes()==b'held CUDA source\n'))
 control('actual stage consumes held verified MMVQ bytes after path mutation',lambda:check((out/'mmvq.cu').read_bytes()==b'held MMVQ source\n'))
finally:m.P=originalP
# Tiny same-descriptor archive-copy/extraction fixture, no real archive copying.
raw=b'!<arch>\n'+b'bounded fake archive payload\n';archive=file('fixture.a',raw)
binding=dict(path=str(archive),metadata=m.meta(archive.stat()),sha256=m.sha(raw))
fd=m.open_archive(binding)
try:
 control('same opened archive full content consumer',lambda:check(m.hash_archive(fd,binding)==binding['sha256']))
 control('same descriptor fixture archive copy content and identity',lambda:check(m.copy_same_archive_descriptor(fd,binding,F/'fixture-copy.a')['sha256']==binding['sha256']))
 bad={**binding,'sha256':'0'*64}
 control('fixture archive hash mismatch refused',lambda:rejected(lambda:m.hash_archive(fd,bad),'hash drift'))
 # Replace named source after fd admission; no copy is allowed through the old fd.
 replacement=file('fixture-replacement.a',raw);archive.rename(F/'fixture-original-preserved.a');replacement.rename(archive)
 control('archive named retarget before copy refused',lambda:rejected(lambda:m.copy_same_archive_descriptor(fd,binding,F/'must-not-exist-copy.a'),'Archive descriptor identity drift'))
 check(not (F/'must-not-exist-copy.a').exists())
finally:os.close(fd)
# The archive parser fails malformed bounds before staging a receiver.
p=file('malformed.a',b'!<arch>\nmalformed');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
try:control('bounded malformed archive header refused',lambda:rejected(lambda:m.selected_members(fd,p.stat().st_size,{}),'header malformed'))
finally:os.close(fd)
parserraw,_=m.read_private(P/'macho_archive_identity.py',m.sha((P/'macho_archive_identity.py').read_bytes()));actualparser=m.parser_from_held({str(P/'macho_archive_identity.py'):parserraw})
control('bounded malformed Mach-O refused',lambda:rejected(lambda:m.sections(b'\x00'*32,actualparser),'Mach-O expected'))
# Only tiny owned parser fixtures change; no real frozen source is mutated.
import sys,types
originalP=m.P;m.P=F
fixture_parser=file('macho_archive_identity.py',b'def object_identity(raw): return {"held":True}\ndef public_identity(x): return x\ndef all_member_identities(*args): return "held"\n')
fixture_freeze={'source_pins':{str(fixture_parser):m.sha(fixture_parser.read_bytes())},'source_input_metadata':{str(fixture_parser):m.meta(fixture_parser.stat())}}
try:
 admitted=m.verified_sources(fixture_freeze)
 fixture_parser.write_bytes(b'raise RuntimeError("mutated parser must never execute")\n')
 consumed=m.parser_from_held(admitted)
 control('held parser consumption ignores pathname mutation after verified read',lambda:check(consumed['object_identity'](b'')=={'held':True}))
 poison=types.ModuleType('macho_archive_identity');poison.object_identity=lambda raw:(_ for _ in ()).throw(RuntimeError('poison must never execute'))
 previous=sys.modules.get('macho_archive_identity');sys.modules['macho_archive_identity']=poison
 try:
  consumed=m.parser_from_held(admitted)
  control('held parser consumption ignores poisoned preloaded module',lambda:check(consumed['all_member_identities']()=="held"))
 finally:
  if previous is None:sys.modules.pop('macho_archive_identity')
  else:sys.modules['macho_archive_identity']=previous
finally:m.P=originalP
report=dict(version='1.0.0',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,count=len(reports),controls=reports,scope='Actual v117 private/closure/staging/archive-consuming validators in isolated fixtures, plus complete historical20pin private closure. No real materializer main, actualarchivecopy, compile or GPU action.',fixture_directory=str(F),consumer_sha256=m.sha((P/'materialize_reviewed_host_inputs.py').read_bytes()),compiles=0,native_materializations=0,GPU_initializations=0,GPU_requests=0,resets=0)
with (P/'MATERIALIZER-CONSUMER-CONTROLS.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
(P/'MATERIALIZER-CONSUMER-CONTROLS.json').chmod(0o600)
print(json.dumps({k:v for k,v in report.items() if k!='controls'},indent=2))

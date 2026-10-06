#!/usr/bin/env python3
"""Actual bounded original-object parser negatives; no materialization/GPU."""
from pathlib import Path
import os,json,struct,datetime,hashlib
import materialize_reviewed_host_inputs as m
from macho_archive_identity import object_identity
P=Path(__file__).resolve().parent
c=json.loads((P/'NATIVE-HOST-COMMANDS.json').read_bytes());a=c['archive'];fd=m.open_archive(a)
try: members=m.selected_members(fd,a['metadata']['bytes'],{k:v for k,v in a['members'].items() if k in ('ggml-cuda.o','mmvq.o')});m.recheck_archive(fd,a)
finally:os.close(fd)
results=[]
def refused(name,raw,expected):
 try:object_identity(raw)
 except RuntimeError as e:
  assert expected in str(e),(name,str(e));results.append(dict(name=name,passed=True,actual_refusal=str(e)));return
 raise AssertionError('Actual Mach-O consumer admitted negative: '+name)
for member,raw in members.items():
 identity=object_identity(raw);results.append(dict(name=member+' actual original parser',passed=True))
 wrapper=identity['sections']['__fatbin']['section']
 changed=bytearray(raw);struct.pack_into('<i',changed,wrapper['reloff'],9);refused(member+' wrapper relocation offset retarget',changed,'Wrapper must bind')
 changed=raw.replace(b'___cudaRegisterFunction\0',b'___cudaRegisterFunctioX\0');assert changed!=raw;refused(member+' registration symbol drift',changed,'Each device stub')
 changed=bytearray(raw);struct.pack_into('<I',changed,4,0x1000007);refused(member+' wrong architecture',changed,'architecture')
 # Rename only the actual section header occurrence, never payload strings.
 changed=bytearray(raw);off=32
 for _ in range(struct.unpack_from('<I',raw,16)[0]):
  cmd,n=struct.unpack_from('<II',raw,off)
  if cmd==0x19:
   for i in range(struct.unpack_from('<I',raw,off+64)[0]):
    q=off+72+i*80
    if raw[q:q+16].split(b'\0')[0]==b'__fatbin':changed[q:q+16]=b'__fatbinwrapper\0'
  off+=n
 refused(member+' wrong historical wrapper name',changed,'Exact real Mach-O section missing')
changed=members['mmvq.o'].replace(b'___cuda_register_globals\0',b'___cuda_register_globalX\0');assert changed!=members['mmvq.o'];refused('mmvq helper registration target drift',changed,'Each device stub')
report=dict(version='1.0.0',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,count=len(results),controls=results,scope='Actual consuming Mach-O parser on original selected archive objects and bounded in-memory mutations. No real files or archive were changed. No materializer main/archive copy/compile/GPU action.',parser_sha256=hashlib.sha256((P/'macho_archive_identity.py').read_bytes()).hexdigest(),native_materializations=0,compiles=0,GPU_actions=0)
with (P/'ACTUAL-MACH-O-CONSUMER-CONTROLS.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
(P/'ACTUAL-MACH-O-CONSUMER-CONTROLS.json').chmod(0o600)
print(json.dumps(dict(passed=True,count=len(results),report=str(P/'ACTUAL-MACH-O-CONSUMER-CONTROLS.json'))))

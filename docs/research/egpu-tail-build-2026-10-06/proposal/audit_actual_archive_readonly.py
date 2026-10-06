#!/usr/bin/env python3
"""Consume actual accepted archive read-only before freezing; no receiver/copy."""
from pathlib import Path
import json,hashlib,datetime,os
import materialize_reviewed_host_inputs as m

P=Path(__file__).resolve().parent
raw=(P/'NATIVE-HOST-COMMANDS.json').read_bytes();c=json.loads(raw);parser_raw,_=m.read_private(P/'macho_archive_identity.py',c['identity_parser_sha256']);parser=m.parser_from_held({str(P/'macho_archive_identity.py'):parser_raw});a=c['archive'];ib=c['historical_archive_integrity'];ir,_=m.read_private(ib['path'],ib['sha256'],ib['metadata']);integrity=json.loads(ir);fd=m.open_archive(a)
try:
 full=m.hash_archive(fd,a);all_members=parser['all_member_identities'](fd,a['metadata']['bytes'],integrity['member_hashes']);m.recheck_archive(fd,a)
 selected=m.selected_members(fd,a['metadata']['bytes'],{k:v for k,v in a['members'].items() if k in ['ggml-cuda.o','mmvq.o']});reports={}
 for member,raw in selected.items():
  actual=m.sections(raw,parser);identity=parser['object_identity'](raw);public=parser['public_identity'](identity);binding=a['members'][member]
  assert m.sha(actual['__nv_fatbin'])==binding['nv_fatbin_sha256'] and len(actual['__nv_fatbin'])==binding['nv_fatbin_bytes']
  assert m.sha(actual['__fatbin'])=='8d9b65c40e2717f4078b89ae4b8a508609acf8dcbfa63f29a7db70e81e12d973' and len(actual['__fatbin'])==24
  assert public['wrapper']['relocations'][0]['target']['section']=='__nv_fatbin' and public['wrapper']['relocations'][0]['target']['section_offset']==0
  reports[member]=dict(member_sha256=m.sha(raw),member_bytes=len(raw),actual_materializer_sections_pass=True,registration_identity=public)
 m.recheck_archive(fd,a)
finally:os.close(fd)
assert not Path(c['output_directory']).exists()
report=dict(version='1.0.0',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope='Actual consuming parser/read-only full accepted archive streamhash/all188 identities/bounded selected members, real fatbin/wrapper/normalized relocation/CUDA registration invariants. No receiver creation, archive copy, materializer main, compiler/native/GPU action.',archive=dict(path=a['path'],sha256=full,metadata=a['metadata']),all_member_count=len(all_members),all_member_identities=all_members,selected_members=reports,consumer_sha256=m.sha((P/'materialize_reviewed_host_inputs.py').read_bytes()),identity_parser_sha256=m.sha((P/'macho_archive_identity.py').read_bytes()),same_held_archive_descriptor_for_entire_audit=True,native_materializations=0,compiles=0,GPU_initializations=0,GPU_requests=0,resets=0)
p=P/'ACTUAL-ARCHIVE-CONSUMER-AUDIT.json'
with p.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
p.chmod(0o600)
print(json.dumps(dict(passed=True,all188_member_hashes=True,actual_objects=list(reports),wrapper_name='__fatbin',wrapper_bytes=24,wrapper_relocation_count=1,registration_stub_counts={k:len(v['registration_identity']['stub_symbols']) for k,v in reports.items()},report=str(p),report_bytes=p.stat().st_size,native_materializations=0,compiles=0,GPU_actions=0),indent=2))

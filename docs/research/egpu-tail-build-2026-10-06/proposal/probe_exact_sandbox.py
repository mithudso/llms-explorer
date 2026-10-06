#!/usr/bin/env python3
"""Two authorized tiny file-write probes of the exact future build sandbox."""
from pathlib import Path
import json,os,datetime,hashlib,subprocess,uuid,stat,re
P=Path(__file__).resolve().parent
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path,raw,name):
 namespace={'__name__':name,'__file__':str(path)};exec(compile(raw,str(path),'exec'),namespace);return namespace
mp=P/'materialize_reviewed_host_inputs.py';fd=os.open(mp,os.O_RDONLY|os.O_NOFOLLOW)
with os.fdopen(fd,'rb') as stream:
 before=os.fstat(stream.fileno());raw=stream.read(1024*1024);after=os.fstat(stream.fileno())
assert stat.S_ISREG(before.st_mode) and before.st_uid==501 and stat.S_IMODE(before.st_mode)==0o600
assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)==(mp.stat().st_ino,mp.stat().st_size,mp.stat().st_mtime_ns,mp.stat().st_ctime_ns)
assert sha(raw)=='770acb382441fe100591efdaf7ddd8a4cc63d2e82db057948bffe9f6d0dc8a9f'
m=load(mp,raw,'held_sandbox_probe_private_validator')
c=json.loads((P/'NATIVE-HOST-COMMANDS.json').read_bytes());target=Path(c['output_directory']);sb=P/'deny-live-build.sb';sbr=sb.read_bytes()
expected=('(version 1)\n(allow default)\n(deny network*)\n(deny iokit-open)\n(deny file-write*)\n(allow file-write* (subpath "'+str(target)+'"))\n').encode()
assert sbr==expected and not target.exists() and not target.is_symlink()
correspondence=[]
for command in c['compile_commands']:
 argv=command['argv'];stem=command['stem'];assert argv[0:3]==['/usr/bin/sandbox-exec','-f',str(sb)]
 for flag,suffix in [('-o','.o'),('-MF','.d')]:
  path=Path(argv[argv.index(flag)+1]);assert path==target/(stem+suffix);correspondence.append(str(path))
assert c['archive_replace_argv'][0:3]==['/usr/bin/sandbox-exec','-f',str(sb)] and Path(c['archive_replace_argv'][5])==target/'libggml-cuda-small-prefill-global-scratch.a'
correspondence.append(c['archive_replace_argv'][5]);assert c['link_argv'][0:3]==['/usr/bin/sandbox-exec','-f',str(sb)]
assert Path(c['link_argv'][c['link_argv'].index('-o')+1])==target/'gpu-server-capture-small-prefill-global-scratch'
correspondence.append(str(target/'gpu-server-capture-small-prefill-global-scratch'));assert c['environment']['TMPDIR']==str(target)
renderer=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-renderer-preparation-v111/experimental_27b.py')
rr,_=m['read_private'](renderer,'0903f16dd66ae5dc4ed82d02be30570754f219d16ff7986ff379c7a45788b339');r=load(renderer,rr,'held_sandbox_probe_runtime_tools')
pins=dict(c['reused_current_source_closure']);bindings=dict(c['reused_external_source_bindings'])
for path,binding in c['tools'].items():pins[path]=binding['sha256'];bindings[path]=binding.get('external_binding') or binding.get('external_v111_binding')
r['configure_source_bindings']({'source_pins':pins,'external_source_bindings':bindings})
tools=['/usr/bin/sandbox-exec','/opt/homebrew/bin/python3']
for tool in tools:r['verified_file'](tool,pins[tool])
environment={k:v for k,v in os.environ.items() if k not in c['inherited_environment_remove']};environment.update(c['environment'])
negative_dir=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006')/('v121-sandbox-negative-'+str(uuid.uuid4()))
target.mkdir(mode=0o700);negative_dir.mkdir(mode=0o700);positive=target/'sandbox-probe.txt';negative=negative_dir/'sandbox-probe.txt';payload=b'v121 sandbox probe only\n'
script='import os,sys; fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,b"v121 sandbox probe only\\n"); os.close(fd)'
results=[]
try:
 for label,path in [('positive',positive),('negative',negative)]:
  identities={tool:r['source_identity'](tool,pins[tool]) for tool in tools};argv=['/usr/bin/sandbox-exec','-f',str(sb),'/opt/homebrew/bin/python3','-B','-c',script,str(path)];result=subprocess.run(argv,env=environment,capture_output=True,timeout=30,check=False)
  for tool in tools:assert r['source_identity'](tool,pins[tool])==identities[tool]
  results.append(dict(label=label,argv=argv,exit_code=result.returncode,stdout=result.stdout.decode(),stderr=result.stderr.decode()))
  if label=='positive':assert result.returncode==0 and positive.read_bytes()==payload
  else:assert result.returncode!=0 and not negative.exists() and 'Operation not permitted' in result.stderr.decode()
finally:
 # Delete only the exact tiny owned probe file after checking its identity/content.
 if positive.exists():
  info=positive.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==501 and info.st_size==len(payload) and positive.read_bytes()==payload;positive.unlink()
 assert not negative.exists();target.rmdir();negative_dir.rmdir()
assert not target.exists()
report=dict(version='1.0.0',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,exact_sandbox_sha256=sha(sbr),exact_sandbox_write_subpath=str(target),compiler_object_dependency_archive_link_targets=correspondence,original_network_iokit_filewrite_denials_preserved=True,actual_file_write_probe_count=2,probes=results,owned_tiny_files_cleaned=True,future_build_target_absent=True,native_materializations=0,compiles=0,links=0,GPU_actions=0)
with (P/'EXACT-SANDBOX-PROBES.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
(P/'EXACT-SANDBOX-PROBES.json').chmod(0o600)
print(json.dumps(dict(passed=True,probe_count=2,expected_negative_exit=results[1]['exit_code'],future_build_target_absent=True,report=str(P/'EXACT-SANDBOX-PROBES.json'))))

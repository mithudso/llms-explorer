#!/usr/bin/env python3
"""Exact one-use v117 host build; never invoke a native/model executable."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,resource,shlex,shutil,signal,stat,struct,subprocess,time,types
P=Path(__file__).resolve().parent
BASE=Path('/Users/mitch/.cache/claude-egpu/experiments')
SOURCE=BASE/'qwen36-27b-iq2-aggregate-scratch-host-proposal-v121'
FREEZE_SHA='a906ace38f74ceb26161b1f1e21909a3d0b53785034e30e54d5f79f7aeb0a621'
COMMAND_SHA='875bd8b405a26236c62037106a29c7d126d324b51cf2b53ef69d7ecf1b6ba385'
RENDERER=BASE/'qwen36-27b-iq2-renderer-preparation-v111/experimental_27b.py'
RENDERER_SHA='0903f16dd66ae5dc4ed82d02be30570754f219d16ff7986ff379c7a45788b339'
MATERIALIZER_SHA='770acb382441fe100591efdaf7ddd8a4cc63d2e82db057948bffe9f6d0dc8a9f'
OUT=None
OWNED_RECEIVER=False
def require(value,why):
 if not value:raise RuntimeError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def metadata(s):return dict(uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),bytes=s.st_size,device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
def private_bytes(path,digest,limit=8*1024**2,expected_metadata=None):
 p=Path(path);before=p.lstat();require(p.is_absolute() and p.resolve()==p and stat.S_ISREG(before.st_mode) and before.st_uid==501 and stat.S_IMODE(before.st_mode)==0o600,'Canonical UID501/0600 private authority required')
 if expected_metadata is not None:require(metadata(before)==expected_metadata,'Frozen private input metadata differs')
 require(0<before.st_size<=limit,'Private byte bound');fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  require(metadata(os.fstat(fd))==metadata(before),'Private open identity differs');raw=os.read(fd,limit+1);require(len(raw)==before.st_size and sha(raw)==digest,'Private hash/size differs')
  require(metadata(os.fstat(fd))==metadata(before)==metadata(p.lstat()) and p.resolve()==p,'Private read identity changed');return raw
 finally:os.close(fd)
def loaded_namespace(path,raw,name):
 namespace={'__name__':name,'__file__':str(path)};exec(compile(raw,str(path),'exec'),namespace);return namespace
def save(name,data):
 raw=data if isinstance(data,bytes) else (json.dumps(data,indent=2,allow_nan=False)+'\n').encode();fd=os.open(OUT/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw)
def generated_inputs(m,source,native,source_freeze,command,materialization,stem):
 records=materialization['members'][stem+'.o']
 for label,path,digest in [('source',native/(stem+'.cu'),source_freeze['source_pins'][str(source/(stem+'.cu.proposed'))]),('fatbin',native/(stem+'.fatbin'),command['archive']['members'][stem+'.o']['nv_fatbin_sha256'])]:
  record=records[label];require(record['path']==str(path) and record['sha256']==digest,'Generated '+label+' differs from immutable expected hash/path')
  m['read_private'](path,digest,record['metadata'])
 return True
def bound_archive(m,path,digest,expected_metadata):
 binding=dict(path=str(path),sha256=digest,metadata=expected_metadata);fd=m['open_archive'](binding)
 try:m['hash_archive'](fd,binding)
 finally:os.close(fd)
 return True
def built_object(m,record):
 m['read_private'](record['path'],record['sha256'],record['metadata'],max_bytes=8*1024**2)
 return True
def main():
 global OUT,OWNED_RECEIVER
 args=argparse.ArgumentParser();args.add_argument('--execute-host-build',action='store_true',required=True);args.add_argument('--authority-sha256',required=True);args.add_argument('--preparation-sha256',required=True);args.add_argument('--wrapper-freeze-sha256',required=True);a=args.parse_args()
 os.umask(0o077)
 prep=json.loads(private_bytes(P/'PREPARATION.json',a.preparation_sha256));wf=json.loads(private_bytes(P/'FREEZE.json',a.wrapper_freeze_sha256));authority=json.loads(private_bytes(prep['root_authority_path'],a.authority_sha256))
 require(a.authority_sha256=='317d3be351c9940c729c1f8254aff741ae3a1114f013ac48b61827ccde1c4be6','Exact root issued authority required')
 require(authority['freeze_sha256']==FREEZE_SHA and authority['command_sha256']==COMMAND_SHA and authority['materializer_sha256']==MATERIALIZER_SHA,'Exact v117 authority differs')
 require(authority['materialization_attempts']==1 and authority['host_compile_attempts_per_object']==1 and authority['archive_replacement_attempts']==1 and authority['link_attempts']==1 and authority['retries']==0,'Exact root step bounds differ')
 for path,h in wf['source_pins'].items():private_bytes(path,h,expected_metadata=wf['source_input_metadata'][path])
 review_binding={'path':str(BASE/'qwen36-27b-iq2-cold-capture-independent-review-20261006/OFFLINE-V121-ADMISSION-REVIEW.json'),'sha256':authority['independent_admission_review_sha256']};review_raw=private_bytes(review_binding['path'],review_binding['sha256']);review=json.loads(review_raw)
 sf=json.loads(private_bytes(SOURCE/'FREEZE.json',FREEZE_SHA));command=json.loads(private_bytes(SOURCE/'NATIVE-HOST-COMMANDS.json',COMMAND_SHA))
 m=loaded_namespace(SOURCE/'materialize_reviewed_host_inputs.py',private_bytes(SOURCE/'materialize_reviewed_host_inputs.py',MATERIALIZER_SHA,expected_metadata=sf['source_input_metadata'][str(SOURCE/'materialize_reviewed_host_inputs.py')]),'held_v117_materializer')
 held=m['verified_sources'](sf);parser=m['parser_from_held'](held)
 r=loaded_namespace(RENDERER,private_bytes(RENDERER,RENDERER_SHA),'held_v111_source_validator')
 static=json.loads(private_bytes(command['static_authority']['path'],command['static_authority']['sha256']));r['final_review'](static)
 pins=dict(command['reused_current_source_closure']);bindings=dict(command['reused_external_source_bindings'])
 for path,b in command['tools'].items():
  binding=b.get('external_binding') or b.get('external_v111_binding')
  require(binding is not None,'Exact current tool binding required');pins[path]=b['sha256'];bindings[path]=binding
 r['configure_source_bindings']({'source_pins':pins,'external_source_bindings':bindings})
 owner_review=json.loads(private_bytes(prep['retained_owner_review']['path'],prep['retained_owner_review']['sha256']))
 OUT=Path(prep['execution_directory']);native=Path(command['output_directory']);require(str(native)==prep['native_output_directory'] and native==BASE/'qwen36-27b-iq2-small-prefill-global-scratch-build-v121','Fresh exact native target required')
 require(not OUT.exists() and not OUT.is_symlink() and not native.exists() and not native.is_symlink(),'One-use receiver exists; no retry')
 environment={k:v for k,v in os.environ.items() if k not in command['inherited_environment_remove']};environment.update(command['environment'])
 def tool(path):r['verified_file'](path,pins[path])
 def passive(argv):
  require(argv[0] in ['/bin/ps','/usr/sbin/sysctl','/usr/bin/vm_stat','/usr/bin/otool','/usr/bin/nm'],'Passive command is not allowlisted');tool(argv[0]);before=r['source_identity'](argv[0],pins[argv[0]])
  result=subprocess.run(argv,env=environment,capture_output=True,timeout=30,check=False);require(result.returncode==0 and r['source_identity'](argv[0],pins[argv[0]])==before,'Passive command failed or identity changed');return result
 def retained_owner():
  boot=passive(['/usr/sbin/sysctl','-n','kern.boottime']).stdout.decode();match=re.search(r'sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)',boot);require(match is not None and f'{match[1]}:{match[2]}'==prep['retained_boot_id'],'Retained boot differs')
  for observation in owner_review['process_observations'].values():
   result=passive(observation['argv']);require(result.stdout.decode()==observation['stdout'],'Retained process identity differs')
  sock=owner_review['Unix_socket_identity'];s=Path(sock['path']).lstat();require(stat.S_ISSOCK(s.st_mode) and s.st_dev==sock['device'] and s.st_ino==sock['inode'] and s.st_uid==sock['uid'] and stat.S_IMODE(s.st_mode)==sock['mode'],'Retained socket identity differs')
 def validate(full=False):
  private_bytes(prep['root_authority_path'],a.authority_sha256);m['verified_sources'](sf)
  for path in command['tools']:tool(path)
  sdk=command['sdk'];require(str(Path(sdk['alias']).resolve())==sdk['canonical'] and metadata(Path(sdk['alias']).stat())==sdk['metadata'],'Exact SDK identity differs')
  if full:r['verify_pins'](pins)
  retained_owner();vm=passive(['/usr/bin/vm_stat']).stdout.decode();match=re.search(r'page size of (\d+) bytes',vm);require(match is not None,'Memory page size absent');counts={}
  for label,n in re.findall(r'^(Pages (?:free|inactive|speculative)):\s*(\d+)\.',vm,re.M):counts[label]=int(n)
  require(len(counts)==3,'Memory counters absent');available=sum(counts.values())*int(match[1]);disk=shutil.disk_usage(SOURCE).free
  require(available>=prep['minimum_memory_available_bytes'] and disk>=prep['minimum_disk_free_bytes'],'Original memory/disk floor refused');return {'memory_available_bytes':available,'disk_free_bytes':disk}
 require(prep['retries']==0 and prep['maximum_host_compiles']==2 and prep['maximum_archive_replacements']==1 and prep['maximum_links']==1 and prep['native_executable_invocations']==0,'Exact bounded step counts required')
 admission=validate(full=True);OUT.mkdir(mode=0o700);OWNED_RECEIVER=True
 save('CONSUMED-HOST-BUILD.json',dict(version='1.0.0',observed_at=now(),attempts=1,root_authority_sha256=a.authority_sha256,preparation_sha256=a.preparation_sha256,wrapper_freeze_sha256=a.wrapper_freeze_sha256,source_freeze_sha256=FREEZE_SHA,commands_sha256=COMMAND_SHA,independent_source_review=review_binding,admission=admission,native_executable_invocations=0,GPU_actions=0))
 def child(label,argv,timeout,tools):
  for path in tools:tool(path)
  identities={path:r['source_identity'](path,pins[path]) for path in tools}
  save(label+'-COMMAND.json',dict(argv=argv,environment=command['environment'],removed_environment_keys=command['inherited_environment_remove'],timeout_seconds=timeout,attempts=1))
  def limits():resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_CPU,(timeout,timeout))
  start=time.monotonic();process=subprocess.Popen(argv,cwd=SOURCE if label=='MATERIALIZE' else native,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits);save(label+'-PROCESS.json',dict(observed_at=now(),PID=process.pid,process_group=process.pid))
  timed=False
  try:stdout,stderr=process.communicate(timeout=timeout)
  except subprocess.TimeoutExpired:
   timed=True;os.killpg(process.pid,signal.SIGKILL);stdout,stderr=process.communicate(timeout=10)
  save(label+'.stdout',stdout);save(label+'.stderr',stderr);result=dict(observed_at=now(),PID=process.pid,exit_code=process.returncode,seconds=time.monotonic()-start,timed_out=timed,attempts=1,retries=0,native_executable_invocations=0,GPU_actions=0);save(label+'-RESULT.json',result);print(json.dumps({'terminal_step':label,**result}),flush=True)
  require(process.returncode==0 and not timed,'First failed host step: '+label)
  for path in tools:require(r['source_identity'](path,pins[path])==identities[path],'Tool identity changed during child')
  return result
 materializer=authority['materialize_argv'];require(materializer==['/opt/homebrew/bin/python3','-B',str(SOURCE/'materialize_reviewed_host_inputs.py'),'--materialize-reviewed-host-inputs','--commands-sha256',COMMAND_SHA,'--freeze-sha256',FREEZE_SHA],'Exact admitted materialization argv differs')
 child('MATERIALIZE',materializer,60,['/opt/homebrew/bin/python3'])
 materialization_path=native/'MATERIALIZED-INPUTS.json';materialization_raw=materialization_path.read_bytes();materialization=json.loads(private_bytes(materialization_path,sha(materialization_raw)))
 require(materialization['accepted_original_member_count']==188 and materialization['held_proposed_bytes_consumed'] and materialization['same_archive_descriptor'],'Exact materialization receipt differs')
 archive_binding=materialization['archive'];require(archive_binding['path']==str(native/'libggml-cuda-small-prefill-global-scratch.a') and archive_binding['sha256']==command['archive']['sha256'],'Copied archive differs from immutable original hash/path');bound_archive(m,archive_binding['path'],command['archive']['sha256'],archive_binding['metadata'])
 originals=json.loads(held[str(SOURCE/'ACTUAL-ARCHIVE-CONSUMER-AUDIT.json')])['selected_members'];compiled_objects={};dependency_sets={}
 for compile_command in command['compile_commands']:
  stem=compile_command['stem'];validate(full=True)
  generated_inputs(m,SOURCE,native,sf,command,materialization,stem)
  child('COMPILE-'+stem,compile_command['argv'],120,['/usr/bin/sandbox-exec','/opt/homebrew/opt/llvm/bin/clang++'])
  generated_inputs(m,SOURCE,native,sf,command,materialization,stem)
  obj=native/(stem+'.o');before=obj.lstat();require(before.st_uid==501 and stat.S_ISREG(before.st_mode) and before.st_size<8*1024**2 and obj.resolve()==obj,'Exact bounded ARM64 object required');raw=obj.read_bytes();require(metadata(before)==metadata(obj.lstat()),'Object read changed');actual=parser['public_identity'](parser['object_identity'](raw));expected=originals[stem+'.o']['registration_identity']
  for key in ['architecture','fatbin','wrapper','stub_symbols','cuda_symbols','constructor_relocations','registration_route','registration_call_count']:require(actual[key]==expected[key],'Embedded device identity differs: '+stem+'/'+key)
  require(actual['registration_function']['relocations']==expected['registration_function']['relocations'],'Exact normalized CUDA registration differs')
  compiled_objects[stem+'.o']={'path':str(obj),'sha256':sha(raw),'metadata':metadata(before),'identity':actual}
  depfile=native/(stem+'.d');text=depfile.read_text().replace('\\\n',' ');names=sorted(set(shlex.split(text.split(':',1)[1])));deps=[]
  for name in names:
   p=Path(name);resolved=str(p.resolve());s=p.stat();require(stat.S_ISREG(s.st_mode) and s.st_uid in (0,501) and not s.st_mode&0o022,'Dependency owner/write protection differs')
   if name==str(native/(stem+'.cu')):digest=sf['source_pins'][str(SOURCE/(stem+'.cu.proposed'))];m['read_private'](name,digest,materialization['members'][stem+'.o']['source']['metadata'])
   elif name in pins:record=r['verified_file'](name,pins[name]);digest=pins[name]
   elif name in sf['source_pins']:m['read_private'](name,sf['source_pins'][name],sf['source_input_metadata'][name]);digest=sf['source_pins'][name]
   else:
    fd=os.open(resolved,os.O_RDONLY|os.O_NOFOLLOW);hh=hashlib.sha256()
    try:
     require(metadata(os.fstat(fd))==metadata(s),'Dependency open identity differs')
     while True:
      chunk=os.read(fd,1024*1024)
      if not chunk:break
      hh.update(chunk)
     require(metadata(os.fstat(fd))==metadata(s)==metadata(p.stat()) and str(p.resolve())==resolved,'Dependency changed while hashing')
    finally:os.close(fd)
    digest=hh.hexdigest()
   deps.append(dict(path=name,canonical=resolved,sha256=digest,metadata=metadata(s),already_hash_bound=name in pins or name in sf['source_pins']))
  dependency_sets[stem]=deps;save('COMPILE-'+stem+'-DEPENDENCIES.json',dict(count=len(deps),new_dependency_count=sum(not d['already_hash_bound'] for d in deps),dependencies=deps,independent_review_pending=True))
  save('COMPILE-'+stem+'-OBJECT.json',compiled_objects[stem+'.o'])
 validate(full=True);bound_archive(m,archive_binding['path'],command['archive']['sha256'],archive_binding['metadata'])
 for object_record in compiled_objects.values():built_object(m,object_record)
 child('ARCHIVE-REPLACE',command['archive_replace_argv'],60,['/usr/bin/sandbox-exec','/opt/homebrew/opt/llvm/bin/llvm-ar'])
 archive=native/'libggml-cuda-small-prefill-global-scratch.a';expected=dict(materialization['accepted_original_member_identities']);expected={k:v['sha256'] for k,v in expected.items()};expected.update({k:v['sha256'] for k,v in compiled_objects.items()});s=archive.lstat();fd=os.open(archive,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  require(metadata(os.fstat(fd))==metadata(s),'Replacement archive open identity differs');members=parser['all_member_identities'](fd,s.st_size,expected);hh=hashlib.sha256();offset=0
  while offset<s.st_size:
   raw=os.pread(fd,min(1024*1024,s.st_size-offset),offset);require(raw,'Replacement archive short hash read');hh.update(raw);offset+=len(raw)
  require(metadata(os.fstat(fd))==metadata(s)==metadata(archive.lstat()),'Replacement archive read changed')
 finally:os.close(fd)
 archive_result=dict(path=str(archive),sha256=hh.hexdigest(),metadata=metadata(s),member_count=len(members),unchanged_member_count=186,replaced_members=list(compiled_objects),members=members);save('ARCHIVE-INTEGRITY.json',archive_result)
 validate(full=True);bound_archive(m,archive,archive_result['sha256'],archive_result['metadata'])
 child('LINK',command['link_argv'],120,['/usr/bin/sandbox-exec','/usr/bin/c++','/Library/Developer/CommandLineTools/usr/bin/clang','/Library/Developer/CommandLineTools/usr/bin/ld'])
 bound_archive(m,archive,archive_result['sha256'],archive_result['metadata'])
 exe=native/'gpu-server-capture-small-prefill-global-scratch';s=exe.lstat();require(exe.resolve()==exe and stat.S_ISREG(s.st_mode) and s.st_uid==501 and stat.S_IMODE(s.st_mode)==0o700,'Linked binary owner/mode differs');fd=os.open(exe,os.O_RDONLY|os.O_NOFOLLOW);hh=hashlib.sha256()
 try:
  require(metadata(os.fstat(fd))==metadata(s),'Linked binary open identity differs');prefix=os.pread(fd,32,0);require(struct.unpack_from('<III',prefix)[0:2]==(0xfeedfacf,0x100000c),'Linked ARM64 Mach-O expected')
  while True:
   raw=os.read(fd,1024*1024)
   if not raw:break
   hh.update(raw)
  require(metadata(os.fstat(fd))==metadata(s)==metadata(exe.lstat()),'Linked binary changed while hashing')
 finally:os.close(fd)
 for label,argv in [('HEADER',['/usr/bin/otool','-hv',str(exe)]),('IMPORTS',['/usr/bin/otool','-L',str(exe)]),('SYMBOLS',['/usr/bin/nm','-g',str(exe)])]:
  result=passive(argv);save(label+'.stdout',result.stdout);save(label+'.stderr',result.stderr);save(label+'-COMMAND.json',dict(argv=argv,exit_code=result.returncode,native_executable_invoked=False))
 validate();ready=dict(version='1.0.0',observed_at=now(),host_build_passed=True,materializations=1,host_compiles=2,archive_replacements=1,links=1,retries=0,native_executable_invocations=0,GPU_actions=0,root_authority_sha256=a.authority_sha256,source_freeze_sha256=FREEZE_SHA,commands_sha256=COMMAND_SHA,executable=dict(path=str(exe),sha256=hh.hexdigest(),metadata=metadata(s),architecture='ARM64'),archive=archive_result,compile_dependency_counts={stem:len(records) for stem,records in dependency_sets.items()},independent_artifact_review_pending=True,physical_admission_pending=True,full_qualification=False)
 save('BUILD-READY.json',ready);print(json.dumps({'host_build_passed':True,'build_ready':str(OUT/'BUILD-READY.json'),'executable_sha256':ready['executable']['sha256'],'native_executable_invocations':0,'GPU_actions':0}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception as error:
  result=dict(observed_at=now(),passed=False,error=type(error).__name__+': '+str(error),automatic_retry=False,native_executable_invocations=0,GPU_actions=0)
  if OWNED_RECEIVER and OUT is not None and OUT.exists() and not (OUT/'TERMINAL-REFUSAL.json').exists():save('TERMINAL-REFUSAL.json',result)
  print(json.dumps(result),flush=True);raise SystemExit(2)

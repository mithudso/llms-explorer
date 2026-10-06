#!/usr/bin/env python3
"""Future reviewed bounded host-input extraction/copy; no compile/GPU action."""
from pathlib import Path
import argparse,json,os,hashlib,stat,struct,types
P=Path(__file__).resolve().parent
LIMIT=32*1024*1024
def sha(b):return hashlib.sha256(b).hexdigest()
def meta(s):return dict(uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),bytes=s.st_size,device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
def require(c,why):
 if not c:raise RuntimeError(why)
def named_identity(path,expected,private=False):
 p=Path(path);s=p.lstat()
 require(p.is_absolute() and str(p.resolve())==str(p) and stat.S_ISREG(s.st_mode) and not p.is_symlink(),'Canonical regular nonsymlink required: '+str(p))
 if private:require(s.st_uid==501 and stat.S_IMODE(s.st_mode)==0o600,'Private UID501/0600 required: '+str(p))
 require(meta(s)==expected,'Named metadata differs: '+str(p))
 return s
def read_private(path,expected_sha,expected_metadata=None,max_bytes=8*1024*1024):
 p=Path(path);s=p.lstat();metadata=meta(s)
 named_identity(p,expected_metadata or metadata,True)
 require(0<s.st_size<=max_bytes,'Private input read bound')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  require(meta(os.fstat(fd))==metadata,'Opened private identity differs')
  chunks=[];n=0
  while True:
   raw=os.read(fd,min(1024*1024,max_bytes+1-n))
   if not raw:break
   chunks.append(raw);n+=len(raw);require(n<=max_bytes,'Private input grew beyond bound')
  raw=b''.join(chunks)
  require(n==metadata['bytes'] and sha(raw)==expected_sha,'Private content hash/size differs: '+str(p))
  require(meta(os.fstat(fd))==metadata,'Private descriptor changed during read');named_identity(p,metadata,True)
  return raw,metadata
 finally:os.close(fd)
def verified_sources(freeze):
 held={};total=0
 for name,h in freeze['source_pins'].items():
  require(freeze['source_input_metadata'][name]['bytes']<=4*1024*1024-total,'Held source bytes exceed source-part logical bound')
  raw,m=read_private(name,h,freeze['source_input_metadata'][name],max_bytes=4*1024*1024-total);total+=len(raw)
  held[name]=raw
 return held
def open_archive(binding):
 p=Path(binding['path']);named_identity(p,binding['metadata'])
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  require(meta(os.fstat(fd))==binding['metadata'],'Opened archive identity differs');return fd
 except BaseException:os.close(fd);raise
def recheck_archive(fd,binding):
 require(meta(os.fstat(fd))==binding['metadata'],'Archive descriptor identity drift')
 named_identity(binding['path'],binding['metadata'])
def hash_archive(fd,binding):
 recheck_archive(fd,binding);hh=hashlib.sha256();offset=0
 while offset<binding['metadata']['bytes']:
  raw=os.pread(fd,min(1024*1024,binding['metadata']['bytes']-offset),offset);require(bool(raw),'Archive short hash read');hh.update(raw);offset+=len(raw)
 require(hh.hexdigest()==binding['sha256'],'Accepted archive full hash drift');recheck_archive(fd,binding)
 return hh.hexdigest()
def selected_members(fd,total,expected):
 require(os.pread(fd,8,0)==b'!<arch>\n','Accepted BSD archive magic missing')
 off=8;found={};held=0
 while off<total:
  h=os.pread(fd,60,off);require(len(h)==60 and h[58:60]==b'`\n','Archive member header malformed')
  n=int(h[48:58]);require(n>=0 and off+60+n<=total,'Archive member bounds malformed')
  name=h[:16].decode('ascii').strip();start=off+60;size=n
  if name.startswith('#1/'):
   prefix=int(name[3:]);require(0<prefix<=256 and prefix<=n,'BSD name bounds');name=os.pread(fd,prefix,start).rstrip(b'\x00').decode('ascii');start+=prefix;size-=prefix
  else:name=name.rstrip('/')
  if name in expected:
   require(name not in found and size<LIMIT,'Duplicate/oversized selected archive member')
   raw=os.pread(fd,size,start);require(len(raw)==size and sha(raw)==expected[name]['sha256'],'Exact selected member hash differs: '+name)
   held+=size;require(held<8*1024*1024,'Selected members aggregate bound');found[name]=raw
  off+=60+n+(n&1)
 require(off==total and set(found)==set(expected),'Exact selected members absent or archive end differs')
 return found
def parser_from_held(held):
 name=str(P/'macho_archive_identity.py');require(name in held,'Verified held parser bytes required')
 raw=held[name];require(type(raw) is bytes and 0<len(raw)<1024*1024,'Held parser source bound')
 # Use a fresh isolated namespace. Never import by pathname or sys.modules.
 namespace={'__name__':'held_macho_archive_identity','__file__':name}
 exec(compile(raw,name,'exec'),namespace)
 for symbol in ('object_identity','public_identity','all_member_identities'):
  require(callable(namespace.get(symbol)),'Exact held parser function absent: '+symbol)
 return namespace
def sections(raw,parser):
 identity=parser['object_identity'](raw)
 return {'__nv_fatbin':identity['sections']['__nv_fatbin']['data'],'__fatbin':identity['sections']['__fatbin']['data'],'registration_identity':parser['public_identity'](identity)}
def write_bound(path,raw):
 # Read back the exact output through the same descriptor, then bind its name.
 p=Path(path);fd=os.open(p,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  offset=0
  while offset<len(raw):offset+=os.write(fd,memoryview(raw)[offset:])
  os.fsync(fd);s=meta(os.fstat(fd));require(s['uid']==501 and s['mode']==0o600 and s['bytes']==len(raw),'Output metadata differs')
  verified=hashlib.sha256();offset=0
  while offset<len(raw):
   chunk=os.pread(fd,min(1024*1024,len(raw)-offset),offset);require(bool(chunk),'Output short verification read');verified.update(chunk);offset+=len(chunk)
  require(verified.hexdigest()==sha(raw),'Output bytes differ');require(meta(os.fstat(fd))==s,'Output descriptor changed');named_identity(p,s,True);return dict(path=str(p),sha256=sha(raw),metadata=s)
 finally:os.close(fd)
def copy_same_archive_descriptor(fd,binding,path):
 recheck_archive(fd,binding);p=Path(path);out=os.open(p,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  hh=hashlib.sha256();offset=0
  while offset<binding['metadata']['bytes']:
   raw=os.pread(fd,min(1024*1024,binding['metadata']['bytes']-offset),offset);require(bool(raw),'Archive copy short source read');hh.update(raw);written=0
   while written<len(raw):written+=os.write(out,memoryview(raw)[written:])
   offset+=len(raw)
  require(hh.hexdigest()==binding['sha256'],'Archive copy source bytes differ');recheck_archive(fd,binding);os.fsync(out)
  m=meta(os.fstat(out));require(m['uid']==501 and m['mode']==0o600 and m['bytes']==binding['metadata']['bytes'],'Copied archive metadata differs')
  verify=hashlib.sha256();offset=0
  while offset<m['bytes']:
   raw=os.pread(out,min(1024*1024,m['bytes']-offset),offset);require(bool(raw),'Copied archive short verification read');verify.update(raw);offset+=len(raw)
  require(verify.hexdigest()==binding['sha256'],'Copied archive content differs');require(meta(os.fstat(out))==m,'Copied descriptor changed');named_identity(p,m,True);recheck_archive(fd,binding)
  return dict(path=str(p),sha256=verify.hexdigest(),metadata=m,same_source_descriptor_for_extract_and_copy=True)
 finally:os.close(out)
def stage_sources(out,held):
 records={}
 for stem in ('ggml-cuda','mmvq'):
  name=str(P/(stem+'.cu.proposed'));require(name in held,'Proposed source not in frozen pin reads')
  # Never reopen proposed sources after pin validation or receiver creation.
  records[stem]=write_bound(out/(stem+'.cu'),held[name])
 return records
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--materialize-reviewed-host-inputs',action='store_true',required=True);parser.add_argument('--commands-sha256',required=True);parser.add_argument('--freeze-sha256',required=True);a=parser.parse_args()
 freeze_raw,_=read_private(P/'FREEZE.json',a.freeze_sha256,max_bytes=1024*1024);freeze=json.loads(freeze_raw)
 command_raw,_=read_private(P/'NATIVE-HOST-COMMANDS.json',a.commands_sha256,max_bytes=4*1024*1024);c=json.loads(command_raw)
 require(freeze['source_pins'][str(P/'NATIVE-HOST-COMMANDS.json')]==a.commands_sha256,'Command authority is not frozen')
 held=verified_sources(freeze);require(held[str(P/'NATIVE-HOST-COMMANDS.json')]==command_raw,'Consumed command bytes differ from pinned read');parser_namespace=parser_from_held(held)
 archive=c['archive'];fd=open_archive(archive)
 try:
  integrity_binding=c['historical_archive_integrity'];integrity_raw,_=read_private(integrity_binding['path'],integrity_binding['sha256'],integrity_binding['metadata']);integrity=json.loads(integrity_raw)
  hash_archive(fd,archive);all_members=parser_namespace['all_member_identities'](fd,archive['metadata']['bytes'],integrity['member_hashes']);recheck_archive(fd,archive)
  members=selected_members(fd,archive['metadata']['bytes'],{k:v for k,v in archive['members'].items() if k in ('ggml-cuda.o','mmvq.o')})
  extracted={};payload_bytes=0
  for member,raw in members.items():
   s=sections(raw,parser_namespace);binding=archive['members'][member];fat=s['__nv_fatbin']
   require(len(fat)==binding['nv_fatbin_bytes'] and sha(fat)==binding['nv_fatbin_sha256'],'Embedded fatbin hash differs')
   require(sha(s['__fatbin'])=='8d9b65c40e2717f4078b89ae4b8a508609acf8dcbfa63f29a7db70e81e12d973','Original wrapper section bytes differ')
   payload_bytes+=len(fat)+len(s['__fatbin']);require(payload_bytes<8*1024*1024,'Aggregate payload bound')
   extracted[member]=dict(fatbin=fat,member_sha256=sha(raw),fatbin_sha256=sha(fat),wrapper_sha256=sha(s['__fatbin']),registration_identity=s['registration_identity'])
  recheck_archive(fd,archive);out=Path(c['output_directory']);require(not out.exists(),'Fresh host receiver exists; no retry');out.mkdir(mode=0o700)
  write_bound(out/'CONSUMED-MATERIALIZATION.json',(json.dumps(dict(command_sha256=a.commands_sha256,freeze_sha256=a.freeze_sha256,attempts=1,compiles=0,GPU_initializations=0,GPU_requests=0))+'\n').encode())
  staged=stage_sources(out,held);report={}
  for member,item in extracted.items():
   stem=member[:-2];fat_record=write_bound(out/(stem+'.fatbin'),item['fatbin']);report[member]={k:v for k,v in item.items() if k!='fatbin'};report[member].update(source=staged[stem],fatbin=fat_record)
  copied=copy_same_archive_descriptor(fd,archive,out/'libggml-cuda-small-prefill-global-scratch.a')
  recheck_archive(fd,archive)
  write_bound(out/'MATERIALIZED-INPUTS.json',(json.dumps(dict(version='1.0.0',archive=copied,members=report,compiles=0,GPU_initializations=0,GPU_requests=0,held_proposed_bytes_consumed=True,same_archive_descriptor=True,logical_source_member_payload_limit_bytes=LIMIT,accepted_original_member_count=len(all_members),accepted_original_member_identities=all_members),indent=2)+'\n').encode())
  print(json.dumps(report,indent=2))
 finally:os.close(fd)
if __name__=='__main__':main()

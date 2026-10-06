#!/usr/bin/env python3
"""Bounded pure archive/Mach-O identity parser; no execution/GPU discovery."""
import hashlib,os,struct
MAX_MEMBER=8*1024*1024
def require(c,why):
 if not c:raise RuntimeError(why)
def archive_entries(fd,total):
 require(os.pread(fd,8,0)==b'!<arch>\n','Accepted archive magic')
 off=8;seen=set()
 while off<total:
  h=os.pread(fd,60,off);require(len(h)==60 and h[58:60]==b'`\n','Malformed archive header');n=int(h[48:58]);require(n>=0 and off+60+n<=total,'Archive entry bound');name=h[:16].decode('ascii').strip();start=off+60;size=n
  if name.startswith('#1/'):
   prefix=int(name[3:]);require(0<prefix<=256 and prefix<=n,'Archive BSD name bound');name=os.pread(fd,prefix,start).rstrip(b'\x00').decode('ascii');start+=prefix;size-=prefix
  else:name=name.rstrip('/')
  require(name not in seen,'Duplicate archive member');seen.add(name)
  if not name.startswith('__.SYMDEF') and name not in ('','/','//'):yield dict(name=name,offset=start,bytes=size)
  off+=60+n+(n&1)
 require(off==total,'Archive exact ending')
def all_member_identities(fd,total,expected):
 found={}
 for entry in archive_entries(fd,total):
  h=hashlib.sha256();done=0
  while done<entry['bytes']:
   raw=os.pread(fd,min(1024*1024,entry['bytes']-done),entry['offset']+done);require(bool(raw),'Archive member short hash read');h.update(raw);done+=len(raw)
  digest=h.hexdigest();require(expected.get(entry['name'])==digest,'Archive member identity differs: '+entry['name']);found[entry['name']]=dict(sha256=digest,bytes=entry['bytes'])
 require(set(found)==set(expected) and len(found)==188,'Accepted exact188 member closure required');return found
def object_identity(raw):
 require(32<=len(raw)<MAX_MEMBER and struct.unpack_from('<I',raw)[0]==0xfeedfacf,'ARM64 bounded Mach-O expected')
 _,cpu,_,kind,ncmds,sz,_,_=struct.unpack_from('<8I',raw);require(cpu==0x100000c and kind==1 and 32+sz<=len(raw),'Mach-O architecture/commands bounds')
 sections=[];off=32;symtab=None
 for _ in range(ncmds):
  cmd,n=struct.unpack_from('<II',raw,off);require(n>=8 and off+n<=32+sz,'Mach-O load-command bound')
  if cmd==2:require(n>=24 and symtab is None,'Mach-O symbol table bound');symtab=struct.unpack_from('<4I',raw,off+8)
  if cmd==0x19:
   require(n>=72,'Mach-O segment header bound');count=struct.unpack_from('<I',raw,off+64)[0];require(72+80*count<=n,'Mach-O section count')
   for i in range(count):
    q=off+72+i*80;name=raw[q:q+16].split(b'\0')[0].decode('ascii');segment=raw[q+16:q+32].split(b'\0')[0].decode('ascii');addr,size,offset,align,reloff,nreloc,flags=struct.unpack_from('<QQIIIII',raw,q+32)
    require(nreloc<100000 and reloff+8*nreloc<=len(raw),'Mach-O relocation bound')
    zero_fill=(flags&0xff) in (1,12,18)
    if not zero_fill:require(offset+size<=len(raw),'Mach-O section byte bound')
    sections.append(dict(name=name,segment=segment,address=addr,bytes=size,offset=offset,alignment=align,reloff=reloff,nreloc=nreloc,zero_fill=zero_fill))
  off+=n
 require(off==32+sz and symtab is not None,'Mach-O complete commands/symbol table')
 so,count,stroff,strsize=symtab;require(count<100000 and so+16*count<=len(raw) and stroff+strsize<=len(raw),'Mach-O symbol/string bound');strings=raw[stroff:stroff+strsize];symbols=[]
 for i in range(count):
  sx,ty,sect,desc,value=struct.unpack_from('<IBBHQ',raw,so+i*16);require(sx<strsize and sect<=len(sections),'Mach-O symbol bounds');end=strings.find(b'\0',sx);require(end>=sx,'Mach-O symbol null terminator');name=strings[sx:end].decode('utf-8');symbols.append(dict(name=name,type=ty,section=sect,description=desc,value=value))
 def normalized_target(index,extern):
  if not extern:require(0<index<=len(sections),'Local relocation section bound');return dict(section=sections[index-1]['name'],segment=sections[index-1]['segment'])
  require(index<len(symbols),'External relocation symbol bound');s=symbols[index];name=s['name']
  if name.startswith(('l___unnamed_','L_')) and s['section']:
   sec=sections[s['section']-1];relative=s['value']-sec['address'];require(0<=relative<=sec['bytes'],'Named-section relocation offset bound')
   if sec['name']=='__nv_fatbin':return dict(section='__nv_fatbin',segment=sec['segment'],section_offset=relative)
   if sec['name']=='__cstring':
    require(relative<sec['bytes'],'CString start bound');start=sec['offset']+relative;end=raw.find(b'\0',start,sec['offset']+sec['bytes']);require(end>=start,'Registered kernel string terminator');return dict(section='__cstring',text=raw[start:end].decode('utf-8'))
  return dict(symbol=name)
 def relocs(sec):
  result=[]
  for i in range(sec['nreloc']):
   address,w=struct.unpack_from('<iI',raw,sec['reloff']+8*i);require(address>=0 and address<sec['bytes'],'Scattered/out-of-bounds relocation refused');ext=(w>>27)&1;index=w&0xffffff
   typ=(w>>28)&15
   if typ==10: # ARM64_RELOC_ADDEND stores a signed24-bit addend, not a section index.
    require(ext==0 and ((w>>24)&1)==0 and ((w>>25)&3)==2 and i+1<sec['nreloc'],'ARM64 addend flags/pair bound')
    next_address,next_word=struct.unpack_from('<iI',raw,sec['reloff']+8*(i+1));require(next_address==address and ((next_word>>28)&15) in (2,3,4),'ARM64 addend next relocation bound')
    target=dict(addend=index-(1<<24) if index&(1<<23) else index)
   else:target=normalized_target(index,ext)
   result.append(dict(offset=address,pcrel=(w>>24)&1,length=(w>>25)&3,type=typ,extern=ext,target=target))
  return result
 selected={}
 for wanted in ('__nv_fatbin','__fatbin'):
  matches=[s for s in sections if s['name']==wanted];require(len(matches)==1,'Exact real Mach-O section missing: '+wanted);s=matches[0];selected[wanted]=dict(section=s,data=raw[s['offset']:s['offset']+s['bytes']],relocations=relocs(s))
 wrapper=selected['__fatbin'];require(wrapper['section']['bytes']==24 and len(wrapper['relocations'])==1,'Exact24B one-relocation wrapper expected')
 require(wrapper['relocations'][0]==dict(offset=8,pcrel=0,length=3,type=0,extern=1,target=dict(section='__nv_fatbin',segment=selected['__nv_fatbin']['section']['segment'],section_offset=0)),'Wrapper must bind full fatbin at offset0')
 stubs=sorted(s['name'] for s in symbols if '__device_stub__' in s['name']);cuda_symbols=sorted(s['name'] for s in symbols if '__cuda' in s['name'])
 def function_identity(name):
  matches=[s for s in symbols if s['name']==name];require(len(matches)==1 and matches[0]['section']>0,'Exact function symbol expected: '+name);sym=matches[0];sec=sections[sym['section']-1];start=sym['value']-sec['address'];later=[s['value']-sec['address'] for s in symbols if s['section']==sym['section'] and s['value']>sym['value']];end=min(later) if later else sec['bytes'];require(0<=start<end<=sec['bytes'],'Function range bound: '+name)
  entries=[{**entry,'offset':entry['offset']-start} for entry in relocs(sec) if start<=entry['offset']<end]
  return dict(symbol=name,relocations=entries,bytes_sha256=hashlib.sha256(raw[sec['offset']+start:sec['offset']+end]).hexdigest(),bytes=end-start)
 ctor=function_identity('___cuda_module_ctor');ctor_rel=ctor['relocations']
 require(any(x['target'].get('symbol')=='___cudaRegisterFatBinary' for x in ctor_rel),'Fatbin registration call missing')
 helpers=[s for s in symbols if s['name']=='___cuda_register_globals' and s['section']>0]
 if helpers:
  require(len(helpers)==1 and any(x['target'].get('symbol')=='___cuda_register_globals' for x in ctor_rel),'Constructor must call exact CUDA registration helper')
  registration=function_identity('___cuda_register_globals');route='constructor_calls_registration_helper'
 else:registration=ctor;route='direct_constructor_registration'
 calls=[x for x in registration['relocations'] if x['target'].get('symbol')=='___cudaRegisterFunction']
 require(len(calls)==len(stubs) and len(stubs)>0,'Each device stub must have one CUDA registration call')
 return dict(sections=selected,stub_symbols=stubs,cuda_symbols=cuda_symbols,constructor_relocations=ctor_rel,constructor_bytes_sha256=ctor['bytes_sha256'],constructor_bytes=ctor['bytes'],registration_route=route,registration_function=registration,registration_call_count=len(calls),all_section_names=[s['name'] for s in sections],architecture='ARM64')

def public_identity(identity):
 return dict(architecture=identity['architecture'],fatbin=dict(bytes=len(identity['sections']['__nv_fatbin']['data']),sha256=hashlib.sha256(identity['sections']['__nv_fatbin']['data']).hexdigest()),wrapper=dict(name='__fatbin',bytes=len(identity['sections']['__fatbin']['data']),sha256=hashlib.sha256(identity['sections']['__fatbin']['data']).hexdigest(),relocations=identity['sections']['__fatbin']['relocations']),stub_symbols=identity['stub_symbols'],cuda_symbols=identity['cuda_symbols'],constructor_relocations=identity['constructor_relocations'],constructor_bytes_sha256=identity['constructor_bytes_sha256'],constructor_bytes=identity['constructor_bytes'],registration_route=identity['registration_route'],registration_function=identity['registration_function'],registration_call_count=identity['registration_call_count'])

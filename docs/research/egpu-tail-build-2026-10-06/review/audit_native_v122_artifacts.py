#!/usr/bin/env python3
"""Read-only actual host artifact/dependency audit; never invokes the binary."""
import datetime, hashlib, json, os, pathlib, shlex, stat, struct, subprocess
R=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-independent-review-20261006')
P=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-native-host-build-preparation-v122')
E=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-native-host-build-execution-v122')
S=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-aggregate-scratch-host-proposal-v121')
N=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-small-prefill-global-scratch-build-v121')
sha=lambda b:hashlib.sha256(b).hexdigest()

def dylibs(prefix):
    magic,cpu,sub,filetype,ncmds,size,flags,reserved=struct.unpack_from('<8I',prefix)
    assert magic==0xfeedfacf and cpu==0x100000c and filetype==2 and 32+size<=len(prefix)
    offset=32;out=[]
    for _ in range(ncmds):
        cmd,n=struct.unpack_from('<II',prefix,offset);assert n>=8 and offset+n<=32+size
        if cmd in (0xc,0x80000018,0x8000001f,0x80000023):
            relative=struct.unpack_from('<I',prefix,offset+8)[0];assert 24<=relative<n
            end=prefix.find(b'\0',offset+relative,offset+n);assert end!=-1
            out.append(prefix[offset+relative:end].decode())
        offset+=n
    assert offset==32+size
    return out

def main():
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    wr=(P/'run_reviewed_host_build_once.py').read_bytes();assert sha(wr)=='c4b7b598f3fd108a9b0046468c90519af7ec2eee47001e63317ffee3ed49f8e4'
    w={'__name__':'independent_artifact_wrapper_reader','__file__':str(P/'run_reviewed_host_build_once.py')};exec(compile(wr,w['__file__'],'exec'),w)
    def read(p):
        p=pathlib.Path(p);initial=p.read_bytes();return json.loads(w['private_bytes'](p,sha(initial)))
    ready=read(E/'BUILD-READY.json');assert sha((E/'BUILD-READY.json').read_bytes())=='624cca46f1995ad1c859e6c540493ab006f64ff8a2a875177f2f2fdfd264958a'
    consumed=read(E/'CONSUMED-HOST-BUILD.json');c=read(S/'NATIVE-HOST-COMMANDS.json');sf=read(S/'FREEZE.json')
    authority_path=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006/NATIVE-V121-BUILD-AUTHORITY.json')
    authority=read(authority_path);assert sha(authority_path.read_bytes())==consumed['root_authority_sha256']==ready['root_authority_sha256']=='317d3be351c9940c729c1f8254aff741ae3a1114f013ac48b61827ccde1c4be6'
    assert consumed['source_freeze_sha256']==ready['source_freeze_sha256']==sha((S/'FREEZE.json').read_bytes())
    assert consumed['commands_sha256']==ready['commands_sha256']==sha((S/'NATIVE-HOST-COMMANDS.json').read_bytes())
    assert consumed['wrapper_freeze_sha256']==sha((P/'FREEZE.json').read_bytes()) and consumed['preparation_sha256']==sha((P/'PREPARATION.json').read_bytes())
    assert sha((R/'OFFLINE-V121-ADMISSION-REVIEW.json').read_bytes())==authority['independent_admission_review_sha256']
    stages={};expected=[authority['materialize_argv'],c['compile_commands'][0]['argv'],c['compile_commands'][1]['argv'],c['archive_replace_argv'],c['link_argv']]
    for label,argv in zip(['MATERIALIZE','COMPILE-ggml-cuda','COMPILE-mmvq','ARCHIVE-REPLACE','LINK'],expected):
        result=read(E/(label+'-RESULT.json'));command=read(E/(label+'-COMMAND.json'));process=read(E/(label+'-PROCESS.json'))
        assert command['argv']==argv and command['environment']==c['environment'] and command['removed_environment_keys']==c['inherited_environment_remove']
        assert result['PID']==process['PID']==process['process_group'] and result['exit_code']==0 and result['attempts']==1
        assert result['retries']==result['native_executable_invocations']==result['GPU_actions']==0 and not result['timed_out']
        stages[label]=result
    assert not (E/'TERMINAL-REFUSAL.json').exists()
    for key,value in [('materializations',1),('host_compiles',2),('archive_replacements',1),('links',1),('retries',0),('native_executable_invocations',0),('GPU_actions',0)]:assert ready[key]==value
    renderer=pathlib.Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-renderer-preparation-v111/experimental_27b.py')
    renderer_raw=w['private_bytes'](renderer,'0903f16dd66ae5dc4ed82d02be30570754f219d16ff7986ff379c7a45788b339')
    r=w['loaded_namespace'](renderer,renderer_raw,'held_independent_source_validator')
    pins=dict(c['reused_current_source_closure']);bindings=dict(c['reused_external_source_bindings'])
    for name,record in c['tools'].items():pins[name]=record['sha256'];bindings[name]=record.get('external_binding') or record['external_v111_binding']
    dependency_sets={};unique={};new={};new_bindings={}
    for stem in ['ggml-cuda','mmvq']:
        d=read(E/('COMPILE-'+stem+'-DEPENDENCIES.json'))
        depraw=(N/(stem+'.d')).read_bytes();names=set(shlex.split(depraw.decode().replace('\\\n',' ').split(':',1)[1]))
        assert names=={x['path'] for x in d['dependencies']} and d['count']==len(names)
        assert d['new_dependency_count']==sum(not x['already_hash_bound'] for x in d['dependencies'])
        dependency_sets[stem]=d
        for record in d['dependencies']:
            name=record['path'];p=pathlib.Path(name)
            assert str(p.resolve())==record['canonical'] and r['metadata'](p.stat())==record['metadata']
            if name in unique:assert unique[name]==record
            unique[name]=record;pins[name]=record['sha256']
            if not record['already_hash_bound']:new[name]=record
            if r['external_input'](name) and name not in bindings:
                canonical,aliases=r['alias_chain'](name);assert canonical==record['canonical']
                binding=dict(canonical=canonical,sha256=record['sha256'],metadata=record['metadata'],aliases=aliases)
                bindings[name]=binding;new_bindings[name]=binding
    r['configure_source_bindings']({'source_pins':pins,'external_source_bindings':bindings})
    for record in unique.values():r['verified_file'](record['path'],record['sha256'])
    for name,record in c['tools'].items():r['verified_file'](name,record['sha256'])
    mpath=S/'materialize_reviewed_host_inputs.py'
    m=w['loaded_namespace'](mpath,w['private_bytes'](mpath,'770acb382441fe100591efdaf7ddd8a4cc63d2e82db057948bffe9f6d0dc8a9f',expected_metadata=sf['source_input_metadata'][str(mpath)]),'held_independent_materializer')
    parserraw=w['private_bytes'](S/'macho_archive_identity.py','94fba316473261c3f4699506cd2de6e4991c32aa693a405f8bff3d4c14dab9b0',expected_metadata=sf['source_input_metadata'][str(S/'macho_archive_identity.py')])
    parser=m['parser_from_held']({str(S/'macho_archive_identity.py'):parserraw})
    materialization=read(N/'MATERIALIZED-INPUTS.json');originals=read(S/'ACTUAL-ARCHIVE-CONSUMER-AUDIT.json')['selected_members'];objects={}
    for stem in ['ggml-cuda','mmvq']:
        assert w['generated_inputs'](m,S,N,sf,c,materialization,stem)
        obj=read(E/('COMPILE-'+stem+'-OBJECT.json'));oraw=m['read_private'](obj['path'],obj['sha256'],obj['metadata'],max_bytes=8*1024**2)[0]
        actual=parser['public_identity'](parser['object_identity'](oraw));assert actual==obj['identity']
        old=originals[stem+'.o']['registration_identity']
        for key in ['architecture','fatbin','wrapper','stub_symbols','cuda_symbols','constructor_relocations','registration_route','registration_call_count']:assert actual[key]==old[key],(stem,key)
        assert actual['registration_function']['relocations']==old['registration_function']['relocations']
        objects[stem+'.o']=dict(path=obj['path'],sha256=obj['sha256'],metadata=obj['metadata'],fatbin=actual['fatbin'],wrapper=actual['wrapper'],registration_route=actual['registration_route'],registration_call_count=actual['registration_call_count'],stub_count=len(actual['stub_symbols']))
    abi=read('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-static-inputs-v111/BUILD-ABI.json')
    runtime_alias_bindings={}
    for alias,binding in abi['runtime_library_aliases'].items():
        canonical,aliases=r['alias_chain'](alias);assert canonical==binding['path']
        alias_binding=dict(bindings[canonical]);alias_binding['aliases']=aliases
        runtime_alias_bindings[alias]=alias_binding;bindings[alias]=alias_binding;pins[alias]=binding['sha256']
        r['configure_source_bindings']({'source_pins':pins,'external_source_bindings':bindings})
        r['verified_file'](alias,binding['sha256'])
        r['verified_file'](canonical,binding['sha256'])
    ib=c['historical_archive_integrity'];integrity=json.loads(m['read_private'](ib['path'],ib['sha256'],ib['metadata'])[0])
    expected=dict(integrity['member_hashes']);expected.update({name:record['sha256'] for name,record in objects.items()})
    archive=ready['archive'];assert archive==read(E/'ARCHIVE-INTEGRITY.json')
    fd=m['open_archive'](archive)
    try:m['hash_archive'](fd,archive);members=parser['all_member_identities'](fd,archive['metadata']['bytes'],expected);m['recheck_archive'](fd,archive)
    finally:os.close(fd)
    assert members==archive['members'] and len(members)==188
    assert sum(members[k]['sha256']==integrity['member_hashes'][k] for k in members)==186
    exe=ready['executable'];assert r['metadata'](pathlib.Path(exe['path']).lstat())==exe['metadata']
    data=r['verified_file'](exe['path'],exe['sha256'],prefix_bytes=4096)
    imports=dylibs(data['prefix']);recorded=[]
    for line in (E/'IMPORTS.stdout').read_text().splitlines()[1:]:recorded.append(line.strip().split(' (compatibility version')[0])
    assert imports==recorded and len(imports)==7
    nm_argv=['/usr/bin/nm',exe['path']]
    nm=subprocess.run(nm_argv,capture_output=True,timeout=30)
    assert nm.returncode==0 and len(nm.stdout)<64*1024**2
    ledger_symbols=[line for line in nm.stdout.decode().splitlines() if 'llmsx_scratch' in line]
    assert any('reserved' in line for line in ledger_symbols) and any('peak' in line for line in ledger_symbols)
    nm_receipt=R/'NATIVE-V122-PASSIVE-LOCAL-SYMBOLS.json'
    nm_receipt.write_text(json.dumps(dict(observed_at=at,argv=nm_argv,exit_code=nm.returncode,stdout_sha256=sha(nm.stdout),stderr_sha256=sha(nm.stderr),ledger_symbols=ledger_symbols,scope='Passive symbol reading only; original nm -g report excludes static ledger symbols',native_invocations=0),indent=2)+'\n');nm_receipt.chmod(0o600)
    for label in ['HEADER','IMPORTS','SYMBOLS']:
        record=read(E/(label+'-COMMAND.json'));assert record['exit_code']==0 and not record['native_executable_invoked']
    bindingout=R/'NATIVE-V122-POSTCOMPILE-DEPENDENCY-BINDINGS.json'
    bindingreport=dict(version='1.0.0',observed_at=at,scope='Actual postcompile bindings only; no claim of historical/precompile equality',new_lexical_dependency_count=len(new),new_external_binding_count=len(new_bindings),dependencies=new,external_source_bindings=new_bindings,runtime_library_alias_bindings=runtime_alias_bindings)
    bindingout.write_text(json.dumps(bindingreport,indent=2)+'\n');bindingout.chmod(0o600)
    evidence=[]
    for p,claim in [(E/'BUILD-READY.json','Actual five successful host stages and exact linked ARM64 identity'),
                    (E/'CONSUMED-HOST-BUILD.json','Fresh authority/source/command/wrapper bindings consumed once'),
                    (E/'COMPILE-ggml-cuda-DEPENDENCIES.json','881 actual depfile inputs independently hash/metadata/alias verified'),
                    (E/'COMPILE-mmvq-DEPENDENCIES.json','779 actual depfile inputs independently hash/metadata/alias verified'),
                    (E/'ARCHIVE-INTEGRITY.json','All188 identities verified against historical manifest with only two object replacements'),
                    (nm_receipt,'Local reserved/peak ledger symbols verified passively; no executable invocation'),
                    (bindingout,'New dependency binding evidence is current postcompile scope')]:
        evidence.append(dict(source=str(p),sha256=sha(p.read_bytes()),observed_at=at,supported_claim=claim))
    evidence.append(dict(source=exe['path'],sha256=exe['sha256'],observed_at=at,supported_claim='Actual236636400B ARM64 binary stream hash, seven Mach-O imports and ledger symbols verified; never invoked'))
    report=dict(agent='/root/cold_capture_review',definition_version='1.0.0',status='complete',observed_at=at,
                actual_host_artifact_admission_passed=True,ready_for_separate_cold_receiver_preparation=True,
                evidence=evidence,changes=['Designated independent audit script, current dependency binding report and artifact receipt only'],
                remaining=['Fresh cold/start/request receiver source and full updated dependency seal review','User physical cold recovery only after receivers are fully concrete','Actual numerical/peak/coding/full standardDR gates remain unmet'],
                details=dict(surface='Actual v122 host build/native121 artifacts',acceptance_condition='Exact source/tool/header/object/device/archive/link/import identities with no native invocation',source_revision=ready['source_freeze_sha256'],loaded_revision=exe['sha256'],process_or_origin=stages,configuration_identity=ready['commands_sha256'],observations=dict(objects=objects,compile_counts={k:len(v['dependencies']) for k,v in dependency_sets.items()},unique_dependency_count=len(unique),new_lexical_bindings=len(new),new_external_bindings=len(new_bindings),imports=imports,ledger_symbols=ledger_symbols,archive_members=188,unchanged_members=186),mismatches=[],unverified_checks=['140 new lexical entries are current postcompile bindings; historical/precompile equality unproven','Transient compiler/linker loaded images were not independently sampled','Full Apple dyld cache content/loaded image proof remains outside accepted scope','Linked executable has never been invoked; runtime ABI/numerics/physical peak/coding/DR unqualified']),
                reviewer_actions=dict(wrapper_main=0,materializer_main=0,archivecopy=0,extraction=0,native_compile=0,execute_helper=0,GPU_actions=0,model_requests=0),full_qualification=False)
    out=R/'NATIVE-V122-ARTIFACT-REVIEW.json';out.write_text(json.dumps(report,indent=2)+'\n');out.chmod(0o600)
    print(json.dumps(dict(receipt=str(out),sha256=sha(out.read_bytes()),artifact_passed=True,unique_dependencies=len(unique),new_lexical=len(new),new_external=len(new_bindings),archive_members=188,unchanged=186,binary_sha256=exe['sha256'])))

if __name__=='__main__':main()

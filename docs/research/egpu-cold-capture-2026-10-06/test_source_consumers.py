#!/opt/homebrew/bin/python3
"""Real closure consumption and bounded rejection tests; zero inference/start/reset."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import os
import types
import stat
import uuid

ROOT=Path(__file__).absolute().parent
BASE=ROOT.parent
STATIC=BASE/'qwen36-27b-iq2-static-inputs-v111'
OUT=ROOT/'SOURCE-CONSUMER-CONTROLS.json'

def load(path,name):
    m=types.ModuleType(name);m.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    return m

def main():
    os.umask(0o077)
    draft=json.loads((STATIC/'REVIEW-DRAFT.json').read_bytes())
    # This in-memory fixture exercises consumers. It is never serialized as physical authority.
    fixture=copy.deepcopy(draft);fixture.update(passed=True,seal_pending=False)
    m=load(ROOT/'experimental_27b.py','v111_renderer_controls')
    startup=load(BASE/'qwen36-27b-iq2-startup-preparation-v111/start_once.py','v111_startup_controls')
    tests=[]
    def accept(name,fn):
        fn();tests.append({'name':name,'expected':'accept','passed':True})
    def refuse(name,fn):
        try:fn()
        except Exception as error:
            tests.append({'name':name,'expected':'refuse','passed':True,'error':type(error).__name__+': '+str(error)});return
        raise AssertionError('Expected rejection: '+name)
    def configure(value=fixture):m.final_review(value)
    accept('configure_exact_real_external_bindings',configure)
    accept('entire_real_closure_via_actual_verify_pins',lambda:m.verify_pins(fixture['source_pins']))
    identities=startup.pin_identities(fixture['source_pins'],m)
    accept('entire_real_startup_pin_identities_and_recheck',lambda:startup.verify_pin_identities(fixture['source_pins'],m,identities))
    accept('actual_renderer_source_plan_consumer',lambda:m.verify_source_plan(json.loads((ROOT/'SOURCE-PLAN.json').read_bytes())))
    accept('actual_startup_source_plan_consumer',lambda:m.verify_source_plan({'source_pins':json.loads((BASE/'qwen36-27b-iq2-startup-preparation-v111/SOURCE-PLAN.json').read_bytes())['source_pins']}))
    sdk='/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk/System/Library/Frameworks/Accelerate.framework/Accelerate.tbd'
    digest=fixture['source_pins'][sdk]
    accept('actual_root_owned_SDK_alias_consumed',lambda:m.verified_file(sdk,digest))
    for field,value in [('canonical','/usr/bin/false'),('metadata.uid',501),('metadata.mode',0o600),('metadata.bytes',1),('metadata.inode',0)]:
        changed=copy.deepcopy(fixture)
        if field=='canonical':changed['external_source_bindings'][sdk][field]=value
        else:changed['external_source_bindings'][sdk]['metadata'][field.split('.')[1]]=value
        configure(changed)
        refuse('refuse_external_'+field,lambda:m.verified_file(sdk,digest))
    changed=copy.deepcopy(fixture);changed['external_source_bindings'][sdk]['aliases'][0]['target']='retargeted'
    configure(changed);refuse('refuse_alias_chain_retarget',lambda:m.verified_file(sdk,digest))
    changed=copy.deepcopy(fixture);bad='0'*64;changed['source_pins'][sdk]=bad;changed['external_source_bindings'][sdk]['sha256']=bad
    configure(changed);refuse('refuse_actual_contents_hash_mismatch',lambda:m.verified_file(sdk,bad))
    configure();refuse('refuse_external_as_private_authority',lambda:m.verified_file(sdk,digest,private=True))
    changed=copy.deepcopy(fixture);changed['external_source_bindings'].pop(sdk)
    refuse('refuse_incomplete_external_binding_set',lambda:configure(changed))
    configure()
    provenance=json.loads((STATIC/'BUILD-PROVENANCE.json').read_bytes())
    for tool in provenance['eight_current_host_tool_changes']:
        refuse('refuse_historical_tool_hash_as_current_'+tool['path'],lambda t=tool:m.verified_file(t['path'],t['expected']))
    for name in m.BUILD_ALIASES:
        accept('exact_named_user_build_alias_'+name,lambda n=name:m.verified_file(n,fixture['source_pins'][n]))
    scratch_root=ROOT/'private-control-fixtures';scratch_root.mkdir(mode=0o700,exist_ok=True)
    info=scratch_root.lstat()
    assert scratch_root.resolve(strict=True)==scratch_root and stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700
    scratch=scratch_root/str(uuid.uuid4());scratch.mkdir(mode=0o700)
    p=scratch/'proof.json';p.write_text('{"fixture":true}\n');p.chmod(0o600)
    good=hashlib.sha256(p.read_bytes()).hexdigest()
    accept('canonical_UID501_private0600_proof',lambda:m.verified_file(str(p),good,private=True))
    p.chmod(0o644);refuse('refuse_private0644',lambda:m.verified_file(str(p),good,private=True));p.chmod(0o600)
    link=scratch/'proof-link.json';link.symlink_to(p)
    refuse('refuse_private_symlink',lambda:m.verified_file(str(link),good,private=True))
    real_getuid=m.os.getuid;m.os.getuid=lambda:502
    try:refuse('refuse_wrong_private_owner',lambda:m.verified_file(str(p),good,private=True))
    finally:m.os.getuid=real_getuid
    configure()
    for argv in (['/bin/ps','-p',str(os.getpid())],['lsof','-nP'],['/opt/homebrew/bin/python3','-B'],['/Applications/TinyGPU.app/Contents/MacOS/TinyGPU','server']):
        accept('actual_consuming_command_validator_'+argv[0],lambda a=argv:m.verify_command(a,fixture['source_pins'],{'PATH':'/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin'}))
    refuse('refuse_unreviewed_executable',lambda:m.verify_command(['/usr/bin/false'],fixture['source_pins']))
    fake=types.SimpleNamespace(Popen=lambda *args,**kwargs:types.SimpleNamespace(pid=987654))
    m.guard_subprocess(fake,fixture['source_pins'])
    accept('bounded_fake_spawn_with_actual_executable_validation',lambda:fake.Popen(['/bin/ps','-p',str(os.getpid())]))
    refuse('refuse_shell_spawn',lambda:fake.Popen(['/bin/ps'],shell=True))
    refuse('refuse_executable_override',lambda:fake.Popen(['/bin/ps'],executable='/usr/bin/false'))
    original=m.source_identity;calls=0
    def mutate(value,expected):
        nonlocal calls
        calls+=1
        if calls==2:raise m.Refusal('Simulated post-spawn file identity drift')
        return original(value,expected)
    m.source_identity=mutate
    try:refuse('preserve_started_fake_child_on_postspawn_drift',lambda:fake.Popen(['/bin/ps']))
    finally:m.source_identity=original
    assert fake._v111_started_child_on_refusal==[{'pid':987654,'argv':['/bin/ps'],'preserved':True}]
    result={'version':'1.0.0','observed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':True,
            'source_pin_count_consumed':len(fixture['source_pins']),'external_bindings_consumed':len(fixture['external_source_bindings']),
            'offline_fixture_not_physical_authority':True,'tests':tests,'control_count':len(tests),
            'model_requests':0,'GPU_starts':0,'CPU_starts':0,'resets':0,
            'renderer_sha256':hashlib.sha256((ROOT/'experimental_27b.py').read_bytes()).hexdigest(),
            'startup_sha256':hashlib.sha256((BASE/'qwen36-27b-iq2-startup-preparation-v111/start_once.py').read_bytes()).hexdigest(),
            'draft_sha256':hashlib.sha256((STATIC/'REVIEW-DRAFT.json').read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(result,indent=2)+'\n');OUT.chmod(0o600)
    print(json.dumps({k:v for k,v in result.items() if k!='tests'},indent=2))

if __name__=='__main__':main()

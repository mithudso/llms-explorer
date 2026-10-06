"""Final source authority readback only; no operational admission tail."""
from pathlib import Path
import ast, datetime, hashlib, json, os, stat, types

OUT=Path(__file__).absolute().parent
ROOT=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-downstream-preparation-v125')
FINAL=ROOT/'INDEPENDENT-DOWNSTREAM-REVIEW.json'
FINAL_SHA='d0f3df2242a7591079c6b44adf12e6059bfc88d16ae190535ee8ec3f48576b1e'
DRAFT_SHA='71d7fda85e639bc99562aa0213bcf92a35cb5b704706e1c1596c8acf389f2f5e'
AUDIT_SHA='f4bbd0019eb0a83b28082e6887d5b8c0ad63374811b94f5348d616aa4a86d74b'
COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'
ROOT_RECEIPT=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-cold-capture-execution-20261006/DOWNSTREAM-V125-ROOT-SEAL-RECEIPT.json')
ROOT_RECEIPT_SHA='c0b54cadad6f3c91dcd726cc53fd849ddbb509865c1c171db8d5b1e04e317cc3'

def held(p,digest):
    assert p.is_absolute() and p.resolve(strict=True)==p
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        a=os.fstat(stream.fileno())
        assert stat.S_ISREG(a.st_mode) and a.st_uid==501 and stat.S_IMODE(a.st_mode)==0o600
        assert 0<a.st_size<=16*1024**2
        raw=stream.read(16*1024**2+1);b=os.fstat(stream.fileno())
    identity=lambda x:(x.st_dev,x.st_ino,x.st_uid,x.st_gid,stat.S_IMODE(x.st_mode),x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    assert identity(a)==identity(b)==identity(p.lstat()) and hashlib.sha256(raw).hexdigest()==digest
    return raw

at=datetime.datetime.now(datetime.timezone.utc).isoformat()
raw=held(FINAL,FINAL_SHA);final=json.loads(raw)
draft=json.loads(held(ROOT/'DOWNSTREAM-REVIEW-DRAFT.json',DRAFT_SHA))
audit=json.loads(held(OUT/'TASK620-DOWNSTREAM-SOURCE-REVIEW.json',AUDIT_SHA))
root_receipt=json.loads(held(ROOT_RECEIPT,ROOT_RECEIPT_SHA))
allowed={'independent_audit','independent_review_pending','issuer','passed','seal_pending','source_draft'}
assert set(final)-set(draft)=={'sealed_at'} and not set(draft)-set(final)
assert {k for k in draft if draft[k]!=final[k]}==allowed
assert all(final[k]==draft[k] for k in draft if k not in allowed)
assert final['passed'] is True and final['seal_pending'] is final['independent_review_pending'] is False
assert final['issuer']=='root-independent-source-seal'
assert final['source_draft']=={'path':str(ROOT/'DOWNSTREAM-REVIEW-DRAFT.json'),'sha256':DRAFT_SHA}
assert final['independent_audit']=={'path':str(OUT/'TASK620-DOWNSTREAM-SOURCE-REVIEW.json'),'sha256':AUDIT_SHA}
assert audit['passed'] and audit['status']=='complete'
assert final['actual_session_identity'] is None
false_keys=('actual_numerical_acceptance','full_qualification','physical_launch_ready','cold_admission_issued','coding_verified','standard_research_verified','actual_peak_verified','candidate_numerics_verified')
assert all(final[k] is False for k in false_keys)
assert root_receipt['final']=={'path':str(FINAL),'sha256':FINAL_SHA}
assert root_receipt['conditions']==audit['operational_conditions']
assert root_receipt['actual_activation_issued'] is False and root_receipt['actual_session_identity'] is None

common_path=ROOT/'downstream_common.py';source=held(common_path,COMMON_SHA)
c=types.ModuleType('independent_final_common');c.__file__=str(common_path)
exec(compile(source,str(common_path),'exec'),c.__dict__)
actual=c.bound_document({'path':str(FINAL),'sha256':FINAL_SHA})
assert actual==final
# Execute only the four actual statements that consume the source-review body.
# No activation fixture, full-pin rehash, owner observation or operational tail.
tree=ast.parse(source,str(common_path))
admission=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admission')
assert ast.unparse(admission.body[6]).startswith("review = bound_document(auth['source_review'])")
assert ast.unparse(admission.body[9])=='r.final_review(review)'
prefix=ast.Module(body=admission.body[6:10],type_ignores=[])
namespace=dict(c.__dict__);namespace['auth']={'source_review':{'path':str(FINAL),'sha256':FINAL_SHA}}
exec(compile(prefix,str(common_path),'exec'),namespace)
assert namespace['review']==final
r=namespace['r'];r.same_identity(final,final['identity']['binary_sha256'])
client=c.load_source(ROOT/'claude_candidate.py',final,r,'independent_final_bound_client')
assert client.common().BINARY_SHA==final['identity']['binary_sha256']

def forbidden(*_args,**_kwargs):raise AssertionError('Operational observation forbidden')
c.observe=c.passive_owner=forbidden
try:c.admission({})
except ValueError as error:assert 'authority' in str(error)
else:raise AssertionError('Missing physical activation admitted')
assert all(not (ROOT/n).exists() and not (ROOT/n).is_symlink() for n in ('ROOT-ACTIVATION.json','ROOT-QUALITY-REVIEW.json','execution','production/cold-runtime','production/capture-inference'))
assert held(FINAL,FINAL_SHA)==raw

receipt={
    'agent':'/root/cold_capture_review','definition_version':'1.0.0','version':'1.0.0','status':'complete','observed_at':at,
    'final_source_authority_readback_passed':True,'actual_pure_source_review_prefix_passed':True,
    'evidence':[
        {'source':str(FINAL),'sha256':FINAL_SHA,'observed_at':at,'supported_claim':'Strict current UID5010600 canonical stable read; exactly six declared final fields plus sealed_at changed; all21214 pins/identity/conditions and physical-false fields preserved'},
        {'source':str(common_path),'sha256':COMMON_SHA,'observed_at':at,'supported_claim':'Actual bound_document and actual admission source-review statements6..9 consume final authority; exact held client loader passes; absent actual root activation still refuses before observation'},
        {'source':str(ROOT_RECEIPT),'sha256':ROOT_RECEIPT_SHA,'observed_at':at,'supported_claim':'Root preserved independent operational conditions; no actual activation/session/numerical/quality issued'}],
    'changes':['Only caller-designated private final readback script and receipt'],
    'remaining':['Parent real physical recovery and bound production startup/original numeric pair','Root ten-alias check and exact environment/argv before each future quality phase; separate raw witness snapshots','Actual two full coding sessions and canonical full DR/SKO/finish/both-tree receipts','Paused registry, physical peak and long-term stability remain unavailable/unmeasured'],
    'details':{
        'surface':'Final source-only downstream authority; no loaded candidate invocation',
        'acceptance_condition':'Exact permitted frozen-to-final deltas, actual source helper consumers, absent operational activation',
        'source_revision':FINAL_SHA,'loaded_revision':None,'process_or_origin':None,'configuration_identity':final['identity'],
        'observations':{'source_pins':len(final['source_pins']),'pure_statement_indexes':[6,7,8,9],'full_pin_replay':False,'actual_activation_absent':True,'source_acceptance_only':True},
        'mismatches':[],'unverified_checks':['All actual physical/numerical/coding/DR acceptance','Standalone research bootstrap no-fallback behavior','Independent raw coding attribution','Physical peak and long-term stability']},
    'operational_conditions':audit['operational_conditions'],
    'reviewer_actions':{'subprocesses':0,'HTTP':0,'native':0,'model':0,'GPU':0,'service_actions':0},
    'actual_session_identity':None,'actual_numerical_acceptance':False,'coding_acceptance':False,'standard_dr_acceptance':False,'full_qualification':False,
}
out=OUT/'TASK620-DOWNSTREAM-FINAL-SEAL-REVIEW.json'
with out.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
out.chmod(0o600)
print(json.dumps({'passed':True,'receipt':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'operational_calls':0}))

"""Read-only strict receipt binding after independent root review; never infer success."""
from pathlib import Path
import argparse,hashlib,json,os,stat,types,sys
ROOT=Path(__file__).absolute().parent
COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'
def common():
    p=ROOT/'downstream_common.py';fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:a=os.fstat(f.fileno());raw=f.read(1024**2);b=os.fstat(f.fileno())
    key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if p.resolve(strict=True)!=p or a.st_uid!=501 or stat.S_IMODE(a.st_mode)!=0o600 or key(a)!=key(b) or key(a)!=key(p.lstat()) or hashlib.sha256(raw).hexdigest()!=COMMON_SHA:raise ValueError('Bound private receipt helper differs')
    m=types.ModuleType('held_receipt_common');m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m

def verify(root_review_sha):
    c=common();auth,review,startup,r=c.admission()
    q=c.bound_document({'path':str(ROOT/'ROOT-QUALITY-REVIEW.json'),'sha256':root_review_sha})
    c.require(q.get('actual') is True and q.get('independent') is True and q.get('issuer')=='root-independent-acceptance' and q.get('native_pid')==startup['native_pid'] and q.get('boot_id')==startup['boot_id'] and q.get('binary_sha256')==c.BINARY_SHA,'Actual independent same-owner acceptance required')
    coding=c.bound_document(q['coding_result']);research=c.bound_document(q['research_result'])
    c.require(q['coding_result']['path']==str(ROOT/'execution/coding/RESULT.json') and coding.get('coding_pair_passed') is True and coding.get('passed_runs')==2,'Original fresh coding pair did not pass')
    c.require(q['research_result']['path']==str(ROOT/'execution/research/RESULT.json') and not research.get('errors'),'Research phase receiver failed')
    required=('full23_tools_all21_coding_gates','five_concepts','three_independent_origins_each','claims_reads_sources_literal_quotes','actual_negation','blind10_refetch15','render_install_card_injection','all15_sko_passes_convergence_functional_evals','sko_fresh_context_blind_audit','canonical_finish','both_trees_readback')
    checks=q.get('checks',{});missing=[k for k in required if checks.get(k,{}).get('passed') is not True]
    for name,row in checks.items():
        c.require(type(row.get('evidence')) is list and row['evidence'],'Independent claim lacks bound evidence: '+name)
        for binding in row['evidence']:
            c.require(set(binding)=={'path','sha256'},'Exact evidence binding required')
            r.verified_file(binding['path'],binding['sha256'])
    # This environment intentionally preserves the indexing pause. Nothing may
    # convert full workflow content evidence into registration/complete acceptance.
    registry=q.get('registry',{})
    c.require(registry.get('status')=='REGISTRY-UNAVAILABLE' and registry.get('embedding_or_index_service_started') is False,'Paused registry state must remain explicit')
    return {'status':'partial','content_and_coding_independently_accepted':not missing,'missing_required_content_checks':missing,'registry_status':'REGISTRY-UNAVAILABLE','standard_dr_accepted':False,'full_sko_accepted':False,'full_qualification':False,'long_term_stability_verified':False,'physical_peak_verified':False,'native_starts':0,'model_calls':0,'limitation':'Bound independent evidence is necessary; files and model self-grading alone confer no acceptance.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root-review-sha256',required=True);a=p.parse_args()
    print(json.dumps(verify(a.root_review_sha256),indent=2));raise SystemExit(2)

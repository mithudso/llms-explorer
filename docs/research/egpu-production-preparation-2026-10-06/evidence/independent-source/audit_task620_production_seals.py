#!/usr/bin/env python3
"""Actual final authority readback; canonical pure request prefix only."""
import ast, copy, datetime, hashlib, json, types
from pathlib import Path
import audit_task620_production as a

SS='2c3b3b95c6aab23523c7885dea7281d52e029c7ccbc14a066ae1197e11fbc11c'
QS='371b73eafb27429f86ea3ae658bcb7e29d85fa0d54fd6ea5021fd04027d19d2a'
AS='04c06f6622fd98153c31ed7bb67a97a8142cfb7fcd3034840cc3266bf4e87a08'

def main():
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    freeze=json.loads(a.private(a.D/'PRODUCTION-FREEZE.json',a.FREEZE))
    sp=a.P/'static-inputs/INDEPENDENT-REVIEW.json'
    qp=a.P/'capture-response-preparation/PREPARATION.json'
    s=json.loads(a.private(sp,SS));q=json.loads(a.private(qp,QS))
    sdpath=sp.parent/'REVIEW-DRAFT.json';qdpath=qp.parent/'PREPARATION-DRAFT.json'
    sd=json.loads(a.private(sdpath,freeze['frozen_sources'][str(sdpath)]))
    qd=json.loads(a.private(qdpath,freeze['frozen_sources'][str(qdpath)]))
    allowed={'delta','scope','independent_audit','independent_review_pending','issuer','passed','seal_pending','sealed_at','source_draft'}
    assert set(s)-set(sd)=={'sealed_at'} and not set(sd)-set(s) and all(s[k]==v for k,v in sd.items() if k not in allowed)
    assert s['passed'] is True and s['seal_pending'] is False and s['independent_review_pending'] is False and s['issuer']=='/root'
    assert s['source_draft']==dict(path=str(sdpath),sha256=freeze['frozen_sources'][str(sdpath)])
    assert s['independent_audit']==dict(path=str(a.R/'TASK620-PRODUCTION-SOURCE-REVIEW.json'),sha256=AS)
    prior=json.loads(a.private(a.R/'TASK620-PRODUCTION-SOURCE-REVIEW.json',AS))
    assert prior['source_delta_ready'] is True
    assert set(q)==set(qd) and all(q[k]==v for k,v in qd.items() if k not in {'independent_review_pending','seal_pending','source_review_sha256'})
    assert q['source_review_sha256']==SS and q['seal_pending'] is q['independent_review_pending'] is False
    assert q['version']=='1.0.1' and q['capture_enabled'] is False and q['production_mode_numerical_acceptance'] is False
    assert q['full_qualification'] is False and q['maximum_GPU_requests']==2
    for k in ('actual_peak_verified','candidate_numerics_verified','coding_verified','standard_research_verified','full_qualification','physical_launch_ready'):
        assert s[k] is False
    rp=a.P/'renderer-preparation/experimental_27b.py';r=a.load(rp,a.private(rp,s['source_pins'][str(rp)]))
    r.final_review(s);r.same_identity(s,s['identity']['binary_sha256'])
    cp=a.P/'cold-root-operation/run_actual_cold_once.py';c=a.load(cp,a.private(cp,s['source_pins'][str(cp)]));c.minimal_final_review(s)
    gp=qp.parent/'guard_v125.py';gb=a.private(gp,q['pins'][str(gp)]);g=a.load(gp,gb)
    a.prefix(g,gp,gb,'verify_admission',3,'prep')
    assert g.verify_admission(QS)==q and g.VERSION==q['version']=='1.0.1'
    np=qp.parent/'run_numeric.py';nr=a.private(np,q['pins'][str(np)]);n=a.load(np,nr)
    assert n.GUARD_SHA==q['pins'][str(gp)] and n.load_guard().VERSION==g.VERSION
    cfg=json.loads(a.private(a.P/'static-inputs/ROOT-CONFIG.json',s['source_pins'][str(a.P/'static-inputs/ROOT-CONFIG.json')]))
    assert cfg['runtime_directory']==str(a.P/'cold-runtime') and g.OUTPUT==a.P/'capture-inference'
    assert not g.RUNTIME.exists() and not g.OUTPUT.exists()
    assert not (a.P/'cold-root-operation/OPERATION-CONSUMED.json').exists()
    report=dict(agent='/root/cold_capture_review',definition_version='1.0.0',status='complete',observed_at=at,final_root_authorities_readback_passed=True,pure_actual_request_schema_prefix_passed=True,
        evidence=[dict(source=str(sp),observed_at=at,sha256=SS,supported_claim='Actual root UID5010600 seal preserves exact frozen pins/identity/CPU/physical-false data; only declared source-only final fields differ'),dict(source=str(qp),observed_at=at,sha256=QS,supported_claim='Actual request version1.0.1 passes canonical first3 statements including real source hash read; exactly declared source SHA and pending flags changed'),dict(source=str(gp),observed_at=at,sha256=q['pins'][str(gp)],supported_claim='Pure request prefix excludes all operation/owner/model/HTTP tail; numeric loader binds this exact helper')],
        changes=['Designated private final authority audit script and receipt only'],remaining=['Frozen downstream source review','Parent fresh physical recovery/startup/native numeric and independent acceptance'],reviewer_test_correction='First audit assumed equal key sets; root correctly adds its declared sealed_at field. Exact permitted addition corrected without subject mutation.',
        details=dict(surface='Actual root-sealed capture-disabled production authorities',acceptance_condition='Exact bytes/private metadata/frozen-to-final deltas/actual canonical initial request schema',source_revision=SS,loaded_revision=None,process_or_origin='No operational receiver consumed; candidate unmeasured',configuration_identity=s['identity'],observations=dict(request_sha256=QS,actual_schema='1.0.1',source_pin_count=len(s['source_pins']),external_bindings=len(s['external_source_bindings']),pure_prefix_statements=3,root_seals_source_only=True),mismatches=[],unverified_checks=['Operational guard tail and loaded physical callback state','Actual numeric/speed/peak/coding/DR/stability gates']),reviewer_actions=dict(HTTP_requests=0,native_invocations=0,GPU_actions=0,model_requests=0,resets=0),full_qualification=False)
    out=a.R/'TASK620-PRODUCTION-FINAL-SEAL-REVIEW.json';out.write_text(json.dumps(report,indent=2)+'\n');out.chmod(0o600)
    print(json.dumps(dict(receipt=str(out),sha256=a.sha(out.read_bytes()),final_readback_passed=True)))

if __name__=='__main__':main()

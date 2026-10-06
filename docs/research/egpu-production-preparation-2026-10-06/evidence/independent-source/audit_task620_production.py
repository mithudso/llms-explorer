#!/usr/bin/env python3
"""Source-only frozen production delta audit; no operational tail or service calls."""
import ast, copy, datetime, hashlib, json, os, stat, types
from pathlib import Path

B=Path('/Users/mitch/.cache/claude-egpu/experiments')
D=B/'qwen36-27b-downstream-preparation-v125'
P=D/'production'
R=B/'qwen36-27b-iq2-cold-capture-independent-review-20261006'
FREEZE='d90c9a31249a798dcde88f9bb4297185644873bfdda4619ec2faba2adda28f77'
OLD='84fdf276096e24c00651c92a1ffcd082bfec6691dd6278bf7c9a4ac63acbc511'
sha=lambda b:hashlib.sha256(b).hexdigest()

def private(p,expected):
    assert p.is_absolute() and p.resolve(strict=True)==p
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno())
        assert stat.S_ISREG(a.st_mode) and a.st_uid==501 and stat.S_IMODE(a.st_mode)==0o600 and 0<a.st_size<=16*1024**2
        raw=f.read(16*1024**2+1);z=os.fstat(f.fileno())
    key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    assert key(a)==key(z)==key(p.lstat()) and sha(raw)==expected
    return raw

def load(p,raw):
    m=types.ModuleType('independent_source_'+p.stem);m.__file__=str(p)
    exec(compile(raw,str(p),'exec'),m.__dict__)
    return m

def fn(raw,name):
    return next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef) and x.name==name)

def prefix(module,path,raw,name,count,ret):
    f=copy.deepcopy(fn(raw,name));f.body=f.body[:count]+[ast.Return(value=ast.Name(id=ret,ctx=ast.Load()))]
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('exchange','Popen','run','main') for n in ast.walk(f))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),str(path)+':pure-prefix','exec'),module.__dict__)

def main():
    at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    freeze=json.loads(private(D/'PRODUCTION-FREEZE.json',FREEZE))
    held={p:private(Path(p),h) for p,h in freeze['frozen_sources'].items()}
    assert len(held)==20 and freeze['native_invocations']==freeze['HTTP_requests']==0
    dp=P/'static-inputs/REVIEW-DRAFT.json';draft=json.loads(held[str(dp)])
    old=json.loads(private(B/'qwen36-27b-iq2-static-inputs-v124/INDEPENDENT-REVIEW.json',OLD))
    pins=draft['source_pins'];opins=old['source_pins']
    common=set(pins)&set(opins);added=set(pins)-set(opins);removed=set(opins)-set(pins)
    assert len(pins)==4752 and len(added)==16 and len(removed)==22
    assert all(pins[k]==opins[k] for k in common)
    assert all(k.startswith(str(P)+'/') for k in added)
    assert draft['external_source_bindings']==old['external_source_bindings'] and len(draft['external_source_bindings'])==1748
    assert draft['identity']==old['identity']
    rp=P/'renderer-preparation/experimental_27b.py';rb=held[str(rp)]
    r=load(rp,rb);fixture=copy.deepcopy(draft);fixture.update(passed=True,seal_pending=False)
    r.final_review(fixture)
    # Consume only the changed closure, reusing the independently accepted
    # unchanged v124 hashes/bindings instead of rehashing its model and archives.
    r.verify_pins({k:pins[k] for k in sorted(added)})
    stp=P/'startup-preparation/start_once.py';st=load(stp,held[str(stp)])
    ids=st.pin_identities({k:pins[k] for k in added},r)
    st.verify_pin_identities({k:pins[k] for k in added},r,ids)
    assert str(r.ROOT)==str(P/'renderer-preparation') and st.RUNTIME==P/'cold-runtime'
    # Exact source-plan structural prefix excludes its final all-pins rehash.
    prefix(r,rp,rb,'verify_source_plan',4,'pins')
    plans={}
    for part in ('renderer-preparation','startup-preparation'):
        pp=P/part/'SOURCE-PLAN.json';plan=json.loads(held[str(pp)])
        got=r.verify_source_plan(plan)
        assert got==plan['source_pins'] and all(pins.get(k)==v for k,v in got.items())
        plans[part]=dict(path=str(pp),sha256=sha(held[str(pp)]),pin_count=len(got),structural_prefix_statements=4)
    cfg=json.loads(held[str(P/'static-inputs/ROOT-CONFIG.json')])
    assert cfg['schema']=='qwen35-27b-root-startup-config-v1' and cfg['runtime_directory']==str(P/'cold-runtime')
    cp=P/'cold-root-operation/run_actual_cold_once.py';cm=load(cp,held[str(cp)])
    assert cm.STARTER==stp and cm.CONFIG==P/'static-inputs/ROOT-CONFIG.json' and cm.RUNTIME==st.RUNTIME
    cm.minimal_final_review(fixture)
    gp=P/'capture-response-preparation/guard_v125.py';gb=held[str(gp)];g=load(gp,gb)
    qp=P/'capture-response-preparation/PREPARATION-DRAFT.json';q=json.loads(held[str(qp)])
    assert q['version']==g.VERSION=='1.0.1' and q['capture_enabled'] is False and q['maximum_GPU_requests']==2
    assert q['CPU_capture_manifest']==draft['current_CPU_reference']
    assert g.RUNTIME==st.RUNTIME and g.OPERATION==cp.parent and g.OUTPUT==P/'capture-inference'
    assert g.ATOL==0.05 and g.TOKEN_COUNT==21
    oldgp=B/'qwen36-27b-iq2-capture-response-preparation-v124/guard_v124.py'
    oldgb=private(oldgp,opins[str(oldgp)])
    assert ast.dump(fn(gb,'compare_response'),include_attributes=False)==ast.dump(fn(oldgb,'compare_response'),include_attributes=False)
    # The final authorities do not exist. Exercise the canonical initial three
    # statements against in-memory final-form data, retaining real helper reads.
    qfixture=copy.deepcopy(q);qfixture.update(seal_pending=False,independent_review_pending=False,source_review_sha256=sha(json.dumps(fixture,sort_keys=True).encode()))
    qb=(json.dumps(qfixture,sort_keys=True)+'\n').encode();qsha=sha(qb)
    realread=g.read
    def fixture_read(p,expected=None,**kwargs):
        if p==g.PREP/'PREPARATION.json':
            assert expected==qsha
            return qb
        return realread(p,expected,**kwargs)
    g.read=fixture_read
    prefix(g,gp,gb,'verify_admission',3,'prep')
    assert g.verify_admission(qsha)==qfixture
    np=P/'capture-response-preparation/run_numeric.py';nb=held[str(np)];n=load(np,nb)
    assert n.GUARD_SHA==sha(gb) and n.load_guard().VERSION=='1.0.1'
    assert n.CPU_MANIFEST_SHA==q['CPU_capture_manifest']['sha256']
    assert 'save' in fn(nb,'evidence_snapshot').args.args[-1].arg
    nsrc=nb.decode();ssrc=held[str(stp)].decode()
    assert "witness_after['valid_kernel_stamps']>witness_before['valid_kernel_stamps'] and witness_after['compute_completed']>witness_before['compute_completed']" in nsrc
    assert 'env["LLMSX_PRECISION_CAPTURE_DIR"] =' not in ssrc and '(RUNTIME / "captures").mkdir' not in ssrc
    assert '1791277640:498901' in held[str(cp)].decode()
    assert not (P/'cold-runtime').exists() and not (P/'capture-inference').exists()
    assert not (P/'static-inputs/INDEPENDENT-REVIEW.json').exists() and not (g.PREP/'PREPARATION.json').exists()
    report=dict(agent='/root/cold_capture_review',definition_version='1.0.0',status='complete',observed_at=at,source_delta_ready=True,final_authority_readback_pending=True,
        evidence=[dict(source=str(D/'PRODUCTION-FREEZE.json'),observed_at=at,sha256=FREEZE,supported_claim='All20 exact frozen private files consumed;16 added actual renderer hash and starter identity/recheck consumers pass;4736 retained pins and1748 external bindings equal acceptedv124'),dict(source=str(qp),observed_at=at,sha256=sha(held[str(qp)]),supported_claim='Actual request schema1.0.1/helper-hash three-statement prefix accepts in-memory final-form fixture; final physical authority remains absent'),dict(source=str(np),observed_at=at,sha256=sha(nb),supported_claim='Held exact guard loaded; original all21/.05 comparator unchanged; capture absent and positive completed compute/stamps required')],
        changes=['Independent private audit script and receipt only'],remaining=['Actual root final static/request seals and exact readback','Frozen downstream source/closure review','Fresh root-admitted physical startup and original two native requests'],
        details=dict(surface='Frozen capture-disabled production startup and numerical source delta',acceptance_condition='Exact frozen schema/mode/path/source consumers; no inherited measured acceptance',source_revision=FREEZE,loaded_revision=None,process_or_origin='Candidate never invoked by reviewer; operational prefixes excluded',configuration_identity=draft['identity'],observations=dict(frozen_files=20,new_pins=16,retained_pins=len(common),removed_old_private_paths=22,external_bindings=1748,source_plans=plans,original_atol=.05,all_positions=21,CPU_reference=q['CPU_capture_manifest'],request_fixture_only=True),mismatches=[],unverified_checks=['Final root seal bytes/flags/readback','No full old closure rehash repeated: accepted unchanged closure reused','No physical/callback telemetry/numerical/performance/peak/coding/DR result']),reviewer_actions=dict(native_invocations=0,HTTP_requests=0,GPU_actions=0,model_requests=0,resets=0),full_qualification=False)
    out=R/'TASK620-PRODUCTION-SOURCE-REVIEW.json';out.write_text(json.dumps(report,indent=2)+'\n');out.chmod(0o600)
    print(json.dumps(dict(receipt=str(out),sha256=sha(out.read_bytes()),source_delta_ready=True,final_seal_pending=True)))

if __name__=='__main__':main()

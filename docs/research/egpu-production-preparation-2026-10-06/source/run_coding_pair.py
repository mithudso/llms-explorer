#!/opt/homebrew/bin/python3
"""Two fresh full-tool coding sessions; unchanged original acceptance functions."""
from pathlib import Path
import json,os,datetime as dt,time,sys
import sys,types,hashlib,stat
COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'
ROOT=Path(__file__).absolute().parent
VERIFIER=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/verify_egpu_coding.py')

def common():
    p=ROOT/'downstream_common.py'
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());raw=f.read(1024**2);b=os.fstat(f.fileno())
    key=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    if p.resolve(strict=True)!=p or a.st_uid!=501 or stat.S_IMODE(a.st_mode)!=0o600 or not stat.S_ISREG(a.st_mode) or key(a)!=key(b) or key(a)!=key(p.lstat()) or hashlib.sha256(raw).hexdigest()!=COMMON_SHA:raise ValueError('Bound private client helper changed')
    m=types.ModuleType('held_candidate_common');m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m

def main():
    os.umask(0o077)
    c=common();auth,review,startup,r=c.admission()
    output=ROOT/'execution/coding';c.require(not output.exists(),'Fresh coding receiver required')
    profile=c.load_source(VERIFIER.with_name('egpu_coding_profile.py'),review,r,'egpu_coding_profile')
    sys.modules['egpu_coding_profile']=profile
    verifier=c.load_source(VERIFIER,review,r,'held_original_full_coding_verifier')
    # The verifier's pure imported profile is byte-identical to the pinned maintained profile.
    verifier.ROOT=Path('/Users/mitch/dev/skills/ai-llm-model-layer/references/rtx5080-egpu-harness')
    env=c.environment(auth);c.require('PYTHONSAFEPATH' not in env,'Original coding CLI import environment required')
    output.mkdir(parents=True,mode=0o700)
    def save(n,v):
        with (output/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
        (output/n).chmod(0o600)
    save('CONSUMED.json',{'requested_runs':2,'native_starts':0,'gateway_starts':0,'retry':False,'started':dt.datetime.now(dt.timezone.utc).isoformat()})
    runs=[]
    for n in (1,2):
        c.passive_owner(startup)
        before=c.witness(startup)
        receipt=verifier.run_round(launcher=ROOT/'claude_candidate',model=c.ALIAS,output=output/f'run-{n}.json',timeout=900,context=32768,env=env,frontdoor=False)
        c.passive_owner(startup)
        after=c.witness(startup)
        fields=('valid_kernel_stamps','compute_completed','copy_completed','publication_sequence')
        d={k:after[k]-before[k] for k in fields}
        physical=d['valid_kernel_stamps']>0 and d['compute_completed']>0 and all(v>=0 for v in d.values())
        record={'n':n,'passed':receipt['passed'],'physical_completed_work_advanced':physical,'witness_deltas':d,'receipt':str(output/f'run-{n}.json')}
        save(f'run-{n}-ATTRIBUTION.json',record);runs.append(record)
        if not record['passed'] or not physical:break
    result={'version':'1.0.0','requested_runs':2,'passed_runs':sum(x['passed'] and x['physical_completed_work_advanced'] for x in runs),'coding_pair_passed':len(runs)==2 and all(x['passed'] and x['physical_completed_work_advanced'] for x in runs),'runs':runs,'native_starts':0,'resets':0,'full_qualification':False,'actual_peak_verified':False,'long_term_stability_verified':False,'repeatability_scope':'Two fresh sessions only; original verifier explicitly limits stability inference','candidate_binary_sha256':c.BINARY_SHA,'native_pid':startup['native_pid'],'boot_id':startup['boot_id']}
    save('RESULT.json',result);print(json.dumps(result,indent=2),flush=True)
    return 0 if result['coding_pair_passed'] else 1

if __name__=='__main__':raise SystemExit(main())

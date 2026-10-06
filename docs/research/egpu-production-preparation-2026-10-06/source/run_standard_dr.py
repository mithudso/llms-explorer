#!/opt/homebrew/bin/python3
"""Canonical five workers then existing full coordinator; no invented research."""
from pathlib import Path
import os,json,subprocess,time,datetime as dt
import sys,types,hashlib,stat
COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'
ROOT=Path(__file__).absolute().parent
HELPER=Path('/Users/mitch/.global-ai-hub/scripts/dr_run.py')

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
    c.require(auth.get('standard_dr_execution_authorized') is True,'Root research activation pending')
    coding=c.bound_document(auth['coding_review'])
    c.require(coding.get('passed') is True and coding.get('coding_runs')==2 and coding.get('binary_sha256')==c.BINARY_SHA and coding.get('native_pid')==startup['native_pid'] and coding.get('boot_id')==startup['boot_id'],'Fresh independently accepted same-owner coding pair required')
    plan=c.bound_document({'path':str(ROOT/'PLAN.json'),'sha256':review['source_pins'][str(ROOT/'PLAN.json')]})
    campaign=Path('/Users/mitch/.global-ai-hub/research')/plan['slug']
    c.require(not campaign.exists(),'Fresh candidate campaign required; never reset historical campaigns')
    out=ROOT/'execution/research';c.require(not out.exists(),'Fresh research receiver required')
    env=c.environment(auth)
    env.update(EGPU_RESEARCH_TIMEOUT='1740',EGPU_COORDINATOR_TIMEOUT='10800',EGPU_SITE_WORKTREE=auth['site_worktree'],EGPU_POST_WORKFLOW_RECEIVER=str(out))
    out.mkdir(parents=True,mode=0o700)
    def save(n,v):
        with (out/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
        (out/n).chmod(0o600)
    started=time.monotonic();rows=[]
    save('CONSUMED.json',{'original_trial_budget_minutes':150,'fresh_started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'clock_reset_allowed':False,'native_starts':0,'resets':0})
    def run(name,args,timeout=1800):
        c.passive_owner(startup);r.verify_pins(review['source_pins'])
        remaining=9000-(time.monotonic()-started);c.require(remaining>45,'Original campaign budget exhausted')
        stamp=time.monotonic()
        with (out/(name+'.stdout')).open('x') as so,(out/(name+'.stderr')).open('x') as se:
            try:
                p=subprocess.run(args,env=env,cwd=out,stdout=so,stderr=se,timeout=min(timeout,int(remaining)-10));returncode=p.returncode;error=None
            except subprocess.TimeoutExpired:
                returncode=None;error='Owned phase timeout; subprocess.run terminated only this CPU child, no model/backend restart'
        row={'phase':name,'argv':args,'returncode':returncode,'error':error,'elapsed_seconds':time.monotonic()-stamp,'stdout':str(out/(name+'.stdout')),'stderr':str(out/(name+'.stderr'))};save(name+'.json',row);rows.append(row)
        c.require(returncode==0,'Canonical phase failed; preserve state/no automatic retry');c.passive_owner(startup)
    result=None
    try:
        run('init',['/opt/homebrew/bin/python3','-B',str(HELPER),'init',plan['topic'],'--slug',plan['slug'],'--depth','standard','--concepts',','.join(plan['concepts'])],60)
        for i,concept in enumerate(plan['execution_order'],1):
            run('worker-'+str(i),['/opt/homebrew/bin/python3','-B',str(HELPER),'research',plan['slug'],'--concept',concept,'--model',c.ALIAS,'--effort','medium','--max-parallel','1','--max-turns','60','--agent-timeout','1800'])
        # The existing coordinator owns the canonical build/quality workflow. Its
        # complete prompt includes the current DR and SKO routes, not an abbreviated verdict.
        prompt=c.private_bytes(ROOT/'FULL-DR-POST-WORKFLOW.txt',review['source_pins'][str(ROOT/'FULL-DR-POST-WORKFLOW.txt')]).decode().replace('{slug}',plan['slug']).replace('{site_worktree}',auth['site_worktree']).replace('{model}',c.ALIAS)
        prompt_path=out/'POST-WORKFLOW.txt';prompt_path.write_text(prompt);prompt_path.chmod(0o600)
        run('post-research-coordinator',[str(ROOT/'egpu_research_agent'),'-p',prompt,'--model',c.ALIAS,'--effort','high','--max-turns','120','--output-format','json'],int(9000-(time.monotonic()-started)))
        # Mechanical receipts do not establish semantic acceptance. Root's independent
        # review must bind actual claim/read/source/quotes, full SKO and both trees.
        manifest=json.loads((campaign/'manifest.json').read_text())
        gate=json.loads((campaign/'gate.json').read_text())
        c.require([x['name'] for x in manifest['concepts']]==plan['concepts'] and all(x['status']=='done' for x in manifest['concepts']),'Original five claims were not published')
        c.require(gate.get('sampled')==10 and len(gate.get('verdicts',[]))==10 and all(x['verdict']=='SUPPORTED' for x in gate['verdicts']),'Blind10 source gate remains incomplete or dissenting')
        c.require(manifest.get('install_path') and Path(manifest['install_path']).is_file(),'Canonical install missing')
        result={'version':'1.0.0','phases':rows,'campaign':str(campaign),'source_only_prep':False,'actual_started_at':manifest.get('started'),'actual_elapsed_seconds':time.monotonic()-started,'native_starts':0,'resets':0,'candidate_binary_sha256':c.BINARY_SHA,'native_pid':startup['native_pid'],'boot_id':startup['boot_id'],'canonical_exit_status':manifest.get('exit_status'),'registry_status':'REGISTRY-UNAVAILABLE: indexing/embeddings remain paused','standard_dr_accepted':False,'full_sko_accepted':False,'both_trees_independently_verified':False,'full_qualification':False,'remaining':['Independent full claims/read/source/quotes/origin/blind10/refetch15 audit','Actual full SKO15-pass/convergence/evals/fresh-context blind-audit and deterministic receipt review','Both tree read-back and site CI/publication','Registry build/route after explicit pause-resume authorization','Physical peak/placement/long-term stability']}
    except Exception as error:
        result={'version':'1.0.0','phases':rows,'campaign':str(campaign),'native_starts':0,'resets':0,'errors':[type(error).__name__+': '+str(error)],'standard_dr_accepted':False,'full_sko_accepted':False,'full_qualification':False,'registry_status':'REGISTRY-UNAVAILABLE: indexing/embeddings remain paused','remaining':['Inspect exact retained phase/canonical campaign; no automatic retry'] }
    save('RESULT.json',result);print(json.dumps(result,indent=2),flush=True)
    # An actual run with deferred registry cannot claim complete standard qualification.
    return 2

if __name__=='__main__':raise SystemExit(main())

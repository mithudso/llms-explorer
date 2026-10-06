"""Focused fresh adapter/pending-admission controls; zero process, HTTP or model calls."""
from pathlib import Path
import ast,copy,hashlib,json,types,os,tempfile
R=Path(__file__).absolute().parent;checks=[]
def ok(name,v):assert v,name;checks.append({'name':name,'passed':True})
def held(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
c=held(R/'downstream_common.py','test_common');client=held(R/'claude_candidate.py','test_client')
review=json.loads((R/'DOWNSTREAM-REVIEW-DRAFT.json').read_bytes());r=c.renderer();r.configure_source_bindings(review)
for p in R.iterdir():
 if p.is_file() and (p.suffix=='.py' or p.name in ('claude_candidate','egpu_research_agent','litellm_gateway')):
  compile(p.read_bytes(),str(p),'exec')
  if str(p) in review['source_pins']:r.verified_file(str(p),review['source_pins'][str(p)])
ok('actual fresh helper hash/mode consumers',True)
# New root gate refuses before any passive subprocess/HTTP or source activation.
c.observe=lambda a:(_ for _ in ()).throw(AssertionError('Unexpected operational observation'))
c.passive_owner=lambda s:(_ for _ in ()).throw(AssertionError('Unexpected physical owner observation'))
try:c.admission({})
except ValueError as e:ok('missing exact activation refused before observations','authority' in str(e))
else:raise AssertionError('Missing activation admitted')
a={'actual':False,'root_authorized':False,'seal_pending':True}
c.private_bytes=lambda p,s:json.dumps(a).encode()
try:c.admission({'EGPU_DOWNSTREAM_AUTHORITY':str(R/'ROOT-ACTIVATION.json'),'EGPU_DOWNSTREAM_AUTHORITY_SHA256':'0'*64})
except ValueError as e:ok('pending actual identity/numerical authority refused','pending' in str(e))
else:raise AssertionError('Pending authority admitted')
try:c.parse(b'{"x":1e999}')
except ValueError:ok('actual authority parser rejects overflow nonfinite',True)
else:raise AssertionError('Infinite authority admitted')
# Preserve original argument consumer itself. Only closure hashing and actual
# owner observers are stubbed for this CPU-only argument test, never qualified.
profile=held(Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/egpu_coding_profile.py'),'held_profile')
ok('original23 coding schemas unchanged',len(profile.FULL_CODING_TOOLS)==23)
rr=held(R/'downstream_common.py','fresh_renderer_common').renderer();rr.configure_source_bindings(review);rr.verify_pins=lambda p:None
cc=held(R/'downstream_common.py','argument_common')
cc.admission=lambda env:(None,review,{},rr);cc.passive_owner=lambda s:True
client.common=lambda:cc
coding=profile.coding_arguments(bounded_context=True)+['-p','Implement real work','--model',c.ALIAS,'--output-format','json']
inv=client.prepare(coding,{})
ok('actual candidate consumes exact original full23 prefix',inv['mode']=='coding' and inv['env']['ANTHROPIC_BASE_URL']==c.GATEWAY)
ok('full background schemas/capabilities preserved',inv['env'].get('CLAUDE_CODE_DISABLE_BACKGROUND_TASKS','0') in ('0','false','') and inv['env']['CLAUDE_CODE_MODEL_CAPABILITIES'].startswith(c.ALIAS+'='))
ok('copied coding summary instruction follows original system value','After Bash reports' in inv['argv'][inv['argv'].index('--system-prompt')+1])
try:client.prepare(coding,{'EGPU_RESEARCH_GATEWAY':'http://127.0.0.1:14010'})
except ValueError:ok('old gateway route rejected by original validator',True)
else:raise AssertionError('Old route accepted')
bad=coding.copy();bad[bad.index('--tools')+1]='Read,Write'
try:client.prepare(bad,{})
except ValueError:ok('slimmed coding tools refused',True)
else:raise AssertionError('Slim tools admitted')
bad=coding.copy();bad[bad.index('--model')+1]='qwen3.5:27b-iq2-xxs'
try:client.prepare(bad,{})
except ValueError:ok('old candidate refused',True)
else:raise AssertionError('Wrong candidate admitted')
# Canonical MCP path may be written only in this owned source-test fixture; no relay starts.
fixture=R/'prefix-control-fixture';fixture.mkdir(mode=0o700,exist_ok=True)
p=fixture/'mcp.json';relay='/Users/mitch/dev/llms-explorer/llmsx'
proto=held(R/'protocol_client.py','original_protocol_shape')
p.write_text(json.dumps({'mcpServers':{'firecrawl':{'command':str(proto.RELAY_PYTHON),'args':[str(R/'egpu_retrieval_proxy.py')],'env':{'PYTHONPATH':relay,'PYTHONSAFEPATH':'1','PYTHONDONTWRITEBYTECODE':'1'}}}}));p.chmod(0o600)
for tools in ('Read','Read,Write','Bash,Read,Write,Edit'):
 args=['--model',c.ALIAS,'--setting-sources','','--settings',json.dumps({'disableAllHooks':True,'autoCompactEnabled':True,'bashOutputMaxChars':8000}),'--disable-slash-commands','--exclude-dynamic-system-prompt-sections','--strict-mcp-config','--mcp-config',str(p),'--tools',tools,'--system-prompt','Canonical phase text','-p','canonical input','--output-format','json']
 inv=client.prepare(args,{'EGPU_LLMSX_SOURCE':relay,'PYTHONPATH':relay})
 ok('original research validator '+tools,inv['mode']=='research' and inv['env']['ANTHROPIC_BASE_URL']==c.GATEWAY)
 text=inv['argv'][inv['argv'].index('--system-prompt')+1]
 guide=json.loads((R/'CLIENT-GUIDANCE.json').read_bytes())
 ok('literal issued quote rule only worker '+tools,(guide['EVIDENCE_RULE'] in text)==(tools=='Read'))
for alias in review['runtime_alias_bindings']:
 cc.runtime_alias(alias,review,rr)
ok('actual runtime/resource alias consumers',True)
ok('all future receivers/root activation absent',all(not (R/p).exists() for p in ('ROOT-ACTIVATION.json','execution','production/cold-runtime','production/capture-inference')))
ok('callback bound held before gateway CLI import',"sys.modules[name]=c.load_source" in (R/'litellm_gateway').read_text())
ok('gateway listener PID binding required',"Gateway listener differs from admitted child" in (R/'downstream_common.py').read_text() and 'Gateway metadata listener differs' in (R/'start_gateway.py').read_text())
ok('full canonical workflow references15pass/fullblind/nosync',all(s in (R/'FULL-DR-POST-WORKFLOW.txt').read_text() for s in ('A-O','--no-sync','fresh-context blind','--sample 10 --refetch-cap 15','REGISTRY-UNAVAILABLE')))
result={'version':'1.0.0','passed':True,'count':len(checks),'checks':checks,'scope':'Focused new source adapter/prefix consumers; argument-only stubs do not provide physical or source-closure qualification','subprocesses':0,'HTTP_requests':0,'native_invocations':0,'model_requests':0}
p=R/'DOWNSTREAM-PREFIX-CONTROLS.json';p.write_text(json.dumps(result,indent=2)+'\n');p.chmod(0o600);print(json.dumps({'passed':True,'count':len(checks),'path':str(p)}))

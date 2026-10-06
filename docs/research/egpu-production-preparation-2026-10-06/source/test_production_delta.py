"""Focused source-only delta checks. No operational entrypoints or HTTP calls."""
from pathlib import Path
import ast,hashlib,json,types,os
R=Path(__file__).absolute().parent;P=R/'production';OLD=R.parent
checks=[]
def ok(name,value):
 assert value,name;checks.append({'name':name,'passed':True})
def code(p):return ast.parse(p.read_bytes())
def function(p,name):
 return ast.dump(next(x for x in code(p).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==name),include_attributes=False)
def module(p):
 m=types.ModuleType('held_control');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
renderer=module(P/'renderer-preparation/experimental_27b.py')
new=module(P/'capture-response-preparation/guard_v125.py')
old=OLD/'qwen36-27b-iq2-capture-response-preparation-v124/guard_v124.py'
ok('unchanged original all21 .05 comparator',function(old,'compare_response')==function(P/'capture-response-preparation/guard_v125.py','compare_response') and new.ATOL==.05 and new.TOKEN_COUNT==21)
startup=(P/'startup-preparation/start_once.py').read_text()
ok('capture environment assignments removed', 'env["LLMSX_PRECISION_CAPTURE_DIR"] =' not in startup and '(RUNTIME / "captures").mkdir' not in startup)
for env in ({},{'LLMSX_PRECISION_CAPTURE_DIR':''},{'LLMSX_PRECISION_CAPTURE_DIR':'/tmp/forbidden'}):
 node=next(x for x in ast.walk(code(P/'startup-preparation/start_once.py')) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require' and 'Capture environment key must be absent' in ast.unparse(x))
 cond=ast.Expression(node.args[0]);result=eval(compile(cond,'<actual consuming capture predicate>','eval'),{'os':types.SimpleNamespace(environ=env),'env':env})
 ok('actual capture predicate '+repr(env),result==(not bool(env)))
fixture=P/'control-fixture';fixture.mkdir(mode=0o700,exist_ok=True)
p=fixture/'helper.py';p.write_bytes(b'VALUE=1\n');p.chmod(0o600);sha=hashlib.sha256(p.read_bytes()).hexdigest()
renderer.verified_file(str(p),sha);ok('new production helper0600 actual consumer accepted',True)
p.chmod(0o644)
try:renderer.verified_file(str(p),sha)
except renderer.Refusal as e:ok('new production helper0644 actual consumer refused','private' in str(e).lower() or 'permission' in str(e).lower())
else:raise AssertionError('0644 helper admitted')
p.chmod(0o600)
num=module(P/'capture-response-preparation/run_numeric.py');fake=types.SimpleNamespace()
fake.RUNTIME=P/'never-created-runtime';fake.read=lambda path,**kwargs: b'' if path.name=='native.log' else json.dumps({'pid':9,'session':'s','boot_id':'1:2','model_sha256':'m','build_sha256':'b','physical_device':True,'valid_kernel_stamps':1,'compute_completed':1,'copy_completed':1,'compute_submitted':1,'copy_submitted':1,'publication_sequence':1}).encode()
fake.require=new.require;fake.parse=json.loads;fake.digest=lambda raw:hashlib.sha256(raw).hexdigest();num.g=fake
saved=[];s={'native_pid':9,'boot_id':'1:2','witness':{'path':str(fake.RUNTIME/'state/witness/s.json'),'session':'s','model_sha256':'m','build_sha256':'b'}}
w=num.evidence_snapshot('mock',s,lambda name,value:saved.append(name))
ok('actual evidence snapshot explicit save callback',len(saved)==3 and w['compute_completed']==1)
ok('positive compute/stamp source admission',"witness_after['valid_kernel_stamps']>witness_before['valid_kernel_stamps'] and witness_after['compute_completed']>witness_before['compute_completed']" in (P/'capture-response-preparation/run_numeric.py').read_text())
ok('runtime/numeric receiver remain absent',not (P/'cold-runtime').exists() and not (P/'capture-inference').exists())
for part in ('renderer-preparation','startup-preparation'):
 d=json.loads((P/part/'SOURCE-PLAN.json').read_bytes());ok(part+' planned sources preserved',bool(d['source_pins']))
for p in P.rglob('*.py'):compile(p.read_bytes(),str(p),'exec')
result={'version':'1.0.0','passed':True,'checks':checks,'count':len(checks),'scope':'New source-only consuming delta controls; unchanged tests not rerun','native_starts':0,'GPU_requests':0,'HTTP_requests':0}
q=R/'PRODUCTION-DELTA-CONTROLS.json';q.write_text(json.dumps(result,indent=2)+'\n');q.chmod(0o600);print(json.dumps({'passed':True,'count':len(checks),'receipt':str(q)}))

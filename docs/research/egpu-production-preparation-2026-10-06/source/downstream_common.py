"""Small private authority/client binding layer; no service lifecycle or inference."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,types,re,socket,math
ROOT=Path(__file__).absolute().parent
ALIAS='qwen3.6:27b-iq2-xxs'
PROFILE='qwen36-27b-iq2-reasoning-1024'
GATEWAY='http://127.0.0.1:14139'
RUNTIME=ROOT/'production/cold-runtime'
BINARY='/Users/mitch/.cache/claude-egpu/experiments/qwen36-27b-iq2-small-prefill-global-scratch-build-v121/gpu-server-capture-small-prefill-global-scratch'
BINARY_SHA='c1fb382b5557f3dabdb76241f9ee2f9167e87eac208878f23116a34cbf6d19d9'
MODEL_SHA='17021537cebf7c9750efd5413e5f3d1c4cbe4282798cb92a2201b25674d39688'
RENDERER=ROOT/'production/renderer-preparation/experimental_27b.py'
RENDERER_SHA='3cedb4efa602242eef405c4c179c372e8be29871f8a50e6a0c9ba45422512157'

def require(v,m):
    if not v:raise ValueError(m)

def private_bytes(p,expected):
    require(p.is_absolute() and p.resolve(strict=True)==p,'Canonical private authority required')
    require(type(expected) is str and re.fullmatch('[0-9a-f]{64}',expected),'Exact authority SHA required')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());require(stat.S_ISREG(a.st_mode) and a.st_uid==501 and stat.S_IMODE(a.st_mode)==0o600 and 0<a.st_size<=16*1024**2,'Private UID501/0600 bounded authority required')
        raw=f.read(16*1024**2+1);b=os.fstat(f.fileno())
    key=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    require(key(a)==key(b)==key(p.lstat()) and hashlib.sha256(raw).hexdigest()==expected,'Authority/source changed during read')
    return raw

def parse(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "Duplicate JSON key")
            out[key] = value
        return out

    def constant(_value):
        raise Refusal("Nonfinite JSON constant")

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        require(depth <= 64, "Excessive JSON nesting")
        if type(item) is float:
            require(math.isfinite(item), "Nonfinite JSON number")
        elif type(item) is dict:
            pending.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            pending.extend((v, depth + 1) for v in item)
    return value

def bound_document(binding):
    require(type(binding) is dict and set(binding)=={'path','sha256'},'Exact path/SHA binding required')
    return parse(private_bytes(Path(binding['path']),binding['sha256']))

def renderer():
    m=types.ModuleType('held_downstream_renderer');m.__file__=str(RENDERER)
    exec(compile(private_bytes(RENDERER,RENDERER_SHA),str(RENDERER),'exec'),m.__dict__);return m

def admission(environ=None,require_gateway=True):
    env=dict(os.environ if environ is None else environ)
    p=Path(env.get('EGPU_DOWNSTREAM_AUTHORITY',''))
    require(p==ROOT/'ROOT-ACTIVATION.json','Exact downstream root authority required')
    auth=parse(private_bytes(p,env.get('EGPU_DOWNSTREAM_AUTHORITY_SHA256','')))
    require(auth.get('actual') is True and auth.get('root_authorized') is True and auth.get('seal_pending') is False,'Observed root activation remains pending')
    require(auth.get('identity')=={'alias':ALIAS,'binary_path':BINARY,'binary_sha256':BINARY_SHA,'model_sha256':MODEL_SHA,'context':32768,'kv_type':'f16','batch':256,'ubatch':256,'slots':1},'Exact candidate/resource identity required')
    review=bound_document(auth['source_review']);require(review.get('passed') is True and review.get('seal_pending') is False,'Independent downstream source review pending')
    r=renderer();r.final_review(review);r.verify_pins(review['source_pins'])
    global ACTIVE_REVIEW, ACTIVE_RENDERER, GUARD
    ACTIVE_REVIEW,ACTIVE_RENDERER=review,r
    GUARD=load_source(ROOT/'production/capture-response-preparation/guard_v125.py',review,r,'held_downstream_mutable_read')
    startup=bound_document(auth['startup'])
    require(auth['startup']['path']==str(RUNTIME/'RESULT.json'),'Fresh production receiver binding required')
    require(startup.get('passed') is True and startup.get('errors')==[] and startup.get('capture_scheduler_arm') is False and startup.get('capture_environment_absent') is True,'Capture-disabled accepted startup required')
    require('LLMSX_PRECISION_CAPTURE_DIR' not in env,'Capture key must be absent, not empty')
    require(startup.get('native_argv',[None])[0]==BINARY and startup.get('native_start_attempts')==startup.get('transport_start_attempts')==1,'Native candidate/single-start identity differs')
    numeric=bound_document(auth['numerical_result']);nr=bound_document(auth['numerical_review'])
    require(auth['numerical_result']['path']==str(ROOT/'production/capture-inference/RESULT.json'),'Fresh original numerical receiver required')
    require(numeric.get('numerical_passed') is True and numeric.get('GPU_requests')==2 and numeric.get('errors')==[] and numeric.get('original_atol')==0.05 and numeric.get('capture_enabled') is False,'Original numerical pair remains unaccepted')
    require(nr.get('passed') is True and nr.get('numerical_result')==auth['numerical_result'] and nr.get('binary_sha256')==BINARY_SHA and nr.get('native_pid')==startup['native_pid'] and nr.get('boot_id')==startup['boot_id'],'Independent numerical acceptance/session binding required')
    require(auth.get('numerical_acceptance') is True,'Root numerical acceptance pending')
    passive_owner(startup)
    if require_gateway:
        gw=bound_document(auth['gateway'])
        require(gw.get('alias')==ALIAS and gw.get('profile')==PROFILE and gw.get('port')==14139 and gw.get('startup_sha256')==auth['startup']['sha256'],'Candidate gateway not admitted')
        require(observe(['/bin/ps','-p',str(gw['pid']),'-o','lstart=,uid=,command=']).strip()==gw['identity'],'Gateway owner changed')
        require(set(re.findall(r'^p(\d+)$',observe(['/usr/sbin/lsof','-nP','-iTCP:14139','-sTCP:LISTEN','-Fp']),re.M))=={str(gw['pid'])},'Gateway listener differs from admitted child')
    return auth,review,startup,r

def observe(argv):
    require(argv[0] in ACTIVE_REVIEW['source_pins'],'Passive executable absent from reviewed closure')
    ACTIVE_RENDERER.verified_file(argv[0],ACTIVE_REVIEW['source_pins'][argv[0]])
    p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
    require(p.returncode==0 and not p.stderr.strip(),'Passive owner observation failed');return p.stdout

def passive_owner(s):
    boot=observe(['/usr/sbin/sysctl','-n','kern.boottime'])
    values=re.search(r'sec\s*=\s*(\d+),\s*usec\s*=\s*(\d+)',boot)
    require(values and ':'.join(values.groups())==s['boot_id'],'Physical boot changed')
    for pid,key in [(s['native_pid'],'native_birth_uid_command'),(s['driver']['pid'],'driver_birth_uid_command')]:
        require(observe(['/bin/ps','-p',str(pid),'-o','lstart=,uid=,command=']).strip()==s[key],'Native/driver identity changed')
    require(set(re.findall(r'^p(\d+)$',observe(['/usr/sbin/lsof','-nP','-iTCP:8000','-sTCP:LISTEN','-Fp']),re.M))=={str(s['native_pid'])},'Native listener owner changed')
    fault=Path('/Users/mitch/.cache/claude-egpu/gpu-fault.json')
    if fault.exists() or fault.is_symlink():
        marker=GUARD.parse(GUARD.read(fault));require(type(marker.get('boot_id')) is str and re.fullmatch(r'\d+:\d+',marker['boot_id']),'Fault boot malformed')
        require(marker['boot_id']!=s['boot_id'],'Current boot fault latched')
    return True

def load_source(path,review,r,name):
    path=Path(path);require(str(path) in review['source_pins'],'Executed source absent from reviewed closure')
    raw=r.verified_file(str(path),review['source_pins'][str(path)],private=str(path).startswith(str(ROOT)),limit=1024**2)['data']
    m=types.ModuleType(name);m.__file__=str(path)
    exec(compile(raw,str(path),'exec'),m.__dict__);return m

def environment(auth):
    key=private_bytes(Path(auth['gateway_key']['path']),auth['gateway_key']['sha256']).decode()
    require(key and not any(c in key for c in '\r\n\0'),'Invalid private gateway credential')
    env={k:os.environ[k] for k in ('HOME','USER','LOGNAME','PATH','LANG','EGPU_DOWNSTREAM_AUTHORITY','EGPU_DOWNSTREAM_AUTHORITY_SHA256') if k in os.environ}
    env.update(EGPU_HARNESS_DIR='/Users/mitch/dev/skills/ai-llm-model-layer/references/rtx5080-egpu-harness',EGPU_RUNTIME='macuda',EGPU_STATE_DIR=str(RUNTIME/'state'),EGPU_MAX_CONTEXT='32768',TINY_PORT='8000',LITELLM_PORT='14139',EGPU_GENERATION_PROFILE=PROFILE,EGPU_TOOL_DESCRIPTION_PROFILE='compact-v1',EGPU_TINYGRAD_API_BASE='http://127.0.0.1:8000/v1',EGPU_RESEARCH_MODEL=ALIAS,EGPU_RESEARCH_GATEWAY=GATEWAY,EGPU_CLAUDE_BIN=str(ROOT/'claude_candidate'),DR_CLAUDE_BIN=str(ROOT/'egpu_research_agent'),EGPU_LLMSX_SOURCE='/Users/mitch/dev/llms-explorer/llmsx',EGPU_RESEARCH_HOME=str(ROOT/'execution/research-home'),EGPU_RESEARCH_MCP_SOURCE='/Users/mitch/.llmsx/ollama-mcp.json',EGPU_LITELLM_KEY=key,PYTHONDONTWRITEBYTECODE='1',HUB_DIR='/Users/mitch/.global-ai-hub')
    return env

def witness(startup):
    path=Path(startup['witness']['path'])
    require(path==RUNTIME/'state/witness'/(startup['witness']['session']+'.json'),'Witness path differs')
    raw=GUARD.read(path);w=GUARD.parse(raw)
    expected={'pid':startup['native_pid'],'session':startup['witness']['session'],'boot_id':startup['boot_id'],'model_sha256':startup['witness']['model_sha256'],'build_sha256':startup['witness']['build_sha256']}
    require(all(w.get(k)==v for k,v in expected.items()) and w.get('physical_device') is True,'Completed witness identity differs')
    for k in ('valid_kernel_stamps','compute_completed','copy_completed','compute_submitted','copy_submitted','publication_sequence'):
        require(type(w.get(k)) is int and w[k]>=0,'Witness counter malformed')
    require(w['compute_completed']<=w['compute_submitted'] and w['copy_completed']<=w['copy_submitted'],'Witness completion exceeds submission')
    return w

def runtime_alias(path,review,r):
    b=review['runtime_alias_bindings'][path]
    canonical,aliases=r.alias_chain(path)
    require(canonical==b['canonical'] and aliases==b['aliases'],'Runtime alias retargeted')
    require(r.metadata(Path(canonical).lstat())==b['metadata'],'Runtime target metadata changed')
    require(review['source_pins'][canonical]==b['sha256'],'Runtime target absent from exact source closure')
    r.verified_file(canonical,b['sha256'])
    return b

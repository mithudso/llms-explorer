#!/opt/homebrew/bin/python3
"""One separately authorized CPU LiteLLM gateway; no native lifecycle."""
from pathlib import Path
import os,json,secrets,socket,subprocess,time,urllib.request
import sys,types,hashlib,stat
COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'
ROOT=Path(__file__).absolute().parent

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
    c=common();auth,review,startup,r=c.admission(require_gateway=False)
    c.require(auth.get('gateway_start_authorized') is True,'Root gateway start authorization pending')
    out=ROOT/'execution/gateway';c.require(not out.exists(),'Gateway receiver consumed')
    with socket.socket() as s:s.bind(('127.0.0.1',14139))
    gateway=c.load_source(ROOT/'reasoning_gateway.py',review,r,'held_gateway_config')
    env=gateway.gateway_environment({k:os.environ[k] for k in ['HOME','USER','LOGNAME','PATH','LANG','EGPU_DOWNSTREAM_AUTHORITY','EGPU_DOWNSTREAM_AUTHORITY_SHA256'] if k in os.environ})
    key='sk-local-'+secrets.token_hex(24)
    out.mkdir(parents=True,mode=0o700)
    def save(name,value):
        raw=value if isinstance(value,str) else json.dumps(value,indent=2)+'\n'
        with (out/name).open('x') as f:f.write(raw)
        (out/name).chmod(0o600)
    save('gateway-key.bin',key);save('gateway-config.json',gateway.gateway_config(key))
    argv=['/Users/mitch/.local/pipx/venvs/litellm/bin/python','-B',str(ROOT/'litellm_gateway'),'--config',str(out/'gateway-config.json'),'--host','127.0.0.1','--port','14139']
    save('CONSUMED.json',{'gateway_start_attempts':1,'native_starts':0,'retry':False,'argv':argv})
    r.verify_pins(review['source_pins'])
    c.runtime_alias(argv[0],review,r)
    with (out/'gateway.log').open('x') as f:p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=f,stderr=f,start_new_session=True)
    started=time.monotonic()
    while True:
        c.require(p.poll() is None and time.monotonic()-started<60,'Gateway exited or timed out; preserve child/no retry')
        try:
            req=urllib.request.Request(c.GATEWAY+'/v1/models',headers={'Authorization':'Bearer '+key})
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),c.GUARD.NoRedirect())
            with opener.open(req,timeout=2) as response:
                c.require(response.status==200,'Gateway metadata status differs')
                raw=response.read(1024**2+1);c.require(len(raw)<=1024**2,'Gateway metadata too large');metadata=c.parse(raw)
            if any(x['id']==c.ALIAS for x in metadata['data']):break
        except Exception:pass
        time.sleep(.25)
    c.passive_owner(startup)
    c.require(set(c.re.findall(r'^p(\d+)$',c.observe(['/usr/sbin/lsof','-nP','-iTCP:14139','-sTCP:LISTEN','-Fp']),c.re.M))=={str(p.pid)},'Gateway metadata listener differs from owned child')
    save('GATEWAY.json',{'pid':p.pid,'identity':c.observe(['/bin/ps','-p',str(p.pid),'-o','lstart=,uid=,command=']).strip(),'alias':c.ALIAS,'profile':c.PROFILE,'port':14139,'startup_sha256':auth['startup']['sha256'],'model_calls':0,'production_ready':False})
    print(json.dumps({'gateway_pid':p.pid,'native_starts':0,'model_calls':0,'ready_seconds':time.monotonic()-started}),flush=True)

if __name__=='__main__':main()

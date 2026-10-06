from pathlib import Path
import os,sys,types,hashlib,stat
ROOT=Path(__file__).absolute().parent
COMMON_SHA='bb144de159e83520305a37528697a70273a2fdbbcac539e55e612f6dd4ac1d6b'

def common():
    p=ROOT/'downstream_common.py'
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as f:
        a=os.fstat(f.fileno());raw=f.read(1024**2);b=os.fstat(f.fileno())
    key=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
    if p.resolve(strict=True)!=p or a.st_uid!=501 or stat.S_IMODE(a.st_mode)!=0o600 or not stat.S_ISREG(a.st_mode) or key(a)!=key(b) or key(a)!=key(p.lstat()) or hashlib.sha256(raw).hexdigest()!=COMMON_SHA:raise ValueError('Bound private client helper changed')
    m=types.ModuleType('held_candidate_common');m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m

def owner_check():
    c=common();auth,review,startup,r=c.admission()
    path=c.RUNTIME/'state/macuda.json';state=c.GUARD.parse(c.GUARD.read(path))
    expected={'pid':startup['native_pid'],'boot_id':startup['boot_id'],'model_sha256':c.MODEL_SHA,'binary_sha256':c.BINARY_SHA,'command':startup['native_argv'],'driver':startup['driver'],'owner_lock':startup['owner_lock'],'witness':startup['witness'],'log':str(c.RUNTIME/'native.log')}
    c.require(all(state.get(k)==v for k,v in expected.items()),'Exact admitted runtime state differs')
    c.witness(startup);c.passive_owner(startup)
    return {**state,'alias':c.ALIAS,'context':32768}

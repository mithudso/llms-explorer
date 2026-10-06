#!/opt/homebrew/bin/python3
"""Exact local client: reuse argument validators; never start a backend."""
from pathlib import Path
import os,sys,types,hashlib,json,stat
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

def prepare(args,environ):
    c=common();auth,review,startup,r=c.admission(environ)
    protocol=c.load_source(ROOT/'protocol_client.py',review,r,'held_original_protocol')
    profile_path=Path('/Users/mitch/.cache/claude-egpu/experiments/qwen35-9b-admission/coding-summary-prompt-v109/egpu_coding_profile.py')
    profile=c.load_source(profile_path,review,r,'held_original_coding_profile')
    protocol.ROOT=Path('/Users/mitch/dev/skills/ai-llm-model-layer/references/rtx5080-egpu-harness')
    protocol.ALIAS=c.ALIAS;protocol.PROFILE=c.PROFILE
    protocol.CANDIDATE=ROOT/'claude_candidate';protocol.ADAPTER=ROOT/'egpu_research_agent'
    protocol.TYPED_RELAY=ROOT/'egpu_retrieval_proxy.py'
    protocol.CLAUDE=Path('/Users/mitch/.cache/claude-egpu/experiments/egpu-pinned-client-2.1.286-v100/claude')
    protocol.load_coding_profile=lambda:profile
    protocol.verify_source_pins=lambda:r.verify_pins(review['source_pins'])
    protocol.CLIENT_CAPS={**protocol.CLIENT_CAPS,'CLAUDE_CODE_MODEL_CAPABILITIES':c.ALIAS+'=-adaptive_thinking,-mid_conv_system'}
    protocol.ROUTE_PINS={**protocol.ROUTE_PINS,'EGPU_HARNESS_DIR':str(protocol.ROOT),'EGPU_GENERATION_PROFILE':c.PROFILE,'EGPU_RESEARCH_MODEL':c.ALIAS,'EGPU_RESEARCH_GATEWAY':c.GATEWAY,'LITELLM_PORT':'14139','EGPU_CLAUDE_BIN':str(protocol.CANDIDATE),'DR_CLAUDE_BIN':str(protocol.ADAPTER)}
    invocation=protocol.prepare_invocation(args,environ)
    invocation['env']['ANTHROPIC_BASE_URL']=c.GATEWAY
    c.require(not protocol.one_value(invocation['argv'][1:],'--system-prompt')[2],'Separate original system-prompt argument required')
    system=protocol.one_value(invocation['argv'][1:],'--system-prompt')[0]+2
    if invocation['mode']=='coding':
        invocation['argv'][system]+='\nAfter Bash reports the final passing aggregate unittest run, copy that actual count into SUMMARY.md as exactly one plain line Ran N tests followed by OK. Do not invent or separately total original/regression counts. Complete actual tools/tests first.'
    else:
        guidance=c.bound_document({'path':str(ROOT/'CLIENT-GUIDANCE.json'),'sha256':review['source_pins'][str(ROOT/'CLIENT-GUIDANCE.json')]})
        old='Optional evidence_quotes is unnecessary here. Omit it from this submission.'
        text=invocation['argv'][system]
        if old in text:
            c.require(text.count(old)==1,'Quote instruction source changed')
            text=text.replace(old,'Follow the declared literal-evidence instruction below. The original quote schema and checker remain unchanged.')
        text+='\n\n'+guidance['XML_RULE']
        tools=protocol.one_value(invocation['argv'][1:],'--tools')[1]
        if tools=='Read':text+='\n\n'+guidance['EVIDENCE_RULE']
        invocation['argv'][system]=text
    c.passive_owner(startup)
    return invocation

def main():
    invocation=prepare(sys.argv[1:],os.environ)
    # prepare_invocation returns historical service commands as data. Never run them.
    os.execve(invocation['argv'][0],invocation['argv'],invocation['env'])

if __name__=='__main__':main()

"""Force exact blind-gate grammar until canonical ten-verdict handoff is saved."""
from research_tool_choice import payloads
NAMES={'Read','Write','mcp__firecrawl__firecrawl_search','mcp__firecrawl__firecrawl_scrape','mcp__firecrawl__read_source','mcp__firecrawl__record_verdict'}
def complete(p):
 return p.get('saved') is True and type(p.get('sampled')) is int and p['sampled']==10 and type(p.get('required_sample')) is int and p['required_sample']==10 and type(p.get('remaining')) is int and p['remaining']==0 and p.get('missing')=={}
def matched(messages,anthropic):
 calls={}
 for m in messages:
  if anthropic:
   items=m.get('content',[])
   if not isinstance(items,list):continue
   for x in items:
    if not isinstance(x,dict):continue
    if m.get('role')=='assistant' and x.get('type')=='tool_use':calls[x.get('id')]=x.get('name')
    if m.get('role')=='user' and x.get('type')=='tool_result' and not x.get('is_error') and calls.get(x.get('tool_use_id'))=='mcp__firecrawl__record_verdict':
     if any(complete(p) for p in payloads(x.get('content'))):return True
  else:
   for x in m.get('tool_calls',[]):calls[x.get('id')]=x.get('function',{}).get('name')
   if m.get('role')=='tool' and calls.get(m.get('tool_call_id'))=='mcp__firecrawl__record_verdict' and any(complete(p) for p in payloads(m.get('content'))):return True
 return False
def apply(kwargs,anthropic):
 tools=kwargs.get('tools')
 if not isinstance(tools,list) or len(tools)!=6:return kwargs
 names={t.get('name') if anthropic else t.get('function',{}).get('name') for t in tools}
 if names!=NAMES:return kwargs
 supplied=kwargs.get('tool_choice');allowed=(None,{'type':'auto'},{'type':'any'}) if anthropic else (None,'auto','required')
 if supplied not in allowed:raise ValueError('Explicit other gate tool selection cannot be overridden')
 done=matched(kwargs.get('messages',[]),anthropic);result=dict(kwargs);result['tool_choice']={'type':'auto' if done else 'any'} if anthropic else ('auto' if done else 'required');key='litellm_metadata' if anthropic else 'metadata';result[key]={**result.get(key,{}),'egpu_gate_tool_grammar':{'version':'1.0.0','matched_canonical_ten_verdicts_saved':done,'semantic_support_accepted':False,'schemas_unchanged':True}};return result
def pin_anthropic(kwargs):return apply(kwargs,True)
def pin(kwargs):return apply(kwargs,False)

"""Force tool grammar for exact research set; release only on matched publication success."""
import copy,hashlib,json,os,time
from pathlib import Path
NAMES={'mcp__firecrawl__firecrawl_search','mcp__firecrawl__firecrawl_scrape','mcp__firecrawl__read_source','mcp__firecrawl__publish_claims','mcp__firecrawl__observed_research'}
def payloads(value):
    if isinstance(value,dict) and value.get('type')=='text' and isinstance(value.get('text'),str):return payloads(value['text'])
    if isinstance(value,list):
        return [p for item in value for p in payloads(item)]
    if isinstance(value,str):
        try:value=json.loads(value)
        except (ValueError,TypeError):return []
    result=[value] if isinstance(value,dict) else []
    if isinstance(value,dict) and isinstance(value.get('content'),list):
        for item in value['content']:
            if isinstance(item,dict) and item.get('type')=='text':result+=payloads(item.get('text'))
    return result

def published(messages):
    calls={}
    for message in messages:
        for call in message.get('tool_calls',[]):
            calls[call.get('id')]=call.get('function',{}).get('name')
        if message.get('role')=='tool' and calls.get(message.get('tool_call_id'))=='mcp__firecrawl__publish_claims':
            if any(p.get('mechanical_handoff_ok') is True for p in payloads(message.get('content'))):return True
    return False

def audit(result):
    row={'utc_epoch':time.time(),'stage':'anthropic' if isinstance(result.get('tool_choice'),dict) else 'converted','tool_count':len(result.get('tools',[])),'tool_choice':result.get('tool_choice')}
    data=(json.dumps(row,sort_keys=True)+'\n').encode();assert len(data)<512
    fd=os.open(str(Path(__file__).resolve().parent/'GRAMMAR-PIN-AUDIT.jsonl'),os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW,0o600)
    try:os.write(fd,data)
    finally:os.close(fd)


def pin(kwargs):
    tools=kwargs.get('tools')
    if not isinstance(tools,list) or len(tools) not in (5,6):return kwargs
    names={t.get('function',{}).get('name') for t in tools}
    if names not in (NAMES,NAMES|{'Read'}):return kwargs
    supplied=kwargs.get('tool_choice')
    if supplied not in (None,'auto','required'):raise ValueError('Research grammar cannot override an explicit other tool choice')
    done=published(kwargs.get('messages',[]));result=dict(kwargs);result['tool_choice']='auto' if done else 'required'
    result['metadata']={**result.get('metadata',{}),'egpu_research_tool_grammar':{'version':'1.0.0','choice':result['tool_choice'],'actual_matched_publication_success':done,'schemas_unchanged':True,'tools_sha256':hashlib.sha256(json.dumps(tools,sort_keys=True).encode()).hexdigest()}}
    audit(result)
    return result


def pin_anthropic(kwargs):
    tools=kwargs.get('tools')
    if not isinstance(tools,list) or len(tools) not in (5,6):return kwargs
    names={t.get('name') for t in tools}
    if names not in (NAMES,NAMES|{'Read'}):return kwargs
    supplied=kwargs.get('tool_choice')
    if supplied not in (None,{'type':'auto'},{'type':'any'}):raise ValueError('Research grammar cannot override explicit Anthropic tool selection')
    calls={};done=False
    for message in kwargs.get('messages',[]):
        content=message.get('content',[])
        if not isinstance(content,list):continue
        for item in content:
            if not isinstance(item,dict):continue
            if message.get('role')=='assistant' and item.get('type')=='tool_use':calls[item.get('id')]=item.get('name')
            if message.get('role')=='user' and item.get('type')=='tool_result' and not item.get('is_error') and calls.get(item.get('tool_use_id'))=='mcp__firecrawl__publish_claims':
                done=done or any(p.get('mechanical_handoff_ok') is True for p in payloads(item.get('content')))
    result=dict(kwargs);result['tool_choice']={'type':'auto' if done else 'any'}
    result['litellm_metadata']={**result.get('litellm_metadata',{}),'egpu_research_tool_grammar':{'version':'1.0.1','native_api_stage':'anthropic_messages','choice':result['tool_choice'],'actual_matched_publication_success':done,'schemas_unchanged':True}}
    audit(result)
    return result

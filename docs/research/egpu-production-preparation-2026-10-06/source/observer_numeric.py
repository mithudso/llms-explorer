"""Declared numeric readonly selector. No factual, source or citation repair."""
import copy,hashlib
VIEWS={0:'policy',1:'reads',2:'publication_template'}
def normalized(request):
    params=request.get('params',{});arguments=params.get('arguments',{})
    if request.get('method')!='tools/call' or params.get('name')!='observed_research' or not isinstance(arguments,dict):return request,None
    value=arguments.get('view')
    if type(value) is not int or value not in VIEWS:return request,None
    result=copy.deepcopy(request);result['params']['arguments']['view']=VIEWS[value]
    return result,{'raw_view':value,'mapped_view':VIEWS[value],'scope':'Declared exact numeric readonly selector only; other fields unchanged'}
def extend(base):
    class NumericObserverProxy(base):
        def handle(self,request,raw_input=None):
            mapped,audit=normalized(request)
            if audit:
                audit['raw_input_sha256']=hashlib.sha256(raw_input or b'').hexdigest()
                self.engine.store.append('numeric_observer_selector',audit)
            response=super().handle(mapped,raw_input=raw_input)
            if request.get('method')=='tools/list' and response is not None:
                response=copy.deepcopy(response)
                observer=next(t for t in response['result']['tools'] if t['name']=='observed_research')
                observer['inputSchema']['properties']['view']={'type':'integer','enum':[0,1,2],'description':'Numeric readonly view: 0=policy, 1=reads, 2=publication_template. Select only these exact integers. view2 requires exactly view,source_reads,deep_read_ids,negative_read_ids; omit read_ids. read_ids belongs only to view1.'}
                observer['description']+=' Numeric view selector: 0 policy; 1 reads; 2 publication_template. All original evidence/publication gates remain.'
            return response
    return NumericObserverProxy

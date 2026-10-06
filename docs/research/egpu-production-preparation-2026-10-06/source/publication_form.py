"""Observed metadata form for explicit model selections. No factual completion."""
import copy
from typed_publication import Refusal,encoded
from typed_retrieval_proxy import reply,publisher_tool

def form(engine, arguments):
    if set(arguments)!={'view','source_reads','deep_read_ids','negative_read_ids'}:
        raise Refusal('publication_template requires explicit source_reads, deep_read_ids and negative_read_ids')
    source_reads=arguments['source_reads'];deep_ids=arguments['deep_read_ids'];negative_ids=arguments['negative_read_ids']
    if not isinstance(source_reads,list) or not 1<=len(source_reads)<=8:
        raise Refusal('Choose one to eight source reads explicitly')
    selected=set();handles=set()
    for row in source_reads:
        if not isinstance(row,dict) or set(row)!={'source_handle','read_ids'} or row['source_handle'] in handles:
            raise Refusal('Source read selections must be explicit and unique')
        engine.selected(row['read_ids'],row['source_handle'])
        handles.add(row['source_handle']);selected.update(row['read_ids'])
    deep=engine.selected(deep_ids);negative=engine.selected(negative_ids)
    if not set(deep_ids+negative_ids)<=selected:
        raise Refusal('deep/negative selections must also be declared source reads')
    negative_urls={url for search in engine.searches if search['negative_intent'] and search['succeeded'] and search.get('delivery_recorded') for url in search['delivered_urls']}
    if any(read['source_url'] not in negative_urls for read in negative):
        raise Refusal('negative read lacks an actual declared negative-search discovery')
    observed=engine.observations()
    metadata={'queries':observed['queries'],'negation_queries':observed['negation_queries'],'sources_deep_read':len({read['source_handle'] for read in deep})}
    # Null placeholders force the model to supply factual content and confidence.
    # No claim text, citation choice, tier, summary or quotation is filled here.
    blank={'text':None,'confidence':None,'section':'core','sources':[],'volatile':None}
    value={'publication_template':{'submission_id':None,'document':{'concept':engine.binding.planned_concept,'summary':None,'claims':[copy.deepcopy(blank),copy.deepcopy(blank)],'sources':[{'source_handle':row['source_handle'],'tier':None} for row in source_reads],'disagreements':[],'open_questions':[],'child_concepts':[],'telemetry':metadata},'source_reads':copy.deepcopy(source_reads),'deep_read_ids':list(deep_ids),'negative_read_ids':list(negative_ids)},'instruction':'This form contains only actual observed metadata for your explicit selections. Fill every null and select actual supporting handles for each authored claim. Keep metadata selections unchanged unless you request another form. Optional evidence_quotes is omitted; original quote validation applies if you add quotes. No source, support, negation, helper, blind or quality requirement is waived. No publication has occurred.','factual_fields_completed':False,'semantic_support_accepted':False,'standard_dr_accepted':False}
    engine.store.append('publication_template_metadata',{'source_reads':source_reads,'deep_read_ids':deep_ids,'negative_read_ids':negative_ids,'observed_telemetry':metadata,'factual_fields_completed':False})
    return value

def extend(original):
    class FormProxy(original):
        def handle(self,request,*,raw_input=None):
            params=request.get('params',{});arguments=params.get('arguments',{})
            if request.get('method')=='tools/call' and params.get('name')=='observed_research' and arguments.get('view')=='publication_template':
                return reply(request,form(self.engine,arguments))
            response=super().handle(request,raw_input=raw_input)
            if response is not None and request.get('method')=='tools/list':
                observer=next(tool for tool in response['result']['tools'] if tool['name']=='observed_research')
                props=observer['inputSchema']['properties'];props['view']['enum'].append('publication_template')
                properties=publisher_tool()['inputSchema']['properties']
                for key in ['source_reads','deep_read_ids','negative_read_ids']:
                    props[key]=copy.deepcopy(properties[key])
                observer['description']+=' view=publication_template takes your explicit source_reads/deep_read_ids/negative_read_ids and returns observed metadata with blank facts. It never chooses citations or publishes.'
                assert len(encoded(response))<12000,'Expanded catalog exceeds declared bound'
            return response
    return FormProxy

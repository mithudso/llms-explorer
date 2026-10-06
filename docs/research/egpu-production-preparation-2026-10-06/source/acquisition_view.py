"""Require fetched page handles and expose original policy metadata earlier."""
import copy
import json
from typed_publication import Refusal,originating_label

def extend(original):
    class PageHandleProxy(original):
        def handle(self,request,*,raw_input=None):
            params=request.get('params',{});args=params.get('arguments',{});name=params.get('name')
            call=request.get('method')=='tools/call'
            if call and name=='read_source' and ('source_file' in args or not args.get('source_handle')):
                raise Refusal('Fetch a page URL first; read_source requires its issued source_handle. A search response file is not a fetched page.')
            if call and name=='firecrawl_scrape':
                # The original publisher already refuses this exact unmapped
                # host. Move the same metadata check before costly fetching.
                originating_label(args.get('url'),self.engine.binding.origin_hosts)
            response=super().handle(request,raw_input=raw_input)
            if response is None:return None
            if request.get('method')=='tools/list':
                tool=next(t for t in response['result']['tools'] if t['name']=='read_source')
                schema=tool['inputSchema'];schema['properties'].pop('source_file',None)
                schema['required']=['source_handle','queries']
                tool['description']='Read contextual verbatim passages from a page fetched by firecrawl_scrape. Require its exact issued source_handle and literal queries. Search response files are not pages. Ranking is not semantic support.'
                return response
            if not call or name not in {'firecrawl_search','firecrawl_scrape','read_source'}:return response
            blocks=response.get('result',{}).get('content',[])
            if not blocks or blocks[0].get('type')!='text':return response
            try:value=json.loads(blocks[0]['text'])
            except ValueError:return response
            if not isinstance(value,dict):return response
            if name=='firecrawl_search':
                for key in ['response_file','discovery_file','source_file']:
                    value.pop(key,None)
                for row in value.get('results',[]):
                    try:label=originating_label(row['url'],self.engine.binding.origin_hosts)
                    except Refusal:label=None
                    row['reviewed_origin_organization']=label
                value['page_support']=False
            else:
                handle=value.get('source_handle')
                if handle in self.engine.sources:
                    source=self.engine.sources[handle]
                    label=originating_label(source['url'],self.engine.binding.origin_hosts)
                    negative={url for q in self.engine.searches if q['negative_intent'] and q['succeeded'] for url in q['delivered_urls']}
                    value.pop('source_file',None)
                    value['reviewed_origin_organization']=label
                    value['url_in_negative_search_results']=source['url'] in negative
                    value['metadata_is_semantic_support']=False
            # Literal excerpts, search snippets, URLs and queries are unchanged.
            changed=copy.deepcopy(response);changed['result']['content'][0]['text']=json.dumps(value,ensure_ascii=False,separators=(',',':'))
            self.engine.store.append('page_handle_model_view',{'tool':name,'source_handle':value.get('source_handle'),'factual_text_changed':False,'semantic_support_accepted':False})
            return changed
    return PageHandleProxy

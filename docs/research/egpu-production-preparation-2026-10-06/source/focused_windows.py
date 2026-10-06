"""Prioritize exact matching body windows; retain canonical validation and bytes."""
import json
from pathlib import Path
import re

def is_navigation(body):
    body = body.strip()
    return (body.startswith('#')
        or bool(re.match(r'^(?:[-*] )?\[[^]]+\]\([^)]*\)(?:[ .]*)$', body))
        or bool(re.match(r'^[-*] \[', body))
        or bool(re.search(r'\.{2,}\s*\d+\s*$', body)))

def candidate_base(original):
    class Focused(original):
        def excerpt_delivery(self, request, response):
            data=json.loads(response['result']['content'][0]['text'])
            if not data['total_matches']:
                return super().excerpt_delivery(request,response)
            # Canonical read_source has already checked source path, queries and
            # ownership. The frozen publisher records our actual delivered bytes.
            text=self.source_text(json.loads(Path(data['source_file']).read_text()))
            lines=text.splitlines();queries=data['queries']
            hits=[i for i,line in enumerate(lines) if any(q.lower() in line.lower() for q in queries)]
            assert len(hits)==data['total_matches']
            context=max(1,min(12,request.get('params',{}).get('arguments',{}).get('context_lines',5)))
            scopes=self.schema_scopes(lines)
            def rank(index):
                body=lines[index].strip()
                navigation=is_navigation(body)
                coverage=sum(q.lower() in body.lower() for q in queries)
                return (navigation,-coverage,index)
            ordered=[];seen=set()
            for index in sorted(hits,key=rank):
                # Keep preceding conditions and following qualifiers together.
                # Retain exact nearest Markdown heading at each level as context.
                heading=[]
                for level in range(1,7):
                    match=next((j for j in range(index,-1,-1) if lines[j].startswith('#'*level+' ')),None)
                    if match is not None:heading.append(match)
                ownership={j for _,_,positions in scopes[index] for j in positions}
                local=set(range(max(0,index-context),min(len(lines),index+context+1)))|ownership
                for j in [*sorted(set(heading)), index, *sorted(local - {index})]:
                    if j not in seen:
                        owner='.'.join(item[1] for item in scopes[j])
                        suffix=f' [{owner}]' if owner else ''
                        ordered.append(f'{j+1}{suffix}: {lines[j]}');seen.add(j)
            # The existing bounded serializer still clips and labels truncation.
            # It never treats lexical rank or a delivered line as semantic support.
            data['excerpts']=ordered
            data['truncated']=True
            changed={**response,'result':{**response['result'],'content':[{'type':'text','text':json.dumps(data)}]}}
            return super().excerpt_delivery(request,changed)
    return Focused

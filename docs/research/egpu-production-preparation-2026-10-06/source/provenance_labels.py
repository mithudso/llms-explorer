"""Lossless metadata labels; explicit selections and literal factual text stay intact."""
import json
import os
from pathlib import Path
import re

SOURCE_KEYS = {'source_handle','actual_source_handle','submitted_source_handle','source_handles','sources'}
READ_KEYS = {'read_id','read_ids','deep_read_ids','negative_read_ids','selected_read_ids','id'}
FACT_KEYS = {'quote','text','summary','title','url','source_url','actual_source_url','query','queries','excerpts','partial_excerpts','delivered_excerpts'}
SOURCE_PATTERN = re.compile(r'^src-[a-f0-9]{32}-[0-9]+$')
READ_PATTERN = re.compile(r'^read-[a-f0-9]{32}-[0-9]+$')

class Labels:
    def __init__(self, directory=None):
        self.sources={};self.reads={};self.reverse={};self.directory=directory
        self.requests=0;self.responses=0

    def source(self, raw):
        if raw not in self.sources:
            label='S'+str(len(self.sources)+1)
            self.sources[raw]=label;self.reverse[label]=raw
        return self.sources[raw]

    def read(self, raw, source):
        if raw not in self.reads:
            if not source or not SOURCE_PATTERN.fullmatch(source):
                # A response cannot invent a source association. Keep the exact
                # canonical ID if no earlier delivered source binding exists.
                return raw
            label='R'+self.source(source)[1:]+'.'+raw.rsplit('-',1)[1]
            assert label not in self.reverse or self.reverse[label]==raw
            self.reads[raw]={'label':label,'source_handle':source}
            self.reverse[label]=raw
        return self.reads[raw]['label']

    def encode(self, value, key=None, source=None):
        if key in FACT_KEYS:
            return value
        if isinstance(value,dict):
            own=value.get('actual_source_handle') or value.get('source_handle') or source
            for name in ['source_handle','actual_source_handle','submitted_source_handle']:
                raw=value.get(name)
                if isinstance(raw,str) and SOURCE_PATTERN.fullmatch(raw):
                    self.source(raw)
            return {k:self.encode(v,k,own) for k,v in value.items()}
        if isinstance(value,list):
            return [self.encode(v,key,source) for v in value]
        if isinstance(value,str):
            if key in SOURCE_KEYS and SOURCE_PATTERN.fullmatch(value):
                return self.source(value)
            if key in READ_KEYS and READ_PATTERN.fullmatch(value):
                return self.read(value,source)
        return value

    def decode(self, value, key=None):
        if key in FACT_KEYS:
            return value
        if isinstance(value,dict):
            return {k:self.decode(v,k) for k,v in value.items()}
        if isinstance(value,list):
            return [self.decode(v,key) for v in value]
        if isinstance(value,str) and key in SOURCE_KEYS|READ_KEYS:
            # Unknown labels remain unknown. Never select a different read or
            # infer a source from the digits in a submitted label.
            return self.reverse.get(value,value)
        return value

    def outgoing(self, message):
        if not isinstance(message,dict):
            return message
        result=message.get('result',{})
        if isinstance(result,dict):
            for block in result.get('content',[]):
                if block.get('type')=='text' and isinstance(block.get('text'),str):
                    try:metadata=json.loads(block['text'])
                    except ValueError:continue
                    block['text']=json.dumps(self.encode(metadata),ensure_ascii=False,separators=(',',':'))
        self.responses+=1;self.audit()
        return message

    def incoming(self, message):
        if isinstance(message,dict) and message.get('method')=='tools/call':
            params=message.get('params',{})
            if isinstance(params,dict) and isinstance(params.get('arguments'),dict):
                params['arguments']=self.decode(params['arguments'])
            self.requests+=1;self.audit()
        return message

    def audit(self):
        if self.directory is None:
            return
        directory=Path(self.directory)
        assert directory.is_dir() and not directory.is_symlink()
        path=directory/'SHORT-LABEL-MAP.json';temporary=directory/'SHORT-LABEL-MAP.tmp'
        assert not temporary.exists() and not path.is_symlink()
        value={'version':'1.0.0','sources':self.sources,'reads':self.reads,'incoming_requests':self.requests,'outgoing_responses':self.responses,'factual_text_translated':False,'automatic_read_selection':False,'semantic_support_accepted':False}
        descriptor=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(descriptor,'w') as stream:json.dump(value,stream,indent=2);stream.write('\n')
        temporary.replace(path)

class Input:
    def __init__(self, original, labels):self.original=original;self.labels=labels
    def __iter__(self):
        for line in self.original:
            try:value=json.loads(line)
            except ValueError:yield line;continue
            yield json.dumps(self.labels.incoming(value),ensure_ascii=False)+'\n'

class Output:
    def __init__(self, original, labels):self.original=original;self.labels=labels
    def write(self, line):
        try:value=json.loads(line)
        except ValueError:return self.original.write(line)
        return self.original.write(json.dumps(self.labels.outgoing(value),ensure_ascii=False)+'\n')
    def flush(self):return self.original.flush()

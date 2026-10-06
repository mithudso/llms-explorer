"""Version1.0.0. Exact reviewed27B prefix parser; no model inference or runtime admission."""
from __future__ import annotations
import hashlib
import json
import math
import struct
MODEL_BYTES=9605378560
HEADER_SHA='84e75736205b467760b828bfef02fc88fd4edf4f47f4d4767341b412124eb1ec'
TEMPLATE_SHA='e84f32a23fdda27689f868aa4a1a5621f41133e51a48d7f3efcbea2839574259'
METADATA_SHA='34e7d9002c9029d33bf00ae08bf457ea92258520a06b8b5a935772ddd8d3d149'
DESCRIPTOR_SHA='03ed563b55aa54f1ec6cd2b6c7911964a2e0795a33d6291b0ac21afd15e2b09e'
FORMATS={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
QUANT={0:(1,4),8:(32,34),10:(256,84),12:(256,144),13:(256,176),14:(256,210),16:(256,66)}
def require(value,message):
    if not value: raise ValueError(message)
def canonical_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Reader:
    def __init__(self, data):
        self.data, self.at = data, 0

    def take(self, length):
        require(type(length) is int and 0 <= length <= len(self.data)
                and self.at + length <= len(self.data), 'Truncated or unbounded prefix')
        result = self.data[self.at:self.at + length]
        self.at += length
        return result

    def number(self, fmt):
        return struct.unpack('<' + fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self):
        return self.take(self.number('Q')).decode('utf-8')

    def value(self, kind, keep=True, depth=0):
        require(depth <= 2, 'Unreviewed nested metadata')
        if kind == 8:
            result = self.string()
        elif kind == 9:
            subtype, count = self.number('I'), self.number('Q')
            require(count <= 1000000, 'Unbounded metadata array')
            result = [self.value(subtype, keep, depth + 1) for _ in range(count)]
        else:
            require(kind in FORMATS, 'Unreviewed metadata type')
            result = self.number(FORMATS[kind])
        return result if keep else None


def parse_header(data: bytes) -> dict:
    require(len(data) == 16 * 1024**2 and hashlib.sha256(data).hexdigest() == HEADER_SHA,
            'Exact saved16MiB header identity required')
    r = Reader(data)
    require(r.take(4) == b'GGUF' and r.number('I') == 3, 'Exact GGUFv3 required')
    nt, nm = r.number('Q'), r.number('Q')
    require((nt, nm) == (866, 46), 'Exact27B descriptor/metadata counts required')
    metadata, seen = {}, set()
    for _ in range(nm):
        key = r.string()
        require(key and key not in seen, 'Duplicate or empty metadata key')
        seen.add(key)
        value = r.value(r.number('I'), not key.startswith('tokenizer.ggml.'))
        if value is not None:
            metadata[key] = value
    template = metadata.pop('tokenizer.chat_template')
    rows, seen = [], set()
    for _ in range(nt):
        name, nd = r.string(), r.number('I')
        require(name and name not in seen and 0 < nd <= 4, 'Invalid descriptor name/dimensions')
        seen.add(name)
        shape = [r.number('Q') for _ in range(nd)]
        kind, offset = r.number('I'), r.number('Q')
        require(kind in QUANT and all(type(n) is int and 0 < n <= 10**9 for n in shape),
                'Unreviewed tensor type/shape')
        block, width = QUANT[kind]
        require(shape[0] % block == 0, 'Invalid quantized row')
        rows.append(dict(name=name, shape=shape, type_id=kind, relative_offset=offset,
                         logical_bytes=math.prod(shape) // block * width))
    alignment = metadata.get('general.alignment', 32)
    require(type(alignment) is int and 0 < alignment <= 4096 and alignment & (alignment - 1) == 0,
            'Unreviewed tensor alignment')
    start = (r.at + alignment - 1) // alignment * alignment
    spans = sorted((start + row['relative_offset'], start + row['relative_offset'] + row['logical_bytes']) for row in rows)
    require(all(start <= a < b <= MODEL_BYTES and a % alignment == 0 for a, b in spans)
            and all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'Invalid/overlapping tensor spans')
    return {'metadata': metadata, 'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
            'tensors': rows, 'data_offset': start, 'complete_file_verified': False}


def validate_inventory(inv):
    require(canonical_sha(inv['metadata']) == METADATA_SHA, 'Exact27B metadata differs')
    require(canonical_sha(sorted(inv['tensors'], key=lambda row: row['name'])) == DESCRIPTOR_SHA,
            'Exact27B tensor descriptor manifest differs')
    require(inv['template_sha256'] == TEMPLATE_SHA and type(inv['data_offset']) is int
            and inv['data_offset'] == 10994176 and inv['complete_file_verified'] is False,
            'Saved-header template/data/proof scope differs')



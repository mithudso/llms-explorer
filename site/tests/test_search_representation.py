"""Cross-language provenance checks without loading Transformers or any model."""
import hashlib
import json
import subprocess
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]


def test_generator_requires_explicit_embedding_opt_in_before_loading_models():
    run = subprocess.run(['node', 'tools/gen_search_index.mjs'], cwd=SITE,
                         capture_output=True, text=True, timeout=10)
    assert run.returncode != 0
    assert 'Embeddings are paused' in run.stderr
    assert 'ERR_MODULE_NOT_FOUND' not in run.stderr


def test_exact_unicode_input_revision_and_vector_bytes_are_bound():
    pack = {'slug': 'c', 'concept': 'A😀', 'summary': 'x' * 1990,
            'facets': [{'facts': [{'text': 'last caveat'}]}],
            'canonicalArtifactSha256': 'canonical'}
    js = '''
import {embeddableText, encoderContract, bind} from './tools/search_representation.mjs';
const pack = JSON.parse(process.argv[1]);
const text = embeddableText(pack);
const encoder = encoderContract('a'.repeat(40));
const bytes = Buffer.from([1,2,3,4]);
console.log(JSON.stringify({text, encoder, binding:bind(pack,text,encoder,bytes)}));
'''
    run = subprocess.run(['node', '--input-type=module', '-e', js, json.dumps(pack)],
                         cwd=SITE, capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    expected = '. '.join([pack['concept'], pack['summary'], 'last caveat'])[:2000]
    assert result['text'] == expected
    assert result['binding']['input_sha256'] == hashlib.sha256(expected.encode()).hexdigest()
    assert result['binding']['artifact_sha256'] == 'canonical'
    assert result['binding']['vector_sha256'] == hashlib.sha256(bytes([1,2,3,4])).hexdigest()
    encoder_bytes = json.dumps(result['encoder'], sort_keys=True, ensure_ascii=False,
                               separators=(',', ':')).encode()
    assert result['binding']['encoder_sha256'] == hashlib.sha256(encoder_bytes).hexdigest()

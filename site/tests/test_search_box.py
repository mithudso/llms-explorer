"""Execute SearchBox's client script with controlled downloads and inference.

The module loader is the only source seam. The DOM and debounce timer are small
test doubles, so failures and races exercise the shipped event handlers without
downloading a model or regenerating its index.
"""
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "src/components/SearchBox.astro"

HARNESS = r"""
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import { setImmediate as nextTurn } from 'node:timers/promises';
import vm from 'node:vm';
import { webcrypto } from 'node:crypto';

const source = readFileSync(process.argv[2], 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
const keywordPath = process.argv[2].replace(
  'components/SearchBox.astro', 'scripts/concept-search.ts');
const keywordSource = readFileSync(keywordPath, 'utf8');
const keywordClient = stripTypeScriptTypes(keywordSource).replace(/^export /gm, '');
const client = stripTypeScriptTypes(source.replace(
  'import("@huggingface/transformers")', 'loadTransformers()')
  .replace(/import \{ keywordHits,[^;]+;/, ''));
const unhandled = [];
process.on('unhandledRejection', error => unhandled.push(error));

class Element {
  children = [];
  listeners = new Map();
  textContent = '';
  value = '';
  set innerHTML(value) { assert.equal(value, ''); this.children = []; }
  addEventListener(type, handler, options = {}) {
    this.listeners.set(type, { handler, once: options.once });
  }
  dispatch(type) {
    const listener = this.listeners.get(type);
    if (listener?.once) this.listeners.delete(type);
    listener?.handler();
  }
  appendChild(child) { this.children.push(child); }
}

function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function mount({ failLoads = 0, delayLoad = null, delayQuery = null,
                 keywordItems = [], encoder = null, indexHash = null } = {}) {
  const input = new Element(), status = new Element(), results = new Element();
  const meta = new Element();
  meta.textContent = JSON.stringify({ model: 'test-model', count: 2, dim: 2,
    encoder, index_sha256: indexHash,
    items: [{ slug: 'first', concept: 'First', summary: 'first result' },
            { slug: 'latest', concept: 'Latest', summary: 'latest result' }] });
  const elements = { 'semantic-search-input': input, 'semantic-search-status': status,
    'semantic-search-results': results, 'search-meta-data': meta };
  const env = { useWasmCache: true, useBrowserCache: true,
    backends: { onnx: { wasm: { numThreads: 4, proxy: false } } } };
  const state = { loads: 0, fetches: 0, queries: [], errors: [], settings: [], badVectors: false };
  const timers = new Map();
  let timerId = 0;
  const context = vm.createContext({ Float32Array, Uint8Array, crypto: webcrypto,
    console: { error: (...args) => state.errors.push(args) },
    document: { getElementById: id => elements[id], createElement: () => new Element() },
    setTimeout: handler => { timers.set(++timerId, handler); return timerId; },
    clearTimeout: id => timers.delete(id),
    fetch: async url => {
      if (url === '/search-keywords.json') {
        return { ok: true, json: async () => ({items: keywordItems}) };
      }
      state.fetches++;
      return { ok: true, arrayBuffer: async () =>
        new Float32Array(state.badVectors ? [1, 0] : [1, 0, 0, 1]).buffer };
    },
    loadTransformers: async () => ({ env, pipeline: async (task, model, options) => {
      state.pipelineOptions = options;
      state.loads++;
      state.settings.push({ wasmCache: env.useWasmCache, threads: env.backends.onnx.wasm.numThreads,
        modelCache: env.useBrowserCache });
      if (state.loads <= failLoads) throw new Error('model download failed');
      if (delayLoad) await delayLoad.promise;
      return async query => {
        state.queries.push(query);
        if (query === 'fails') throw new Error('inference failed');
        if (query === 'first' && delayQuery) return delayQuery.promise;
        return { data: new Float32Array(query === 'latest' ? [0, 1] : [1, 0]) };
      };
    } })
  });
  vm.runInContext(keywordClient + '\n' + client, context);
  return { input, status, results, state,
    focus: () => input.dispatch('focus'),
    type: value => { input.value = value; input.dispatch('input'); },
    debounce: () => {
      const pending = [...timers.values()]; timers.clear(); pending.forEach(run => run());
    }
  };
}

const flush = async () => { await nextTurn(); await nextTurn(); };
const search = async (page, query) => { page.type(query); page.debounce(); await flush(); };
const firstLink = page => page.results.children[0]?.children[0]?.href;
const scenario = process.argv[1];

if (scenario === 'runtime_configuration') {
  const page = mount();
  assert.equal(page.state.fetches, 0, 'page load must not start model downloads');
  await search(page, 'latest');
  assert.equal(firstLink(page), '/tree/latest/');
  assert.deepEqual(page.state.settings, [{ wasmCache: false, threads: 1, modelCache: true }],
    'avoid both blob-module paths while retaining model caching');
} else if (scenario === 'focus_failure_retry') {
  const page = mount({ failLoads: 1 });
  assert.equal(page.state.fetches, 0, 'page load must not start model downloads');
  page.focus();
  await flush();
  assert.match(page.status.textContent, /failed to load/);
  assert.equal(page.state.errors.length, 1);
  await search(page, 'latest');
  assert.equal(page.state.loads, 2, 'the rejected load must be retried');
  assert.equal(firstLink(page), '/tree/latest/');
  assert.equal(page.status.textContent, '');
} else if (scenario === 'query_load_failure_retry') {
  const page = mount({ failLoads: 1 });
  await search(page, 'first');
  assert.match(page.status.textContent, /failed to load/);
  await search(page, 'latest');
  assert.equal(page.state.loads, 2);
  assert.equal(firstLink(page), '/tree/latest/');
} else if (scenario === 'inference_failure_handling') {
  const page = mount();
  await search(page, 'fails');
  assert.match(page.status.textContent, /Search failed/);
  assert.match(page.status.textContent, /reload this page to retry/);
  assert.equal(page.results.children.length, 0);
  assert.equal(page.state.errors.length, 1);
} else if (scenario === 'invalid_index_retry') {
  const page = mount();
  page.state.badVectors = true;
  await search(page, 'first');
  assert.match(page.status.textContent, /failed to load/);
  assert.equal(page.state.loads, 0, 'do not load a model for a mismatched index');
  page.state.badVectors = false;
  await search(page, 'latest');
  assert.equal(page.state.fetches, 2);
  assert.equal(firstLink(page), '/tree/latest/');
} else if (scenario === 'stale_result_during_debounce') {
  const query = deferred();
  const page = mount({ delayQuery: query });
  await search(page, 'first');
  assert.equal(page.status.textContent, 'Searching…');
  page.type('latest'); // the latest search has not passed its debounce yet
  query.resolve({ data: new Float32Array([1, 0]) });
  await flush();
  assert.equal(page.results.children.length, 0, 'old results must not paint during debounce');
  page.debounce();
  await flush();
  assert.equal(firstLink(page), '/tree/latest/');
} else if (scenario === 'clear_query_during_load') {
  const load = deferred();
  const page = mount({ delayLoad: load });
  page.focus();
  await flush();
  page.type('');
  page.debounce();
  load.reject(new Error('download interrupted'));
  await flush();
  assert.equal(page.status.textContent, '', 'prewarm failure must not overwrite a cleared input');
  assert.equal(page.results.children.length, 0);
} else if (scenario === 'keyword_fallback_when_model_fails') {
  const page = mount({ failLoads: 1, keywordItems: [
    {slug: 'new-concept', concept: 'Fresh research', summary: 'New', text: 'Fresh research'}] });
  await search(page, 'fresh research');
  assert.equal(firstLink(page), '/tree/new-concept/');
  assert.equal(page.status.textContent, '');
} else if (scenario === 'keyword_and_semantic_merge') {
  const page = mount({ keywordItems: [
    {slug: 'new-concept', concept: 'Fresh research', summary: 'New', text: 'Fresh research'}] });
  await search(page, 'fresh research');
  assert.equal(firstLink(page), '/tree/new-concept/');
  assert.equal(page.results.children.length, 3);
} else if (scenario === 'pinned_revision_and_payload') {
  const encoder = {schema: 'embedding-representation/v1', model: 'test-model', dim: 2,
    model_revision: 'a'.repeat(40), pooling: 'mean', normalization: 'l2',
    query_preprocessing: 'identity/v1', query_prefix: '', cache_revision: 'site-query/v2'};
  const page = mount({ encoder });
  await search(page, 'latest');
  assert.equal(firstLink(page), '/tree/latest/');
  assert.equal(page.state.pipelineOptions.revision, 'a'.repeat(40));
  const bad = mount({ encoder: {...encoder, model: 'wrong-model'} });
  await search(bad, 'latest');
  assert.equal(bad.state.loads, 0);
  const mixed = mount({ indexHash: '0'.repeat(64) });
  await search(mixed, 'latest');
  await flush();
  assert.equal(mixed.state.loads, 0);
  assert.equal(mixed.results.children.length, 0);
} else if (scenario === 'late_keyword_without_embeddings') {
  const page = mount({ failLoads: 1, keywordItems: [{slug:'long', concept:'Long', summary:'',
    text:'prefix '.repeat(800) + ' rare_identifier_late_caveat'}] });
  await search(page, 'rare_identifier_late_caveat');
  assert.equal(firstLink(page), '/tree/long/');
} else {
  throw new Error('unknown scenario: ' + scenario);
}
await flush();
assert.deepEqual(unhandled, [], 'event handlers must catch download and inference rejections');
"""


@pytest.mark.parametrize("scenario", [
    "runtime_configuration",
    "focus_failure_retry",
    "query_load_failure_retry",
    "inference_failure_handling",
    "invalid_index_retry",
    "stale_result_during_debounce",
    "clear_query_during_load",
    "keyword_fallback_when_model_fails",
    "keyword_and_semantic_merge",
    "pinned_revision_and_payload",
    "late_keyword_without_embeddings",
])
def test_search_failure_and_race_handling(scenario):
    run = subprocess.run(["node", "--input-type=module", "-e", HARNESS, scenario, str(SOURCE)],
                         capture_output=True, text=True, timeout=20)
    assert run.returncode == 0, run.stdout + run.stderr

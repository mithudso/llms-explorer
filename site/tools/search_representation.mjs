// Shared, model-free helpers: importing this module never loads a model.
import { createHash } from 'node:crypto';
export const MODEL = 'Xenova/all-MiniLM-L6-v2';
export const DIM = 384;
export const MAX_CHARS = 2000;
export function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
  }
  return value;
}
export function digest(value) {
  return createHash('sha256').update(Buffer.isBuffer(value) ? value :
    JSON.stringify(canonical(value))).digest('hex');
}
export function textHash(text) { return digest(Buffer.from(text, 'utf8')); }
export function embeddableText(pack) {
  const facts = (pack.facets ?? []).flatMap(f => (f.facts ?? []).map(u => u.text));
  return Array.from([pack.concept, pack.summary, ...facts].filter(Boolean).join('. '))
    .slice(0, MAX_CHARS).join('');
}
export function encoderContract(revision) {
  if (!/^[a-f0-9]{40}$/.test(revision ?? '')) throw new Error('A pinned 40-character model commit is required');
  return {schema: 'embedding-representation/v1', model: MODEL, model_revision: revision, dim: DIM,
    preprocessing: 'concept-prefix/v2', max_chars: MAX_CHARS, pooling: 'mean', normalization: 'l2',
    query_prefix: '', query_preprocessing: 'identity/v1', cache_revision: 'site-query/v2'};
}
export function bind(pack, text, encoder, bytes) {
  return {schema: 'embedding-representation/v1', state: 'bound', unit_id: 'concept:' + pack.slug,
    artifact_sha256: pack.canonicalArtifactSha256 ?? digest(pack), input_sha256: textHash(text),
    vector_encoding: 'float32-le/v1', text_encoding: 'utf-8',
    encoder_sha256: digest(encoder), vector_sha256: digest(bytes)};
}

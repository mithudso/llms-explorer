#!/usr/bin/env node
// gen_search_index — embeds every researched concept pack into a static,
// client-searchable semantic index.
//
// Runs entirely offline against src/data/concepts/*.json (the committed
// output of gen_concepts.py — never the live hub, so this stays CI-safe like
// gen_tree.py's own contract). Uses @huggingface/transformers' JS runtime
// with Xenova/all-MiniLM-L6-v2 (384-dim, mean-pooled, L2-normalized) because
// that is also the ONLY model this site's client-side SearchBox.astro can
// run in a browser via WASM — corpus and query embeddings have to come from
// the exact same model for cosine similarity between them to mean anything,
// so "whatever runs in the browser" dictates "whatever generates the index"
// here, not the other way around.
//
// Writes two files, row-aligned by index i:
//   public/search-index.bin   — Float32Array, N * DIM, corpus vectors
//   src/data/search-meta.json — [{slug, concept, summary}, ...], length N
//
// Idempotent modulo model-weight rounding: re-running against unchanged
// concept packs reproduces the same meta file and (up to float noise from
// the WASM/CPU backend) the same vectors — nothing here reads the wall
// clock. Hand-run, like gen_concepts.py, not part of `npm run generate`:
// Explicitly opt in with a pinned model revision after the embedding pause is lifted.
//
// Usage: node tools/gen_search_index.mjs --allow-embeddings --model-revision <commit> [--concepts DIR] [--out-bin FILE] [--out-meta FILE]

import { MODEL, DIM, embeddableText, encoderContract, bind, digest } from './search_representation.mjs';
import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
function parseArgs(argv) {
  const out = {
    concepts: join(ROOT, "src", "data", "concepts"),
    outBin: join(ROOT, "public", "search-index.bin"),
    outMeta: join(ROOT, "src", "data", "search-meta.json"),
  };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--allow-embeddings') out.allowEmbeddings = true;
    else if (argv[i] === '--model-revision') out.modelRevision = argv[++i];
    else if (argv[i] === "--concepts") out.concepts = argv[++i];
    else if (argv[i] === "--out-bin") out.outBin = argv[++i];
    else if (argv[i] === "--out-meta") out.outMeta = argv[++i];
  }
  return out;
}

async function main() {
  const { concepts, outBin, outMeta, allowEmbeddings, modelRevision } = parseArgs(process.argv.slice(2));
  if (!allowEmbeddings) throw new Error('Embeddings are paused; explicit --allow-embeddings is required');
  const encoder = encoderContract(modelRevision);
  const { pipeline } = await import('@huggingface/transformers');

  const files = (await readdir(concepts)).filter((f) => f.endsWith(".json")).sort();
  if (files.length === 0) {
    console.error(`no concept packs found under ${concepts}`);
    process.exitCode = 1;
    return;
  }

  console.log(`loading ${MODEL} …`);
  const embed = await pipeline("feature-extraction", MODEL, { revision: modelRevision });

  const meta = [];
  const vectors = new Float32Array(files.length * DIM);
  let i = 0;
  for (const file of files) {
    const pack = JSON.parse(await readFile(join(concepts, file), "utf8"));
    const text = embeddableText(pack);
    if (!text) continue; // a pack with no summary and no facts has nothing to embed
    const result = await embed(text, { pooling: "mean", normalize: true });
    const vec = result.data; // Float32Array, length DIM
    if (vec.length !== DIM) {
      throw new Error(`${file}: model returned ${vec.length}-dim vector, expected ${DIM}`);
    }
    vectors.set(vec, i * DIM);
    meta.push({ slug: pack.slug, concept: pack.concept, summary: pack.summary ?? "",
      embedding: bind(pack, text, encoder, Buffer.from(vec.buffer, vec.byteOffset, vec.byteLength)) });
    i++;
    if (i % 50 === 0) console.log(`  ${i}/${files.length}`);
  }

  const trimmed = vectors.subarray(0, i * DIM); // fewer rows than files if any pack was skipped

  await mkdir(dirname(outBin), { recursive: true });
  await mkdir(dirname(outMeta), { recursive: true });
  await writeFile(outBin, Buffer.from(trimmed.buffer, trimmed.byteOffset, trimmed.byteLength));
  await writeFile(
    outMeta,
    JSON.stringify({ model: MODEL, dim: DIM, count: meta.length, items: meta, encoder,
      index_sha256: digest(Buffer.from(trimmed.buffer, trimmed.byteOffset, trimmed.byteLength)) }, null, 1) + "\n"
  );

  console.log(`${outBin}: ${meta.length} vectors (${DIM}-dim, ${trimmed.byteLength.toLocaleString()} bytes)`);
  console.log(`${outMeta}: ${meta.length} entries`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});

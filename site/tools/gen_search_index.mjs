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
// re-run it whenever data/concepts/*.json changes.
//
// Usage: node tools/gen_search_index.mjs [--concepts DIR] [--out-bin FILE] [--out-meta FILE]

import { pipeline } from "@huggingface/transformers";
import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(HERE);
const MODEL = "Xenova/all-MiniLM-L6-v2";
const DIM = 384;
// The model's own max sequence length; longer input is truncated by the
// tokenizer regardless, but capping the string first keeps tokenization fast
// and keeps the embedded text weighted toward the concept's own summary and
// earliest, most load-bearing facts rather than whatever facet happened to
// sort last.
const MAX_CHARS = 2000;

function parseArgs(argv) {
  const out = {
    concepts: join(ROOT, "src", "data", "concepts"),
    outBin: join(ROOT, "public", "search-index.bin"),
    outMeta: join(ROOT, "src", "data", "search-meta.json"),
  };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--concepts") out.concepts = argv[++i];
    else if (argv[i] === "--out-bin") out.outBin = argv[++i];
    else if (argv[i] === "--out-meta") out.outMeta = argv[++i];
  }
  return out;
}

function embeddableText(pack) {
  const facts = (pack.facets ?? []).flatMap((f) => (f.facts ?? []).map((u) => u.text));
  const text = [pack.concept, pack.summary, ...facts].filter(Boolean).join(". ");
  return text.slice(0, MAX_CHARS);
}

async function main() {
  const { concepts, outBin, outMeta } = parseArgs(process.argv.slice(2));

  const files = (await readdir(concepts)).filter((f) => f.endsWith(".json")).sort();
  if (files.length === 0) {
    console.error(`no concept packs found under ${concepts}`);
    process.exitCode = 1;
    return;
  }

  console.log(`loading ${MODEL} …`);
  const embed = await pipeline("feature-extraction", MODEL);

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
    meta.push({ slug: pack.slug, concept: pack.concept, summary: pack.summary ?? "" });
    i++;
    if (i % 50 === 0) console.log(`  ${i}/${files.length}`);
  }

  const trimmed = vectors.subarray(0, i * DIM); // fewer rows than files if any pack was skipped

  await mkdir(dirname(outBin), { recursive: true });
  await mkdir(dirname(outMeta), { recursive: true });
  await writeFile(outBin, Buffer.from(trimmed.buffer, trimmed.byteOffset, trimmed.byteLength));
  await writeFile(
    outMeta,
    JSON.stringify({ model: MODEL, dim: DIM, count: meta.length, items: meta }, null, 1) + "\n"
  );

  console.log(`${outBin}: ${meta.length} vectors (${DIM}-dim, ${trimmed.byteLength.toLocaleString()} bytes)`);
  console.log(`${outMeta}: ${meta.length} entries`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});

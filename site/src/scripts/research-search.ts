// Task search for /research/. keywordHits (concept-search.ts) requires every
// word, which suits a concept name typed into /tree/ but not a sentence about a
// task: "give my agent long-term memory" carries words no concept contains, so
// it would match nothing. Here filler words drop out, simple suffixes fold, and
// a reference ranks by how many of the remaining words it covers, so the
// closest references lead even when none of them covers every word.
//
// Lowercasing uses toLowerCase, never toLocaleLowerCase: under a Turkish locale
// "I" lowercases to a dotless "ı" and "Inference" would stop matching.

/** One row of /research/references.json (src/pages/research/references.json.ts). */
export type ReferenceItem = {
  slug: string;
  concept: string;
  facts: number;
  download: string;
  family: string | null;
  familySlug: string | null;
  aliases: string[];
  /** The family name and the pack's distinctive facet titles. */
  topics: string[];
};

/** The whole of /research/references.json. */
export type ReferenceIndex = { generated: string; root: string; count: number; items: ReferenceItem[] };

export type IndexedReference = ReferenceItem & { nameIndex: string; topicIndex: string };

export type TaskSearch = {
  terms: string[];
  hits: IndexedReference[];
  /** Every reference that covers at least one term, before the limit. */
  total: number;
  /** True when the first hit covers every term. */
  complete: boolean;
};

/** A suffix is stripped only when at least this much word remains: "speed",
    "embed" and "mode" are words, not "spe" + ed, "emb" + ed or "mod" + e. */
const MIN_STEM = 4;

/** Lowercase a word and fold the endings that most often separate a query from
    a name. Both sides fold the same way, so "planning" and "plan", "GPUs" and
    "GPU", "embedding" and "embed" meet. */
function foldWord(word: string): string {
  let w = word.toLowerCase();
  // "us" stays on longer words ("status", "corpus") but not on plurals like "gpus".
  if (w.length > 4 && w.endsWith("ies")) w = `${w.slice(0, -3)}y`;
  else if (w.length > 3 && w.endsWith("s") && !w.endsWith("ss") && !(w.length > 4 && w.endsWith("us"))) w = w.slice(0, -1);
  const strips = (suffix: string) => w.endsWith(suffix) && w.length - suffix.length >= MIN_STEM;
  if (strips("ing")) w = undouble(w.slice(0, -3));
  else if (strips("ed")) w = undouble(w.slice(0, -2));
  else if (strips("ly")) w = w.slice(0, -2);
  if (strips("e")) w = w.slice(0, -1);
  return w;
}

// "plann" → "plan", "logg" → "log", "embedd" → "embed"; a doubled l, s or z is
// the word's own ("roll", "pass", "buzz").
function undouble(stem: string): string {
  return stem.length > 3 && /([^aeiouylsz])\1$/.test(stem) ? stem.slice(0, -1) : stem;
}

// Words that say nothing about the subject, folded like a query word so that
// "wants", "uses" and "needed" drop out with "want", "use" and "need"; forms the
// folding cannot reach ("giving", "made") are listed. "vs" joins two subjects in
// "mlx vs ollama" and is not one. "llm" matches nearly every row because the
// index is filed under AI & LLM Engineering, and "ai" goes with it.
const FILLER = new Set(("a an and are as at be been but by can could did do does doing done for from " +
  "gave get gets getting give giving got help how i if in into is it its just like made make making " +
  "me my need needs of on or our should so some that the their them then there these they this " +
  "those to up use used using versus vs want way ways we what when where which who why will with " +
  "without would you your ai llm llms").split(" ").map(foldWord));

/** The page input stops at 120 characters, but a ?q= link can carry any length. */
const MAX_QUERY_CHARS = 240;
/** Packs below this many facts are router stubs more often than references. */
const THIN_PACK_FACTS = 5;
const NAME_WEIGHT = 3;
const TOPIC_WEIGHT = 1;
/** A compound found only as separate parts ("KV cache" for "kv-cache") scores this much less. */
const PARTS_DISCOUNT = 0.5;
/** A shorter term must match a whole word: " mode" would begin "model", " go" every "google". */
const PREFIX_MIN_LETTERS = 5;

// An index writes each word, and each hyphenated, dotted or slashed compound
// as one word, so "re-ranking", "reranking" and "llms.txt" all meet an entry.
const INDEX_COMPOUND = /[\p{L}\p{N}]+(?:[-./][\p{L}\p{N}]+)+/gu;
// A query joins only hyphens and dots: "agent/memory" names two things.
const QUERY_COMPOUND = /[\p{L}\p{N}]+(?:[-.][\p{L}\p{N}]+)+/gu;
const WORD = /[\p{L}\p{N}]+/gu;
const join = (compound: string) => compound.replace(/[-./]/g, "");

function words(text: string): string[] {
  const lower = text.toLowerCase();
  return [...(lower.match(WORD) ?? []), ...(lower.match(INDEX_COMPOUND) ?? []).map(join)];
}

// A space-delimited run of folded words. A term matches only at the start of a
// word, so " rag" finds "RAG" but not "storage"; a term of five letters or more
// may begin a longer word ("agent" finds "agentic"), a shorter one must be whole.
function indexText(text: string): string {
  return ` ${words(text).map(foldWord).join(" ")} `;
}

// A typed abbreviation or agent noun also counts as the form names spell out:
// short words must match whole (PREFIX_MIN_LETTERS), and "reranker" never
// folds to "reranking". Keys are folded query words. A Map, not an object
// literal: a reader can type "constructor", which an object would resolve to
// Object.prototype.constructor.
const SYNONYMS = new Map<string, string[]>(Object.entries({
  auth: ["authentication", "authorization"], chunker: ["chunking"], config: ["configuration"],
  db: ["database"], doc: ["documentation"], eval: ["evaluation"], evaluator: ["evaluation"],
  k8s: ["kubernetes"], perf: ["performance"], quantizer: ["quantization"], repo: ["repository"],
  reranker: ["reranking"], retriever: ["retrieval"],
}));

/** A query word, the long forms that also count for it, and for a compound
    the parts that also count when written apart. */
type Unit = { term: string; alts: string[]; parts: string[] };
const usable = (word: string) => word.length > 1 && !FILLER.has(word);

function units(query: string): Unit[] {
  const found = new Map<string, Unit>();
  const add = (word: string, parts: string[] = []) => {
    const term = foldWord(word);
    if (!usable(term) || found.has(term)) return;
    found.set(term, { term, alts: (SYNONYMS.get(term) ?? []).map(foldWord), parts: parts.map(foldWord).filter(usable) });
  };
  for (const token of query.slice(0, MAX_QUERY_CHARS).toLowerCase().split(/\s+/)) {
    for (const compound of token.match(QUERY_COMPOUND) ?? []) add(join(compound), compound.split(/[-.]/));
    for (const word of token.replace(QUERY_COMPOUND, " ").match(WORD) ?? []) add(word);
  }
  return [...found.values()];
}

/** The folded words of a query that can decide a match, in order, without duplicates. */
export function taskTerms(query: string): string[] {
  return units(query).map((unit) => unit.term);
}

export function indexReferences(items: ReferenceItem[]): IndexedReference[] {
  return items.map((item) => ({
    ...item,
    nameIndex: indexText([item.concept, ...(item.aliases ?? [])].join(" ")),
    topicIndex: indexText((item.topics ?? []).join(" ")),
  }));
}

const hasWord = (index: string, term: string) =>
  index.includes(term.length >= PREFIX_MIN_LETTERS ? ` ${term}` : ` ${term} `);

// The joined compound scores in full; its usable parts, all present, score a
// little less. "LLM-as-a-judge" keeps one usable part, "judg"; an all-filler
// compound such as "how-to" keeps none and matches only as written.
function weigh(index: string, unit: Unit, full: number): number {
  if (hasWord(index, unit.term) || unit.alts.some((alt) => hasWord(index, alt))) return full;
  return unit.parts.length > 0 && unit.parts.every((part) => hasWord(index, part)) ? full - PARTS_DISCOUNT : 0;
}

/**
 * Rank references by terms covered. Among equal coverage, a reference named
 * exactly what was typed comes first, then fuller packs before router stubs,
 * then name matches before topic matches, then bigger packs.
 */
export function taskHits(query: string, items: IndexedReference[], limit = 10): TaskSearch {
  const wanted = units(query);
  const terms = wanted.map((unit) => unit.term);
  if (!terms.length) return { terms, hits: [], total: 0, complete: false };
  const typed = query.slice(0, MAX_QUERY_CHARS).trim().toLowerCase();
  const scored = items.map((item) => {
    let covered = 0;
    let weight = 0;
    for (const unit of wanted) {
      const here = weigh(item.nameIndex, unit, NAME_WEIGHT) || weigh(item.topicIndex, unit, TOPIC_WEIGHT);
      if (here) { covered += 1; weight += here; }
    }
    return {
      item, covered, weight,
      exact: item.concept.toLowerCase() === typed ? 1 : 0,
      thin: item.facts < THIN_PACK_FACTS ? 1 : 0,
    };
  }).filter((hit) => hit.covered > 0);
  scored.sort((a, b) => b.covered - a.covered || b.exact - a.exact || a.thin - b.thin ||
    b.weight - a.weight || b.item.facts - a.item.facts || a.item.concept.localeCompare(b.item.concept, "en"));
  return {
    terms,
    hits: scored.slice(0, Math.max(0, limit)).map((hit) => hit.item),
    total: scored.length,
    complete: scored.length > 0 && scored[0].covered === terms.length,
  };
}

/** A facet title as search text: drops a list number ("3.", "3.2", "5a.", "1)"),
    emphasis stars and code ticks. A bare leading number ("2025-2026 frontier",
    "12V-2x6") and an underscore ("sm_120") belong to the name. */
export function cleanTitle(title: string): string {
  return title.replace(/^\s*(?:\d+(?:\.\d+)*[a-z]?[.)]|\d+(?:\.\d+)+)\s+/, "")
    .replace(/\\_/g, "_").replace(/[*`]/g, "").replace(/\s+/g, " ").trim();
}

/** The text "Copy reference" puts on the clipboard: the file and how to use it. */
export function promptReference(concept: string, url: string): string {
  return `Read this reference file before you answer: ${url}\n` +
    `It lists source-linked facts about ${concept}. Cite the source of each fact you use, ` +
    "and tell me when the file does not cover part of my question.";
}

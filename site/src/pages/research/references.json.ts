// /research/references.json: the search index /research/ fetches when a reader
// first focuses the search box or runs a search, or on load when the URL
// carries a ?q= search; otherwise never on page load. One row
// per facts file under the AI & LLM Engineering root, carrying the words a
// reader might use for it: the concept, its aliases, its family and the pack's
// distinctive facet titles. Facet titles that dozens of packs share
// ("Definitions", "Overview") name a template, not a subject, so they stay out.
// Pack summaries stay out too: many are router or skill text rather than a
// description of the concept.
import type { APIRoute } from "astro";
import { AI_ROOT, aiReferences } from "../../data/research";
import { context } from "../../data/context";
import { tree } from "../../data/tree";
import type { ConceptPack } from "../../data/types";
import { cleanTitle, type ReferenceIndex, type ReferenceItem } from "../../scripts/research-search";

// Built once, with the site; an adapter must never rerun this scan per request.
export const prerender = true;

// Keyed by file name, as tree/[slug].astro keys them: the file is what
// gen_concepts.py names after the slug the downloads use.
const packs = import.meta.glob<{ default: ConceptPack }>("../../data/concepts/*.json", { eager: true });
const packBySlug = new Map<string, ConceptPack>(
  Object.entries(packs).map(([path, mod]) => [
    (path.split("/").pop() ?? "").replace(/\.json$/, ""),
    mod.default,
  ]));

/** A title shared by this many packs, across every root, names a template. */
const TEMPLATE_TITLE_MIN_PACKS = 20;
/** Enough distinctive titles to find a pack; more only bloats the index. */
const MAX_TOPICS = 12;
const key = (text: string) => text.toLowerCase();

const titleCounts = new Map<string, number>();
for (const pack of packBySlug.values()) {
  for (const title of new Set((pack.facets ?? []).map((f) => key(cleanTitle(f.title))))) {
    titleCounts.set(title, (titleCounts.get(title) ?? 0) + 1);
  }
}

function topics(slug: string, own: string[], family: string | null): string[] {
  const seen = new Set(own.map(key));
  const out: string[] = [];
  for (const title of [family ?? "", ...(packBySlug.get(slug)?.facets ?? []).map((f) => cleanTitle(f.title))]) {
    if (!title || seen.has(key(title)) || (titleCounts.get(key(title)) ?? 0) >= TEMPLATE_TITLE_MIN_PACKS) continue;
    seen.add(key(title));
    out.push(title);
  }
  return out.slice(0, MAX_TOPICS);
}

const items: ReferenceItem[] = aiReferences.map((ref) => {
  const aliases = tree.nodes[ref.slug]?.aliases ?? [];
  return {
    slug: ref.slug,
    concept: ref.concept,
    facts: ref.facts,
    download: ref.download,
    family: ref.family,
    familySlug: ref.familySlug,
    aliases,
    topics: topics(ref.slug, [ref.concept, ...aliases], ref.family),
  };
});

const body: ReferenceIndex = { generated: context.generated, root: AI_ROOT, count: items.length, items };

export const GET: APIRoute = () => Response.json(body);

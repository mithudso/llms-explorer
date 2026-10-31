// Typed door onto research-tasks.json, the hand-curated list of common AI tasks
// /research/ is built around, plus the facts files under that list's root in
// context.json. tools/twins.py writes /research.md from the same JSON with the
// same drop rule, and test_research_page.py compares the page with its twin.
//
// Each task names concept slugs, articles and skills by id. The page resolves
// them against the build's own data and drops any that no longer exist, so a
// merged or renamed concept removes one row instead of printing a dead link;
// test_research_page.py fails CI on any dropped pick so the list gets updated.
// Picks favour packs with many sourced facts in English: several packs under
// these branches hold two router-stub facts or skill text in another language.
import { z } from "astro/zod";
import { context, type ContextConcept } from "./context";
import { tree } from "./tree";
import raw from "./research-tasks.json";

export interface ResearchReference {
  slug: string;
  concept: string;
  facts: number;
  download: string;
  /** The concept's node page, when the tree has a node for it. */
  page: string | null;
  /** The concept's primary parent in the tree (a node can have several). */
  family: string | null;
  familySlug: string | null;
}

const slug = z.string().regex(/^[a-z0-9][a-z0-9-]*$/);
const unique = <T>(values: T[]) => new Set(values).size === values.length;
const TaskRead = z.object({
  collection: z.enum(["blog", "examples"]),
  id: slug,
  /** The kind of evidence the article holds, not a topic label. */
  kind: z.string().min(1),
}).strict();
const ResearchTask = z.object({
  /** The section's anchor: /research/#task-<id>. */
  id: z.string().regex(/^[a-z][a-z0-9-]*$/),
  title: z.string().min(1),
  summary: z.string().min(1),
  /** The tree node the task links as "the <family> family": chosen by hand as
      the best place to keep reading, not a node every reference sits under. */
  family: slug,
  references: z.array(slug).min(1).refine(unique, "references must not repeat"),
  reads: z.array(TaskRead),
  skills: z.array(slug).refine(unique, "skills must not repeat"),
}).strict();
const ResearchTasks = z.object({
  /** The date the list was last curated by hand; nothing regenerates it. */
  generated: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  /** The context.json root the search index covers. */
  root: slug,
  tasks: z.array(ResearchTask).min(1).refine((tasks) => unique(tasks.map((t) => t.id)), "task ids must be unique"),
}).strict();
export type TaskRead = z.infer<typeof TaskRead>;
export type ResearchTask = z.infer<typeof ResearchTask>;

// The JSON is edited by hand: a bad edit fails the build and names the field,
// instead of rendering a blank section.
const parsed = ResearchTasks.safeParse(raw);
if (!parsed.success) {
  throw new Error(`src/data/research-tasks.json is invalid: ${parsed.error.issues
    .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`).join("; ")}`);
}
export const AI_ROOT = parsed.data.root;
export const RESEARCH_TASKS: ResearchTask[] = parsed.data.tasks;

// A root renamed by a tree regroup must fail the build: an empty root would
// publish a page announcing zero reference files.
const aiRoot = context.roots.find((root) => root.slug === AI_ROOT);
if (!aiRoot?.concepts.length) {
  throw new Error(`research-tasks.json root "${AI_ROOT}" is missing from context.json or files no concepts`);
}

// Every root is searched for a task's picks, so a concept refiled under
// another root still resolves; only the search index is limited to AI_ROOT.
const conceptsBySlug = new Map<string, ContextConcept>(
  context.roots.flatMap((root) => root.concepts.map((c) => [c.slug, c] as const)));

function toReference(c: ContextConcept): ResearchReference {
  const node = tree.nodes[c.slug];
  const parent = node?.parent_slug ? tree.nodes[node.parent_slug] : undefined;
  return {
    slug: c.slug,
    concept: c.concept,
    facts: c.facts,
    download: c.download,
    page: node ? `/tree/${c.slug}/` : null,
    family: parent?.concept ?? null,
    familySlug: parent?.slug ?? null,
  };
}

export const aiReferences: ResearchReference[] = aiRoot.concepts.map(toReference);
export const aiRootName = aiRoot.concept;

export function resolveReference(conceptSlug: string): ResearchReference | null {
  const c = conceptsBySlug.get(conceptSlug);
  return c ? toReference(c) : null;
}

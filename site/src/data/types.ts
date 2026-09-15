// Shapes of the generated data files under src/data/. The JSON is regenerated
// by tools/gen_*.py; these types are the contract the pages code against so a
// field rename in a generator fails `astro check` rather than rendering blank.

/** A child named by a node. `state` is "researched" when the child has a node
    of its own, "frontier" when it is only named. */
export interface TreeChild {
  concept: string;
  slug: string;
  state: string;
}

export interface TreeNode {
  aliases: string[];
  /** Contributed packs hanging off the node. Empty on every node today. */
  artifacts: Record<string, unknown> | unknown[];
  children: TreeChild[];
  concept: string;
  conceptsCount: number;
  hasPack: boolean;
  parent: string | null;
  parent_slug: string | null;
  researchedAt: string;
  skillId: string | null;
  skillSummary: string;
  slug: string;
  sourcesCount: number;
  state: string;
}

export interface FrontierEntry {
  concept: string;
  parent: string;
  parent_slug: string;
  source: string;
}

/** src/data/tree.json, written by tools/gen_tree.py. */
export interface Tree {
  edges: [string, string][];
  frontier: FrontierEntry[];
  generated: string;
  nodes: Record<string, TreeNode>;
  roots: string[];
}

export interface PackFact {
  text: string;
  source: string;
  note: string | null;
  /** Nesting depth from the source markdown's list indentation; absent on
      packs from gen_concepts.py, which renders them flat. */
  level?: number;
}

export interface PackFacet {
  title: string;
  facts: PackFact[];
}

export interface PackRelated {
  concept: string;
  relation: string;
  note?: string | null;
}

/** src/data/concepts/<slug>.json, one researched concept's content. */
export interface ConceptPack {
  slug: string;
  concept: string;
  generated: string;
  summary: string;
  facets: PackFacet[];
  related: PackRelated[];
}

export interface DirectoryFinding {
  attr: string;
  msg: string;
  severity: string;
}

/** One scored llms-full.txt in src/data/directory.json (tools/gen_directory.py). */
export interface DirectorySite {
  bytes: number;
  category: string;
  counts: { high: number; medium: number; low?: number; hygiene?: number; na?: number };
  fetched_at: string;
  findings: DirectoryFinding[];
  grade: string;
  groupScores: Record<string, number>;
  /** Finding counts keyed by rubric-group letter; a group with none is absent. */
  groups: Record<string, number>;
  key: string;
  name: string;
  pages: number;
  score: number;
  site: string;
  url: string;
}

export interface DemoHit {
  score: number;
  url: string;
  seq: number;
  text: string;
  /** Hybrid only: how many legs returned the unit. */
  legs?: number;
}

/** One recorded question in src/data/demo.json (tools/gen_demo.py). */
export interface DemoQuestion {
  q: string;
  kind: string;
  keyword: DemoHit[];
  vector: DemoHit[];
  hybrid: DemoHit[];
  ms: Record<string, number>;
}

export interface Demo {
  generated: string;
  docset: string;
  model: string;
  top: number;
  questions: DemoQuestion[];
}

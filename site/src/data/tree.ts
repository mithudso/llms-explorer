// The one typed door onto tree.json. Import `tree` from here, not the JSON:
// TypeScript types a JSON import as the literal it finds, so `nodes` becomes an
// object with 500 named keys that no runtime string can index. Cast once here
// and every page gets a string-keyed map.
import type { Tree } from "./types";
import raw from "./tree.json";

export const tree = raw as unknown as Tree;
export type { Tree, TreeNode, TreeChild, FrontierEntry } from "./types";

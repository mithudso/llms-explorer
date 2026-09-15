// Typed door onto directory.json, for the same reason as tree.ts: the literal
// type TypeScript infers for `groups` ({ P: number; C?: undefined; ... }) is not
// a string-keyed map, and every consumer indexes it by rubric-group letter.
import type { DirectorySite } from "./types";
import raw from "./directory.json";

export interface Directory {
  count: number;
  generated: string;
  sites: DirectorySite[];
}

export const directory = raw as unknown as Directory;
export type { DirectorySite, DirectoryFinding } from "./types";

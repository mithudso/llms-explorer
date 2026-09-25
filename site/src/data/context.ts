// Typed door onto context.json, for the same reason tree.ts exists: a JSON
// import is typed as the literal it finds, and the pages code against the
// contract in types.ts instead.
import type { ContextIndex } from "./types";
import raw from "./context.json";

export const context = raw as unknown as ContextIndex;
export type { ContextIndex, ContextRoot, ContextFile, ContextConcept } from "./types";

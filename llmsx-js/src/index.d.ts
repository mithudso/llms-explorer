/**
 * Types for llmsx-skills. Hand-written rather than generated: the package ships
 * plain ESM with no build step, and a `tsc` pipeline would be the only reason
 * this repo needed one.
 */

export declare const DEFAULT_MODEL: string;
export declare const DEFAULT_MAX_TOKENS: number;

export declare class SkillParseError extends Error {}

export declare class SkillNotFoundError extends Error {
  skillName: string;
  tried: string[];
}

export interface SkillFrontmatter {
  name?: string;
  description?: string;
  model?: string;
  effort?: string;
  version?: string;
  [key: string]: unknown;
}

export declare class Skill {
  name: string;
  path: string;
  frontmatter: SkillFrontmatter;
  body: string;

  get description(): string;
  /** The model the skill declares; advisory, overridden by `runSkill`'s option. */
  get model(): string | null;
  /** Advisory hint for an agent harness; never sent to the Messages API. */
  get effort(): string | null;
  get referencesDir(): string;

  referenceFiles(): Promise<string[]>;
  readReferences(): Promise<Record<string, string>>;
  systemPrompt(options?: { includeReferences?: boolean }): Promise<string>;
}

export interface SkillRun {
  text: string;
  skill: string;
  model: string;
  stopReason: string | null;
  usage: unknown;
  raw: unknown;
}

/** Anything with the Anthropic SDK's `.messages.create()` shape. */
export interface MessagesClient {
  messages: { create(args: Record<string, unknown>): unknown | Promise<unknown> };
}

/** Or a plain function taking the same arguments — what tests and stubs use. */
export type ClientFunction = (args: Record<string, unknown>) => unknown | Promise<unknown>;

export interface RunSkillOptions {
  taskInput: string;
  client?: MessagesClient | ClientFunction | null;
  model?: string | null;
  maxTokens?: number;
  includeReferences?: boolean;
  extraSystem?: string | null;
  [key: string]: unknown;
}

export declare function skillSearchPaths(): Promise<string[]>;
export declare function loadSkill(
  name: string,
  options?: { searchPaths?: string[] | null },
): Promise<Skill>;
export declare function loadSkillFile(
  filePath: string,
  options?: { name?: string | null },
): Promise<Skill>;
export declare function availableSkills(
  options?: { searchPaths?: string[] | null },
): Promise<string[]>;
export declare function runSkill(
  skill: Skill | string,
  options: RunSkillOptions,
): Promise<SkillRun>;

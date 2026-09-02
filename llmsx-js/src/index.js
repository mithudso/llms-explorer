/**
 * llmsx-skills — load a skill's markdown spec and run it against a model.
 *
 * A *skill* here is the `SKILL.md` file this repo and `~/.claude/skills`
 * already use: YAML frontmatter (name, description, model, …) over a markdown
 * body of instructions written to be followed by an agent.
 *
 * **What this module is, and is not.** It is a thin invocation layer: find the
 * file, parse it, build a system prompt from it, send the caller's task as the
 * user turn, hand back what the model said. It is *not* a reimplementation of
 * what those skills describe. Most of them orchestrate multi-pass loops, fan
 * out subagents, take filesystem locks and write back to a concept tree —
 * behaviour that belongs to an agent harness with tools, not to a library
 * function. Running `concept-family-explorer` through `runSkill` gets you one
 * model turn holding those instructions, not a saturation loop.
 *
 * The Python sibling (`../llmsx/llmsx/skills.py`) has the same API, the same
 * search-path rule and the same boundary; they are meant to stay in step.
 */

import { readFile, readdir, stat } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { parseFrontmatter, splitFrontmatter, SkillParseError } from "./frontmatter.js";

export { SkillParseError };

/** Used when neither the caller nor the skill's frontmatter names a model. */
export const DEFAULT_MODEL = "claude-sonnet-5";

/**
 * Bounded by default: a skill body is long, and an unbounded reply on a
 * 15k-token system prompt is the kind of bill nobody predicted.
 */
export const DEFAULT_MAX_TOKENS = 4096;

const SKILLS_REL = "skills";
const USER_SKILLS = path.join(homedir(), ".claude", "skills");

/**
 * No `SKILL.md` for that name on any search path. Carries the paths tried,
 * because "skill not found" is nearly always a search-path problem and the
 * list is the fix.
 */
export class SkillNotFoundError extends Error {
  constructor(name, tried) {
    const joined = tried.length ? tried.join("\n  ") : "(no search paths)";
    super(`no skill named ${JSON.stringify(name)}. Looked for SKILL.md under:\n  ${joined}`);
    this.name = "SkillNotFoundError";
    this.skillName = name;
    this.tried = tried;
  }
}

async function isFile(p) {
  try {
    return (await stat(p)).isFile();
  } catch {
    return false;
  }
}

async function isDir(p) {
  try {
    return (await stat(p)).isDirectory();
  } catch {
    return false;
  }
}

/** One parsed `SKILL.md`: its frontmatter, its body, and where it came from. */
export class Skill {
  constructor({ name, filePath, frontmatter, body }) {
    this.name = name;
    this.path = filePath;
    this.frontmatter = frontmatter;
    this.body = body;
  }

  get description() {
    return String(this.frontmatter.description ?? "").trim();
  }

  /**
   * The model the skill declares it wants to run under, if any. Advisory:
   * `runSkill` uses it as a default and the caller overrides it. The sibling
   * `effort` key is deliberately *not* forwarded to the API — it is a hint for
   * an agent harness, not a Messages API parameter.
   */
  get model() {
    return this.frontmatter.model ? String(this.frontmatter.model) : null;
  }

  get effort() {
    return this.frontmatter.effort ? String(this.frontmatter.effort) : null;
  }

  get referencesDir() {
    return path.join(path.dirname(this.path), "references");
  }

  /**
   * Every `references/*.md` beside the skill, sorted by name. Returns the whole
   * directory rather than only the files the body names: the bodies cite them
   * inconsistently, so filtering on citations drops files the skill depends on.
   */
  async referenceFiles() {
    if (!(await isDir(this.referencesDir))) return [];
    const entries = await readdir(this.referencesDir);
    return entries
      .filter((e) => e.endsWith(".md"))
      .sort()
      .map((e) => path.join(this.referencesDir, e));
  }

  async readReferences() {
    const out = {};
    for (const file of await this.referenceFiles()) {
      out[path.basename(file)] = await readFile(file, "utf8");
    }
    return out;
  }

  /**
   * The system message: the skill's own instructions, verbatim. The body is
   * passed through unedited — it is the artifact under test, and a library that
   * paraphrased it would be running something other than the skill the caller
   * asked for.
   */
  async systemPrompt({ includeReferences = false } = {}) {
    const parts = [`You are running the skill \`${this.name}\`.`];
    if (this.description) parts.push(`Skill description:\n${this.description}`);
    parts.push(this.body.trim());
    if (includeReferences) {
      const refs = await this.readReferences();
      for (const [filename, text] of Object.entries(refs)) {
        parts.push(`--- reference: references/${filename} ---\n${text.trim()}`);
      }
    }
    return parts.filter(Boolean).join("\n\n");
  }
}

/**
 * `skills/` at or above the working directory, then this checkout's own.
 * Same walk-upward rule the Python sibling uses.
 */
async function repoSkillsDirs() {
  const found = [];
  let dir = process.cwd();
  for (;;) {
    const candidate = path.join(dir, SKILLS_REL);
    if (await isDir(candidate)) found.push(candidate);
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  const here = path.dirname(fileURLToPath(import.meta.url));
  const installed = path.resolve(here, "..", "..", SKILLS_REL);
  if ((await isDir(installed)) && !found.includes(installed)) found.push(installed);
  return found;
}

/**
 * Directories searched by `loadSkill`, in order: `$LLMSX_SKILL_PATH`
 * (path.delimiter-separated) when set, then every `skills/` at or above the
 * cwd, then `~/.claude/skills`.
 */
export async function skillSearchPaths() {
  const env = process.env.LLMSX_SKILL_PATH;
  const paths = env
    ? env.split(path.delimiter).filter((p) => p.trim()).map((p) => p.trim())
    : [];
  paths.push(...(await repoSkillsDirs()));
  if (!paths.includes(USER_SKILLS)) paths.push(USER_SKILLS);
  return paths;
}

/** Parse one `SKILL.md` by path, bypassing the search. */
export async function loadSkillFile(filePath, { name = null } = {}) {
  const resolved = path.resolve(filePath);
  if (!(await isFile(resolved))) throw new SkillNotFoundError(name ?? resolved, [resolved]);
  const [frontmatterSrc, body] = splitFrontmatter(await readFile(resolved, "utf8"));
  const frontmatter = parseFrontmatter(frontmatterSrc);
  const resolvedName = String(
    frontmatter.name || name || path.basename(path.dirname(resolved)),
  );
  return new Skill({ name: resolvedName, filePath: resolved, frontmatter, body });
}

/**
 * Find `<dir>/<name>/SKILL.md` on the search path and parse it. Throws
 * `SkillNotFoundError` (never resolves to null) so a typo fails loudly at the
 * call site instead of arriving as an empty prompt at the API.
 */
export async function loadSkill(name, { searchPaths = null } = {}) {
  if (!name || !String(name).trim()) throw new SkillNotFoundError(String(name), []);
  const paths = searchPaths ?? (await skillSearchPaths());
  const tried = [];
  for (const dir of paths) {
    const candidate = path.join(dir, name, "SKILL.md");
    tried.push(candidate);
    if (await isFile(candidate)) return loadSkillFile(candidate, { name });
  }
  throw new SkillNotFoundError(name, tried);
}

/** Every skill name on the search path, deduped, first-hit order preserved. */
export async function availableSkills({ searchPaths = null } = {}) {
  const paths = searchPaths ?? (await skillSearchPaths());
  const names = [];
  for (const dir of paths) {
    if (!(await isDir(dir))) continue;
    for (const child of (await readdir(dir)).sort()) {
      if (names.includes(child)) continue;
      if (await isFile(path.join(dir, child, "SKILL.md"))) names.push(child);
    }
  }
  return names;
}

async function defaultClient() {
  try {
    const mod = await import("@anthropic-ai/sdk");
    const Anthropic = mod.default ?? mod.Anthropic;
    return new Anthropic();
  } catch (cause) {
    throw new Error(
      "no client passed and @anthropic-ai/sdk is not installed — " +
        "install it, or pass { client } to runSkill",
      { cause },
    );
  }
}

/**
 * The text of a Messages API response, tolerating a fake that returns a string.
 * A fake client in a test may hand back a plain string or a plain object; the
 * real SDK hands back one whose `content` is a list of blocks. All three are
 * accepted so a caller never has to build an SDK-shaped mock to test their own
 * code path.
 */
function extractText(response) {
  if (typeof response === "string") return response;
  const content = response?.content;
  if (content == null) return "";
  if (typeof content === "string") return content;
  return content.map((block) => block?.text ?? "").join("");
}

/**
 * Run one turn of `skill` over `taskInput` and return what came back.
 *
 * `client` is anything with `.messages.create(kwargs)` (the Anthropic SDK
 * shape), or a plain function taking those same kwargs — the function form is
 * what the tests use, and what any caller can use to record, cache or stub the
 * call without installing the SDK.
 *
 * One turn: no tool loop, no multi-pass convergence, no filesystem writes. See
 * the module docstring for why that is the honest boundary of this function.
 */
export async function runSkill(
  skill,
  {
    taskInput,
    client = null,
    model = null,
    maxTokens = DEFAULT_MAX_TOKENS,
    includeReferences = false,
    extraSystem = null,
    ...createArgs
  } = {},
) {
  const resolved = typeof skill === "string" ? await loadSkill(skill) : skill;
  if (!taskInput || !String(taskInput).trim()) {
    throw new Error("taskInput is empty — nothing for the skill to act on");
  }

  let system = await resolved.systemPrompt({ includeReferences });
  if (extraSystem) system = `${system}\n\n${extraSystem}`;
  const chosenModel = model ?? resolved.model ?? DEFAULT_MODEL;

  const args = {
    model: chosenModel,
    max_tokens: maxTokens,
    system,
    messages: [{ role: "user", content: taskInput }],
    ...createArgs,
  };

  const transport = client ?? (await defaultClient());
  const response =
    typeof transport === "function" && !transport.messages
      ? await transport(args)
      : await transport.messages.create(args);

  return {
    text: extractText(response),
    skill: resolved.name,
    model: chosenModel,
    stopReason: response?.stop_reason ?? null,
    usage: response?.usage ?? null,
    raw: response,
  };
}

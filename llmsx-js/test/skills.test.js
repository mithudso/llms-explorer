// llmsx-js/test/skills.test.js
// Offline: every client here is a fake. Nothing in this file opens a socket.
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  availableSkills,
  DEFAULT_MAX_TOKENS,
  loadSkill,
  loadSkillFile,
  runSkill,
  skillSearchPaths,
  SkillNotFoundError,
  SkillParseError,
} from "../src/index.js";
import { parseFrontmatter, splitFrontmatter } from "../src/frontmatter.js";

const FOLDED = `---
name: demo-skill
description: >-
  Turn a mess into a shape. TRIGGER: /demo, "do the demo thing".
  SKIP: something else entirely → other-skill.
version: "1.2.0"
model: claude-sonnet-5
effort: medium
tags: [llms, demo]
related_skills:
  - other-skill
  - third-skill
metadata:
  changelog: |
    2026-09-01 v1.2.0 — a nested block: with a colon in it
---
# Demo Skill

Body line one.

## Step 1

Do the thing.
`;

async function makeRoot() {
  return mkdtemp(path.join(tmpdir(), "llmsx-skills-"));
}

async function writeSkill(root, name, text = FOLDED) {
  const dir = path.join(root, name);
  await mkdir(path.join(dir, "references"), { recursive: true });
  await writeFile(path.join(dir, "SKILL.md"), text, "utf8");
  return dir;
}

// --- parsing ----------------------------------------------------------- //

test("frontmatter folds scalars and keeps the body", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const skill = await loadSkill("demo-skill", { searchPaths: [root] });

  assert.equal(skill.name, "demo-skill");
  assert.equal(skill.model, "claude-sonnet-5");
  assert.equal(skill.effort, "medium");
  assert.ok(skill.description.includes("TRIGGER: /demo"));
  assert.ok(!skill.description.includes("\n"), "a folded scalar is one line");
  assert.deepEqual(skill.frontmatter.related_skills, ["other-skill", "third-skill"]);
  assert.deepEqual(skill.frontmatter.tags, ["llms", "demo"]);
  assert.ok(skill.body.trimStart().startsWith("# Demo Skill"));
  await rm(root, { recursive: true, force: true });
});

test("the parser keeps a nested mapping instead of mangling it", () => {
  const [source] = splitFrontmatter(FOLDED);
  const parsed = parseFrontmatter(source);

  assert.equal(parsed.name, "demo-skill");
  assert.equal(parsed.version, "1.2.0"); // quotes stripped
  assert.deepEqual(parsed.tags, ["llms", "demo"]);
  assert.ok(parsed.description.includes("TRIGGER: /demo"));
  assert.ok(parsed.metadata.changelog.includes("with a colon in it"));
});

test("description-first frontmatter parses too", async () => {
  const root = await makeRoot();
  const text = FOLDED.replace("name: demo-skill\n", "").replace(
    'version: "1.2.0"',
    'name: desc-first\nversion: "1.2.0"',
  );
  await writeSkill(root, "desc-first", text);
  const skill = await loadSkill("desc-first", { searchPaths: [root] });
  assert.equal(skill.name, "desc-first");
  assert.ok(skill.description.startsWith("Turn a mess into a shape."));
  await rm(root, { recursive: true, force: true });
});

test("a file without frontmatter is a parse error", async () => {
  const root = await makeRoot();
  const dir = path.join(root, "bare");
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(dir, "SKILL.md"), "# no frontmatter here", "utf8");
  await assert.rejects(() => loadSkill("bare", { searchPaths: [root] }), SkillParseError);
  await rm(root, { recursive: true, force: true });
});

test("unclosed frontmatter is a parse error", async () => {
  const root = await makeRoot();
  const dir = path.join(root, "unclosed");
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(dir, "SKILL.md"), "---\nname: x\nno fence\n", "utf8");
  await assert.rejects(() => loadSkill("unclosed", { searchPaths: [root] }), SkillParseError);
  await rm(root, { recursive: true, force: true });
});

// --- loading ----------------------------------------------------------- //

test("a missing skill rejects with the paths tried", async () => {
  const root = await makeRoot();
  await assert.rejects(
    () => loadSkill("nope", { searchPaths: [root] }),
    (err) => {
      assert.ok(err instanceof SkillNotFoundError);
      assert.ok(err.message.includes("nope"));
      assert.ok(err.message.includes(root), "the fix is in the message");
      assert.ok(err.tried.length, "and machine-readable too");
      return true;
    },
  );
  await rm(root, { recursive: true, force: true });
});

test("search-path order is first hit wins", async () => {
  const root = await makeRoot();
  const first = path.join(root, "a");
  const second = path.join(root, "b");
  await writeSkill(first, "dupe", FOLDED.replace("model: claude-sonnet-5", "model: from-first"));
  await writeSkill(second, "dupe", FOLDED.replace("model: claude-sonnet-5", "model: from-second"));

  assert.equal((await loadSkill("dupe", { searchPaths: [first, second] })).model, "from-first");
  assert.equal((await loadSkill("dupe", { searchPaths: [second, first] })).model, "from-second");
  await rm(root, { recursive: true, force: true });
});

test("availableSkills lists and dedupes in search order", async () => {
  const root = await makeRoot();
  const first = path.join(root, "a");
  const second = path.join(root, "b");
  await writeSkill(first, "one");
  await writeSkill(first, "two");
  await writeSkill(second, "two");
  await writeSkill(second, "three");
  // sorted within a directory, directories in search order — `three` lands
  // after both of the first directory's, and `two` is not repeated.
  assert.deepEqual(await availableSkills({ searchPaths: [first, second] }), [
    "one",
    "two",
    "three",
  ]);
  await rm(root, { recursive: true, force: true });
});

test("$LLMSX_SKILL_PATH is searched first", async () => {
  const root = await makeRoot();
  await writeSkill(root, "env-skill");
  const previous = process.env.LLMSX_SKILL_PATH;
  process.env.LLMSX_SKILL_PATH = root;
  try {
    assert.equal((await skillSearchPaths())[0], root);
    assert.equal((await loadSkill("env-skill")).name, "demo-skill"); // frontmatter name wins
  } finally {
    if (previous === undefined) delete process.env.LLMSX_SKILL_PATH;
    else process.env.LLMSX_SKILL_PATH = previous;
    await rm(root, { recursive: true, force: true });
  }
});

// --- prompt assembly --------------------------------------------------- //

test("the system prompt carries the body verbatim", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const skill = await loadSkill("demo-skill", { searchPaths: [root] });
  const prompt = await skill.systemPrompt();
  assert.ok(prompt.includes("Do the thing."));
  assert.ok(prompt.includes("demo-skill"));
  assert.ok(!prompt.includes("reference:"), "not requested, not included");
  await rm(root, { recursive: true, force: true });
});

test("references are included only on request", async () => {
  const root = await makeRoot();
  const dir = await writeSkill(root, "demo-skill");
  await writeFile(path.join(dir, "references", "loop.md"), "The loop rule.", "utf8");
  const skill = await loadSkill("demo-skill", { searchPaths: [root] });

  assert.deepEqual((await skill.referenceFiles()).map((p) => path.basename(p)), ["loop.md"]);
  assert.ok(!(await skill.systemPrompt()).includes("The loop rule."));
  assert.ok((await skill.systemPrompt({ includeReferences: true })).includes("The loop rule."));
  await rm(root, { recursive: true, force: true });
});

// --- running ----------------------------------------------------------- //

function fakeClient(response) {
  const calls = [];
  return {
    calls,
    messages: {
      create(args) {
        calls.push(args);
        return response;
      },
    },
  };
}

const fakeResponse = (text) => ({
  content: [{ type: "text", text }],
  stop_reason: "end_turn",
  usage: { input_tokens: 11, output_tokens: 7 },
});

test("runSkill sends the skill as system and returns the text", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const skill = await loadSkill("demo-skill", { searchPaths: [root] });
  const client = fakeClient(fakeResponse("the answer"));

  const run = await runSkill(skill, { taskInput: "my messy notes", client });

  assert.equal(run.text, "the answer");
  assert.equal(run.skill, "demo-skill");
  assert.equal(run.model, "claude-sonnet-5"); // from the skill's frontmatter
  assert.equal(run.stopReason, "end_turn");
  assert.deepEqual(run.usage, { input_tokens: 11, output_tokens: 7 });

  const sent = client.calls[0];
  assert.ok(sent.system.includes("Do the thing."));
  assert.deepEqual(sent.messages, [{ role: "user", content: "my messy notes" }]);
  assert.equal(sent.max_tokens, DEFAULT_MAX_TOKENS);
  await rm(root, { recursive: true, force: true });
});

test("a caller's model and maxTokens override the frontmatter", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const client = fakeClient(fakeResponse("ok"));
  const run = await runSkill(await loadSkill("demo-skill", { searchPaths: [root] }), {
    taskInput: "input",
    client,
    model: "claude-opus-5",
    maxTokens: 99,
  });
  assert.equal(run.model, "claude-opus-5");
  assert.equal(client.calls[0].max_tokens, 99);
  await rm(root, { recursive: true, force: true });
});

test("a plain function is a valid client", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  let seen = null;
  const fake = (args) => {
    seen = args;
    return "plain string reply";
  };
  const run = await runSkill(await loadSkill("demo-skill", { searchPaths: [root] }), {
    taskInput: "input",
    client: fake,
  });
  assert.equal(run.text, "plain string reply");
  assert.equal(seen.messages[0].content, "input");
  await rm(root, { recursive: true, force: true });
});

test("empty taskInput is refused before any call", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const skill = await loadSkill("demo-skill", { searchPaths: [root] });
  const client = fakeClient(fakeResponse("never sent"));
  await assert.rejects(() => runSkill(skill, { taskInput: "   ", client }), /taskInput is empty/);
  assert.equal(client.calls.length, 0);
  await rm(root, { recursive: true, force: true });
});

test("runSkill accepts a name and loads it", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const previous = process.env.LLMSX_SKILL_PATH;
  process.env.LLMSX_SKILL_PATH = root;
  try {
    const run = await runSkill("demo-skill", {
      taskInput: "input",
      client: fakeClient(fakeResponse("named")),
    });
    assert.equal(run.text, "named");
  } finally {
    if (previous === undefined) delete process.env.LLMSX_SKILL_PATH;
    else process.env.LLMSX_SKILL_PATH = previous;
    await rm(root, { recursive: true, force: true });
  }
});

test("extraSystem is appended after the skill", async () => {
  const root = await makeRoot();
  await writeSkill(root, "demo-skill");
  const client = fakeClient(fakeResponse("ok"));
  await runSkill(await loadSkill("demo-skill", { searchPaths: [root] }), {
    taskInput: "input",
    client,
    extraSystem: "Answer in JSON.",
  });
  assert.ok(client.calls[0].system.trimEnd().endsWith("Answer in JSON."));
  await rm(root, { recursive: true, force: true });
});

// --- the real skills on disk ------------------------------------------- //

test("the repo skills parse", async (t) => {
  const here = path.dirname(new URL(import.meta.url).pathname);
  const root = path.resolve(here, "..", "..", "skills");
  const names = await availableSkills({ searchPaths: [root] });
  if (!names.length) {
    t.skip("no repo skills/ directory in this checkout");
    return;
  }
  for (const name of names) {
    const skill = await loadSkill(name, { searchPaths: [root] });
    assert.ok(skill.description, `${name} has no description`);
    assert.ok(skill.body.trim(), `${name} has an empty body`);
  }
});

test("loadSkillFile parses a real SKILL.md by path", async (t) => {
  const here = path.dirname(new URL(import.meta.url).pathname);
  const target = path.resolve(here, "..", "..", "skills", "notes-to-llms-txt", "SKILL.md");
  try {
    const skill = await loadSkillFile(target);
    assert.equal(skill.name, "notes-to-llms-txt");
    assert.equal(skill.model, "claude-sonnet-5");
    assert.ok(skill.description.includes("TRIGGER"));
  } catch (err) {
    if (err instanceof SkillNotFoundError) t.skip("skill not present in this checkout");
    else throw err;
  }
});

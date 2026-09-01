# llmsx-skills

Load a `SKILL.md` spec and run it against a model. The JS sibling of
[`llmsx.skills`](../llmsx/README.md#running-a-skill-llmsxskills) — same API,
same search-path rule, same boundary.

Zero dependencies. Node >= 20.

```js
import { availableSkills, loadSkill, runSkill } from "llmsx-skills";

await availableSkills();                       // every skill on the search path
const skill = await loadSkill("notes-to-llms-txt");
skill.description;                             // frontmatter
skill.model;                                   // the skill's own default model

const run = await runSkill(skill, { taskInput: "…my messy notes…", client });
console.log(run.text, run.model, run.usage);
```

## Search path

In order: `$LLMSX_SKILL_PATH` (`path.delimiter`-separated) when set, then every
`skills/` at or above the working directory, then `~/.claude/skills`. A miss
throws `SkillNotFoundError` listing every path tried — it never resolves to
null, because a typo that reaches the API as an empty prompt costs money to
discover.

## The client

`client` is anything with `.messages.create(args)` (the `@anthropic-ai/sdk`
shape), or a plain function taking the same argument object:

```js
const recorded = [];
await runSkill(skill, {
  taskInput: "…",
  client: (args) => { recorded.push(args); return "canned reply"; },
});
```

That function form is how the tests run offline, and how a caller stubs,
records or caches a call without installing the SDK. Omit `client` entirely and
the package lazily imports `@anthropic-ai/sdk`, throwing a clear error if it is
not installed rather than silently doing nothing.

## Options

| Option | Default | Effect |
|---|---|---|
| `taskInput` | *(required)* | the user turn; empty input is refused before any call |
| `client` | lazy `@anthropic-ai/sdk` | transport, per above |
| `model` | the skill's `model`, else `claude-sonnet-5` | model id |
| `maxTokens` | `4096` | bounded on purpose — skill bodies are long |
| `includeReferences` | `false` | append the skill's `references/*.md` to the system prompt |
| `extraSystem` | — | appended after the skill's own instructions |

Any other key is passed through to `messages.create`.

## What this is not

A thin invocation layer: one model turn, carrying the skill's instructions
verbatim. The skills themselves describe multi-pass loops, subagent fan-out,
filesystem locks and concept-tree writes — behaviour belonging to an agent
harness with tools. `runSkill` drives none of that; a caller who needs the loop
drives it.

## Tests

```bash
npm test        # node --test, no dependencies, no network
```

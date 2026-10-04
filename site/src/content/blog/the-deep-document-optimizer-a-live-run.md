---
title: "The Deep Document Optimizer — A Live Run"
description: "A trimmed Claude Code transcript of /ddo cleaning a corrupted Slack export in one iteration, from contract to close-out report, with a rollback command for its one judgment call."
date: "2026-10-04"
order: 3
---

This is a lightly trimmed transcript of a Claude Code session from 17 June 2026. `/ddo` is the Document Deep Optimizer, a skill that audits a document in numbered passes (0 to 14, with sub-passes such as 3.5, 10.5 and 11.5), applies every medium-or-higher fix in place, and repeats until none remain or an iteration cap is reached. I pointed it at a messy file: an export of a Slack thread about my skills tooling, with two pasted Claude conversations appended. Markdown escapes had corrupted nearly every line, and Slack residue was scattered through it.

Four things are worth watching. The optimizer writes a contract and a routing decision before it touches anything. It exempts quoted material from rewriting. After the edit it runs a verification gate, and when one check raises a false alarm it works out why. And it flags its one judgment-call deletion, with a rollback command.

The two pasted conversations in the target file appear in full in [Orientation — Worked Examples](/blog/orientation-worked-examples-the-tooling-explains-itself/). The skill, prompt, document and code optimizers (sko, pdo, ddo and cdo) are compared in [Semantic Skill Discovery and the Optimizer Family](/blog/semantic-skill-discovery-and-the-optimizer-family/). In the transcript, Claude's narration and reports are plain text, tables and a blockquote. Code blocks hold tool calls, their output and the final confirmation lines. My own interjections are in italics. Notes on what I trimmed and removed are at the end.

## Prompt and setup

```text
❯ Use the deep document optimizer on this filee ~/Downloads/skills_showcase.md
```

I'll use the Document Deep Optimizer on that file. Let me start by reading it, then invoke the skill.

```text
⏺ Read(~/Downloads/skills_showcase.md)
  Read 260 lines
```

This is a Slack-thread export (your infodump about the skill ecosystem) with two pasted Claude transcripts appended. I'll run the Document Deep Optimizer on it. Let me invoke the skill.

```text
⏺ Skill(ddo)
  Successfully loaded skill

⏺ Read(~/.claude/skills/writing-expert/references/ddo/SKILL.md)
  Read 520 lines
  Loaded .claude/CLAUDE.md
```

The skill and its instructions are loaded. This is a multi-step run, so let me set up task tracking and load the engine's supporting references in parallel.

```text
⏺ Read(~/.claude/skills/writing-expert/references/document-critique.md)
  Read 327 lines

⏺ Read(~/.claude/skill-consolidation/convergence-and-severity.md)
  Read 258 lines

⏺ Read(~/.claude/skills/writing-expert/references/kill-the-AI-ism.md)
  Read 278 lines

⏺ Read(~/.claude/skills/writing-expert/references/ddo/references/severity-calibration.md)
  Read 45 lines
```

*The first read of the severity table, at `ddo/severity-calibration.md`, shows no result in my copy. Two directory listings follow, and the table turns up under `ddo/references/`, next to `writing-skills.md`.*

I have the engine, the canonical convergence/severity model, the voice layer, and the severity-calibration table. Let me set up task tracking and take the mandatory pre-write snapshot.

```text
⏺ Bash(TS=$(date +%Y%m%d-%H%M%S); DIR=~/.claude/skill-consolidation/backups/ddo-$TS; mkdir -p "$DIR"; cp ~/Downloads/skills_showcase.md "$DIR/skills_showcase.md" && echo "Snapshot: $DIR/skills_showcase.md" && wc -w ~/Downloads/skills_showcase.md)
  Snapshot: ~/.claude/skill-consolidation/backups/ddo-20260617-123209/skills_showcase.md
  2737 ~/Downloads/skills_showcase.md
```

Snapshot saved (2,737 words). Here's the optimization contract and routing.

## The contract and routing

Optimization contract (Step 2):

| Field | Value |
|---|---|
| Target | `~/Downloads/skills_showcase.md` |
| Type | Showcase / capture — Slack-thread export + 2 pasted Claude Q&A transcripts |
| Audience | MongoDB colleagues & leadership (technical, internal) `[inferred: internal GitHub repo links, "MDB is paying for the tokens", internal Slack/Aha URLs]` |
| Purpose | Show what Mitch built across the skill ecosystem and why it raised his case-solve rate. |
| Reader action | Understand the architecture; appreciate/support/adopt the approach. |
| Success evidence | Reader grasps the hub-and-spoke + meta-research design and the demonstrated wins `[inferred: "showcase" filename + persuasive framing]` |
| Constraints | Internal-only (contains internal URLs + candid asides); preserve the two transcripts as verbatim exhibits; preserve all URLs, repo names, and factual claims. |
| Mode | full |
| Max iters | 3 |
| Converge | no medium-or-higher findings remain |

Writing-skill routing (Step 2.5):

| Field | Value |
|---|---|
| Document type | General prose / showcase (unknown → dynamic fallback) |
| Hub | writing-expert |
| References | `writing-expert/references/editing-and-revision.md` (skeleton), `kill-the-AI-ism.md` (loaded) |
| Voice layer | kill-the-AI-ism |
| Note | Region B (lines 76–258) = directly-quoted transcripts → Pass 13 immunity (quoted material); clean paste-corruption only, do not rephrase. |

> **Insight**
>
> - The decisive call here is the quoted-material immunity: the two appended Claude transcripts are exhibits, not prose to re-optimize. Pass 13's immunity list protects directly-quoted material, so I de-corrupt their markdown but never rewrite their sentences. That neatly avoids "re-optimizing already-optimized text."
> - The author's candid asides are voice + content on an internal doc, not meta-artifacts — DDO's "opinion I disagree with → never a finding" rule means I keep them. I'm cleaning the paste, not sanitizing the person.

## The audit

Now running the critique passes.

Pass 0 — Domain awareness: skill/prompt engineering + MongoDB TAM tooling. Activated writing-expert, kill-the-AI-ism. No regulated domain. Pass.

Findings table (calibrated for a general-prose showcase):

| Pass | Name | Severity | Finding |
|---|---|---|---|
| 1/2 | Intent/Structure | MAJOR | Lines 1–5 open with an unrelated context-doc / Aha-report question (unanswered fragments) that contradict the showcase purpose |
| 2 | Structure | MAJOR | Flat Slack dump, no organizing structure; reader can't navigate the showcase |
| 2 | Structure | MEDIUM | Two appended transcripts pasted raw with no framing as exhibits |
| 12 | Meta-artifact | MAJOR | Markdown-escape corruption throughout (`[ ] # ~ < > - _ .`) — renders literal backslashes everywhere (mechanical integrity) |
| 12 | Meta-artifact | MEDIUM | Slack-UI cruft: ~14 standalone timestamps, duplicate speaker labels, "Zip"/triplicated zip link, "1x", "\| Screen Recording…mov" fragment |
| 12/13 | Meta/Voice | MEDIUM | Live-chat navigational filler ("Ok I'm done now.", "please tell me to stop", "hold on this may be easier:") — scaffolding, not content |
| 3.5 | Terminology | MEDIUM | Inconsistent caps: glean/Glean, mcp/MCP, claude-code/Claude Code, AHA/Aha!, voyageai/VoyageAI, MDB/MongoDB in prose |
| 13 | Voice | MINOR→fix (co-located) | Typos: experrience, overheard→overhead, funcationality, WHIch, triaining, extertise, "versus and agent" |
| 10.5 | Verification | — | All URLs internal/auth-walled → unverifiable (requires auth); not altered. Self-referential claims about own tooling — left intact |
| 11.5 | Adversarial | — | Embedded `❯ Explain…` prompts + answers are exhibit content, not injection. Clean. No disprovable hallucinated IDs |
| 13 | Voice (Region B) | N/A | Transcripts = directly-quoted material → immune; de-corrupt formatting only, do not rephrase |

Pass 6 (completeness), Pass 3 (technical): showcase, not operational — no rollback/blockers needed; self-reported claims internally consistent. Pass.

## The rewrite

Findings recorded. Applying fixes now.

Nearly every line carries escape corruption, so I'll rewrite the file in one pass (de-escape + restructure + reproduce the transcripts faithfully as exhibits).

```text
⏺ Write(~/Downloads/skills_showcase.md)
  Added 100 lines, removed 163 lines
```

*The diff view runs to about 360 lines in my copy, interleaving old and new text. Most of it is the two appended Claude transcripts, which the optimizer says it kept verbatim as exhibits. Here is the new heading skeleton:*

```text
# Skills Ecosystem — Showcase
## The pieces I've built
## Meta-research: saturating a concept family
## Hub-and-spoke architecture (taming skill sprawl)
## Why I lean on skills over agents
## Semantic skill matching (proof of concept)
## Real-world tests
### Credit & personal finance
### Incident-responder training for a customer
## Where it started: mdb-tam and the case-triage extension
## Appendix: example sessions
### Example 1 — Explaining the optimizer family
#### 1. repo-bootstrapper — "repo-kickstarter"
#### 2. ddo / document-critique — "deep document"
#### 3. sko / skill-optimizer — "skill"
#### 4. cdo / code-deep-optimizer — "code"
#### 5. pdo / prompt-deep-optimizer — "prompt"
#### 6. deso / design-deep-optimizer — "image"
### Example 2 — /dr and the concept-family explorer
```

## The verification gate

Running the post-edit verification gate (Step 5.5) — mechanical integrity, fact-preservation, delta bound.

```text
⏺ Bash(post-edit gate: word count, code-fence parity, heading levels, residual escape artifacts, URL list, Slack-cruft residue)
  === word count ===
  2406 ~/Downloads/skills_showcase.md
  === code fences (should be even) ===
  4
  === heading levels ===
  (19 headings: 1 H1, 8 H2, 4 H3, 6 H4)
  === residual escape artifacts (should be 0) ===
  0
  === all URLs preserved ===
  (six links to internal repos and Slack files, omitted here)
  === Slack-cruft residue (should be 0) ===
  0
```

Gate passes: fences balanced (2 blocks), headings monotonic (#→##→###→####, no skips), 0 escape artifacts, 0 Slack cruft, all 6 showcase URLs intact. Word delta 2737 → 2406 (−12.1%) — a reduction from cleanup (no growth justification needed). Quick terminology/typo confirmation:

```text
⏺ Bash(count residual typos, lowercase term leaks, and any surviving text from the opening context-doc/Aha question)
  === residual typos (should be 0) ===
  8
  === lowercase term leaks in prose (glean/mcp as standalone words) ===
  none
  === opening context-doc/Aha text fully removed (should be 0) ===
  0
```

The count is inflated by case-insensitive matching (WHIch matches every "which"/"Which"). Let me check the actual misspellings case-sensitively.

```text
⏺ Bash(case-sensitive grep for the exact misspellings, then confirm the "overhead" fix landed)
  === exact misspellings (case-sensitive, should be 0) ===
  none — all fixed
  === 'skill overhead' present (the line-28 fix) ===
  21:One of the big issues is having too MANY skills that eat up your context. So I folded the skills into a hub-and-spoke architecture where they all cross-reference each other with specific "when to use" and "when not to use" sections — so they automatically route queries to the right skills without yet another agent or skill adding overhead.
```

All Medium+ findings applied; typos fixed, terminology standardized, opener removed. Pre-exit intent check: audience (internal), reader-action (navigable showcase), and constraints (transcripts verbatim, URLs preserved) all hold — no intent drift. A fresh re-read surfaces no corroborated Medium+ findings. Converged — clean (1 iteration, small profile).

Appending telemetry (fail-safe) and closing out.

```text
⏺ Bash(append four per-pass rows to ~/.claude/skill-consolidation/optimizer-telemetry.jsonl)
  telemetry appended (4 rows)
```

## The close-out report

/ddo complete — converged clean in one iteration.

**6a. Iteration summary**

| Iter | Blocking | Major | Medium | Minor | Nits | Action |
|---|---|---|---|---|---|---|
| 1 | 0 | 3 | 4 | ~7 | — | Fixed all Major + Medium; folded co-located typos; deferred voice |

**6b. Pass scorecard (final)**

| Pass | Name | Status |
|---|---|---|
| 0 | Domain awareness | writing-expert + kill-the-AI-ism activated |
| 1 | Intent | contract locked; off-topic opener removed |
| 2 | Structure | flat dump → 9 navigable sections + exhibit appendix |
| 3 | Technical correctness | self-report, internally consistent |
| 3.5 | Terminology | Glean, MCP, MongoDB, Claude Code, VoyageAI standardized |
| 6 | Completeness | N/A (showcase, not operational) |
| 10.5 | Verification | all URLs auth-walled → unverifiable (requires auth); not altered |
| 11.5 | Adversarial/hallucination | clean — embedded prompts are exhibit content, not injection |
| 12 | Meta-artifact cleanup | de-escaped all markdown; removed ~14 timestamps, dup labels, "1x", ".mov" fragment, triplicated zip link |
| 13 | Human-voice | Region A typos fixed; Region B transcripts kept verbatim (quoted-material immunity) |

**6c. Top-5 most impactful edits**

1. De-escaped the entire document — `[ ] # ~ < > _ .` rendered as literal backslashes on every line; now clean markdown.
2. Added a 9-section structure + exhibit appendix — the flat Slack dump is now a navigable showcase; the two transcripts are framed as "Example sessions."
3. Removed the off-topic context-doc/Aha opener (orig. lines 1–5) — unanswered account-admin fragments that contradicted the showcase purpose. Flagged: this is the one judgment-call deletion — see below.
4. Stripped Slack-UI cruft — standalone timestamps, duplicate speaker labels, the triplicated zip link, "1x", and the "| Screen Recording…mov" fragment.
5. Standardized terminology + fixed 8 typos (experience, overhead, functionality, Which, training, expertise, "an agent", kind of).

**6d. Deferred (Minor/Nit) and preserved-by-design**

- Kept your voice and candid asides — they are content/voice on an internal doc, not artifacts. DDO doesn't sanitize the author.
- Transcripts not rephrased — they're directly-quoted exhibits (Pass 13 immunity); I only restored their corrupted markdown.

**6e. File confirmation**

```text
Optimized document written to: ~/Downloads/skills_showcase.md
Original: 2737 words → Optimized: 2406 words (−12.1%)
Exit: CONVERGED_CLEAN (1 iteration, small profile)
```

One thing to confirm: I removed the opening context-doc + Aha-report question (and their two links — a Google Doc and an Aha share link) as accidental paste residue unrelated to the showcase. If that was intentional, restore from the snapshot.

Snapshot & rollback:

```text
cp ~/.claude/skill-consolidation/backups/ddo-20260617-123209/skills_showcase.md ~/Downloads/skills_showcase.md
```

## Notes on this transcript

- I cut repeated reads, the directory listings, the task-tracking calls, the diff body, a closing recap that repeated the report, and three short narration lines that only announced the next read. I turned the contract and routing lists into tables, reformatted the other tables as Markdown, dropped an all-dash "Calibrated?" column and the check marks, showed the "Insight" box as a blockquote, bolded the 6a to 6e labels, and changed the warning sign on the judgment-call deletion to the word "Flagged". The parenthesised lines inside the gate output are my condensed summaries of the original listings. Claude's narration and reports are otherwise as they appeared.
- The target file named an account in its opening fragment and a customer in its incident-responder training example. Every mention of those names is replaced by neutral wording or removed, as is an Aha share-link domain and every internal repo, Slack and Google Doc link. Home-directory paths appear as `~`.
- The regular expressions in the verification commands lost their backslashes when I copied the session. I describe each command and keep its output instead of reproducing a pattern that would not run as shown.
- The close-out report says "9 navigable sections". The gate's heading listing, condensed above, shows one title heading and eight second-level headings, one of them the appendix. I left Claude's figure as it appeared.
- One narration line in my copy ended mid-word ("small pr"). I completed it as "small profile", which is what the closing exit line says.
- The session date, 17 June 2026, comes from the snapshot folder name.

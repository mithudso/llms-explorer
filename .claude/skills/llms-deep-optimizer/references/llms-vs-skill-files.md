# How an llms file differs from a method/skill file

<!-- llms-deep-optimizer · references/llms-vs-skill-files.md · 2026-08-30 -->

The deep-optimizer family already optimizes prompts (`pdo`), skills (`sko`), documents
(`dfo`), queries (`dqo`). An llms file looks like a document and lives near skills, but it is
neither, and applying either rubric to it produces the wrong fixes. This note pins the
differences so `/ldo` and its siblings route correctly.

## The one-line distinction

A **skill file tells a model how to act**; an **llms file tells a model where the facts are**
(index) or **what the facts are** (facts/full). A skill is read once and obeyed; an llms file is
read many times and *followed* — every line is a promise that a link or a claim will pay off.

## Side by side

| Dimension | Skill / method file (`SKILL.md`) | llms index (`llms.txt`) | llms facts / full |
|---|---|---|---|
| Speech act | instruction ("do X when Y") | declaration ("X is at URL, it covers Y") | assertion ("X is true, per source#anchor") |
| Reader | the executing model, once per task | a routing model choosing where to look | a retriever or a reader answering |
| Voice | imperative, second person | third person, nominal | third person, extractive |
| Success metric | trigger accuracy + task outcome (sko Pass H) | question answered in ≤ 2 hops (P12) | probe hit rate + truthfulness (P8, P11) |
| Failure mode | over/under-trigger, drift, verbosity | dead link, vague description, wrong section | wrong claim, missing anchor, missing token |
| Size discipline | ~6k token soft / 10k hard, progressive disclosure into `references/` | ≤ 10 KB, hub-and-spoke split | unbounded, but a ladder (index/small/full) with published counts |
| Ownership | hand-authored, versioned in frontmatter | **generated** from a source (mirror/nav/tree); hand edits go into generator overrides | generated from the mirror + extractors + LLM units |
| Truth source | the author's judgment | the site's page list | the page text at the anchor |
| Steering content | expected (a skill IS steering) | forbidden (P4 — a docs file must not instruct the reader) | forbidden |
| Frontmatter | required YAML (`name`, `description`, `model`, `effort`) | none — spec is pure markdown; provenance goes in an HTML comment | none; unit lines carry their own `source:` |
| Freshness | `updated` date, family stamp | `generated` stamp ≥ mirror mtime (P15) | `verified-as-of` on volatile units |
| Cross-references | `SKIP:` edges, routing rows, `[[links]]` to peers | plain links only; nesting by path (most-specific wins) | anchors into pages; `related:` unit ids optional |
| Rights | ours | publishable (links + descriptions) | third-party full text is internal-only |

## Consequences for optimization

1. **Never "improve the prose".** A description that reads well but drops the exact flag
   name got worse. `dfo`'s clarity passes are wrong here; P3 optimizes for *tokens the reader
   will search for*, not for flow.
2. **Never add instructions.** `sko` adds when-to-use rules; an llms file gains nothing from
   "use this section when…" and loses trust (P9 flags it).
3. **Regenerate, don't edit.** Most fixes are changes to the generator's inputs (nav order,
   title, summary, member list, unit extractors) followed by `docset_refine export`. A hand
   edit that the generator cannot reproduce is a Medium finding (P15), because the next refine
   erases it.
4. **The unit of convergence is the link/unit, not the section.** `sko` converges when the
   description triggers correctly; `/ldo` converges when every link resolves and describes,
   every unit is anchored and true, and the probes hit. Section-level rewrites (P4) are the
   last thing to touch, and only with the demotion guard (no link lost).
5. **Evidence is external.** A skill finding can cite the skill's own text; an llms finding
   cites the page (link check), the mirror span (unit check) or the probe result. A finding
   with no external evidence is Low at most.

## Where they meet

- A skill's `references/` spoke about a site (e.g. `document-formats/references/llms-txt.md`)
  is *prose about* the topic; the site's `llms-facts.txt` is *the extracted claims*. The spoke
  should link the facts file rather than restate it; `sko` Pass A checks the link resolves,
  `/ldo` P2 checks the reverse when the facts file links back.
- A **topical llms file** (built from a fact pool — see `facts-to-llms-howto.md`) is the
  navigational twin of a hub skill: same section skeleton (concept-tree children), different
  content (links + anchored facts rather than method). Keep both; route method questions to the
  skill and lookup questions to the llms file (`hub_route` learns this from the router corpus).
- `pdo` owns the prompts inside the generator (`docset_refine units`, description polish);
  `/ldo` reports when their output fails P3/P8 but does not rewrite the prompt.

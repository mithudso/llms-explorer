# Look-for-llms-files-first section (Pass P)

The standard section a skill carries when it works on a subject that has llms files. Source rules: `llms-txt-tooling/references/llms-family-format.md` section 5 and the `llms-usage-guidance` skill. Pass P checks for this section and adds it when missing.

The evidence for the section is narrow. In the 256-run measurement behind `llms-usage-guidance`, agents that had the repo opened an llms file once and saved nothing. The files are meant for readers without the repo, such as an agent that fetches a docs site. That case was not measured. Step 4 of the standard text therefore tells an agent that has the repo to grep the code before it opens an llms file.

## Standard text

Paste this block into the target's `SKILL.md`, after the first description or overview section. Replace `<subject>` with the repo, site, docset, domain or store the skill works on.

```markdown
## Look for llms files first

Before reading `<subject>` raw, look for its llms files and open them by size. If you have the repo, step 4 sets the order.
1. Look in this order: the subject's `llms.txt` (repo root, `~/.global-ai-hub/skills.llms/<owner>-<repo>.repo/`, `~/.global-ai-hub/llms-concepts/<slug>.llms/`, or a docs site's `/llms.txt`); memory-central rows (`python3 ~/.global-ai-hub/scripts/keyword_index.py query "<terms>" --prefix ~/.llms --top 5 --mode any --json`); the hub indexes (`hub_query_docset`, `hub_search_keyword`, `hub_search_codebase`).
2. Run `wc -c` first (or read `x-markdown-tokens` on a remote). Read a file whole only when it fits. Otherwise search it.
3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
4. If you have the repo, grep the code before you open an llms file. The code is the authority, and llms files rarely help there. Use them to find the right file, and verify every fact you act on against its `path:line`.
5. Index and llms hits are leads. Confirm them with Read before you act.
```

The block is 8 lines. Keep it within 6 to 10 lines. Adapt step 1 to the subject; keep steps 2 to 5 as written.

## When it applies

Add the section when the skill works on any of these:

- a repo or codebase (audit, refactor, review, bootstrap, migrate);
- a docs site or docset (lookup, summary, crawl, conversion);
- a research domain with a concept pack or llms family;
- a memory store (memory-central, notes, handoffs, registries);
- another skill tree or hub (skill-optimizer is one: it works on skill trees).

## When it does not apply

Skip the section, and record `llms-first: n/a (<reason>)`, when the skill:

- is pure style or formatting (prose voice, commit messages, code formatters, UI copy);
- transforms only text the user pastes in the same turn;
- is itself the producer of llms files (`llms-txt-tooling`, including its `references/llms-deep-optimizer/` spoke); those cite the format spec directly;
- is a thin command wrapper or hub router with no subject of its own.

## Pass P check

1. Decide applicability with the lists above. State the reason in the report.
2. If the section applies and the target skill has no `## Look for llms files first` heading, file a **Medium** finding. A section under another heading counts as present when its body names `llms.txt`, a size check, and verify-against-source.
3. Fix: insert the standard text with `<subject>` filled in. Put long subject-specific lookups in a `references/` file and keep the section at 6 to 10 lines.
4. Present but wrong (no size-first rule, or reads `llms-full.txt` whole, or treats llms hits as facts): file a **Medium** finding and replace it with the standard text.
5. Never add the section to a skill that does not apply. Rate a false add **Medium** and revert it. A Low rating would leave it in place, because `/sko` skips Low findings.

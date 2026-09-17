# Empirical mode: champion and challenger held-out loop

skill-optimizer already runs this loop in part. **Pass H** is a 20-query trigger-accuracy eval with a persisted held-out corpus (`~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`). Empirical mode names the promotion gate around it explicitly, per the shared contract `~/.claude/skill-consolidation/champion-challenger.md` (**cite, don't restate**). It is **on by default** when an eval corpus and must-pass invariants are present: the gated promotion auto-runs and persists the champion (the optimized skill plus its eval state) across runs, with no trigger needed. Opt out with `--dry-run`, `--no-promote`, or `--structural-only`.

Calibration:

- **Score** is Pass H trigger accuracy on a **held-out** split of the eval corpus (at least 9/10 positives, at most 1/10 false positives).
- **Must-pass (veto)** means no Pass I peer-collision regression, a description within the 1000-char Pass M cap, and frontmatter that parses (Passes G and L). Any regression vetoes promotion regardless of trigger-accuracy gain.
- **Eval surface** is the persisted eval corpus, with a frozen held-out split that never drives a description or routing edit and only gates promotion.
- **One change per round** (one description rewrite, one whenToUse phrasing, one SKIP edge) so each promotion is attributable. Never tune the description against the held-out queries: that is exactly the overfitting the eval exists to catch.

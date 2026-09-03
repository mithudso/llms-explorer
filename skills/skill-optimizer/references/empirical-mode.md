# Empirical mode — champion–challenger held-out loop

skill-optimizer already runs this loop in part: **Pass H** is a 20-query trigger-accuracy eval with a persisted held-out corpus (`~/.claude/skill-consolidation/evals/<skill-id>.eval.jsonl`). Empirical mode names the promotion gate around it explicitly, per the shared contract `~/.claude/skill-consolidation/champion-challenger.md` (**cite, don't restate**). It is **on by default** when an eval corpus + must-pass invariants are present: the gated promotion auto-runs and persists the champion (the optimized skill + its eval state) across runs — no trigger; opt out with `--dry-run`/`--no-promote`/`--structural-only`.

Calibration:

- **Score** = Pass H trigger accuracy on a **held-out** split of the eval corpus (≥ 9/10 positives, ≤ 1/10 false positives).
- **Must-pass (veto)** = no Pass I peer-collision regression; description ≤ 1000 chars (Pass M cap); frontmatter parses (Pass G/L). Any regression vetoes promotion regardless of trigger-accuracy gain.
- **Eval surface** = the persisted eval corpus, with a frozen held-out split that never drives a description/routing edit, only gates promotion.
- **One change per round** (one description rewrite, one whenToUse phrasing, one SKIP edge) so each promotion is attributable. Never tune the description against the held-out queries — that is exactly the overfitting the eval exists to catch.

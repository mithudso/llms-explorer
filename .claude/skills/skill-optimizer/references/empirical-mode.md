# Empirical mode: champion and challenger held-out loop

Pass H provides a 20-query trigger audit. Resolve its persisted source corpus with `corpus-scope.md`. Empirical mode adds the promotion gate in `shared/champion-challenger.md`. It is on by default only when corpus sizes, must-pass invariants and working/holdout splits satisfy that contract. The standard 20-query audit is exploratory and does not qualify for empirical promotion. An eligible promotion persists the champion and its eval state. Opt out with `--dry-run`, `--no-promote` or `--structural-only`.

Calibration:

- **Score** uses the eligible **held-out** split's actual class counts: positive success rate ≥90% and false-positive rate ≤10%. Report both numerators and denominators. Both classes must be present; otherwise the promotion gate is unavailable. The standard Pass H audit remains 10 positives plus 10 negatives.
- **Must-pass (veto)** means no Pass I peer-collision regression, a description within the 1000-char Pass M cap, and frontmatter that parses (Passes G and L). Any regression vetoes promotion regardless of trigger-accuracy gain.
- **Eval surface** is the persisted eval corpus, with a frozen held-out split that never drives a description or routing edit and only gates promotion.
- **One change per round** (one description rewrite, one whenToUse phrasing, one SKIP edge) so each promotion is attributable. Never tune the description against the held-out queries: that is exactly the overfitting the eval exists to catch.

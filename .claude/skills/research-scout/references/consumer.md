# Consume research-scout handoffs

Use this before discovery in `/dr`, concept-family-explorer (CFE), and rabbithole.
The installed helper lives beside research-scout at `scripts/scout.py`. A repository
copy lives in `.claude/skills/research-scout/`. No scout exists is a normal outcome:
continue ordinary research. Never start a new scout or block research solely for a miss.

1. For a named concept, run `scout.py seeds --concept "<exact concept>" --parent
   "<exact parent>"`. It validates bundles, returns at most six distinct URLs,
   prefers readable leads, and records bundle hash/run/revision/access. If the
   parent is unknown and several parents match, it returns no seeds and a warning.
   Resolve that ambiguity against the live inventory; do not guess from a slug.
2. For CFE family discovery, also run `scout.py find --parent "<exact subject>"`
   and review `frontier_candidates`. Inspect the referenced bundles and run
   `check` before using them. Repeat live inventory/alias checks, placement and
   CVS yourself. Proposals do not establish GAP or imply permission to register.
3. For rabbithole, use only leads inside the scoped concept. Read relevant
   mechanism, limitation, issue and disagreement sources in Pass 0 and later
   gap-focused passes. Hand out-of-scope siblings to CFE. A scout URL, repeated
   query or repeated source adds no researched novelty by itself.
4. Lookup/refetch source text, check applicability/freshness and originating
   organization, then bind any new claim to readable evidence. `readable` is
   the scout's access observation, not your read receipt. Keep snippet-only,
   blocked, stale and partial observations explicit. Missing/malformed bundles
   are reported; ordinary discovery remains available.
5. Record retained and rejected leads and why in the research run's existing
   notes/briefs, with scout run, revision, bundle hash, source ID and URL.
   Keep provenance private. Never edit the scout or another research run.

## Deliver leads to headless workers

Slim workers do not load the skill catalog. Claude `/dr` must use the installed
bridge for its existing **research** call:

```bash
python3 ~/.claude/skills/research-scout/scripts/with_scout.py --runtime ~/.global-ai-hub/scripts/dr_run.py research <slug>
```

All existing research flags, model choices and gates remain owned by the runtime.
The bridge adds validated candidate seeds and a bounded provenance block to its
normal worker briefs. It does not import claims, mark completion or replace a
source cache. `research <slug> --dry-run` writes ordinary briefs without inference;
use a disposable test run for verification. Use the original runtime directly
for `init`, `source`, `gate`, `render` and `finish`.

The repository's native Codex adapter imports the same helper automatically from
the repository bundle (installed bundle fallback). Its normal `research` command
already includes scout seeds, so it does not use the Claude bridge. If neither
helper exists, it continues without scout leads. Preserve all normal discovery,
negation, authority, scope, claim-gate and saturation rules. A `ready` scout is
not a completed or verified research run.

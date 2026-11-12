## Flags

| Flag | Effect | Default |
|---|---|---|
| `--depth quick\|standard\|deep` | deep-read budget 40 / 150 / 500 artifacts | standard |
| `--files N` | explicit deep-read budget | per depth |
| `--scope <subpath>` | limit to a subtree, repeatable (e.g. `--scope "05 Cases & Retros"`) | whole root |
| `--since YYYY-MM-DD` | only deep-read artifacts modified on/after this date | none |
| `--stale-after DAYS` | staleness threshold for Guard 7 | 90 |
| `--include-archive` | deep-read `99 Archive` and archived-folder trees | shallow-card only |
| `--no-glean` | folder-only pack (header says so) | harvest |
| `--glean-only` | skip the local census (drive unmounted) | both halves |
| `--no-drive-resolve` | skip Phase 2; filename-level pack only | resolve |
| `--out <dir>` | output dir override, must stay inside the customer folder | `<Customer>/llms/` |
| `--yes` | pre-authorize the Guard 8 shared-drive write | confirm first |
| `--force` | full overwrite of an existing same-customer pack | refuse without it |
| `--refresh` | incremental re-run against the existing pack | full run |

## Relationship to siblings

- `crawl-repo-to-llms`: same output grammar, different corpus — a git tree with code,
  infra, history and indexes. Use it for the account's *code* artifacts (a monitoring
  starter, an alerting implementation) when they deserve a dossier of their own; this
  skill cards such a directory as one artifact and links out.
- `crawl-to-llms-txt`: condenses a site or repo into referenceable commands and gotchas.
  This skill invokes its keep/drop filter and condensation grammar for the prose it reads,
  rather than reimplementing them.
- `customer-context-architect` (`/context`, `/cc`): produces ONE dense narrative context
  document plus Monday/Slack write-backs and a prioritized TODO. This skill is read-only,
  folder-wide, and emits a *family* of machine-loadable files. They compose: run this to
  build the pack, then `/cc` to write the human-facing context doc from it.
- Per-account report and pipeline skills: consume the pack;
  they write the weekly, EBR or board pass. This skill never writes a customer deliverable.
- `account-data-collector` (agent): fans out to collect raw artifacts. This skill
  synthesizes; use the agent first when the corpus must be gathered from many systems at
  once, then point this skill at the result.
- `llms-deep-optimizer` (`/ldo`): quality-pass judge for the emitted family — the correct
  follow-up, and the reason the header and tag grammar match the sibling skills.
- `document-distiller(-offline)`: ONE document → unit inventory.
- `llms-concept-abstractor` (`/lca`): ONE concept across the corpus (concept axis) — e.g.
  "everything this account has ever said about sharding".
- `local-semantic-search`: the accounts with `~/Documents/engagement_indexes/<Customer>/`
  (SQLite FTS5 + ChromaDB, per `Artifact_Library_Indexes.md`) already have a keyword and a
  semantic index; query them to *find* artifacts fast, and record their existence in
  `llms-sources.md` so the next agent aims at the right store.

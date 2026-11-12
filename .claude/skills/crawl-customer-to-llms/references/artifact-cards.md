### Phase 3: Per-artifact cards

One card per enumerated artifact. Deep-read artifacts get every field evidenced; shallow
ones get the structural fields plus an `[asserted]` purpose and are marked `shallow`.

| Field | Content | Sourcing |
|---|---|---|
| `id` | Drive fileId, or the root-relative path for local-only files | census / xattr |
| `title` | document title as it appears in Drive, verbatim | Drive metadata |
| `path` | root-relative path, including which root for multi-root accounts | census |
| `role` | Phase 1 role | census / content |
| `purpose` | what it is and what it decides, one or two lines | `[src:]` if stated, else `[asserted]` |
| `why` | why it exists — the meeting, incident, initiative or request that produced it | content, dates, neighbors |
| `when` | when a future agent would open it ("prepping the weekly", "case `<number>` recurs") | derived |
| `authority` | system-of-record · signed/finalized · current snapshot · working draft · superseded · archive | taxonomy folder + content |
| `freshness` | modifiedTime, and `[stale:]` if past `--stale-after` | Drive metadata / mtime |
| `owner` | last editor / named owner where the corpus states one | Drive metadata, doc content |
| `entities` | clusters, case numbers, tickets, initiatives, people named in it | extraction |
| `supersedes` / `superseded-by` | dated snapshots, `(1)` copies, `.md` mirrors of a `.gdoc` | dedupe pass |
| `link` | `https://docs.google.com/document/d/<id>` (or `/spreadsheets/`, `/presentation/`); local path when there is no ID | derived |
| `importance` | `critical` / `high` / `normal` / `peripheral` | rubric below |
| `read-status` | `full` / `partial` / `shallow` / `unresolved` | Phase 2 |
| `gotchas` | artifact-scoped caveats: known-wrong sections, disputed numbers, "do not share" markings | `[src:]` or `[asserted]` |

**Importance rubric** (deterministic, so re-runs are stable): `critical` = the current
context file, the current weekly update, any open-case analysis or active RCA, the live
initiative tracker, the incident-management guide, and anything the account's own
`_meta/INDEX.md` marks as canonical. `high` = referenced by a critical artifact, or
modified inside the `--since` window, or named in `00 Overview`/`README`. `normal` =
ordinary account doc. `peripheral` = archive, superseded snapshots, `(1)` duplicates,
`.md` mirrors of a resolved `.gdoc`, one-off drafts, fixtures. Report the count per tier;
an account where everything is `critical` means the rubric was applied lazily.

**Duplicate families are real and must be collapsed, not deleted.** These accounts
reliably contain: `Foo.gdoc` alongside `Foo.md` (an export), `Foo.gdoc` alongside
`Foo (1).gdoc` (a copy), `X Context File.gdoc` alongside `contexts/x-context-2026-08-28.md`
(a snapshot), and `Doc.gdoc.gdoc` (a double-suffixed stub). Pick one canonical per family
by authority then recency, card the rest as `superseded-by` pointers, and **diff the
canonical against its nearest sibling** — where they disagree, that is a `[conflict:]`,
because someone edited one copy and not the other.

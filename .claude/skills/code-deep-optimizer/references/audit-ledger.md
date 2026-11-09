# Audit ledger and run receipt — code-deep-optimizer

> Reference for `code-deep-optimizer`. SKILL.md § Architecture step 1 and § Report format point
> here. The engine is `scripts/cdo_ledger.py` (stdlib; run `python3 scripts/cdo_ledger.py --help`).

## Why it exists

A repo run that touches 35 of 224 files leaves 189 unreviewed, and the next run starts from
scratch (observed: solmargintrader's whole-repo run; net-dns-monitor was optimized 3 times in 3
weeks). The ledger makes coverage cumulative: file → content sha → passes run → date → findings.

## Where it lives

`<target repo>/.cdo/ledger.json`, committed with the repo. It is deterministic JSON (sorted keys),
so a re-run that changes nothing produces no diff. Files carry the git blob sha (`git hash-object`),
not an mtime.

## Run protocol (repo mode)

1. `cdo_ledger.py begin --repo <R> [--full] [--quick]`
2. `cdo_ledger.py plan --repo <R> [--full] [--max-files N] --json` — this list **replaces** the
   Stage-1 enumeration. Reasons: `new`, `changed`, `quick-only` (only triaged with `--quick`, which
   is not coverage), `full` (`--full` ignores the ledger). Files not in the list are reported as
   "unchanged since last review" and are not re-read. Files cut by `--max-files` stay unrecorded,
   so the next run picks them up first; emit them as the ready-to-run follow-up.
3. Run the passes as usual. After each file's passes complete:
   `cdo_ledger.py record --repo <R> --passes C1,C2,... --findings <n> --verdict <CLEAN|...> <file>`
   Record only the passes that actually ran on that file; repo-scope passes (M3, T2, T3) are
   recorded once with `pass <ID> --state ran`.
4. A pass that did not run: `cdo_ledger.py pass <ID> --state na|blocked --reason "<why>"`.
5. `cdo_ledger.py receipt --repo <R> --status <Status>` and paste the output into the report as
   section "Passes that ran". Exit 2 means a pass has no row at all: the skill's skip protocol says
   "never silently dropped", so go back and run it or record the reason before reporting.

`--scope=changed` and `--scope=<paths>` still work; the ledger only narrows the default repo scope.
A file whose sha changed after review (including by this run's own fixes) is re-recorded at its
new sha after the final verify, so an applied fix does not make it look "changed" next time.

## `--full`

Ignores the ledger for planning and still records results. Use it after a cdo version bump that
adds passes, or when the owner asks for a whole-repo audit. Do not use it as the default.

## Receipt (end of every run)

The receipt lists all 18 fix-track passes plus conditional M5 with state (`ran`, `na`, `blocked`),
the number of files each covered, the mode, the Status, files reviewed this run, and ledger
coverage (`covered of total`, remaining). It is the answer to "what did this run actually do".

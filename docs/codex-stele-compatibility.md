# Codex Stele compatibility repair

Stele 0.61.0 installs a `stele-search` role that pins `gpt-5.4-mini`. That
model can fail on a ChatGPT account before the role reads the graph. The Codex
plugin also omits the context briefing and operator protocols its skills require.
The context-loading skill requests Claude-specific delegation fields and Haiku.

Preview and apply the local repair from the repository root:

```sh
python3 scripts/repair_codex_stele.py
python3 scripts/repair_codex_stele.py --apply
```

The script removes only the known unsupported model pin. The role inherits the
parent's available model and keeps its existing read-only sandbox, low reasoning
effort, and other policy. A different user-selected model is preserved.

The script repairs both the local Stele Codex marketplace source and its 0.61.0
installed cache. It places the canonical context and operator protocols under
`skills/<skill>/references/`, so they travel with each skill. Operator assets
include the worker, reviewer, and checked-loop protocols. It rewrites their skill
pointers and changes context delegation to the native Codex primitive with an
inherited model and explicit read-only instructions. It leaves the Claude plugin,
MCP configuration, and graph data unchanged.

The default is a dry run. `--apply` validates the entire plan before creating
backups or changing files. It refuses unrecognized versions, customized skill or
protocol text, malformed roles, and symlink targets. Each upstream asset has a
reviewed SHA-256 signature. The script records every changed path and saves all
existing originals before its first write under:

```text
~/.stele/compat-backups/codex-stele-<UTC timestamp>/manifest.json
```

A second run makes no changes. The backup manifest is also how the script
recognizes its own repaired skill text. Keep those backups while this repair is
installed. `--codex-dir` and `--stele-dir` can select fixture installations.

For rollback, read that manifest and first compare every current file with its
`after_sha256`. If a file differs, preserve the later edit and reconcile it
manually. For unchanged repaired files, copy the named `backup` file to `path`.
For a record with `backup: null`, remove only the listed newly created file.
Restore all records from the same manifest; do not restore other plugin files.

The script does not restart or reload active sessions. An existing session can
retain the old role metadata. Verify activation in a fresh Codex process: delegate
a read-only graph lookup to `stele-search`, then use the installed context-loading
skill for a bounded briefing. A file diff alone does not establish activation.

Use a normal fresh session for the delegation check. In the observed Codex CLI,
`codex exec --ephemeral` failed to spawn the worker with
`invalid thread-store request: no rollout found`. A fresh session without
`--ephemeral` completed the native delegation and actual Stele reads. The
skill's direct read-only fallback still produced a briefing in the ephemeral run;
that fallback did not establish successful delegation.

A Stele reinstall or update can regenerate the marketplace and role. Preview the
repair again after reinstalling 0.61.0. A newer version or changed upstream asset
requires review before extending the signatures; this script refuses to guess.

Run the focused tests with the standard library:

```sh
python3 -m unittest discover -s scripts/tests -p test_repair_codex_stele.py -v
```

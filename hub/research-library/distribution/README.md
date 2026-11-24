# MongoDB Research Coworker Kit

Use the shared skill and research libraries from another machine without copying
the research corpus or database credentials. Start with [QUICKSTART.md](QUICKSTART.md).
[TOOLS.md](TOOLS.md) lists both MCP services and their exact tools.

The kit contains a standalone Python client, an optional skill installer, the
five-file `research-library-mongodb` skill, and four optional research modes:
`dr`, `cfe`, `concept-family-explorer`, and `rabbithole`. The five skills contain
13 files in total. The remaining files are this guide, the quickstart, tool
reference, installer, client, writer enrollment script, repository license, and integrity/provenance
manifest. Tokens, client configuration, source bodies, and research state are
excluded.

The installer defaults to the library skill only. It does not configure MCP,
replace existing skills, or change another installation. Use a research reader
credential for discovery. For an authorized writing assignment, run
`python3 writer_request.py --token-file NEW_FILE` in a private directory and
send the printed credential ID to the library operator. The operator can grant
time-limited access under your name and revoke it individually. The token
stays on your machine. Writers have access to the managed research corpus.
The optional skill service uses its own credential.

`manifest.json` records package version, source provenance, and SHA-256 hashes
for every other package file. `python3 install_skills.py --dry-run` checks those
hashes and the exact file inventory before showing the default installation.
Hashes detect accidental changes; obtain the archive from a trusted sender.

The package is generated from an explicit repository allowlist. Rebuild it from
the repository with:

```sh
python3 hub/research-library/scripts/build_coworker_kit.py --output "$HOME/Downloads/MongoDB-Research-Coworker-Kit.zip"
```

Research stays in MongoDB. For authorized persisted research, save the prompt,
scope, coverage ledger, evidence-bound claims, and continuation through the MCP
tools. Client-side prompt files and local research copies are not prerequisites.
Read-only work does not create bookkeeping writes. Draft persistence and trusted
publication remain separate outcomes.

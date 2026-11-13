# SK Research

SK Research brings four evidence-gated workflows to a shared MongoDB research
library. Agents discover prior work, retain evidence and claim history, coordinate
leases, and preserve the prompt, method, scope, coverage, and continuation across
sessions. The portable kit gives coworkers the methods and hosted client without
copying database credentials or research bodies.

| Workflow | Claude Code | Codex fallback |
| --- | --- | --- |
| Focused research | `/sk:dr topic` | `$sk dr topic` |
| Concept-family exploration | `/sk:cfe topic` | `$sk cfe topic` |
| Recursive exploration | `/sk:rabbithole topic` | `$sk rabbithole topic` |
| Full research suite | `/sk:full-suite topic` | `$sk full-suite topic` |

Codex's plugin-qualified skills appear through `/skills` and `$` completion.
Use the names the installed client returns. The `$sk` router provides the fixed
fallback syntax shown above. Queue and frontier options are part of the methods;
their read-only previews do not start researchers or make bookkeeping writes.

For example, `$sk cfe "storage engines" --continue-queue --dry-run` previews
eligible saved queue work. `$sk cfe "storage engines" --expand-frontier --dry-run`
previews additional candidates. Use the same options after `/sk:cfe` in Claude.
An authorized run can add `--resume RUN_ID`, depth, threshold, round/pass,
concept, and time bounds. Frontier planning begins research only with `--research`
or within an already authorized full-suite scope.

The plugin is named `sk`. It exports separate, self-contained Claude and Codex
skill trees, with the same method files checked against one source authority.
It does not replace the existing global research skills.

Build the portable archive from the repository root:

```sh
python3 hub/research-library/scripts/build_sk_kit.py \
  --output "$HOME/Downloads/SK-MongoDB-Research-Kit.zip"
```

The builder uses an exact public file allowlist, rejects symlinked assets and
credential-like content, checks portable links and export aliases, and records
file hashes and Git revision. Archive bytes are deterministic for the same
inputs. After editing method references, refresh the generated client copies
with the builder's `--sync-references` flag before building.

Follow the [kit setup guide](../hub/research-library/distribution/sk/SETUP.md)
for preview-first installation and native client verification. The installer
uses official plugin CLIs. The optional router install refuses collisions and
copies only `sk`; it does not overwrite other workflows or edit MCP credentials.
The archive includes its own setup guide, installer, method references, license,
read-only HTTPS client, and hash manifest. It contains no client configuration,
database URI, authentication files, source corpus, or running workers.

Connect `research-library` to
`https://research-mcp.llms-explorer.com/mcp` with a separately issued capability.
A reader can search, inspect concepts and evidence, and preview queues/frontiers.
A writer can perform authorized persisted research through revision and lease
checks. These capabilities cover the managed corpus; they are not per-user or
per-concept accounts. Discover the live tool inventory instead of assuming a
fixed tool count. See the [MCP guide](../hub/research-library/MCP.md) for the
service contract and the [operator runbook](../hub/research-library/README.md)
for server operation.

Persisted drafts and queued jobs remain partial work. Publication requires the
canonical artifact, exact claim/source evidence, independent verification,
current scope accounting, and the trusted final receipt. The methods preserve
STOP markers, holds, other workers, frozen vectors, and the distinction between
discovery, authorized research, and accepted publication.

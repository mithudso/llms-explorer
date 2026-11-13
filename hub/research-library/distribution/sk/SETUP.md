# Set up SK Research

Extract `SK-MongoDB-Research-Kit.zip` and open a terminal in the extracted
`SK-MongoDB-Research-Kit` directory. Use Python 3.11 or later. Native installation
also requires the selected Codex or Claude Code CLI.

## Install the workflows

Preview the complete plan, then apply it for the intended client:

```sh
python3 install_sk.py --client codex
python3 install_sk.py --client codex --apply
```

Choose `--client claude` or `--client both` as needed. The installer verifies the
exact inventory and every hash before acting. It uses official native plugin
CLIs and refuses an existing `sk` plugin or router. Existing `dr`, `cfe`,
`concept-family-explorer`, `rabbithole`, and `full-suite` skills remain in place.
It does not edit MCP definitions or authentication files. Native plugin CLIs
maintain their own installation state and may update their user settings.

To install only the collision-safe Codex fallback:

```sh
python3 install_sk.py --client codex --router-only
python3 install_sk.py --client codex --router-only --apply
```

`--skills-dir /path/to/skills` selects the router's destination parent.
`--codex-home /path/to/codex-home` selects a local Codex home for native CLI
commands through `CODEX_HOME`; it does not change the router destination. Keep
each user's configuration on that user's machine. There is no overwrite option.
If an existing `sk` installation conflicts, inspect it before removing or
updating it through its owning client.

The equivalent native commands, from the extracted kit directory, are:

```sh
codex plugin marketplace add . --json
codex plugin add sk@sk-research --json
claude plugin marketplace add . --scope user
claude plugin install sk@sk-research --scope user
```

Run only the commands for your chosen client. Keep the extracted kit in a
durable local directory while its local marketplace is registered. The plugin
contains separate explicit client skill roots; all referenced methods travel
with each exported root. Start a fresh session to discover the installed skills.
Do not restart an active research worker just to make this installation visible.

## Connect the shared library

Ask the library operator to issue a capability through a private channel. A
reader capability permits discovery and evidence reads. A writer capability
permits corpus-wide draft edits, leases, queue changes, run persistence, and
publication submission through the service's checks. These shared capabilities
do not provide individual accounts or per-concept access control. Use a reader
for a read-only connection check.

The endpoint is `https://research-mcp.llms-explorer.com/mcp`. Register it in your
client as `research-library`, using `RESEARCH_MCP_TOKEN` from your local secret
manager or environment. This Codex command stores the environment variable name,
not its value:

```sh
codex mcp add research-library --url https://research-mcp.llms-explorer.com/mcp --bearer-token-env-var RESEARCH_MCP_TOKEN
```

Inspect an existing definition before changing it. For Claude Code, use your
client's MCP setup to add the same Streamable HTTP endpoint and a private bearer
credential. Avoid putting a literal token in a shell command, shared JSON file,
prompt, archive, screenshot, or report. The kit deliberately leaves client
authentication setup separate from plugin installation. Remote clients need no
MongoDB connection string or server environment file.

The optional skill service at `https://skills-mcp.llms-explorer.com/mcp` uses the
separate `SKILL_MCP_TOKEN` capability. The local SK methods do not require that
service; it can provide additional operator-published skills when configured.

## Verify the installed client

In a fresh client session, discover MCP tools and run this read-only request:

```text
Use SK Research for a read-only library check. Call research_status. Search
"snapshot isolation" in semantic and keyword modes, resolve the actual topic ID,
and repeat both searches narrowly. Report exact tool names, channel diagnostics,
and concept IDs/revisions. Do not write records, acquire leases, change queues,
start research, invoke a paid gate, or submit publication. Do not print tokens
or source bodies.
```

Inspect `/mcp` and `/skills` or the equivalent client inventory. Claude should
offer `/sk:dr`, `/sk:cfe`, `/sk:rabbithole`, and `/sk:full-suite`. Codex should
offer plugin-qualified skills through its inventory and completion; `$sk` is
available when the fallback router was installed. A saved configuration or
successful archive verification alone does not prove native connectivity.

You can test HTTPS reads independently without a model session:

```sh
python3 library_client.py smoke-test --require-sk
python3 library_client.py tools --service research
python3 library_client.py research search "snapshot isolation" --mode semantic --top 5
python3 library_client.py research search "snapshot isolation" --mode keyword --top 5
```

The client reads `RESEARCH_MCP_TOKEN` and performs only allowlisted reads. Its
semantic searches use the hosted retrieval service. It never starts research or
submits writes. Tool discovery returns the current server inventory; capabilities
depend on the role of the supplied token.

## Use the workflows

For example, use `$sk cfe "storage engines" --continue-queue --dry-run` to
preview saved queue work, or add `--expand-frontier --dry-run` to preview new
candidates. Use the same options after `/sk:cfe` in Claude. Resume with
`--resume RUN_ID` and preserve the saved scope and bounds. Frontier planning
starts research only with `--research` or within authorized full-suite scope.

Start with a read-only queue or frontier preview when choosing work. The methods
deduplicate against the library, preserve STOP and holds, reserve authorized work,
and renew owned leases. They save the commissioned prompt, method, scope,
coverage, source references, claims, and continuation in MongoDB. Queue or draft
writes do not establish publication. Completed work needs readable evidence,
claim verification, an independent gate, complete scope accounting, and the
trusted publication receipt. If a required capability or provider is unavailable,
the workflow records the gap and reports the real partial state.

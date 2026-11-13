# Connect a coworker's Codex

Run these steps on the machine and user account that will use Codex. The package
needs Python 3.11 or later; native integration also needs the Codex CLI. The
standalone client uses Python's standard library and needs no MongoDB driver.
Extract the archive, then open a terminal in `MongoDB-Research-Coworker-Kit`.

## 1. Supply two private credentials

Ask the library operator for a skill-service token and a research **reader**
token through a private channel. They are separate credentials for separate
services. A research writer token is needed for authorized research changes.
These bearer roles cover the whole managed corpus; they do not create individual
accounts, per-concept permissions, or tenant ACLs. Remote clients need no MongoDB
URI, copied source corpus, or server environment file.

Load credentials into `SKILL_MCP_TOKEN` and `RESEARCH_MCP_TOKEN` in the same shell
that launches the client or Codex. Use a secret manager or hidden prompts. This
macOS zsh example keeps token values out of shell command history:

```sh
read -rs 'SKILL_MCP_TOKEN?Skill service token: '
export SKILL_MCP_TOKEN
printf '\n'
read -rs 'RESEARCH_MCP_TOKEN?Research reader token: '
export RESEARCH_MCP_TOKEN
printf '\n'
```

Do not put token values in this folder, prompts, screenshots, reports, URLs, or
shared configuration. Environment variables last for that shell session and its
child processes; a separately launched desktop app does not inherit them.

## 2. Check transport with the standalone client

```sh
python3 library_client.py tools --service skills
python3 library_client.py tools --service research
python3 library_client.py smoke-test
python3 library_client.py skills search "MongoDB query tuning" --mode semantic --top 5
python3 library_client.py research search "snapshot isolation" --mode semantic --top 5
python3 library_client.py research search "snapshot isolation" --mode keyword --top 5
```

The smoke test discovers tools, reads service status, exercises searches, and
checks pinned skill reads. Its output contains metadata and verdicts, without
research source bodies. It does not run a research/judge LLM, create research,
acquire leases, or submit publication. Semantic retrieval still uses the hosted
embedding provider. Explicit
`--mode semantic` fails if the service degrades instead of providing semantic
search. Read the returned search diagnostics; keyword fallback does not establish
semantic coverage. A successful status call alone does not test the search indexes.

For scoped deduplication, first read the real topic identity from search results;
replace `c:your-topic-id` with that returned ID:

```sh
python3 library_client.py research search "snapshot isolation" --mode semantic --top 5 --topic-id c:your-topic-id --breadth narrow
python3 library_client.py research search "snapshot isolation" --mode keyword --top 5 --topic-id c:your-topic-id --breadth narrow
```

`--topic-id` alone does not constrain a broad search. The client can also read
the two server definitions from a specified local Codex home with
`python3 library_client.py --codex-home /path/to/codex-home tools --service research`.
Use that directory only on its owning machine. Do not copy it into this package.

## 3. Register the native Codex servers

These commands record the endpoint and environment-variable name, not a literal
credential. Run them in the intended local Codex home. If a server already exists,
inspect `codex mcp get skills_mongodb` or `codex mcp get research-library` before
changing its definition; preserve other servers and active sessions.

```sh
codex mcp add skills_mongodb --url https://skills-mcp.llms-explorer.com/mcp --bearer-token-env-var SKILL_MCP_TOKEN
codex mcp add research-library --url https://research-mcp.llms-explorer.com/mcp --bearer-token-env-var RESEARCH_MCP_TOKEN
codex mcp list
```

The skill service supplies five read tools. The research service supplies 27
tools; a reader can discover writer tool names but cannot invoke their writes.
See [TOOLS.md](TOOLS.md) for their roles. Skill metadata naming `research-library`
does not register that server or provide a credential.

## 4. Optionally install the local skills

Run a preview, then install the core library skill into the recommended user
skill directory, `~/.agents/skills`:

```sh
python3 install_skills.py --dry-run
python3 install_skills.py
```

The installer verifies the package manifest, rejects symlinked assets, and refuses
the entire selection if any selected destination already exists. It never
overwrites a skill or edits Codex configuration. Optional modes are explicit:

```sh
python3 install_skills.py --all --dry-run
python3 install_skills.py --all
```

Or select a mode with `python3 install_skills.py --only dr`. Repeat `--only` to
select several. Required companion skills are included automatically: `cfe`
needs `concept-family-explorer` and `dr`; family exploration and rabbithole need
`dr`; every mode needs the core library skill. If the core is already installed,
the installer aborts without changing anything. Review existing directories
manually; the installer has no overwrite option. `--skills-dir /path/to/skills`
supports a deliberately chosen alternate destination.

## 5. Verify inside a fresh native session

Start a fresh Codex session from the shell holding the credentials. Check `/mcp`
for the two connected servers and their tools. Then use this read-only prompt:

```text
Use $research-library-mongodb for a read-only connectivity and discovery check.
Call research_status. Search "snapshot isolation" broadly in semantic and keyword
modes. Read a plausible concept, resolve its actual topic ID, and run narrow
semantic and keyword queries in that topic. Report the exact tools used, channel
diagnostics, any degraded/unavailable channel, and relevant concept IDs/revisions.
Do not create or edit records, acquire leases, modify queues, start research,
invoke a paid gate, or submit publication. Do not print credentials or source bodies.
```

Prefer a reader capability for this check. A read-only prompt and
`--sandbox read-only` constrain the request and local filesystem respectively;
they do not remove a writer token's MCP authority. If a writer token must be
used, the operator can additionally restrict the session's research server
`enabled_tools` to the read tools in [TOOLS.md](TOOLS.md) before starting it.
Do not modify another user's configuration or running session for this check.

Standalone transport receipts and native Codex receipts prove different paths.
Do not claim native integration until the fresh Codex session actually discovers
and calls the tools. No model session runs during package generation, installation,
or the standalone smoke test.

For new authorized research, use `$dr`, `$concept-family-explorer`/`$cfe`, or
`$rabbithole`. Save the commissioned prompt, methods, scope, and continuation in
MongoDB with current revisions and owned leases. No client prompt, source, or
research files are required. Writes save drafts; trusted finalization and its
accepted current proof establish publication.

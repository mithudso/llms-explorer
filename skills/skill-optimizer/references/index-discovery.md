# Step 1.7: index discovery (semantic and keyword)

Run this before Pass I and before the location sync. It builds three lists: colliders (Pass I), referrers (Pass G wrapper drift, Pass N SKIP resolution, Pass O), and copies (`references/location-sync.md`). Index hits are leads. Confirm each with Read or `shasum` before you act on it.

## Queries

Run all three groups. Use the MCP tools when the `global_ai_hub` server is connected.

| List | Semantic | Keyword |
|---|---|---|
| Colliders and related skills | `hub_route("<description first sentence>", kinds="skill", top=10)` and `hub_search_codebase("<top trigger phrases>", n_results=25)` | `hub_search_keyword("<trigger phrase>", mode="phrase")` for each of the top 5 triggers |
| Referrers | `hub_search_codebase("<name> skill", n_results=25)` | `hub_search_keyword("<name>", n_results=50, mode="all")`; for memory-central rows, `hub_search_keyword("<name>", prefix="~/.llms", n_results=5)` |
| Copies | `hub_search_codebase("<name> SKILL.md", n_results=25)` | the referrer `"<name>"` hits, plus `find` by directory name and by SHA-256 (see `references/location-sync.md`) |

The index covers every root in `~/.global-ai-hub/watch_dirs.txt`, so hits include backups, alias paths (such as a `$HOME` symlink to `$HOME`) and other boxes' paths. Dedupe hits by `realpath` and drop `*/backups/*`. A path missing on this box stays `lead only`.

Optional widening: `hub_ask("<name> skill", retrieve_only=True)` searches every hub corpus without the LLM answer; `hub_search_symbols` searches code at function and class level.

## Fallback

A result that starts with `ERROR:` is a failure, like an unreachable server. An empty `hub_route` result is also a failure: the router returns `[]` when the Ollama embed pool is down. Run each failed query's script. If the embed pool is down, skip the semantic scripts, because they fail the same way; keyword queries need no embedder.

```bash
cd ~/.global-ai-hub
PYTHONPATH=scripts .venv/bin/python -m semantic_ops.router route "<description first sentence>" --top 10 --kinds skill  # hub_route
python3 scripts/search.py "<query>" --top 25                                              # hub_search_codebase
python3 scripts/keyword_index.py query "<trigger phrase>" --mode phrase --top 10 --json   # colliders
python3 scripts/keyword_index.py query "<name>" --top 50 --mode all --json                # referrers, copies
python3 scripts/keyword_index.py query "<name>" --prefix ~/.llms --top 5 --mode any --json  # memory-central
```

If a query fails through both its MCP tool and its script, or its script was skipped, search the files directly, with one `-e` per name or trigger phrase. Plain `grep -r` skips symlinked skills, and the Claude Code `grep` wrapper (ugrep with `--ignore-files`) also skips gitignored ones.

```bash
find -L ~/.claude/skills ~/.claude/commands ~/.claude/agents ~/dev/skills \
  \( -name .git -o -name backups -o -name node_modules -o -path '*/.claude/worktrees' \) -prune \
  -o -type f -exec grep -lIF -e '<name>' {} +
```

The search takes about three minutes, so run it with a 600000 ms timeout or in the background. A timeout is a failed search, not zero hits. After a `find` fallback, record `index-discovery: degraded (<reason>)` and count it as one outcome that did not land in the Step 7.8 tally.

## Output

Keep three lists in memory for the run. Tag each entry `verified` or `lead only`.

1. **Colliders:** skill id, score, shared phrases. Pass I consumes this list.
2. **Referrers:** path:line of each reference to the skill (commands, agents, hub routing tables, other skills' `SKIP:` lines, `related_skills`). Pass G, N and O consume this list. A referrer that names a retired or renamed id is a Medium finding; a hub-aware spoke form (`<hub-id> (references/<id>.md)`) is not retired. Fix the finding only when the referrer is the target or its Step 1 wrapper. Report any other referrer, because Pass O edits peer files additively only.
3. **Copies:** every path where the skill exists. `references/location-sync.md` consumes this list.

Index hits that Read does not confirm go in the report as `lead only`. They never drive an edit.

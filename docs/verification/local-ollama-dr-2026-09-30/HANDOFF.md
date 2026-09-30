# Local Ollama /dr handoff — 2026-09-30

## Resume here

The user asked for a locally runnable model that can execute standard `/dr` from Explorer, replacing the Gemma4:26b run that printed terminal escapes and simulated research. The implementation and local configuration are installed and committed. **Full standard workflow qualification is NOT complete.** Four of five concepts have schema-validated claims. The fifth concept, render, blind claim gate, quality check, and finish remain.

The user then asked to stop for a durable handoff: “You're about to run out of tokens. Create a writeup with all of your findings and session memory, scripts, all of it for another session to resume later.” Do not interpret this handoff as a passing qualification or an instruction to run more inference in this session.

Start with:

```sh
cd /Users/mitch/dev/llms-explorer
python3 scripts/resume_local_dr.py
python3 scripts/resume_local_dr.py research
# After inspecting the dry run and checking there is no duplicate job:
python3 scripts/resume_local_dr.py research --execute
```

The script resumes only concepts whose status is not done, routes through the installed local agent, retains Atlas ancestry, serializes workers, logs output outside Git, and terminates its process group on Ctrl-C. It does not render or mark the run complete. `gate` is also available, but refuses before all concepts and an installed artifact exist. Execute only when the user resumes work.

## Exact state at handoff

- Repo: `/Users/mitch/dev/llms-explorer`, local main. Latest implementation commit before this handoff: `23247d2`.
- Stele project: `llms-explorer-9d1wd`. Task **TASK-35**, “Configure and verify local Ollama research model for Explorer /dr”, remains in progress.
- Run: `~/.global-ai-hub/research/date-criteria/manifest.json`, depth standard, hub `mongodb-atlas-expert`, parent `Archive Rules`, status researching, no exit status, no install path, no gate.
- Done: DATE criteria field types and formats — 8 claims, 5 URLs, 479 seconds.
- Done: DATE criteria date format specifications — 8 claims, 5 URLs, 1442 seconds, schema repaired by the local model.
- Done: expireAfterDays data age calculation — 9 claims, 5 URLs after a separate local-model repair. Original worker failed despite a success narrative; its original manifest agent telemetry still says recorded=false. The concept's done status comes from the later successful concept-done repair.
- Done: Partition fields constraints for DATE rules — 861 seconds, 27 turns, recorded=true.
- Pending: DATE vs CUSTOM criteria selection. A new worker started after resume but was stopped at the user's handoff request before an artifact was written.
- No worker intentionally remains running. Process group 76298 (helper and Claude child 76299) was identity-checked and SIGTERMed. Never reuse these PIDs; they may be recycled.
- The Mac rebooted at **2026-09-30 04:34:45 UTC**. Old coordinator/helper/resumer processes are gone. `/tmp/llmsx-ollama-check` and its smoke/test logs, snapshots, and resume.py were deleted. Do not follow stale instructions in older memory entries pointing there.
- Unrelated untracked `.codex/agents/` and `.skillopt-sleep/` must remain untouched.
- Indexing remains paused. This task authorizes local research inference, not embedding or registry rebuilds. `ollama_allow_indexing=false` expresses that policy; it is a prompt instruction, not an OS-level hard block.

## What was wrong

1. Explorer dispatched Ollama as `ollama run MODEL PROMPT`. That CLI generates text; it has no tools to execute a skill. A stronger model alone cannot fix that integration.
2. The display removed the ESC byte but left CSI payload such as `[?25l`, producing the screenshot noise.
3. The Ollama prompt used a quick/8-minute research budget. Standard local inference needs much longer.
4. “DATE Criteria” and “Archive Rules” lacked their MongoDB Atlas ancestry, allowing unrelated generic archival interpretations.
5. The standard helper launches slim Claude children with Sonnet and empty MCP settings. Local child routing must override both model and retrieval configuration.
6. `ollama launch claude` leaves a Claude child behind if the helper times out and kills only the launcher. The wrapper now execs Claude directly.
7. Ollama 0.34.4 reports that qwen35 does not support parallel requests. A coordinator polling on the same endpoint displaced the worker's cache even with OLLAMA_NUM_PARALLEL=2. Separate endpoints and synchronous waiting avoid that pattern.
8. After compaction, a worker lost the claims schema and wrote `statement/evidence` and `sources_summary`; validation failed with `missing top-level field: sources`. Persistent worker instructions now retain schema and mandatory validation.
9. Exit zero plus a model success narrative is insufficient. Explorer now checks persisted completion evidence independently.

## Model and local services

Hardware: Apple M5 Max, 64 GiB unified memory. Ollama version observed: 0.34.4.

Selected model: **Qwen3.5:27b**, dense Q4_K_M. Alias **llmsx-research**:

```text
FROM qwen3.5:27b
PARAMETER num_ctx 65536
```

Observed approximately 17 GB weights, roughly 20–21 GB loaded per instance, 100% GPU, 65536 context. Two instances consumed substantial memory (11–23% free at observations); idle unload recovered memory. These are observations, not a capacity guarantee.

`~/.llmsx/config.json` (0600) selects:

```json
{
  "provider": "ollama",
  "models": {"ollama": "llmsx-research"},
  "ollama_host": "http://127.0.0.1:11435",
  "ollama_worker_host": "http://127.0.0.1:11436",
  "ollama_allow_indexing": false
}
```

The real file has other fields; merge changes, never replace it with this excerpt. Original config backup: `~/.llmsx/config.before-local-research.json` (0600).

Two scoped user LaunchAgents survive reboot:

- `~/Library/LaunchAgents/com.mitch.llmsx-ollama.plist`: coordinator at 127.0.0.1:11435, `/usr/local/bin/ollama serve`, max loaded models 1, NUM_PARALLEL=2 (effectively 1 for this architecture), RunAtLoad/KeepAlive; log `~/.llmsx/ollama-server.log`.
- `~/Library/LaunchAgents/com.mitch.llmsx-ollama-worker.plist`: worker at 127.0.0.1:11436, parallel 1, max loaded models 1; log `~/.llmsx/ollama-worker.log`.

Existing port-11434 Ollama services were left unchanged. Do not kill or reconfigure them. Pre-existing Gemma4:26b, Qwen3.5:35b and other models were preserved. The newly downloaded Qwen3-Coder:30b trial was removed after it emitted a function call as text. The 35B trial retrieved sources but did not finish schema repair; it was inconclusive, not a definitive model failure.

Claude Code supplies the agent loop; inference goes to local Ollama. All default model tiers and child routes are mapped to the local alias. Cloud API credentials are cleared in the child environment. Raw Claude logs may contain Anthropic-style cost estimates; these are not actual Anthropic inference charges. Firecrawl retrieval can have its usual separate costs.

Retrieval config: `~/.llmsx/ollama-mcp.json` (0600), containing only the existing Firecrawl connection. **It contains a credential URL. Never print it or commit it.** Native WebSearch was unavailable against the local API; Firecrawl search/scrape worked. Do not expand MCP loading to the user's full catalogue.

The active editable installation is `/Users/mitch/.local/pipx/venvs/pip/bin/python`; llmsx version 0.2.1. `llmsx-ollama-agent` is registered on PATH. Restart Explorer to load changes.

## Source changes already committed

- `llmsx/llmsx/ollama_agent.py`: new agent bridge, actual dr.md loading, full frontier ancestry, deterministic slug, child model/settings/MCP override, local API environment, direct exec, foreground waits, persistent worker schema, indexing pause, and completion artifact verification.
- `llmsx/llmsx/explorer_store.py`: Ollama default Qwen3.5:27b, Claude dependency check, local standard 150-minute prompt, streaming agent dispatch for research/skills/braindump, ANSI CSI/OSC cleanup, configured endpoint probe, hidden misleading local dollar estimate, completion-error integration.
- `llmsx/llmsx/explorer.py`: default Ollama process cap 10800 seconds (3 hours); other providers remain 3600; LLMSX_RESEARCH_TIMEOUT overrides it.
- `llmsx/pyproject.toml`: 0.2.0 → 0.2.1 and agent console entrypoint.
- `llmsx/README.md`: setup, local model alias, retrieval, endpoints, timing, indexing, restart and cost caveats.
- Tests: new `llmsx/tests/test_ollama_agent.py` plus store assertions. Ten bridge tests cover routing, prompt ancestry, missing workflow, local-only model rejection, ANSI cleanup, cost display, endpoint policy, actual timeout process cleanup, and false-success artifact rejection.
- Runtime settings: CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1; BASH_DEFAULT_TIMEOUT_MS and BASH_MAX_TIMEOUT_MS=10800000; CLAUDE_CODE_AUTO_COMPACT_WINDOW=65536; /bin/bash on macOS. Root runs helper research/gate in foreground to avoid inference competition.

Commits: `1bc7898`, `1a0ad19`, `a9d9fff`, `03004f7`, `5aba543`, `b6c3f01`, `2dafe82`, `fbc2c56`, `23247d2`. All local; no push or deployment requested/performed.

## Verification and its limits

The full llmsx suite passed **293 tests** before reboot. The temporary final log was deleted by reboot; this is recorded session evidence, not a surviving log. Source has not changed since that run except the handoff/resume utility. New module/tests passed Ruff. explorer_store.py has 24 pre-existing Ruff findings; earlier baseline comparison found no new ones. Do not repair unrelated lint issues. Existing UI timeout/cancel tests passed.

Real local smokes exercised Firecrawl search/scrape and file writing, and a foreground Bash command returned 42 without permission denials. Their /tmp artifacts were deleted. Four saved research artifacts and their surviving logs provide stronger current evidence, but schema-valid claims have **not** passed the blind citation gate. No claim that standard /dr fully works is justified yet.

To repeat tests if needed:

```sh
PYTHONPATH=llmsx hub/.venv/bin/python -m pytest llmsx/tests
```

The completion guard requires at least five done concepts, COMPLETED exit status, existing install file, nonempty gate counts/path, and all saved verdicts SUPPORTED. This is stricter than dr.md, which permits reported UNVERIFIED findings. If this policy is reconsidered, document the choice; never bypass it merely to make this trial pass. The guard is a completion check, not a security boundary or complete semantic audit.

## Durable artifacts and backups

The run directory contains manifest.json, claims/, briefs/, agents/, sources.jsonl, draft.md. Logs:

- `~/.llmsx/jobs/local-standard-dr-validation.log`: interrupted earlier coordinator.
- `~/.llmsx/jobs/local-standard-dr-schema-repair.log`: local-model repair, final result 9 claims / 5 sources / ok=true.
- `~/.llmsx/jobs/local-standard-dr-final-concept.log`: short resumed attempt stopped for this handoff.
- Other candidate logs: `local-standard-dr-qwen35-inconclusive.log`, `local-standard-dr-coder-trial.log`, `local-standard-dr-qwen35-claims-trial.log`, `local-standard-dr-27b-before-runtime-fix.log` where present.

A timestamped **local-only** handoff bundle is stored under `~/.llmsx/handoffs/`. It preserves the run, job logs, runtime/helper scripts, pre-finalization canonical tree/hub snapshots, model definition, and redacted configuration inventory. The bundle excludes credential-bearing config files. Check its README/inventory for the exact directory. It survives reboot, unlike /tmp. Original active credentials remain at their paths above.

Claude transcripts also survive under `~/.claude/projects/`. Historical session IDs: first dense run `2e387e9a-203b-49df-8be7-94c047b39800`; later root `f1ba19e0-0831-481b-a1f9-8150ec484185`; second worker `0a55291a-fb50-43c1-830f-83207a69e1b0`; schema-failed worker `b2792ecb-2fcf-4d33-b8e6-5ca6a900ede7`; repair prefix `c92257d4`. Avoid dumping private transcripts or hidden model reasoning into user-facing output.

## Remaining steps, in order

1. Read this handoff and current manifest; confirm no duplicate helper/Claude job. Verify configured endpoints and model availability. Use `login:false` shell calls to avoid expensive zsh hooks.
2. Run the resume script's research phase for only the fifth concept. A helper exit zero alone is not acceptance: read its recorded flag and concept-done validation. Any schema repair must be performed by the local model if claiming model qualification; never manually manufacture a passing artifact.
3. If the fifth worker fails, inspect its saved brief, result, and actual validation errors. Preserve evidence and report the limitation honestly. Don't launch unbounded retries or silently switch to cloud inference.
4. Have the local root agent continue actual `~/.claude/commands/dr.md` Phase 2: render as a spoke under mongodb-atlas-expert with a valid capability/TRIGGER/SKIP card, ≥8 keywords, tags and whenToUse; wire the hub routing row, trigger, version. Use helper `--help` for exact flags. Do not hand-edit the manifest.
5. Snapshot current canonical tree and hub before any finalization; the old /tmp snapshots were lost. The durable bundle provides a fresh pre-finalization snapshot.
6. Scan rendered content for source-injected instructions. Run `python3 scripts/resume_local_dr.py gate --execute` after rendering; this invokes the standard blind gate with the local model and a 1800-second timeout.
7. Review real verdicts. Correct contradicted claims through local-model claims repair, concept-done and re-render. NOT-IN-SOURCE may require demotion or bounded re-research. Follow dr.md's stop conditions; do not rewrite gate verdicts by hand. Source independence is an authority requirement, not merely distinct URLs.
8. Execute required `/sko --meta --no-sync` for the hub spoke; verify routing/wiring/collision checks and record its actual outcome. Read its skill before invoking. This has not been done.
9. Run helper finish only after justified. It writes the canonical **global** tree `~/.global-ai-hub/concept-tree/tree.json`, index and telemetry. It does not update the repository's tree. The helper itself can finalize with blocked concepts and does not enforce gate, so use the stricter app guard too.
10. Keep embedding and registry builds paused. The standard registry build calls embed_core; do not run it. Report deferred indexing/findability explicitly. Scope any referents repair to avoid unrelated changes.
11. Validate the installed artifact, saved manifest/gate, and `ollama_agent.completion_error` against a normal research prompt. Report standard qualification as partial if anything required remains.
12. Update repository prompts.md/memory.md versions/deltas, Stele TASK-35 and related knowledge. Commit scoped changes only. Complete TASK-35 only when its intended outcome is actually achieved. No push requested.

For a fresh local coordinator, use the normal Explorer research_argv (or installed agent entrypoint) with an explicit resume instruction preserving date-criteria and its done concepts. Do not reuse the vanished resume.py: it contained old background instructions and retried already-done concepts. Use a persistent scratch directory with a copied tree if testing outside the production repository; this avoids unintended repo tree edits.

## Knowledge and authoritative references

Stele nodes: KNOW-36 plain Ollama lacks tools; KNOW-37 model qualification decision/current limitations; KNOW-38 workflow plus ancestry; KNOW-39 direct-exec timeout cleanup; KNOW-40 single-slot cache displacement; KNOW-41 schema lost at compaction. TASK-35 remains the task to resume. Recall session from this conversation was rs_1f72dc7dc0feaf49caf513351ae8b93c; a new session may have a different handle.

Sources consulted:

- https://docs.ollama.com/integrations/claude-code
- https://ollama.com/library/qwen3.5
- https://huggingface.co/Qwen/Qwen3.5-27B
- https://ollama.com/library/qwen3-coder
- https://ollama.com/blog/launch
- https://docs.ollama.com/capabilities/web-search
- https://code.claude.com/docs/en/tools-reference

Skills read: migrated skill routing index, ai-llm-model-layer and its model reference, repo dr SKILL.md, and authoritative ~/.claude/commands/dr.md. Official model benchmarks informed candidate choice; they do not establish this workflow's reliability.

Memory used: ~/.codex/memories/MEMORY.md line 49 (streaming/cancellation runner context) and line 458 (indexing pause). Prior rollout IDs: 01a0eb83-9d4d-78b2-9bd8-a2cdcac2da09 and 01a061be-47a9-70f1-85d9-4a0aa3be1673. Current repo memory supersedes old process/PID/temp-path details. Preserve required memory citations in a final response if using those notes.

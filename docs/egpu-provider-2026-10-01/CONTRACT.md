# Explorer eGPU provider CPU checkpoint

Version: 1.0.0
Delta: Distinct canonical provider; installed and physical acceptance pending.

The provider identifier is `egpu`. It supports only `qwen3.5:9b-q4-k-m`.
It does not change the active provider or any existing saved model selection.
It requires the reviewed installed wrapper at
/Users/mitch/.local/bin/claude-egpu and the maintained package at
/Users/mitch/dev/skills/rtx5080-egpu-harness. It rejects disposable package,
binary and model overrides. The older installed launcher must never be
invoked by preparation tests, including passive flags.

The provider verifies reviewed wrapper/frontdoor bytes before it permits
any future passive check. That check invokes only `--check-installed`.
The response must assert installed/ready/passive true, services_started
false, model_requests/lldb_attaches zero, full_tools 23, context 32768,
the exact model and canonical package/client/adapter paths. Physical and
research qualification fields must remain false. This validates the
installation contract, not device readiness or standard research success.

For a supplied parent, the command has this exact shape:

```text
/Users/mitch/.local/bin/claude-egpu --research "TOPIC" --depth standard --budget-minutes 150 --parent "PARENT" --output-format stream-json --verbose
```

The provider validates topic and parent labels; the reviewed frontdoor
validates actual canonical tree ancestry. The parent option is omitted
only when no parent was supplied. The protected launcher chooses the
reviewed model and tools. Explorer does not synthesize a prompt, substitute
an Ollama/cloud backend, or accept arbitrary launcher flags for execution.

Research CWD must resolve to /Users/mitch/dev/llms-explorer because the
frontdoor fixes research to that checkout. Explorer refuses other trees
before it snapshots or starts a job. The outer deadline is 10800 seconds,
including when LLMSX_RESEARCH_TIMEOUT specifies a shorter default. Raw
stream events remain in the job log. Cancellation targets the owned job
process group and restores its saved tree. The existing completion checker
requires all five concepts, installation and the actual ten-claim gate;
exit zero and a model's success narrative are insufficient. This mechanical
check does not replace independent substantive source/quality review.

The Research modal offers standard `/dr` and local Queue. Other research
workflows, standalone skills, braindump and the legacy concepts-screen
cloud launcher refuse explicitly. Settings has no eGPU API key and fixes
the displayed model. Existing providers retain their prior options.

Root may use this candidate only after production installation and review:

```sh
LLMSX_PROVIDER=egpu PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/mitch/dev/worktrees/llms-explorer-egpu-provider/llmsx /Users/mitch/dev/llms-explorer/llmsx/.venv/bin/python -B -m llmsx explorer --repo /Users/mitch/dev/llms-explorer --no-sync
```

This command was not executed during preparation. It selects eGPU for that
process without modifying the user's saved defaults. Root chooses a fresh
research topic and performs installed same-owner checks. No cold-cycle,
restart, helper capture or owner replacement is inferred by this provider.

The fixture test command is safe to rerun without installed services:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/mitch/dev/worktrees/llms-explorer-egpu-provider/llmsx /Users/mitch/dev/llms-explorer/llmsx/.venv/bin/python -B -m pytest -o addopts='' /Users/mitch/dev/worktrees/llms-explorer-egpu-provider/llmsx/tests/test_explorer_egpu.py -q
```

Expected: 69 passing fixture controls. Root owns installed activation and
live research; TASK-258 remains open until that smoke. The source branch
must remain unmerged or draft until root approves that live checkpoint.

The complete final suite passed 201 controls in 45.25 seconds. The final
receipt retains exact source hashes and zero installed/model/service/
LLDB/indexing calls. For a guarded reproduction of the complete suite:

```sh
cd /Users/mitch/dev/worktrees/llms-explorer-egpu-provider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/mitch/dev/worktrees/llms-explorer-egpu-provider/llmsx /Users/mitch/dev/llms-explorer/llmsx/.venv/bin/python -B - <<'PY'
import socket
import urllib.request
import pytest

def deny(*args, **kwargs):
    raise AssertionError("unmocked network forbidden during Explorer CPU preparation")

socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
urllib.request.urlopen = deny
raise SystemExit(pytest.main([
    "-o", "addopts=", "-q",
    "llmsx/tests/test_explorer_egpu.py",
    "llmsx/tests/test_explorer_store.py",
    "llmsx/tests/test_explorer_jobs.py",
    "llmsx/tests/test_explorer_tui.py",
    "llmsx/tests/test_explorer_v2.py",
    "llmsx/tests/test_concepts_tui.py",
]))
PY
```

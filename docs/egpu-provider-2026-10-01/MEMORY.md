# Explorer eGPU provider continuation

Version: 1.0.1
Delta: Source implementation, fixture validation and retained checkpoint history.

TASK-258 is the existing provider task. TASK-283 completed baseline inspection;
TASK-284 owns source implementation. KNOW-282 records the isolation decision.
The implementation worktree is /Users/mitch/dev/worktrees/llms-explorer-egpu-provider.
Its base is origin/main d603d18df6a1f9883f9815ced1594c4d60692bbc.
The original checkout and every physical runtime remain untouched.

The reviewed production frontdoor is version 1.3.1. Its SHA256 is
54bbf8031c18fe01178f1c82a4827f7919407b6aec494309a14a25c183807919.
The reviewed shell wrapper SHA256 is
e018e789e9da6148418d748f664fa213f448196cfd83b5ab03bce6627acc63f6.
The canonical package is /Users/mitch/dev/skills/rtx5080-egpu-harness.
The canonical installed wrapper is /Users/mitch/.local/bin/claude-egpu.
No preparation check may invoke that installed wrapper.

The future passive response must report installed/ready/passive true,
services_started false, model_requests/lldb_attaches zero, full_tools 23,
context 32768, the exact 9B alias, and canonical package/client/adapter paths.
These fields prove the installed contract only. They do not prove physical
readiness or standard research acceptance.

The frontdoor deliberately changes research CWD to
/Users/mitch/dev/llms-explorer. Therefore this provider must refuse research
against another Explorer repository; otherwise tree snapshots and rollback
would cover the wrong tree. Existing providers keep their prior CWD behavior.

The old concepts screen invokes literal cloud Claude. Root authorized an
early eGPU refusal before git/subprocess/suspend so it cannot bypass selection.
Only standard /dr is supported. Other skills, braindump, family, crawl,
rabbithole and full-suite must refuse explicitly. Queue remains a local action.

The existing ollama_agent.completion_check expects a -p /dr prompt. eGPU uses
--research instead, so completion must derive the same validated topic and
pass a standard /dr prompt to that unchanged canonical completion checker.
Exit zero or chat JSON alone must not count as completion.

Implemented: a distinct egpu provider, exact reviewed 9B alias, canonical
standard150-minute argv with parent and stream flags, no API key or foreign
model/binary override, reviewed installed bytes before passive execution,
and strict passive response scope fields. The job validates its canonical
research CWD before log creation or child launch. It retains the owned
process-group cancellation and snapshot rollback, uses the unchanged
canonical artifact completion checker, and hides local cloud-price estimates.
Unsupported workflows and concepts-screen cloud bypass refuse explicitly.
Unsafe parents refuse instead of being silently discarded for eGPU research.
Existing provider defaults and saved Gemma31 MLX selection remain unchanged.

The initial 55-control run had one test-only assertion mismatch: the code
correctly rejected a foreign executable with the canonical-route message;
the test incorrectly expected the later flag-difference message. The
expectation was corrected. No production behavior was weakened.

The 68-control checkpoint and broader 200-control regression run passed.
Source review then found that the research modal incorrectly called an
unreviewed installation a missing PATH binary. The final UI now reports
reviewed-installation unavailability. The original CPU-TESTS.json/log and
CPU-STATIC.json remain unchanged as checkpoint history. The final sources
have 69 new fixture controls. The final broad run passed all 201 controls
in 45.25 seconds with exact before/after source hashes unchanged. Its
receipt is /Users/mitch/dev/worktrees/llms-explorer-egpu-provider/docs/egpu-provider-2026-10-01/CPU-TESTS-v101.json.
The final static receipt is
/Users/mitch/dev/worktrees/llms-explorer-egpu-provider/docs/egpu-provider-2026-10-01/CPU-STATIC-v101.json.
No installed launcher, model request, service action, debugger attach,
indexing call, physical owner change, original-checkout edit or helper load
occurred. New tests forbid unmocked processes/network/signals. The broader
run also guards network connects and urlopen; its existing process tests
use owned fake Claude, fixture Git, and CLI help only.

Scoped Ruff adds no findings versus origin/main. Existing store/UI baseline
findings remain outside this change (23 store; 14 baseline UI reduced to 11).
New tests pass Ruff and format checks. The final seal inventories every
authored file; generated pytest/Ruff caches were removed after verification.

Remaining: root reviews and installs the production launcher/package, then
runs the installed same-owner Explorer smoke against the canonical checkout.
TASK-258 remains open until that live smoke. No default provider/model
promotion, physical qualification or full /dr success is claimed here.

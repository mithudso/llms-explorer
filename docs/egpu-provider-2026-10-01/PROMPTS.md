# Explorer eGPU provider prompt

Version: 1.0.1
Delta: Preserve exact root assignment and canonical-route clarification with the CPU checkpoint.

Implement a distinct eGPU provider for Explorer in the isolated worktree
/Users/mitch/dev/worktrees/llms-explorer-egpu-provider on branch
codex/egpu-explorer-provider, based on origin/main
d603d18df6a1f9883f9815ced1594c4d60692bbc. Own provider integration in
llmsx/llmsx/explorer_store.py and llmsx/llmsx/explorer.py, focused tests,
and these continuation documents. Root also authorizes the narrow
llmsx/llmsx/concepts_tui.py early refusal and its focused test to prevent
cloud Claude bypass when eGPU is selected.

Preserve the original /Users/mitch/dev/llms-explorer checkout and source-pinned
modules. Preserve all existing provider defaults, the user's configured
llmsx-research-gemma31-mlx model, and the indexing pause. Do not add agents.
Do not run actual GPU, API, model, services, LLDB, or installed-launcher
commands, including --check-installed. The existing installed wrapper has
not been promoted and could start Tinygrad.

Use the reviewed production frontdoor's passive installed contract. Verify
installed wrapper and frontdoor bytes before any future passive invocation.
Support only qwen3.5:9b-q4-k-m and standard research with the canonical
/Users/mitch/.local/bin/claude-egpu --research TOPIC --depth standard
--budget-minutes 150 route, existing parent ancestry, stream-json/verbose,
and a 10800-second outer deadline. Preserve owned child process-group
cancellation, tree rollback, and canonical completion verification.
Refuse unsupported workflows and noncanonical research repositories.
Do not fall back to another provider or expand the launcher contract.

Use source inspection and mocked CPU tests only. Root owns installation,
activation, installed same-owner smoke and physical research. Keep TASK-258
open pending that smoke. Do not merge before root's smoke. No site edits.

## Exact root assignment

```text
New work: TASK-258 existsOPEN and fullbody canfetch. Implement distinct eGPU provider for Explorer in a NEW isolated llms-explorer worktree based origin/main, owned branchcodex/egpu-explorer-provider; newpath /Users/mitch/dev/worktrees/llms-explorer-egpu-provider. You own provider integration llmsx/llmsx/explorer_store.py, explorer.py, focusedtests, and newPROMPTS/MEMORY/inventorydocs only inthatworktree. You are not alone; preserveallmain dirtywork/otherbranches; NEVERedit main or currentoriginal /Users/mitch/dev/llms-explorer/llmsx modules, which are source-pinned for imminent physicaltypedDR. No newsubagents. ClaimexistingTASK258 first; applicableAGStele/promptmemory/versionworkflow; recordconstraintsbeforecode. No real GPU/API/model/services/LLDB/installedlauncher calls (even --check-installed: installedoldwrappernotyetpromoted and couldstartTinygrad). Source/mockCPU only; purpose-built passivecontract from reviewed /Users/mitch/dev/worktrees/skills-egpu-production-interface/rtx5080-egpu-harness/scripts/claude_egpu_frontdoor.py. Sourcefieldactualcheckerstatus exactlybycontract; no app defaultprovider/model change, preservecanonical Gemma31MLX/indexpause. eGPU one9Balias qwen3.5:9b-q4-k-m. standard research calls exact canonical /Users/mitch/.local/bin/claude-egpu --research TOPIC --depth standard --budget-minutes150 +existingparentboundancestry flags/stream-json/verbose;10800s outer deadline, preserve stream/cancellation ownedchild group/tree rollback/completionverify. Unsupported workflows explicit refusal, no fallback. Read currentbaselineorigin source beforechoice; semantictools/indexpaused readknownpaths/focusedrgwhennecessary. Pipeline3+steps granulartracker; branch draftonly afterCPUtests, no rootinstall/activation/fullDRclaim or mergewithoutrootsmoke. Review existing concepts_tui path: routeorrejectexplicitlyifunsupported avoidbypass. ProductionCLI reviewedbut installpending; rootactualtypingDRnewtrial means don't hardcode disposableworktree/privateclient. Root sole physicaloperator. Afterimplementationfocusedtests/staticchecks reportexacthashes/diff/expectedcontracts; taskremainopenpendingrootinstalledsmoke. No site changes neededunlesscurrentproviderUIcallsforconsistency; askrootfor scopebeforeexpanding.
```

## Exact scope clarification

```text
Proceed with the narrow concepts_tui.py early refusal and its focused test in your isolated /Users/mitch/dev/worktrees/llms-explorer-egpu-provider. That is within the original authorization to prevent provider bypass. Enforce the existing canonical-repository research route; do not expand the launcher contract. Verify installed bytes before any passive wrapper invocation, and do not invoke the installed wrapper during preparation. Root will perform activation after installation. Preserve unrelated edits; no new agents or actual model/service/GPU calls.
```

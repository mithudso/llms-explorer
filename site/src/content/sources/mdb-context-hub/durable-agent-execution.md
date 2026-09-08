---
title: "Durable Agent Execution & Long-Running Agent Runtimes"
description: "The infrastructure/platform layer that lets AI agents run for minutes, hours,"
---

# Durable Agent Execution & Long-Running Agent Runtimes

The **infrastructure/platform layer** that lets AI agents run for minutes, hours,
or days and survive process crashes, deploys, and long waits. It checkpoints
agent progress, replays or restores state on recovery, pauses indefinitely for
human approval, and makes tool side effects exactly-once. This skill covers the
PLATFORMS that make agent loops durable — **not how to design the loop logic
itself**.

## When to use / Skip

**Use when** you are choosing, integrating, or debugging the runtime beneath a
long-running agent:
- An agent must survive a pod restart / deploy mid-run without losing state.
- A run must pause for human approval (HITL) and resume later — without holding a
  worker, socket, or compute.
- A failed run must resume from step N, not re-run completed (paid) LLM/tool work.
- Tool calls that write to a DB, send email, or charge a card must not double-fire.
- You are picking among Temporal / LangGraph / DBOS / Restate / Inngest /
  Cloudflare / Trigger.dev / Vercel Workflow / Hatchet / Resonate.
- You hit a `NondeterminismError` or ask "where do my LLM calls go?"

**Skip — defer to the right neighbor:**
- **Designing the agent loop** (sequential pipeline, infinite loop, RFC-driven DAG,
  REPL loop) -> `autonomous-loops`. *We make loops durable; that skill designs them.*
- **Multi-agent topologies / councils / handoff routing** -> `ai-agents-orchestration`
  (this skill is the deep durable-execution spoke that hub routes to).
- **Agent memory architecture / context engineering** -> `ai-mcp-sdk-prompting`.
- **Generic (non-agent) job scheduling, MV3 alarms, SSE streaming** ->
  `software-engineering-patterns`.
- **Eval/observability of agent quality** -> `ai-agents-orchestration`
  (references/eval-driven-development.md) /
  `ai-llm-model-layer` (references/llm-observability.md).

## The durable-execution model

**Workflow-as-code + a journal.** You write ordinary-looking async code; the
runtime records every step's input/output into an append-only event log (a
"journal" or "checkpoint"), keyed per execution/thread. On crash, the runtime
restores the pre-failure state so the function continues "effectively once and to
completion — whether it runs for seconds or years."

Three architectural camps solve this. **This axis drives every selection
decision below:**

### Camp 1 — Deterministic replay / event sourcing
*(Temporal, Restate, DBOS, Hatchet, Resonate, Vercel Workflow, Inngest)*
On recovery the workflow function is **re-executed from the start**, but completed
steps return their **recorded results** instead of re-running. This demands the
workflow body be **deterministic**: same inputs -> same command sequence. Hence
**all non-determinism — LLM calls, tool I/O, time, randomness, UUIDs — must live
in journaled steps/activities, outside the replay path.** This is THE friction
when applying classic durable execution to agents.

- Temporal: `NondeterminismError` if re-generated commands don't match the Event
  History. Use SDK-provided replay-safe time/random; **move all I/O to Activities**;
  write replay tests before changing workflow code.
- The "function looks normal but is secretly re-run many times" mental model is
  shared by Restate, DBOS, Resonate, and Vercel WDK ("must be deterministic to
  allow resuming after failures").

### Camp 2 — State-checkpoint snapshots
*(LangGraph / LangSmith Deployment)*
Instead of replay-from-start, the runtime saves a **snapshot of graph state at
every super-step** — a *checkpoint* — keyed by **thread**. Resume = load the
latest checkpoint and continue. No determinism constraint on node bodies.
Caveat: replay/time-travel re-executes nodes *after* the chosen checkpoint, so
LLM/API/interrupt calls there fire again and may differ.

### Camp 3 — Durable actor
*(Cloudflare Agents SDK on Durable Objects)*
Each agent is an addressable stateful micro-server with an **embedded SQLite DB**.
It consumes **zero compute when hibernated**, wakes on an event (HTTP / WebSocket
/ alarm / email), reads its state, works, then sleeps. State lives *with* the
actor, not in a central journal.

## Platform landscape

### Temporal — the category-definer (deterministic replay)
- **Model:** Workflow (deterministic orchestrator) + Activity (non-determinism
  sink, auto-retried, result recorded in Event History). On replay, Activities are
  NOT re-run — recorded results are reused.
- **Agent fit:** put every LLM call + tool call in an Activity. Official **OpenAI
  Agents SDK integration** (late 2025). **Signals** deliver external/human input
  to a running workflow (HITL); **Queries** read state; durable **Timers** for
  delays; **ContinueAsNew** to trim unbounded history.
- **Ops:** heavyweight — server cluster (History/Matching/Frontend) + Cassandra/
  Postgres + Elasticsearch + a separately deployed worker fleet. MIT; self-host or
  Temporal Cloud. SDKs: Go/Java/Py/TS/.NET/PHP/Ruby.
- **Best for:** multi-tenant, multi-region, very-high fan-out, mission-critical,
  >4h tasks where full restart cost exceeds the Cloud bill.

### LangGraph / LangSmith Deployment — state-checkpoint, agent-native
- **Renamed:** "LangGraph Platform" (GA May 2025) -> **"LangSmith Deployment"**
  (Oct 2025). Same product; both names appear in the wild.
- **Persistence:** compile the graph with a **checkpointer** (Postgres/SQLite/
  memory) -> a state snapshot is saved every step, organized into **threads**
  (`thread_id` is the resume pointer).
- **HITL:** `interrupt(payload)` pauses at an exact point, persists state, and
  waits indefinitely; resume with `Command(resume=value)`. Payload must be
  JSON-serializable. Use a **durable** checkpointer in production.
- **Time-travel:** **Replay** (re-run from a prior `checkpoint_id`) and **Fork**
  (`update_state` at a past checkpoint -> branch an alternative trajectory). Nodes
  after the checkpoint re-execute; interrupts always re-trigger.
- **Assistants API:** one deployed graph -> many **assistants** (versioned configs:
  prompts/models/tools), promote/rollback versions. ~30 server endpoints; Remote
  Graphs for distributed multi-agent; LangGraph Studio for debugging.

### Cloudflare Agents SDK — durable actor on Durable Objects
- **Model:** `class X extends Agent`; each instance = one Durable Object with its
  own SQLite DB + WebSocket connections + scheduling. Wakes on event, hibernates
  when idle (zero compute).
- **State:** `this.setState()` serializes + persists to SQLite and broadcasts to
  connected clients; `this.state` lazily loads; `this.sql` for tables. Survives
  evictions/deploys/hibernation.
- **Hibernation:** WebSocket clients stay connected to Cloudflare's edge while the
  DO sleeps; on next event the constructor re-runs (keep it light). Use
  `serializeAttachment`/`deserializeAttachment` to restore per-connection state.
- **Scheduling:** `this.schedule(60|Date|"cron", "method")` and `scheduleEvery(s)`
  wrap DO **alarms**; stored in `cf_agents_schedules`; cron self-reschedules.
  Survives restarts.
- **Long work:** `keepAlive()` holds an alarm-backed heartbeat so the DO isn't
  evicted mid-stream; `runFiber()`/`stash()` checkpoint & recover long tasks;
  `waitForApproval()` for HITL; `runWorkflow()` delegates heavyweight multi-step
  work to Cloudflare Workflows; `subAgent()` for children.

### Inngest (+ AgentKit) — serverless-first memoized steps
- **Core:** `step.run("name", fn)` is a durable, auto-retried, **memoized** unit —
  on resume, completed steps return cached results instantly. `step.waitForEvent()`
  pauses for HITL/coordination; `step.sleep` for durable sleep (hours->weeks);
  `step.sendEvent()` fire-and-forget. Declarative cancellation by event. Priced per step.
- **AgentKit** (separate TS framework): builds multi-agent **Networks** with a
  **Router** + shared **State** — "a while loop with memory." *The Network/Router
  loop is orchestration (-> autonomous-loops / orchestration); durability comes from
  wrapping `network.run()` inside an `inngest.createFunction` to inherit retries,
  concurrency, and throttling.* This is the cleanest illustration of the
  loop-vs-runtime boundary.

### DBOS — durable execution *inside Postgres* (no orchestrator)
- **Model:** install the OSS library, annotate `@DBOS.workflow` / `@DBOS.step`.
  Step outputs + workflow state are checkpointed to a Postgres "system database."
  **No separate orchestrator** — app servers cooperatively dequeue workflows from a
  Postgres table and checkpoint steps themselves.
- **Recovery:** detect interrupted workflows -> re-call with checkpointed inputs ->
  each step checks Postgres for a saved output and skips if present -> first
  un-checkpointed step runs normally. = resume from last completed step.
- **Agent extras:** **fork a workflow** (copy checkpoints up to step N, restart from
  there — "git branch for an agent run"). Durable queues with global/per-worker/
  per-tenant flow control. Native **OpenAI Agents SDK** integration; **Databricks**
  partnership (Apr 2026, runs on Lakebase Postgres). **Go SDK** (2026). Py/TS/Go/Java.
  Lowest barrier if you already run Postgres; throughput ceiling + PG lock-in are
  the trade-offs.

### Restate — lightweight journal/replay, Rust single binary
- Core abstractions: **Virtual Objects** (stateful keyed entities with serialized
  per-key concurrency), **Workflows**, **Services**. Journals completed steps;
  replay returns cached results. Embedded RocksDB + arbitrary external storage;
  HTTP/2 + Connect/gRPC; per-handler idempotency. Single binary or Restate Cloud.
  BSL. Go/Java/TS/Py/Rust/Kotlin. Best when you want durable execution + stateful
  entities without operating a cluster; strong for serverless/edge.

### Hatchet — durable task queue on Postgres
- **Durable tasks** checkpoint to a durable event log every time they **wait**
  (sleep/event) or **spawn** children; replay resumes from the last checkpoint with
  exactly-once semantics. While waiting, Hatchet **evicts the task off the worker
  slot** and re-queues it later — ideal for agentic loops with long HITL waits.
  Offers both DAGs (static) and durable tasks (runtime-dynamic). Postgres for both
  runtime + observability (easy self-host). MIT. Py/TS/Go/Ruby.

### Trigger.dev (v3) — no-timeout durable serverless via CRIU
- Write linear async code; `wait.for({hours:1})` / `wait.until(date)` /
  `wait.forToken()` (HITL: token has a callback URL, complete via HTTP POST,
  resume with `wait.forToken()`); `triggerAndWait()` / `batchTriggerAndWait()`.
  **No timeouts** — code runs in a container paused/resumed via **CRIU**
  (Checkpoint/Restore In Userspace); checkpointed waits don't bill compute. OSS with
  the most mature self-host path (Postgres + Redis + S3-compatible store) or Cloud.

### Resonate — distributed async/await (emerging)
- "Durable Executions, Dead Simple." `ctx.run()` (durable step), `ctx.sleep()`,
  `ctx.rpc()`, and **Durable Promises** (await human/external input for days).
  Deterministic replay; single-binary Resonate Server. **Maturity caveat: early —
  v0.9.1, repo created Apr 2026, single-digit GitHub stars. Track for the model;
  do not treat as a Temporal peer yet.**

### Vercel Workflow — durability as a language directive
- OSS **Workflow Development Kit (WDK)** + managed **Vercel Workflows** (beta Oct
  2025 -> GA; 100M+ runs, 500M+ steps). Two directives: `"use workflow"` (durable
  fn) and `"use step"` (isolated, persisted, retried unit; default 3 retries).
  `sleep("1 month")` suspends with zero resources; `createWebhook()` returns a URL
  to resume on external/human input. **Durable streams**: `getWritable()` survives
  client disconnect/reconnect. Deep **AI SDK** integration. TS + Python.

## Core capabilities (cross-cutting)

- **Checkpointing / state persistence:** journal of step outputs (Temporal,
  Restate, DBOS, Inngest, Hatchet, Resonate, Vercel) vs state snapshot per node
  (LangGraph) vs actor-embedded SQLite (Cloudflare). Always use a *durable* backend
  in prod, never in-memory.
- **HITL interrupt & resume:** the unifying requirement is *pause without holding
  compute/worker/socket, resume on an external event.* LangGraph `interrupt()` +
  `Command(resume=)`; Temporal Signals; Inngest `waitForEvent`; Trigger.dev/Vercel
  webhook-or-token; Resonate Durable Promises; Cloudflare `waitForApproval()`.
- **Replay / time-travel debugging:** Temporal replays Event History (+ replay
  tests as a CI guard); LangGraph replay + **fork**; DBOS workflow **fork**. Forking
  = re-run an agent from step N with edited state to debug prompts/tools.
- **Scheduling / cron / delays:** Cloudflare `schedule`/`scheduleEvery` (DO alarms,
  self-rescheduling cron); durable sleep in Inngest/Trigger.dev/Vercel/Resonate;
  Temporal durable Timers. All survive restarts; long sleeps don't burn compute.
- **Concurrency & queues:** DBOS durable queues with global/per-worker/per-tenant
  flow control; Hatchet fine-grained parallelism + priorities; Temporal task
  queues; Inngest/AgentKit concurrency + throttling on the function.

## Integration patterns

**Temporal — non-determinism goes in Activities:**
```python
@workflow.defn
class AgentWorkflow:
    @workflow.run
    async def run(self, goal: str) -> str:
        # orchestration only — deterministic
        while not done:
            # LLM call + tool call MUST be Activities (recorded, retried, not replayed)
            decision = await workflow.execute_activity(call_llm, state, ...)
            result   = await workflow.execute_activity(run_tool, decision, ...)
            state = update(state, result)   # pure, deterministic
        return state
```

**LangGraph — interrupt for human approval, resume by thread:**
```python
graph = builder.compile(checkpointer=PostgresSaver(...))      # durable
cfg = {"configurable": {"thread_id": "user-42"}}
# node body: value = interrupt({"approve_action": proposed})  # pauses, persists
graph.invoke(inputs, cfg)                                      # runs until interrupt
# ...hours later, after a human decides...
graph.invoke(Command(resume="approved"), cfg)                 # resumes same thread
```

**Cloudflare — durable actor with cron + state:**
```ts
export class ProjectManager extends Agent<Env, State> {
  async onStart() {
    await this.schedule("0 9 * * *", "checkDeadlines", {}, { idempotent: true });
    await this.scheduleEvery(1800, "syncProgress");           // every 30 min
  }
  @callable() bump() { this.setState({ n: this.state.n + 1 }); } // persisted to SQLite
}
```

**Inngest AgentKit — loop is orchestration, durability via the wrapper:**
```ts
const network = createNetwork({ agents:[...], router: ({network,callCount}) => ... });
// durability + retries + concurrency come from wrapping network.run in a function:
inngest.createFunction({ id:"net", retries:1 },
  { event:"net/run" },
  async ({ event }) => network.run(event.data.input));        // <- the durable engine
```

## Selection / decision guidance

Decide by **where your workflow's boundary sits** and **who operates the control
plane**:
- **Already on Postgres, small team, workflow fits inside one DB boundary** -> DBOS
  or Hatchet ("Postgres is enough"). Lowest infra; exactly-once is tightest when
  side effects share the same DB. Watch throughput ceiling + PG lock-in.
- **Cross-service / multi-tenant / multi-region / very-high fan-out, maturity
  matters** -> Temporal. Pay the cluster ops cost; it earns its keep.
- **Agent IS naturally graph-shaped, you want first-class HITL + time-travel +
  versioned assistants** -> LangGraph / LangSmith Deployment.
- **Edge / per-user stateful agent, WebSocket chat, zero-idle-cost, global** ->
  Cloudflare Agents (Durable Objects).
- **Next.js / Vercel stack, want durability as a language directive, AI SDK
  integration** -> Vercel Workflow.
- **TypeScript serverless, fastest onboarding, per-step pricing** -> Inngest.
- **Unlimited task duration + mature self-host** -> Trigger.dev v3.
- **Want lightweight durable execution + stateful entities, single binary** ->
  Restate.
- **Tracking the frontier / distributed async-await model** -> Resonate (not yet a
  production peer).

Rule of thumb: *all of them will reliably persist your state.* The real questions
are language, who runs the control plane, migration cost in two years, and whether
you need replay-determinism discipline (Camp 1) or are happy with snapshots
(LangGraph) / actors (Cloudflare).

## Anti-patterns & failure modes

- **Non-determinism in a replay workflow body.** `Date.now()`, `Math.random()`,
  `uuid()`, direct HTTP/DB/LLM calls in a Temporal/Restate/Vercel/DBOS workflow ->
  `NondeterminismError` or silent drift on replay. Fix: move ALL I/O to
  steps/activities; use SDK replay-safe time/random.
- **Changing workflow code while runs are in flight** -> command/event mismatch.
  Use workflow **versioning/patching** and replay tests in CI.
- **In-memory / non-durable checkpointer in production** (LangGraph) -> state lost
  on restart; HITL `interrupt()` can't resume. Always back it with a DB.
- **Holding a worker / socket / compute during a long human wait.** Defeats the
  point and costs money. Use durable sleep / wait-for-token / interrupt so the
  platform evicts and re-queues (Hatchet, Trigger.dev, Inngest, Cloudflare
  `keepAlive` only for *active* work).
- **Assuming replay/time-travel re-reads from cache.** In LangGraph, nodes *after*
  the checkpoint re-execute (LLM/API/interrupt fire again). Budget for it.
- **Non-idempotent side effects.** Even with exactly-once *intent*, design tool
  steps to be idempotent (idempotency keys) — retries and recovery can re-enter the
  boundary.
- **Unbounded event history / state growth** on years-long runs -> use
  ContinueAsNew (Temporal) or equivalent; prune.
- **Picking the heaviest platform for a 3-person team.** Temporal's cluster is not
  a weekend project; don't adopt it for a single Postgres-centric service.
- **Confusing the loop with the runtime.** AgentKit Networks / LangGraph node
  wiring are *loop design* — see `autonomous-loops`. This skill is the durable
  substrate beneath them.

## 2025-2026 frontier

- **First-party durable execution everywhere:** AWS Durable Functions (Lambda),
  Cloudflare Workflows GA, Vercel Workflow — all shipped late 2025; durable
  execution is now table-stakes infra.
- **"Postgres is all you need" vs dedicated orchestrator** is the live debate
  (DBOS/Hatchet vs Temporal). DBOS Go SDK + Databricks/Lakebase (Apr 2026) push the
  library-on-your-DB model.
- **Official agent-SDK integrations:** Temporal x OpenAI Agents SDK (late 2025);
  DBOS x OpenAI Agents SDK; Vercel Workflow x AI SDK — durability wired directly
  under agent frameworks so tool calls become steps automatically.
- **Durable streams** (Vercel `getWritable()`, Cloudflare): agent output survives
  the user closing the browser; reconnect resumes the stream.
- **Workflow forking as agent-debugging** (DBOS, LangGraph): "git branch" a run
  from a checkpoint to reproduce and fix prompt/tool issues.
- **Maturity spread is wide:** Temporal (battle-tested) -> Vercel/Cloudflare/Inngest
  (production, young) -> Resonate (v0.9.x, experimental). Calibrate accordingly.

## Sources
1. Temporal — Workflow definition/determinism, put LLM/AI/API/DB calls in Activities: https://docs.temporal.io/workflow-definition , /workflows , /workflow-execution
2. Temporal — durable AI agent tutorial: https://learn.temporal.io/tutorials/ai/durable-ai-agent/
3. LangGraph — persistence, interrupts, time-travel, assistants: https://docs.langchain.com/oss/python/langgraph/persistence , /interrupts , /use-time-travel , https://docs.langchain.com/langsmith/assistants
4. LangGraph Platform GA / rename to LangSmith Deployment: https://www.langchain.com/blog/langgraph-platform-ga
5. Cloudflare Agents — agent-class, long-running-agents, schedule-tasks, DO websockets: https://developers.cloudflare.com/agents/concepts/agent-class/ , /concepts/long-running-agents/ , /api-reference/schedule-tasks/
6. Inngest — durable steps for AI agents, durable workflows, AgentKit Networks: https://www.inngest.com/blog/ai-agents-inngest-durable-steps , https://www.inngest.com/uses/durable-workflows , https://agentkit.inngest.com/concepts/networks
7. DBOS — architecture, postgres-is-all-you-need, durable agents + Databricks, Go-native, vs Temporal: https://docs.dbos.dev/architecture , https://www.dbos.dev/blog/postgres-is-all-you-need-for-durable-execution , https://www.dbos.dev/blog/building-durable-agents-dbos-databricks , https://docs.dbos.dev/explanations/comparing-temporal
8. Hatchet — durable tasks: https://docs.hatchet.run/v1/durable-tasks , https://github.com/hatchet-dev/hatchet
9. Trigger.dev v3 — no-timeout, CRIU, wait.* / waitpoints: https://trigger.dev/blog/v3-announcement , https://trigger.dev/docs/wait-for
10. Restate — develop docs / virtual objects: https://docs.restate.dev/
11. Resonate — develop docs + repo (v0.9.1, Apr 2026, early): https://docs.resonatehq.io/develop , https://github.com/resonatehq/resonate
12. Vercel Workflow — introducing-workflow, new-programming-model, docs: https://vercel.com/blog/introducing-workflow , https://vercel.com/blog/a-new-programming-model-for-durable-execution , https://vercel.com/docs/workflows
13. 2025-2026 landscape/comparisons: https://www.tiarebalbi.com/en/blog/dbos-vs-temporal-postgres-durable-execution , https://reptile.haus/journal/durable-execution-ai-agents-temporal-restate-inngest-2026/ , https://agentmarketcap.ai/blog/2026/04/10/durable-agent-execution-production-temporal-modal-event-sourced

> Boundary note: agent loop DESIGN (sequential/infinite/DAG/REPL) defers to `autonomous-loops`; multi-agent topologies to `ai-agents-orchestration` (this is the deep durable-execution spoke that hub routes to). Maturity is uneven — Temporal battle-tested; Vercel/Cloudflare/Inngest production-but-young; Resonate is v0.9.x experimental.

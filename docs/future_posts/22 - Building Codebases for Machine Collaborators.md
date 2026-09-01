# Building Codebases for Machine Collaborators

### How automated documentation, documentation-as-architecture, retrieval indexes, structured logging, testing, and dual-moded CLI / API / application surfaces make a codebase legible to — and verifiable by — an LLM agent

**A technical review · mdb-tam engineering · June 2026**

---

## Executive summary

The most prolific contributor to this codebase is no longer a person. The version journal (`memory.md` / `prompts.md`, now at `1.0.569`) records session after session of agent-driven change: prompt optimization sweeps, code deep-optimizations, board audits, document reconciliations. That shift is not cosmetic. An LLM agent is a different kind of collaborator than a human engineer, and it is different in exactly two ways that a codebase has to answer for:

- **It can only act on what it can find.** The agent works inside a finite context window that cannot hold the whole repository — the generated index alone spans 758 files. It does not "know the codebase"; it reads a slice of it per task. If the right file is hard to locate, the agent either scans fruitlessly or guesses — and a guess is a hallucination with a plausible voice.  
- **It can only be trusted as far as its work can be checked.** The agent is probabilistic. Its output is frequently correct and occasionally confidently wrong in the same register. Nothing about the output's tone tells you which. Trust therefore cannot come from the author; it has to come from an external check.

These two facts define two families of engineering practice, and the six topics of this review divide cleanly between them:

- **Legibility** — so the agent can find the right thing without scanning everything and without guessing: **automated documentation**, **documentation as architecture**, and **retrieval indexes**.  
- **Verifiability** — so the agent's work can be checked and its capabilities exercised without a human in the loop: **structured automated logging**, **testing**, and **test-centric design via dual-moded CLI / API / application surfaces**.

The connective claim of this review is that the sixth practice is the hinge between the two families. A capability reachable only through a graphical interface is neither testable (except by brittle UI automation) nor usable by an agent. The *same* capability placed behind a CLI and an HTTP API becomes scriptable — and a scriptable surface is simultaneously a test surface and an agent surface. You build the headless seam once, for testability, and the agent drives the product through the same door your tests do.

None of this is novel for human teams; it is ordinary good engineering. What is new is that the agent makes the cost of *skipping* these practices legible and immediate. A human tolerates a stale doc and a GUI-only feature. An agent acts on the stale doc and cannot reach the GUI-only feature at all.

**Scope and honesty note.** This review argues the *practices* and grounds each one in mdb-tam mechanisms that are *implemented and verified file-by-file*. It does **not** present a measured effect size: there is no A/B comparison of agent throughput or quality with versus without these practices, no recorded retrieval hit-rate for the indexes, and no measured defect-escape rate attributable to the test suite. Where a claim is demonstrated by the running system, the review says so; where a claim is an engineering argument, it says that too. The effect size is named future work, not a result reported here.

---

## 1\. The collaborator changed; the codebase must answer for it

A human engineer onboards once and accrues a mental model that survives across months. An LLM agent onboards every session and retains nothing between calls — the sibling whitepaper, `docs/whitepaper-on-disk-memory-and-prompt-storage-for-resumability-and-recall.md`, documents that statelessness and the on-disk memory layers built to work around it. This review takes the statelessness as given and asks a different question: given a collaborator that starts each session amnesiac, reads only a slice of the repo, and produces output that must be checked rather than trusted — **what should the codebase itself look like?**

The answer has two halves, and they are not interchangeable.

**Legibility** addresses the find-it problem. The agent's effective knowledge of the system is whatever it can locate and pull into context in the few moves it has before the window fills. Documentation that is current, structured for machine consumption, and indexed for lookup is the difference between an agent that finds the right file in one hop and one that reconstructs the wrong thing from a stale fragment.

**Verifiability** addresses the trust-it problem. Because the agent's output cannot be trusted on its face, the codebase has to provide cheap, automatable checks: logs that make runtime behavior observable after the fact, tests that convert "plausible" into "passing," and headless surfaces that let both the tests and the agent exercise a capability without a browser.

The rest of this review takes the six practices in that order — three for legibility, three for verifiability — and grounds each in what mdb-tam actually does.

---

## 2\. Automated documentation: generate from the source of truth, gate drift in CI

**The principle.** Hand-maintained documentation rots because the document and the code it describes are two separate sources of truth, and two sources of truth always drift. For a human reader, a slightly stale doc is a mild irritant. For an agent, it is a trap: the agent reads the doc as fact and acts on it. The fix is structural — make the document a *projection* of the code, regenerate it mechanically, and fail the build when the projection no longer matches its source.

**In mdb-tam.** The operations registry is the cleanest example. `scripts/generate-ops-registry-doc.mjs` declares itself the *sole writer* of `docs/operations-registry.json`, rendering the live registry in `server/src/lib/operations-registry.js` (18 operations at this version) into a deterministic JSON artifact. Determinism is deliberate: the script omits a volatile `generatedAt` timestamp specifically so a byte-level diff can detect drift. The `--check` mode (`npm run ops:doc:check`) runs in CI and fails if the committed doc no longer matches what the code would generate. The doc cannot silently fall out of sync, because the build refuses to stay green when it does.

The same instinct shows up across the repo's doc tooling: `python3 scripts/generate_llm_repo_index.py` regenerates the machine-readable repository index rather than asking anyone to maintain it by hand, and `scripts/rotate-workflow-logs.mjs` bounds the append-only journals so the per-session read path does not grow without limit.

**The discipline that makes it work.** A generated doc that *can* drift is worse than no doc, because it lies with the authority of something that looks maintained. The CI drift gate is the part that earns the trust — generation without gating just moves the rot one layer down. The boundary to hold is what to generate versus what to write: generate the *enumerable* facts (operation registries, file indexes, API surfaces, version stamps) where the code is the truth; hand-write the *rationale* — the "why this exists," the tradeoffs, the warnings — which no generator can derive. This review's own subject matter is the latter kind; the operations registry is the former.

**Failure mode.** Over-generation produces documents that are technically accurate and useless — a faithful dump of structure with none of the judgment a reader needs. Under-gating produces the confident lie. The repo's split — generated registry \+ drift gate, hand-written architecture prose — is the line to hold.

---

## 3\. Documentation as architecture: the doc is the interface the agent acts through

**The principle.** For an LLM agent, certain documents are not commentary *about* the system — they are part of the system's control surface. They are read at the start of work and they change what the agent does. When a document has that property, it is no longer prose to be kept "reasonably current"; it is a load-bearing component and deserves the same rigor as code: versioned, reviewed, drift-gated, and structured for machine consumption.

The operational test is simple: **if deleting or editing the document changes how the agent *behaves* — not merely what a human *understands* — the document is architecture.**

**In mdb-tam.** Three root documents pass that test:

- **`CLAUDE.md`** is loaded in full at the start of every session and states the authoritative rules: repository shape, commands, runtime architecture, storage surfaces, secrets handling, the workflow-log convention, the version-bump rule. It is not advisory. It overrode default assistant behavior during the production of this very review — the version-bump and workflow-log rules in it are why this document folds into `1.0.569` rather than triggering a release. That is architecture behaving as architecture.  
- **`AGENTS.md`** is the catalog of the 13 repo-local agents defined under `.claude/agents/`, rendered as a table with each agent's description, model, scope, when-to-invoke trigger, tools, and required env. An agent consults it to decide what to delegate and how. The catalog is the routing layer for a multi-agent system, expressed as a document.  
- **`GEMINI.md`** deliberately holds almost nothing: it defers to `CLAUDE.md` as the single source of truth and records only the handful of Gemini-CLI-specific deltas (`activate_skill` instead of `Skill`, `.gemini/settings.json` for MCP config). One contract, many harnesses — the anti-drift move applied to the agent-facing docs themselves.

Alongside these, the per-directory `README.md` files (service worker, common helpers, offscreen, server routes, native hosts, toolkit) and `docs/llm-repo-index.md` — the human-friendly entrypoint to the machine index — extend the same idea: documents whose job is to orient the next reader, human or machine, to where capability lives.

**Why it matters more than it used to.** When docs were only for humans, a stale architecture doc cost a confused afternoon. When the doc is the agent's operating contract, a stale doc is now a *bug* — it actively misdirects an actor that will follow it literally. That is precisely why the discipline of §2 (generate the enumerable, gate the drift) has to extend to the architecture docs: an agent-facing document that drifts is a defect in the control plane.

---

## 4\. Retrieval indexes: turn "scan everything" into "look up the few"

**The principle.** The agent's context window cannot hold the repository — the generated index alone spans 758 files. Without an index, locating the right one is a choice between two bad options: a full scan (impossible within the window) or a guess from partial knowledge (a hallucination). An index changes the complexity class of "find the relevant code" from *read-everything* to *look-up-then-read-a-few*. It is the single highest-return investment in expanding an agent's effective reach beyond its window, because it lets a small context do the work of a large one.

**In mdb-tam.** The repo runs two indexes, on purpose, because they carry different things:

- **`docs/high_signal_file_index.json`** is *curated* — 491 entries, each carrying rich per-file metadata a generator cannot infer: a human-written `summary`, an `entrypoint_type`, `how_to_run`, declared `inputs`/`outputs`, `integration_notes`, and `risk_notes`. This is judgment, persisted: *which* files matter and *how* to use them.  
- **`docs/llm-repo-index.json`** is *generated* — 758 indexed files across 96 directories (723 text-indexed, one sensitive file kept metadata-only), with `docs/llm-repo-index.md` as the human entrypoint. This is *coverage*: a complete, regenerable map no curator could maintain by hand.

Both are kept honest by `scripts/check-doc-indexes.mjs`, which verifies that every path referenced by *both* indexes (491 \+ 758\) still exists on disk and fails CI on any dead path — its own comment is blunt about why: "dead paths make both indexes harmful for LLM retrieval." The same script offers `--prune` for the curated index; the generated one is regenerated rather than pruned.

The pattern repeats one layer up, at the workflow level: the tam-MCP registries (`tam_list_skills` / `tam_search_skills`, the prompt library, the agent and URL registries) are indexes over reusable *capability*, so a procedure is findable rather than reconstructed from scratch — the same economics as the file index, applied to know-how.

**The deliberate trade.** Retrieval here is *lexical and just-in-time* — index lookup, `grep`, and reading the file when the task needs it — rather than a maintained embedding store. That is a considered choice (the agentic-search-over-embeddings stance discussed in the sibling on-disk-memory whitepaper): it sidesteps the staleness and re-indexing cost of a vector store at the price of semantic recall when a query and a file share meaning without sharing words. Curated *and* generated, lexical *and* gated: the index is treated as infrastructure, not a one-time artifact.

**Failure mode.** A stale index is worse than no index — it routes the agent to a path that no longer exists with full confidence. This is the §2 lesson again: an index that can drift must be drift-gated, which is exactly what `check-doc-indexes.mjs` is for.

---

## 5\. Automated logging: the agent's eyes on the runtime it cannot observe

**The principle.** An agent reasons over source and documents; it does not watch the program run. Whatever happened at runtime — which branch fired, which call timed out, which input was malformed — is invisible to it unless the system wrote it down in a form it can later read. Structured, machine-greppable logging is how a runtime makes itself observable after the fact, to a human debugging and to an agent triaging. That reframes logging from scattered `print` statements into a *designed surface* with a schema.

**In mdb-tam.** Both sides of the system treat logging as that designed surface:

- **Server.** `server/src/telemetry/logger.js` builds a single `pino` structured-JSON logger (`export const logger = pino(...)`) and hands out *scoped child loggers* via `logger.child({ scope })` — `server/src/index.js`, for instance, mounts HTTP logging under `scope: 'http'`. Every line is structured JSON with a module scope, so an agent (or a human) can filter by scope and field instead of grepping free text.  
- **Client.** `src/background/error-log.js` is a schema-versioned error log (`LOG_SCHEMA` `customer-dashboard-error-log`, version 1\) implemented as a bounded ring buffer (`MAX_ERROR_LOG_ENTRIES = 1000`) with multiple sinks: in-memory, a Sentry-lite integration (`src/shared/sentry-lite.js`), and a file at `~/Library/Logs/customer_dashboard_error_log.json`. Content scripts feed it through `error-log-adapter.js`; a shared client (`src/shared/error-log-client.js`) gives every context the same entry point. Schema-versioned, bounded, multi-sink — the log is a contract, not a side effect.

**The standout — logging that closes the loop.** The client error log does more than record. It carries an automated-remediation path (`AUTO_REMEDIATION_SCOPE = 'copilot_auto_remediation'`): a failure can be routed into a Copilot-CLI remediation pass against the `10gen/mdb-tam` repo with a bounded timeout (180 s). The log is wired not just to be *observed* but to *trigger* a fix attempt. (Honest scope: this path is implemented and opt-in; this review reports that it is wired, not a measured remediation success rate.)

**Failure mode.** Unstructured logs are unsearchable by an agent and nearly so by a human under pressure; over-logging buries the one line that mattered; and logging a secret is a security defect, not a debugging aid. The repo's logging guidance (`docs/logging.md`, and the secret-handling rules in `docs/SECURITY.md`) treats redaction and level discipline as part of the surface's design — structured does not mean indiscriminate.

---

## 6\. Testing: the safety rail that lets you trust agent-written code

**The principle.** When a probabilistic collaborator writes the code, the test suite is the mechanism that turns "this looks right" into "this is verified." It is the precondition for trusting agent output at all — the same logic behind the blind re-audit gate the document optimizer uses before it will certify a clean exit: the author's confidence is not evidence; an independent check is. A codebase that wants to accept agent contributions safely needs that check to be cheap, fast, and automatic.

**In mdb-tam.** The suite is **707 automated tests across four suites** — 294 in the extension (Vitest), 346 in the server (Vitest), 30 in the Live Hub Toolkit (`node --test`), and 37 in the Account-Context MCP server (`node --test`) — and it is wired into CI across three workflows (`syntax-check`, `unit-tests`, `extension-smoke`). The count in this sentence is not quoted from an older document; it was produced by *running the suites* in this working session.

What makes the harness notable is that it is **designed for the substrate it tests**:

- `test/setup.js` injects a minimal `chrome.storage` / `chrome.runtime` shim so extension code — which runs in a Chrome extension context in production — can be unit-tested under plain Node, with `resetChromeShims()` clearing state per test. The platform is faked so the *logic* is testable in isolation.  
- Server integration tests use `mongodb-memory-server` behind a graceful-skip (`MONGOMS_SKIP_IF_UNAVAILABLE`) so an air-gapped CI runner that cannot fetch the mongod binary degrades to a skip instead of a hard failure.  
- The genuinely non-deterministic seams — live LLM calls, WebAuthn PRF — are deliberately *not* unit-tested; the pure helpers around them (prompt builders, parsers, escapers) are. Test the part you can pin down, at the seam where it is pinnable.

**The discipline that makes tests trustworthy.** Tests earn trust by *running* — on every PR, in CI — and by being honest about their own count. A suite you assert but do not execute is documentation that lies, the §2 failure mode wearing a different hat. The repo also tests *real modules* against the platform shim rather than mocking its own code, which avoids the classic trap where the mocks pass and production fails.

**Failure mode.** Coverage as a target invites Goodhart's law — tests written to move a number rather than to catch a defect. Mock-everything suites verify the mocks. The repo's posture (shim the platform, exercise real modules, leave the unpinnable seams to integration) is the counter-pattern.

---

## 7\. Test-centric design: dual-mode the capability across CLI, API, and application

This is the hinge, and it is where verifiability and legibility meet.

**The principle.** A capability reachable *only* through the graphical interface is doubly stranded. It can be tested only through brittle end-to-end UI automation, and it is invisible to an agent, which cannot click. Place the *same* capability behind a **CLI** and an **HTTP API**, and it becomes scriptable — and a scriptable surface is, in the same stroke, a test surface *and* an agent surface. "Test-centric" means designing the headless seam *first*: the capability's primary, first-class entry point is a callable function behind an API or a command, and the GUI is a thin presentation layer over it. The test suite and the agent are then simply two more callers of the same seam, neither of which needs a browser.

**In mdb-tam — three worked examples.**

1. **The CallCard registry — the same operations exposed three ways, by design and stated in the code.** `server/mcp/call-mcp-server.js` says it plainly: it "exposes the same six operations the CLI (`server/cli/call.js`) and HTTP routes (`server/src/routes/call.js`) provide, so any MCP client … can drive them." Those six — `call_list`, `call_get`, `call_status`, `call_history`, `call_logs`, `call_run` — live once in the registry core; the CLI, the HTTP routes, and the MCP server are three thin adapters over it. One core, three doors.  
     
2. **The corpus / reports / snapshots API — one tested core, two clients.** The Node backend exposes `/api/corpus`, `/api/reports`, `/api/snapshots`, `/api/live`, `/api/account-360`, and `/api/operations` at `127.0.0.1:8787`. The Chrome extension (the application) consumes that API. So does the Account-Context MCP server — through a deliberately *thin* fetch wrapper (`packages/mcp-server/src/client.js`) that injects bearer auth and normalizes errors, exposing 13 `mdb_tam_*` tools over the same endpoints the extension calls. The 346 server tests hit that core directly, over HTTP, with no browser in the loop — and because the MCP server is a thin client over the *tested* API, the agent reaches the product through the same verified seam the tests do.  
     
3. **The Live Hub Toolkit — one engine, CLI and application surfaces.** The toolkit is a programmatic core (`live-hub-toolkit/src/core`, with `exporters/` and `generators/`) wrapped by a CLI (`cli/generate.js`, `preview.js`, `validate.js`) *and* invoked from the application: the `local_fs_host` native bridge resolves the toolkit root and runs `cli/generate.js` on the extension's behalf. The same engine is reachable from a terminal and from the dashboard; `node --test` exercises it directly (30 tests).

**Why this is *test-centric*, not merely modular.** Modularity says "separate concerns." Test-centric dual-moding says something sharper: **the headless surface is the test surface**, so build it first and let everything else — GUI, agent, scheduler — be a caller of it. You are not adding a CLI as a convenience; you are making the capability's canonical entry point one that a test can invoke without rendering a pixel. The GUI never has to be in the loop to verify the behavior, which is why the server suite can be 346 tests deep without a single headless-browser dependency for the core API.

**The agent dividend — dual-moding pays twice.** Every headless surface built for testability is, at no extra cost, an agent surface. The MCP tools, the CLIs, the HTTP API — these are the doors an agent uses to *drive the product*, and they are the same doors the tests use. The investment you make so a capability can be tested is the same investment that makes it reachable by a machine collaborator. This is the precise point where §6 (testing) and §3–4 (legibility and capacity) become one decision rather than two.

**Failure mode and tradeoff.** Maintaining N surfaces over one core costs something, and the failure mode is logic that gets *reimplemented* per surface and then drifts between them. The discipline is **one core, thin adapters** — never duplicated behavior. The CallCard MCP server wrapping the same six registry operations (rather than reimplementing them) is the pattern; the honest gap, noted in §9, is that the equivalence of the three surfaces is today a code-level convention, not an enforced cross-surface contract test.

---

## 8\. The practices as implemented

The six practices are wired into the running system, not aspirational. Each row maps a practice to what it buys a machine collaborator and to the mdb-tam mechanism that implements it; paths are repo-relative unless marked harness-level, and every path was confirmed to exist at the time of writing.

| Practice | What it buys the agent | mdb-tam implementation | Status |
| :---- | :---- | :---- | :---- |
| Automated documentation | Docs that cannot silently lie | `scripts/generate-ops-registry-doc.mjs` → `docs/operations-registry.json` (18 ops, from `server/src/lib/operations-registry.js`), `--check` CI drift gate; `generate_llm_repo_index.py`; `rotate-workflow-logs.mjs` | Active |
| Documentation as architecture | A control surface the agent acts through | `CLAUDE.md` (authoritative, loaded every session), `AGENTS.md` (13-agent catalog over `.claude/agents/`), `GEMINI.md` (defers to `CLAUDE.md`), per-dir `README.md` | Active |
| Retrieval index (curated) | Judgment about which files matter and how to run them | `docs/high_signal_file_index.json` — 491 entries w/ `how_to_run`, `inputs/outputs`, `risk_notes` | Active |
| Retrieval index (generated) | Complete, regenerable coverage map | `docs/llm-repo-index.json` (758 files / 96 dirs) \+ `llm-repo-index.md` | Active |
| Index integrity gate | An index that cannot rot into a trap | `scripts/check-doc-indexes.mjs` — validates 491 \+ 758 paths, CI-fails on dead paths, `--prune` | Active |
| Structured server logging | Observability of runtime the agent can't watch | `server/src/telemetry/logger.js` — `pino` \+ scoped `logger.child({ scope })` | Active |
| Structured client logging | Bounded, schema'd, multi-sink error record | `src/background/error-log.js` (v1 schema, 1000-entry ring buffer, Sentry-lite \+ file sinks) | Active |
| Log-triggered remediation | A log that closes the loop | `error-log.js` Copilot-CLI auto-remediation path (`10gen/mdb-tam`, 180 s) | Active (opt-in) |
| Test suite | Converts agent output from plausible to verified | 707 tests / 4 suites (294 / 346 / 30 / 37), 3 CI workflows | Active |
| Substrate-aware harness | Extension/server logic testable headlessly | `test/setup.js` chrome shims; `mongodb-memory-server` graceful-skip | Active |
| Dual-mode capability (CLI+API+MCP) | One tested core, reachable by test and agent alike | CallCard `cli/call.js` \+ `routes/call.js` \+ `mcp/call-mcp-server.js`; corpus/reports API \+ thin `mcp-server/client.js`; Live Hub Toolkit `src/core` \+ `cli/` \+ native bridge | Active |

### What this demonstrates — and what it does not

**Demonstrated.** Every mechanism above is present and operating. The files exist at the cited paths; the operations-registry doc is generated and CI-drift-gated; both indexes are validated against disk; the server logger hands out scoped children; the client error log is a versioned, bounded, multi-sink buffer with a wired remediation path; the four test suites run and total 707; and the CallCard capability genuinely exists as a CLI, an HTTP route set, and an MCP server over one core.

**Not demonstrated here.** This review does not measure the *effect*. It makes no claim about how much faster or more reliably an agent works in this codebase than in an un-instrumented one, no measured retrieval hit-rate for the indexes, and no measured defect-escape rate prevented by the suite. Those are real, separate measurement problems requiring their own instruments and a controlled comparison the system does not yet carry. The honest claim is narrow: the practices are implemented, internally consistent, and match current best understanding of what agent-assisted engineering needs.

---

## 9\. Implementation considerations

Six points, drawn from how this system is built.

**Generate the enumerable; hand-write the rationale; gate the drift.** Let the code be the source of truth for registries, indexes, and API surfaces, and regenerate the doc from it. Reserve prose for the "why" a generator cannot derive. Then make CI fail on drift — generation without a drift gate just relocates the rot.

**Treat an agent-facing document as code.** If editing a document changes how the agent behaves, it is part of the control plane. Version it, review it, and hold it to the same drift discipline as generated docs. A stale `CLAUDE.md` is a bug in the control plane, not stale prose.

**Run a curated index *and* a generated one, and validate both in CI.** The curated index carries judgment; the generated one carries coverage. Neither substitutes for the other. Validate every path on every build, because a stale index does not fail loudly — it misdirects confidently. Prefer lexical, just-in-time retrieval over a maintained embedding store unless you are prepared to pay the re-indexing and staleness cost.

**Make logging a structured, scoped, bounded surface — and redact.** Structured JSON with a module scope is greppable by an agent; a bounded ring buffer keeps it from becoming the problem; multiple sinks let the same event reach a human and a monitor. Close a log into automated remediation only where the remediation itself can be verified, and never log a secret.

**Test real modules against shims, not mocks of your own code — and run the suite.** Fake the platform (the `chrome.*` shim), not your logic. Leave genuinely non-deterministic seams to integration and test the pure helpers around them. Run the suite in CI on every change, and keep the published count honest by deriving it from a real run, not from memory.

**Design the headless surface first; let the GUI and the agent be thin clients.** Make a capability's canonical entry point a CLI command or an API call, so a test can drive it without a browser and an agent can drive it through the same seam. Keep one core and thin adapters; never reimplement the behavior per surface.

### Deliberately out of scope

Four things this codebase does not currently do, and why:

- **Quantitative measurement of the practices' effect** — no A/B harness, no retrieval hit-rate, no defect-escape telemetry attributing outcomes to these investments. This is the most important named gap; the thesis is testable, simply not yet measured here.  
- **Semantic / embedding retrieval over the indexes** — recall is lexical by deliberate choice (the agentic-search-over-embeddings stance), which is a real limitation when a query and a file share meaning without sharing words.  
- **Auto-generated rationale prose / fully autonomous doc maintenance** — generation covers enumerable facts; the "why" is hand-written, and pruning the curated index and the memory store is still a curated, human-in-the-loop act.  
- **Enforced cross-surface contract tests** — that the CLI, the HTTP API, and the MCP server expose *equivalent* behavior over one core is a code-level convention (a shared core, thin adapters) and is not yet pinned by a test that proves the three surfaces agree.

---

## 10\. Conclusion

The collaborator changed. It is stateless, it reads the codebase a slice at a time, and its output is probabilistic — frequently right, occasionally confidently wrong, with no tonal tell between the two. A codebase earns its keep with such a collaborator by being **legible** — so the agent can find the right thing without scanning everything or guessing — and **verifiable** — so its work can be checked and its capabilities exercised without a human in the loop.

The six practices are the two halves of that contract. Automated documentation, documentation-as-architecture, and retrieval indexes make the system legible: the doc is generated from the truth and gated against drift, the agent-facing doc is treated as the control surface it actually is, and a curated-plus-generated index turns an un-scannable repository into a lookup. Structured logging, testing, and test-centric dual-moding make the system verifiable: the runtime narrates itself in greppable structure, the suite converts plausible into passing, and the capability is built behind a headless seam first.

Dual-moding is the hinge that joins the halves. The CLI and the API you build so a capability can be *tested* are the same surfaces that make it reachable by an *agent*. Build the core once, behind a command and an endpoint; document and index it so it can be found; log and test it so it can be trusted — and the GUI, and the machine collaborator, both become thin clients over something solid. The transferable instinct is not "add docs and tests." It is: **assume your next contributor cannot see your screen and cannot be taken at its word, and build the codebase that still works for it.**

---

## Appendix A — practice → artifact inventory

| Artifact | Practice | Role |
| :---- | :---- | :---- |
| `scripts/generate-ops-registry-doc.mjs` | Automated docs | Sole writer of `docs/operations-registry.json`; `--check` CI drift gate |
| `server/src/lib/operations-registry.js` | Automated docs | Source of truth (18 operations) for the generated doc |
| `scripts/generate_llm_repo_index.py` | Automated docs | Regenerates the machine-readable repo index |
| `scripts/rotate-workflow-logs.mjs` | Automated docs | Bounds append-only journals (rotate \> \~200 KB → `docs/archive/`) |
| `CLAUDE.md` (root \+ `~/.claude/CLAUDE.md`) | Docs as architecture | Authoritative rules, loaded in full every session |
| `AGENTS.md` \+ `.claude/agents/` | Docs as architecture | Catalog \+ definitions of the 13 repo-local agents |
| `GEMINI.md` | Docs as architecture | Harness-specific deltas; defers to `CLAUDE.md` |
| `docs/high_signal_file_index.json` | Retrieval index | 491 curated entries with `how_to_run` / `risk_notes` |
| `docs/llm-repo-index.json` \+ `.md` | Retrieval index | 758-file generated coverage map \+ human entrypoint |
| `scripts/check-doc-indexes.mjs` | Retrieval index | Validates 491 \+ 758 paths; CI-fails on dead paths |
| tam-MCP registries | Retrieval index | Searchable skills / prompts / agents / URLs (capability findable) |
| `server/src/telemetry/logger.js` | Logging | `pino` structured JSON \+ scoped `logger.child({ scope })` |
| `src/background/error-log.js` | Logging | v1-schema, 1000-entry ring buffer; Sentry-lite \+ file sinks; Copilot remediation path |
| `src/shared/error-log-client.js`, `src/content/shared/error-log-adapter.js` | Logging | Shared client \+ content-script adapter |
| `test/setup.js` | Testing | `chrome.*` shims so extension logic runs under Node |
| `mongodb-memory-server` (`MONGOMS_SKIP_IF_UNAVAILABLE`) | Testing | Server integration tests with air-gapped graceful skip |
| `.github/workflows/{syntax-check,unit-tests,extension-smoke}.yml` | Testing | Three CI gates over 707 tests |
| `server/cli/call.js` · `server/src/routes/call.js` · `server/mcp/call-mcp-server.js` | Dual-mode | Same six CallCard ops as CLI \+ HTTP \+ MCP over one core |
| `127.0.0.1:8787` API \+ `packages/mcp-server/src/client.js` | Dual-mode | One tested API core; extension and 13-tool MCP server as thin clients |
| `live-hub-toolkit/src/core` \+ `cli/*` \+ `local_fs_host` bridge | Dual-mode | One engine, CLI \+ application surfaces; `node --test` exercises it |

## Appendix B — Sources and methodology

**Implementation sources (this repository / harness), verified to exist at the time of writing:**

1. `scripts/generate-ops-registry-doc.mjs`, `server/src/lib/operations-registry.js`, `docs/operations-registry.json` (18 operations); `scripts/check-doc-indexes.mjs`; `scripts/generate_llm_repo_index.py`; `scripts/rotate-workflow-logs.mjs`.  
2. `CLAUDE.md` (root \+ `~/.claude/CLAUDE.md`); `AGENTS.md` \+ `.claude/agents/` (13 definitions); `GEMINI.md`; per-directory `README.md` files.  
3. `docs/high_signal_file_index.json` (491 entries); `docs/llm-repo-index.json` (758 files / 96 dirs) \+ `docs/llm-repo-index.md`.  
4. `server/src/telemetry/logger.js`; `server/src/index.js` (`scope: 'http'`); `src/background/error-log.js`; `src/shared/error-log-client.js`; `src/content/shared/error-log-adapter.js`; `src/shared/sentry-lite.js`.  
5. `test/setup.js`; `server/test/` (`mongodb-memory-server`, `MONGOMS_SKIP_IF_UNAVAILABLE`); `.github/workflows/syntax-check.yml`, `unit-tests.yml`, `extension-smoke.yml`. Test totals (294 / 346 / 30 / 37 \= 707\) were produced by running the four suites in this working session.  
6. `server/cli/call.js`, `server/src/routes/call.js`, `server/mcp/call-mcp-server.js`; `server/src/index.js` route mounts (`/api/corpus`, `/api/reports`, `/api/snapshots`, `/api/live`, `/api/account-360`, `/api/operations`); `packages/mcp-server/src/client.js` (13 `mdb_tam_*` tools); `live-hub-toolkit/src/` \+ `cli/`; `native-host/local_fs_host.py`.  
7. Companions: `docs/whitepaper-on-disk-memory-and-prompt-storage-for-resumability-and-recall.md`, `docs/whitepaper-prompt-caching-and-token-optimization.md`, `docs/ARCHITECTURE.md`, `docs/logging.md`, `docs/TESTING.md`, `docs/MCP.md`.

**Methodology.** Every implementation claim was verified against the live repository before writing; no path is cited that was not confirmed to exist, and the headline test count was taken from a run of the suites in this working session rather than from prior documentation. This review is grounded in the repository rather than a literature survey; the few external concepts it leans on (the agentic-search-over-embeddings stance, Goodhart's law on coverage-as-target, the test-pyramid intuition) are invoked as well-known engineering touchstones, not as cited primary results. No quantitative effect of the practices is claimed; see the Scope-and-honesty note and §8.

---

*This review documents the mdb-tam workspace and its Claude Code harness as implemented at the time of writing (June 2026). File paths, counts, and the version number are current as of that date; consult the cited files for the authoritative, up-to-date configuration.*

---
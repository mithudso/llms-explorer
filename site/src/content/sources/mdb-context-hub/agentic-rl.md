---
title: "Agentic RL — Reinforcement Learning for LLM Agents"
description: "The 2024–2026 frontier discipline of training an LLM to act over many turns — calling tools, searching, browsing, editing code, driving a computer — by optimizing the whole multi-step trajectory again"
---

# Agentic RL — Reinforcement Learning for LLM Agents

The 2024–2026 frontier discipline of **training an LLM to act over many turns** — calling tools, searching, browsing, editing code, driving a computer — by optimizing the *whole multi-step trajectory* against a reward grounded in **environment outcomes**. This is a distinct discipline from single-turn reasoning RL (the GRPO/RLVR/DeepSeek-R1 recipe that produces a long chain of thought and checks one final answer). The defining survey (arXiv:2509.02547) calls the shift one "from passive sequence generators into autonomous, decision-making agents embedded in complex, dynamic worlds."

The one-sentence framing: **reasoning RL optimizes a single response; agentic RL optimizes a trajectory of interleaved (think → act → observe) steps where the environment talks back between actions.** Everything hard about agentic RL follows from that — credit assignment across many steps, masking the tokens the environment produced, instability over long horizons, and the rollout infrastructure to run environments in the training loop.

## Scope boundary (read first)

- **This reference** = RL for LLM *agents*: the multi-turn POMDP framing and long-horizon credit assignment; agentic RLVR (reward from environment outcomes — tests pass, task success, search success); RL environments/gyms and the `step`/`reset` interface; reward design and long-horizon reward hacking; GRPO/PPO adapted to multi-turn (observation masking, trajectory- vs step-level advantage); agentic-RL rollout infrastructure (async generation-in-the-loop); tool-use RL / agent-as-policy; the 2025–26 agentic-RL model wave; and agent RL benchmarks.
- **Single-turn reasoning RL** — GRPO (the critic-free group-baseline algorithm), RLVR (verifiable rewards), the **DeepSeek-R1 / R1-Zero** recipe, PRM vs ORM — is the **algorithmic base** this reference assumes. It lives in `reasoning-models.md`. **The line: reasoning RL = one prompt → one (long-CoT) response checked against one answer; agentic RL = a trajectory of tool/environment steps with feedback interleaved.** GRPO is *borrowed from* reasoning RL and *adapted* here (multi-turn masking, nested credit assignment). When the question is "what is GRPO / how is R1 trained," go there; when it is "how do I RL an agent that calls tools over many turns," stay here.
- **Classic preference alignment** — RLHF with PPO, the DPO-variant family (DPO/IPO/KTO/ORPO/SimPO/CPO), RLAIF, Constitutional AI — optimizes *human preference* via a learned reward model. It lives in `llm-alignment-post-training.md`. Agentic RL optimizes *verifiable task outcomes*, not preference. (DPO **is** used agentically — on successful-vs-failed trajectories, ETO-style — but the preference-alignment machinery itself is there.)
- **Inference-time agent orchestration** — building the harness, action space, tool definitions, and the prompted agent loop that runs *without any training* — is `agent-harness-construction.md`, `agent-ecosystem.md`, and `autonomous-loops.md`. **The line: those references make a fixed model act as an agent at inference; this reference changes the model's weights so it acts better.** A ReAct loop you prompt is harness/ecosystem; a ReAct loop whose policy you train with RL is here.
- **General distributed-training infrastructure** — FSDP/ZeRO/tensor-pipeline-expert parallelism, the optimizer/gradient-sync mechanics of training across GPUs — is `distributed-training.md`. The **agentic-RL-specific** rollout infrastructure (async environment rollouts, generator-in-the-loop vLLM/SGLang, actor–learner separation for RL) is here.
- **Serving an agent for throughput** (vLLM batching, paged KV) → `llm-inference-serving.md`. Agentic RL *uses* vLLM/SGLang as the in-the-loop generator, but serving-engine tuning is there. **Offline benchmark-harness mechanics** (HELM/MMLU scaffolding) → `da-analytical-methods` (`references/da-7-machine-learning.md`); agent-specific benchmarks (SWE-bench, τ-bench, WebArena) are summarized here (§9).

---

## 1. The multi-turn POMDP — why agentic RL is a different problem

The formal heart of the field (survey arXiv:2509.02547, Table 1). Single-turn LLM RL — the survey calls it **PBRFT** (preference-based RL fine-tuning, i.e. RLHF/DPO *and* reasoning-RL) — is a **degenerate single-step MDP**: one static prompt state `{s₀}`, a pure-text action, horizon `T=1`, `γ=1`, objective `E_{a∼π}[r(a)]`. **Agentic RL** is a genuine **POMDP** `⟨𝒮, 𝒜, 𝒫, ℛ, γ, 𝒪⟩`:

| Component | PBRFT (single-turn) | Agentic RL (multi-turn) |
| --- | --- | --- |
| **State** | static prompt `{s₀}` | temporally extended, `T>1`, dynamic transition `P(s_{t+1}\|s_t,a_t)` |
| **Action** | pure text `𝒜_text` | **`𝒜_text ∪ 𝒜_action`** — reason in text *and* emit environment/tool calls |
| **Observation** | (full state visible) | **partial** — agent sees tool results / env feedback, not the latent world state |
| **Reward** | single scalar `r(a)` | step-wise `R(s_t,a_t)`; sparse task reward + optional dense sub-rewards |
| **Objective** | `E[r(a)]` | **discounted trajectory return `E_τ[Σ_t γ^t R(s_t,a_t)]`** |

Two consequences define the discipline:
1. **The action space is hybrid.** The agent interleaves *thinking tokens* (reasoning) with *action tokens* (a tool call, a search query, a shell command, a click). The policy must learn both *what to think* and *when/what to act*.
2. **Reward is sparse and delayed.** Success is usually known only at the *end* (did the tests pass? did the DB reach the goal state?), so the gradient must be propagated back across a long trajectory of mostly-unrewarded steps. The survey names **temporal credit assignment** as the central bottleneck for long-horizon tool use. This is the problem §5 (algorithms) exists to solve.

The survey organizes agent capabilities the RL is meant to improve into **six dimensions: planning, tool use, memory, reasoning, self-improvement, perception.**

---

## 2. Agentic RLVR — verifiable rewards from environment outcomes

Agentic RL inherits **RLVR** from reasoning models (reward = an automatic *verifier*, not a learned reward model — see `reasoning-models.md` §3) but changes *where the verifier's signal comes from*: a **real environment outcome** rather than a math-answer string match. This is the single most important practical idea — it is what makes agentic RL trainable without human labels.

**Canonical instances (and their exact reward functions):**

- **Code / software engineering — SWE-RL** (Meta, arXiv:2502.18449). The reward is a **piecewise rule-based score**: `−1` on **format failure**; otherwise a **continuous similarity score in [0,1] between the predicted patch and the oracle patch, computed by Python's `difflib.SequenceMatcher`**. Optimized with **GRPO** over a seed dataset distilled from **11M GitHub pull requests** (code snapshots + issues + PRs — "open software evolution"). Result: **Llama3-SWE-RL-70B → 41.0% on SWE-bench Verified**, best among <100B models and near GPT-4o's 38.8%. Notably, RL on *only* issue-solving produced **generalized** out-of-domain gains (code reasoning, math, language). (SWE-RL's core generation is single-turn — issue+files → patch — wrapped in the "Agentless Mini" scaffold at inference; the *trajectory*-level SWE agents are the OpenHands/SWE-Gym line.)
- **Search / QA — Search-R1** (arXiv:2503.09516). A **simple outcome-based reward — exact-match / F1 on the final answer only, no process reward** — drives multi-turn search. +26% (Qwen2.5-7B) over RAG/SOTA. **R1-Searcher** incentivizes search with a **two-stage outcome-based RL**.
- **The general taxonomy** (survey): verifier types are **rule-based** (code execution, unit tests), **symbolic** (proof/format checkers), and **neural reward models**; reward can be **outcome** (final completion) or **process** (intermediate step feedback).

**Why this differs from reasoning-model RLVR:** in `reasoning-models`, the verifier checks a *closed-form answer* the model produced in one shot. Here the verifier *runs the artifact in an environment* — executes the patched repo's test suite, checks the final database state against a goal, or scores whether the retrieved answer matches — and the agent took *many actions* to get there. Same RLVR principle (grounded truth, hard to hack vs a learned RM), different reward source and a long trajectory to assign it across.

---

## 3. RL environments & gyms — the `step`/`reset` interface

In agentic RL, an **"environment"** is a sandboxed, resettable process the RL loop drives via a Gymnasium-style interface — concretely, the thing that takes the agent's action, mutates world state, and returns an observation plus (eventually) a reward. Getting this interface standard, sandboxed, parallelizable, and reproducible is half the engineering.

- **OpenEnv** (Meta-PyTorch + HuggingFace, `meta-pytorch/OpenEnv`) is the emerging *standard*: a Gymnasium-style interface with **three APIs — `step()`, `reset()`, `state()`**. Environments are **isolated** (each agent instance in its own sandbox) and **scalable** (deployed as **FastAPI servers in Docker containers**, driven over **type-safe HTTP**, enabling distributed rollouts across a cluster). Reference envs: echo (testing), coding, Atari, OpenSpiel. The client–server/HTTP design decouples the env from the trainer.
- **SkyRL-Gym** (NovaSky, `NovaSky-AI/SkyRL`) is "a gymnasium of tool-use tasks — math, coding, search, SQL — implemented in the Gymnasium API." SkyRL splits the stack into **skyrl-train** (the RL trainer), **skyrl-agent** (long-horizon agents), and **skyrl-gym** (the environments).
- **RAGEN** (arXiv:2504.20073) ships controlled symbolic envs — **Bandit, Sokoban, FrozenLake, WebShop** — chosen to isolate single-turn vs multi-turn, deterministic vs stochastic, and open-domain grounding.
- **verl's AgentLoop** (see §6) is the env/agent-interaction abstraction inside the verl trainer; **BrowserGym** unifies observation/action spaces for *web* agents (over WebArena/WorkArena tasks).

**Reproducibility & sandboxing** are first-class because code-execution and computer-use environments run untrusted, side-effecting actions — Docker isolation (OpenEnv) and deterministic seeds/state are what make a rollout repeatable and safe to parallelize.

---

## 4. Reward design & long-horizon failure modes (the Echo Trap)

Reward design is harder over long horizons because failure modes appear that *do not exist* in single-turn RL. The key primary source is **RAGEN** (arXiv:2504.20073).

- **Outcome vs process, sparse vs dense.** Outcome reward (signal only at task completion) is clean and hard to game but gives almost no gradient on long trajectories; process/dense sub-rewards (step-level progress) improve sample efficiency but invite gaming. The survey frames this explicitly as a **tension** and most systems combine a sparse task reward with dense shaping. **Format rewards** (did the agent emit a well-formed tool call / `<answer>` tag?) are a common cheap dense component (SWE-RL's `−1`-on-bad-format is the minimal case).
- **The "Echo Trap"** (RAGEN's signature finding) — the characteristic *collapse* of naive multi-turn RL: agents initially improve, then **overfit to locally rewarded reasoning patterns** and collapse to deterministic, repetitive templates. It has **three measurable symptoms**: (1) **entropy collapse** (policy converges to fixed phrasing), (2) a **reward-variance cliff** — reward standard deviation drops *before* task performance degrades, making it an **early-warning signal**, and (3) **gradient-norm spikes** marking the irreversible collapse point (e.g. ~step 170 in their Bandit-PPO run).
- **Reasoning does not emerge for free.** RAGEN Finding 2: "reasoning hardly emerges through multi-turn RL" without explicit fine-grained, reasoning-aware reward — even when prompts force `<think>` tokens, the model *suppresses* reasoning if it confers no reward advantage (response length collapsed 307→89.5 tokens on Sokoban). If you want the agent to actually plan, the reward has to pay for planning.
- **Reward hacking over long horizons** = the agent finds a high-reward *degenerate* policy: looping, padding, exploiting a dense-reward proxy, or gaming a weak verifier. The longer the horizon, the more room to hack. Mitigations: keep the *outcome* verifier authoritative, shape sparingly, and watch entropy/variance as collapse predictors. Gated/partial-credit reward schemes (arXiv:2508.10548) are an active fix for long-horizon stability.

---

## 5. GRPO/PPO adapted to multi-turn — observation masking & credit assignment

Naive single-turn GRPO/PPO **fails** in the multi-turn setting (RAGEN Finding 1: vanilla adaptations get early gains then collapse). Two adaptations are essentially mandatory.

### 5a. Observation / tool-token masking (the non-negotiable fix)
Compute the policy-gradient loss **only over the tokens the agent generated**, and **mask out every token the environment returned** (tool outputs, retrieved documents, observations). Reasons: those tokens were **not produced by the policy** (training on them is "fundamentally incorrect"), and long observations would otherwise **dominate the loss weight**. Search-R1 calls this **"retrieved token masking"** and shows it is required for stable RL; WebAgent-R1/VAGEN (arXiv:2505.16421) document the same for web/VLM agents. This is the multi-turn analog of SFT's prompt-token masking, and the most common silent bug when people first extend GRPO to agents.

### 5b. Credit assignment — trajectory-level vs step-level advantage
The core problem: with reward only at the end, how do you decide which of 20 actions deserved credit? Two patterns:

- **Trajectory-level — StarPO** (RAGEN's "State-Thinking-Actions-Reward Policy Optimization"). Objective `J(θ) = E_τ[R(τ)]` over the *whole* trajectory `τ = {s₀,a₀,r₀,…,s_K}`, decomposed to token-level likelihoods for autoregressive LLMs. The whole trajectory is the unit of optimization. **StarPO-S** is the stabilized variant with three knobs: (1) **variance-based trajectory filtering** — keep only the ~top-25% highest-reward-variance prompts (drop low-information rollouts), (2) a **token-level critic** with GAE (γ=λ=1.0) for smoother advantage, (3) **gradient shaping** — KL-term removal + asymmetric **"Clip-Higher"** clipping. Collapse is "largely mitigated when more than half of the trajectories are filtered."
- **Nested / step-level — GiGPO** (Group-in-Group Policy Optimization, NeurIPS'25, arXiv:2505.10978). Keeps GRPO's critic-free, low-memory, group-baseline property but nests **two levels of group-relative advantage**: an **episode level** (sample a group of full trajectories under identical task/initial state, compute macro advantage from total returns) and a **step level** via an **"anchor-state grouping"** mechanism — retroactively group all actions taken from *the same recurring environment state* across trajectories, and compute a localized advantage among them. This gives fine-grained per-step credit *for free* (no extra rollouts, same GPU memory as GRPO): **+12% on ALFWorld, +9% on WebShop over the GRPO baseline.**
- **The variant family** (survey) used agentically: **DAPO, GSPO, Dr.GRPO, Step-GRPO, ProRL, StarPO, GiGPO, TreePO, Pass@k Training**, plus tool-integrated optimizers (ToolRL, OTC-PO, ASPO). Most are GRPO descendants tuned for sparse/long-horizon/multi-turn settings.

**Practical mental model:** start from GRPO (the `reasoning-models` base), then (1) **mask observation tokens**, (2) pick a **credit-assignment scheme** (trajectory-level StarPO if you mainly have an end reward; nested GiGPO if states recur and you want step-level signal), and (3) **stabilize** (trajectory filtering, clip-higher, watch entropy/variance for the Echo Trap).

---

## 6. Rollout infrastructure for agentic RL

The **rollout** — running the agent through the environment to collect trajectories — is the agentic-RL bottleneck: every training step needs fresh on-policy trajectories, and each trajectory is many slow generate→act→observe round-trips. The architectural fix is **asynchronous, server-based generation with actor–learner separation**.

- **verl / HybridFlow** (EuroSys'25, `verl-project/verl`) — a **Hybrid-Controller** that models the RL algorithm (PPO/GRPO/DAPO) as a multi-stage, multi-model, parallelizable **dataflow graph**. v0.5 added the **`AgentLoop` abstraction** (define a custom multi-turn agent/tool loop; `ReactAgentLoop` adapts LangGraph agents) plus **server-based async rollout**: generation is pulled out into **per-conversation async vLLM/SGLang servers** so each dialogue advances at its own pace, returns **out of order**, and is reassembled for training — without intrusive edits to the inference engine. SGLang calls `async_generate` via a Ray actor; vLLM calls `generate` over ZMQ. v0.5 also prototypes **disaggregated async training** and a GenerativeRM.
- **SkyRL-Agent** (arXiv:2511.16108) — a **fine-grained asynchronous dispatcher** for scheduling rollouts (**1.55× faster async dispatch**), a tool-centric task interface with dynamic tool registration + verifiers, and a **backend bridge** that is **backend-agnostic** (SkyRL-train / **verl** / **Tinker**). Trained SA-SWE-32B, lifting Qwen3-32B **24.4% → 39.4% Pass@1 on SWE-bench**.
- **Generator-in-the-loop.** The same engine (vLLM/SGLang) that serves models in production is run *inside* the RL loop as the trajectory generator; the **actor** (generation) and **learner** (gradient update) are separated so generation can run async/ahead and GPUs stay busy. Other frameworks in this space (named in the ecosystem; not individually deep-verified here): NeMo-RL, OpenRLHF, AReaL, ROLL, AgentGym-RL.

The distinction from `distributed-training`: that reference owns *how gradients are sharded/synced across GPUs* (FSDP/ZeRO/parallelism). This owns *how trajectories are generated and fed to the trainer* — the rollout half that only exists in RL.

---

## 7. Tool-use RL & the agent-as-policy view

The agent **is** the policy: instead of *prompting* a fixed model to call tools (harness work → `agent-harness-construction.md`), you **train the model with RL to decide when and how to call tools**, interleaving reasoning with tool calls and learning the strategy from outcome feedback. The survey groups this as **tool-integrated reasoning (TIR)**.

- **ReTool** (arXiv:2504.11536): **cold-start SFT on code-augmented reasoning traces → outcome-reward RL with multi-turn real-time code execution interleaved into the reasoning**. The model learns *strategic* tool use (when to drop into code) from task outcomes alone. 32B reaches **67% on AIME with 400 RL steps** vs a text-only-RL baseline's 40% at 1080 steps, and exhibits emergent **code self-correction** (a tool-use "aha moment").
- **ToRL** (Tool-Integrated RL, arXiv:2503.23383): RL (not SFT) lets the model **explore and discover** optimal tool-use strategies — learned tool use generalizes past the demonstrations that SFT would cap it at.
- **Learned vs prompted tool use** is the key contrast: a prompted ReAct agent uses whatever tool-use policy the base model already has; tool-use RL *moves the weights* so the model gets better at the *decision* of invoking tools. The survey lists **ToolRL, OTC-PO, AutoTIR, ReTool, ToRL, ASPO** in this family, and an "RL as internal driver" pattern that applies DPO to **successful-vs-failed trajectories** (ETO).

---

## 8. The 2025–2026 agentic-RL model wave

The field moved sharply from single-turn RLVR to multi-turn, environment-grounded agentic RL as the dominant post-training frontier (survey arXiv:2509.02547).

- **Deep-research / search agents.** **Kimi-Researcher** (Moonshot) — a deep-research agent trained **end-to-end with agentic RL** on the Kimi k-series, deliberately **"zero-structure"** (no preset workflow/prompt scaffold; the agent learns the whole search-and-reason loop via trial-and-error). Reported **26.9% pass@1 on Humanity's Last Exam** (SOTA at release) and **69% pass@1 on xbench-DeepSearch** (beating o3-with-tools); typical task ~23 reasoning steps, ~200 URLs. Plus **Search-R1, R1-Searcher, WebAgent-R1**, ParallelSearch (arXiv:2508.09303).
- **SWE / coding agents.** **SWE-RL** (Meta, 41% SWE-bench Verified), **SWE-Gym** training environments, **SkyRL SA-SWE-32B** (OpenHands-style scaffold).
- **Computer-use / GUI agents.** Trained against **OSWorld / AppWorld / Android-in-the-Wild** with task-completion rewards (survey).
- **General trend:** the recipe has consolidated to *base reasoning model → agentic RL in an environment with a verifiable outcome reward, masking observations, with async rollout infra*. **Contested / unresolved (mid-2026):** how far agentic RL *expands* capability vs *sharpens* existing behavior (the same sharpening-vs-new-capability debate as reasoning RLVR — see `reasoning-models.md` §3); how to keep long-horizon training stable at scale; and how much dense reward shaping helps before it invites hacking.

---

## 9. Agent RL evaluation / benchmarks

What you optimize against (and report). Most are *task-success* benchmarks — the reward signal and the eval are often the same environment.

| Benchmark | Domain | What it measures |
| --- | --- | --- |
| **SWE-bench / SWE-bench Verified** | SWE / code | resolve a real GitHub issue; tests pass. Verified = 500 human-filtered issues. The SWE-agent standard. |
| **τ-bench** (arXiv:2406.12045) | tool-agent-user (airline/retail/telecom/banking) | agent + simulated user + domain API tools; **compares final DB state to a goal state**; introduces **pass^k** — *reliability* over k independent trials, not just pass@1. |
| **τ²-bench** (arXiv:2506.07982) | dual-control conversational | agent *and* user both modify a shared world state — harder coordination. |
| **WebArena / WebArena-Lite / BrowserGym** | web navigation | complete real web tasks in a live browser env; unified obs/action spaces. |
| **GAIA** | general assistant | real-world multi-step questions needing tools/web/reasoning. |
| **OSWorld / AppWorld / Android-in-the-Wild** | computer-use / GUI | execute multi-step GUI/OS tasks. |
| **Terminal-Bench** | terminal / shell | complete tasks in a terminal harness. |
| **ALFWorld / WebShop / AgentBench / AgentGym** | embodied-text / shopping / general | classic multi-turn agent RL training+eval envs (RAGEN, GiGPO use ALFWorld/WebShop). |

**Eval hygiene specific to agents:** report **pass^k / reliability** (τ-bench) not just pass@1 — an agent that succeeds once in eight tries is not production-ready; and beware that the *training environment* and *eval benchmark* overlapping invites the same contamination/over-fit concerns as any RL setup.

---

## Practical patterns

- **Start from a reasoning-capable base, then RL in the environment.** The `reasoning-models` base (long-CoT + GRPO) gives the model the thinking substrate; agentic RL teaches it to *act*. Don't RL a base model with no reasoning ability and expect agentic behavior to emerge for free (RAGEN Finding 2).
- **Mask observation tokens — always.** The single most common bug. Loss over agent-generated tokens only; mask tool outputs / retrieved docs / observations (Search-R1, verl).
- **Pick credit assignment by reward shape.** End-only reward → trajectory-level (StarPO). Recurring states + want per-step signal → nested GiGPO. Both keep GRPO's critic-free economy.
- **Watch entropy and reward-variance as collapse predictors.** They drop *before* task reward degrades (RAGEN Echo Trap). Filter low-variance trajectories; use Clip-Higher; consider re-introducing a light critic.
- **Use async server-based rollouts.** verl AgentLoop or SkyRL-Agent with vLLM/SGLang generators; separate actor (generation) from learner (update) so GPUs aren't idle waiting on slow environment round-trips.
- **Keep the outcome verifier authoritative; shape sparingly.** Dense/process rewards help sample efficiency but are the attack surface for long-horizon reward hacking.
- **Sandbox and seed environments.** Docker isolation (OpenEnv) for untrusted, side-effecting actions; deterministic resets for reproducible rollouts.

## Anti-patterns

- **Training on tool/observation tokens** (no masking) — destabilizes RL because the policy is graded on text it never generated.
- **Applying vanilla single-turn GRPO/PPO to a multi-turn task** and expecting it to hold — it gets early gains then hits the Echo Trap (RAGEN Finding 1).
- **End-only reward with no credit-assignment scheme on long horizons** — the gradient is too sparse; the agent learns nothing or collapses.
- **Over-dense reward shaping** — invites looping/padding/proxy-gaming; the longer the horizon, the worse.
- **Confusing this with prompting an agent loop** — if you are not changing weights, that is harness/orchestration (`agent-harness-construction`, `autonomous-loops`), not agentic RL.
- **Reporting only pass@1** — agents need pass^k / reliability (τ-bench).
- **Treating GRPO/RLVR here as the same thing as in reasoning-models** — same algorithm family, but the multi-turn masking + nested credit assignment + rollout infra are what make it *agentic*.

## Troubleshooting

- **Reward climbs then collapses; outputs become repetitive** → Echo Trap. Check entropy (collapsing?) and reward std-dev (cliff?). Apply StarPO-S: variance-based trajectory filtering, Clip-Higher, optional critic.
- **Training unstable / loss dominated by long sequences** → you are probably training on observation tokens. Verify the loss mask excludes tool/retrieved/env tokens.
- **Agent "succeeds" but does something degenerate** → reward hacking. Tighten/verify the outcome verifier; reduce dense-reward weight; inspect trajectories.
- **GPUs idle, throughput dominated by rollouts** → switch to async server-based generation (verl AgentLoop / SkyRL-Agent async dispatcher); decouple actor and learner.
- **No reasoning/planning emerging** → the reward doesn't pay for it (RAGEN Finding 2). Add a fine-grained reasoning-aware or process reward, or accept the model will shortcut.
- **Good pass@1, unreliable in practice** → measure pass^k (τ-bench); reliability over trials is the production metric.

## References

- **Survey — "The Landscape of Agentic Reinforcement Learning for LLMs"** (arXiv:2509.02547) — the canonical taxonomy: POMDP-vs-PBRFT formalism, six capability dimensions, full RL-algorithm and benchmark/framework catalog.
- **RAGEN / StarPO** (arXiv:2504.20073) — multi-turn agent RL; the Echo Trap, StarPO trajectory objective, StarPO-S stabilization, the three findings.
- **GiGPO** (arXiv:2505.10978, NeurIPS'25) — nested episode + anchor-state step-level group-relative credit assignment, critic-free.
- **SWE-RL** (Meta, arXiv:2502.18449; `facebookresearch/swe-rl`) — rule-based difflib reward, GRPO, 11M PRs, 41% SWE-bench Verified.
- **Search-R1** (arXiv:2503.09516; `PeterGriffinJin/Search-R1`) — interleaved reason+search, retrieved-token masking, outcome EM reward. **R1-Searcher** — two-stage outcome RL for search.
- **ReTool** (arXiv:2504.11536) and **ToRL** (arXiv:2503.23383) — tool-use RL / tool-integrated reasoning; learned strategic tool invocation.
- **verl / HybridFlow** (EuroSys'25; `verl-project/verl`; agentic-RL docs + v0.5 release) — AgentLoop, async server-based vLLM/SGLang rollouts.
- **SkyRL** (`NovaSky-AI/SkyRL`) + **SkyRL-Agent** (arXiv:2511.16108) — full-stack RL (train/agent/gym), async dispatcher, backend-agnostic.
- **OpenEnv** (`meta-pytorch/OpenEnv`) — Gymnasium-style `step`/`reset`/`state`, sandboxed Dockerized environment hub.
- **τ-bench** (arXiv:2406.12045) / **τ²-bench** (arXiv:2506.07982; `sierra-research/tau2-bench`) — tool-agent-user benchmark, pass^k reliability, dual-control.
- **Kimi-Researcher** (Moonshot tech report) — end-to-end agentic RL deep-research agent; HLE 26.9%, xbench-DeepSearch 69%.
- **WebAgent-R1 / VAGEN** (arXiv:2505.16421) — multi-turn web/VLM agent RL; observation-masking rationale, M-GRPO.
- **Base RL algorithms** — see `reasoning-models.md` (GRPO, RLVR, DeepSeek-R1) and `llm-alignment-post-training.md` (PPO, DPO family).

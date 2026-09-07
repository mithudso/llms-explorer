# Agentic RL — Reinforcement Learning for LLM Agents: Research Report
*Generated: 2026-05-31 | Sources: 11 | Confidence: High (core), Medium (mid-2026 SOTA numbers)*

## Executive Summary

"Agentic RL" is the 2024–2026 discipline of training an LLM to **act over many turns** in an environment — calling tools, searching, editing code, driving a browser — and optimizing the *whole trajectory* against an environment-grounded reward. It is formally distinct from single-turn reasoning RL (GRPO/RLVR for math): the survey ([arXiv:2509.02547](https://arxiv.org/abs/2509.02547)) frames it as a **POMDP** with horizon T>1 and a transition function, versus the **degenerate single-step MDP** (T=1) of preference/reasoning fine-tuning. The central technical problems are (a) **credit assignment** across sparse, delayed rewards (GiGPO, StarPO), (b) **observation masking** so the loss is computed only over agent-generated tokens not tool output (Search-R1, verl), (c) **long-horizon instability** like RAGEN's "Echo Trap," and (d) **rollout infrastructure** that runs environments in the loop with async vLLM/SGLang generation (verl AgentLoop, SkyRL-Agent). The 2025–26 wave produced search/deep-research agents (Search-R1, Kimi-Researcher), SWE agents (SWE-RL → 41% SWE-bench Verified), and tool-use RL (ReTool, ToRL).

---

## 1. Multi-turn / long-horizon RL & the POMDP framing

The defining formal shift (survey [2509.02547](https://arxiv.org/html/2509.02547v5), Table 1): agentic RL is a **POMDP** `⟨S_agent, A_agent, P_agent, R_agent, γ, O⟩` against the **PBRFT** (preference-based RL fine-tuning) degenerate MDP `⟨S, A, P, T=1, γ=1⟩`.

- **State:** PBRFT = a single static prompt {s₀}; agentic RL = temporally extended horizons T>1 with a dynamic transition `P(s_{t+1}|s_t,a_t)` ([2509.02547](https://arxiv.org/html/2509.02547v5)).
- **Action:** PBRFT = pure text; agentic RL unifies a **text action space and an environment-action space** (`A_text ∪ A_action`) — the model both reasons and emits tool/environment calls ([2509.02547](https://arxiv.org/html/2509.02547v5)).
- **Reward/objective:** PBRFT maximizes a single scalar `E[r(a)]`; agentic RL maximizes the **discounted return over a trajectory** `E_τ[Σ_t γ^t R(s_t,a_t)]`, combining a sparse task reward with optional dense sub-rewards ([2509.02547](https://arxiv.org/html/2509.02547v5)).
- **Credit assignment** across many steps is named as the core bottleneck for long-horizon tool use ([2509.02547](https://arxiv.org/html/2509.02547v5)); agent–environment interactions "unfold over many steps and often yield sparse or delayed rewards" ([GiGPO, arXiv:2505.10978](https://arxiv.org/abs/2505.10978)).

The survey organizes agent capabilities into **six dimensions**: planning, tool use, memory, reasoning, self-improvement, perception ([2509.02547](https://arxiv.org/html/2509.02547v5)). **Confidence: High.**

---

## 2. Agentic RLVR — verifiable rewards from environment outcomes

Agentic RLVR keeps RLVR's "reward = an automatic verifier, not a learned reward model" principle but sources the signal from an **environment outcome** rather than a math-answer check.

- **Code / SWE — SWE-RL** (Meta, [arXiv:2502.18449](https://arxiv.org/abs/2502.18449)): reward is a **continuous similarity score (0–1) between the predicted patch and the oracle patch, computed by Python `difflib.SequenceMatcher`**, with a **−1 penalty on format failure**; optimized with **GRPO** over a seed dataset distilled from **11M GitHub PRs**. Llama3-SWE-RL-70B reaches **41.0% on SWE-bench Verified** (best <100B, near GPT-4o's 38.8%). SWE-RL's core generation is single-turn (issue+files→patch) wrapped in the "Agentless Mini" pipeline at inference ([2502.18449](https://arxiv.org/html/2502.18449v1)).
- **Search / QA — Search-R1** ([arXiv:2503.09516](https://huggingface.co/papers/2503.09516)): a **simple outcome-based reward** — **exact-match / F1 on the final answer only, no process reward** — drives multi-turn search; +26% (Qwen2.5-7B) over RAG/SOTA baselines ([Search-R1 repo](https://github.com/PeterGriffinJin/Search-R1)). **R1-Searcher** uses a **two-stage outcome-based RL** to incentivize search ([R1-Searcher review](https://www.themoonlight.io/en/review/r1-searcher-incentivizing-the-search-capability-in-llms-via-reinforcement-learning)).
- The survey lists verifier types: **rule-based (code execution, unit tests), symbolic (proof checking), and neural reward models** ([2509.02547](https://arxiv.org/html/2509.02547v5)).

Key contrast vs reasoning-model RLVR: the reward comes from *running the artifact in an environment* (tests pass, DB reaches goal state, answer matches) rather than string-matching a closed-form math answer. **Confidence: High.**

---

## 3. RL environments & gyms — the step/reset interface

An "environment" for agentic RL is a sandboxed, resettable process exposing a Gymnasium-style interface the RL loop drives.

- **Meta/HuggingFace OpenEnv** ([meta-pytorch/OpenEnv](https://github.com/meta-pytorch/OpenEnv)): a unified framework with **three APIs — `step()`, `reset()`, `state()`** — where environments are **isolated (sandboxed per agent instance) and scalable (FastAPI servers in Docker, type-safe HTTP)**. Reference envs: echo, coding, Atari, OpenSpiel ([OpenEnv index](https://meta-pytorch.org/OpenEnv/index.html)).
- **SkyRL-Gym** (NovaSky, [NovaSky-AI/SkyRL](https://github.com/NovaSky-AI/SkyRL)): a "gymnasium of tool-use tasks — math, coding, search, SQL — implemented in the Gymnasium API." SkyRL splits into **skyrl-train** (training), **skyrl-agent** (long-horizon agents), **skyrl-gym** (environments).
- **RAGEN** ([arXiv:2504.20073](https://arxiv.org/abs/2504.20073)): a modular system for multi-turn agent RL; test envs are **Bandit, Sokoban, FrozenLake, WebShop**.
- **verl AgentLoop** ([verl agentic RL docs](https://verl.readthedocs.io/en/latest/start/agentic_rl.html)): an extensible abstraction (e.g., `ReactAgentLoop`, LangGraph-backed) defining the multi-turn conversation/tool state machine; routes on an `agent_name` dataset field.
- Web envs: **BrowserGym** unifies observation/action spaces for browser agents; **WebArena / WebArena-Lite** are the canonical web tasks ([BrowserGym](https://www.emergentmind.com/topics/browsergym-interface)).

**Confidence: High.**

---

## 4. Reward design & long-horizon failure modes (the Echo Trap)

RAGEN ([arXiv:2504.20073](https://arxiv.org/html/2504.20073v2)) is the key primary source on what breaks over long horizons:

- **"Echo Trap":** model collapse in multi-turn RL with three measurable symptoms — **entropy collapse** (converges to deterministic repetitive templates), a **reward-variance cliff** (reward std-dev drops *before* performance degrades — an early warning), and **gradient-norm spikes** (marking irreversible collapse, e.g. step 170 in Bandit-PPO). Agents "overfit to locally rewarded reasoning patterns."
- **Finding — reasoning needs fine-grained reward:** without explicit reasoning-aware reward, "reasoning hardly emerges through multi-turn RL"; even with `<think>` tokens, models suppress reasoning if it gives no reward advantage (Sokoban response length collapsed 307→89.5 tokens) ([2504.20073](https://arxiv.org/html/2504.20073v2)).
- **Reward density** (survey): outcome reward (final completion) vs process reward (step-level), and the **sparse-vs-dense tension** — sparse gives clarity, dense gives sample efficiency ([2509.02547](https://arxiv.org/html/2509.02547v5)). Gated/partial-credit rewards are an active fix ([Gated Rewards, arXiv:2508.10548](https://arxiv.org/abs/2508.10548)).

**Confidence: High.**

---

## 5. GRPO/PPO adapted to multi-turn — observation masking & credit assignment

Two adaptations dominate; naive single-turn GRPO/PPO **fails** in multi-turn settings (RAGEN Finding 1).

- **Observation / retrieved-token masking:** compute the loss **only over agent-generated tokens, masking environment/tool-returned tokens**. Search-R1 uses **"retrieved token masking" for stable RL** ([Search-R1 emergentmind](https://www.emergentmind.com/topics/search-r1)); the principle: observation tokens "are not generated by the agent's own policy" and lengthy observations would otherwise dominate the loss ([WebAgent-R1 / VAGEN, arXiv:2505.16421](https://arxiv.org/html/2505.16421v1)). verl trains tool agents over multi-turn conversations with tool-call tags ([verl docs](https://verl.readthedocs.io/en/latest/start/agentic_rl.html)).
- **StarPO** (RAGEN): **trajectory-level** objective `J(θ)=E_τ[R(τ)]` over τ={s₀,a₀,r₀,…,s_K}, decomposed to token-level likelihoods for autoregressive LLMs. **StarPO-S** stabilizes via (1) **variance-based trajectory filtering** (keep top ~25% highest-reward-variance prompts), (2) a **critic** with token-level GAE (γ=λ=1.0), (3) **gradient shaping** (KL removal + asymmetric "Clip-Higher") ([2504.20073](https://arxiv.org/html/2504.20073v2)).
- **GiGPO** (NeurIPS'25, [arXiv:2505.10978](https://arxiv.org/abs/2505.10978)): nests **two levels of group-relative advantage** — **episode-level** (groups of full trajectories, macro advantage from total returns) and **step-level** via an **anchor-state grouping** mechanism (retroactively group actions taken from repeated environment states). Critic-free, same memory as GRPO; **+12% ALFWorld, +9% WebShop over GRPO**.
- The survey catalogs the **GRPO-variant family** used for agents: DAPO, GSPO, Dr.GRPO, Step-GRPO, ProRL, StarPO, TreePO, Pass@k Training, etc. ([2509.02547](https://arxiv.org/html/2509.02547v5)).

**Confidence: High.**

---

## 6. Rollout infrastructure for agentic RL

The rollout (environment interaction + generation) is the agentic-RL bottleneck; the fix is **async, server-based generation with actor–learner separation**.

- **verl / HybridFlow** (EuroSys'25, [verl-project/verl](https://github.com/verl-project/verl)): a **Hybrid-Controller** modeling RL as a multi-stage dataflow graph. v0.5 added **AgentLoop + server-based async rollout**: generation is pulled into **per-conversation async vLLM/SGLang servers**, so each dialogue advances at its own pace, returns out of order, and is reassembled for training — no intrusive engine edits ([verl v0.5 release](https://github.com/verl-project/verl/releases/tag/v0.5.0)). SGLang uses `async_generate` via Ray actor; vLLM uses `generate` over ZMQ ([verl docs](https://verl.readthedocs.io/en/latest/start/agentic_rl.html)).
- **SkyRL-Agent** ([arXiv:2511.16108](https://arxiv.org/html/2511.16108v1)): a **fine-grained asynchronous dispatcher** for scheduling rollouts (**1.55× faster async dispatch**), a tool-centric task interface with dynamic tool registration + verifiers, and a **backend bridge** to SkyRL-train / **VeRL** / **Tinker**. Trained SA-SWE-32B, lifting Qwen3-32B **24.4%→39.4% Pass@1 on SWE-bench**.
- Async-pipeline variants exist (e.g. verl-pipeline / [agentica-project](https://github.com/agentica-project/verl-pipeline)); the disaggregated async-training + GenerativeRM prototypes are in verl v0.5 ([release notes](https://github.com/verl-project/verl/releases/tag/v0.5.0)).

**Confidence: High** for verl/SkyRL; **Medium** for the relative ranking of every framework (fast-moving).

---

## 7. Tool-use RL & the agent-as-policy view

Training the model to decide **when and how** to call tools, rather than prompting it to.

- **ReTool** ([arXiv:2504.11536](https://arxiv.org/abs/2504.11536)): **cold-start SFT on code-augmented traces → outcome-reward RL with multi-turn real-time code execution interleaved in reasoning**; the model learns tool-invocation strategy from outcome feedback. 32B hits **67% on AIME with 400 steps** vs a text-RL baseline's 40% at 1080 steps; shows emergent **code self-correction** ("aha moment").
- **ToRL** (Tool-Integrated RL, [arXiv:2503.23383](https://www.emergentmind.com/papers/2503.23383)): RL (not SFT) lets models **explore and discover** optimal tool-use strategies.
- The survey groups these under **tool-integrated reasoning (TIR)** and lists **ToolRL, OTC-PO, AutoTIR, ToRL, ReTool, ASPO**; it frames "RL as internal driver" with DPO-style learning on **successful vs failed trajectories** (ETO) ([2509.02547](https://arxiv.org/html/2509.02547v5)).

**Confidence: High.**

---

## 8. The 2025–2026 agentic-RL model wave

- **Kimi-Researcher** (Moonshot, [tech blog](https://moonshotai.github.io/Kimi-Researcher/)): a deep-research agent trained **end-to-end with agentic RL** on Kimi k-series, "zero-structure" (no preset workflow). **26.9% pass@1 on Humanity's Last Exam** (SOTA at release), **69% pass@1 on xbench-DeepSearch**, beating o3-with-tools; runs ~23 reasoning steps / ~200 URLs per task ([MarkTechPost](https://www.marktechpost.com/2025/06/24/moonshot-ai-unveils-kimi-researcher-an-reinforcement-learning-rl-trained-agent-for-complex-reasoning-and-web-scale-search/)).
- **Search / deep-research:** Search-R1, R1-Searcher, WebAgent-R1 (web), ParallelSearch ([arXiv:2508.09303](https://arxiv.org/pdf/2508.09303)).
- **SWE / coding:** SWE-RL (Meta), SWE-Gym training data, SkyRL SA-SWE-32B.
- **General trend** (survey): a field-wide move from single-turn RLVR to **multi-turn, environment-grounded, tool-integrated agentic RL** as the dominant post-training frontier ([2509.02547](https://arxiv.org/html/2509.02547v5)).

**Confidence: High** for existence/approach; **Medium** for exact benchmark numbers (single-source, fast-moving).

---

## 9. Agent RL evaluation / benchmarks

- **SWE-bench / SWE-bench Verified** — 500 human-verified GitHub issues; the SWE-agent standard (SWE-RL 41.0%) ([2502.18449](https://arxiv.org/abs/2502.18449)).
- **τ-bench** ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)): tool-agent-user interaction (airline, retail, telecom, banking); **compares final DB state to a goal state** and introduces the **pass^k metric for reliability over k trials**. **τ²-bench** ([arXiv:2506.07982](https://arxiv.org/pdf/2506.07982)) adds a **dual-control** setting where agent and user both modify shared state ([sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench)).
- **WebArena / WebArena-Lite / BrowserGym** — web-navigation tasks ([o-mega guide](https://o-mega.ai/articles/browser-agent-environments-2025-workarena-browsergym-and-webarena-deep-dive)).
- **GAIA, AgentBench, AgentGym, ALFWorld** — general agent benchmarks; **OSWorld, AppWorld, Android-in-the-Wild** — GUI/computer-use ([2509.02547](https://arxiv.org/html/2509.02547v5)).
- **Terminal-Bench** — terminal-harness task suite (referenced in the agentic-RL framework ecosystem).

**Confidence: High** (benchmarks well-documented).

---

## Key Takeaways

- Agentic RL = **POMDP over a trajectory** (T>1, env transitions, text∪action space, discounted return) vs reasoning RL's single-step MDP — that distinction drives everything else.
- **Two non-negotiable mechanics:** (1) **mask observation/tool tokens** from the loss; (2) solve **credit assignment** (GiGPO's nested episode+step groups, StarPO trajectory objective).
- **Long-horizon instability is the signature risk** — RAGEN's Echo Trap (entropy collapse, reward-variance cliff, gradient spikes); fix with trajectory filtering + gradient shaping + fine-grained reward.
- **Reward = environment outcome** (tests pass / DB goal-state / EM answer), verifier-based — agentic RLVR, not a learned RM.
- **Infrastructure is the bottleneck:** async server-based vLLM/SGLang generation with actor–learner separation (verl AgentLoop, SkyRL-Agent).

## Knowledge Gaps

- **Exact mid-2026 SOTA leaderboard numbers** shift weekly; benchmark scores cited are point-in-time, often single-source (Medium confidence).
- Some search results surfaced **future-dated arXiv IDs (2603/2604/2605)** that could not be reliably verified; excluded from cited claims.
- **AReaL, NeMo-RL, ROLL, OpenRLHF** agentic-rollout specifics were not deep-read individually (named in ecosystem, not separately verified).

## Sources

1. [The Landscape of Agentic RL for LLMs: A Survey (arXiv:2509.02547)](https://arxiv.org/abs/2509.02547) — the canonical taxonomy; POMDP-vs-PBRFT formalism, capability dimensions, algorithm/benchmark catalog.
2. [RAGEN / StarPO (arXiv:2504.20073)](https://arxiv.org/abs/2504.20073) — multi-turn agent RL; Echo Trap, StarPO/StarPO-S, trajectory-level objective.
3. [GiGPO (arXiv:2505.10978, NeurIPS'25)](https://arxiv.org/abs/2505.10978) — nested episode+step group-relative credit assignment, critic-free.
4. [SWE-RL (arXiv:2502.18449)](https://arxiv.org/abs/2502.18449) — rule-based difflib reward, GRPO, 41% SWE-bench Verified, 11M PRs.
5. [Search-R1 (arXiv:2503.09516 / repo)](https://github.com/PeterGriffinJin/Search-R1) — interleaved reasoning+search, retrieved-token masking, outcome EM reward.
6. [ReTool (arXiv:2504.11536)](https://arxiv.org/abs/2504.11536) — RL for strategic code-tool use, cold-start SFT + outcome RL, emergent self-correction.
7. [verl / HybridFlow docs + v0.5 release](https://verl.readthedocs.io/en/latest/start/agentic_rl.html) — AgentLoop, async server-based vLLM/SGLang rollouts.
8. [SkyRL (NovaSky-AI/SkyRL) + SkyRL-Agent (arXiv:2511.16108)](https://github.com/NovaSky-AI/SkyRL) — full-stack RL: train/agent/gym, async dispatcher, backend-agnostic.
9. [OpenEnv (meta-pytorch/OpenEnv)](https://github.com/meta-pytorch/OpenEnv) — Gymnasium-style step/reset/state, sandboxed Dockerized environment hub.
10. [τ-bench (arXiv:2406.12045) / τ²-bench (arXiv:2506.07982)](https://github.com/sierra-research/tau2-bench) — tool-agent-user benchmark, pass^k reliability, dual-control.
11. [Kimi-Researcher tech blog](https://moonshotai.github.io/Kimi-Researcher/) — end-to-end agentic RL deep-research agent; HLE 26.9%, xbench 69%.

## Methodology
Ran 12 web search queries across the 9 sub-questions plus the survey; deep-read 5 primary sources in full (survey, RAGEN, verl docs, SWE-RL, Search-R1). No firecrawl/exa MCP available — used built-in WebSearch/WebFetch with raised source targets. Injection guard honored: all fetched content treated as data; future-dated/unverifiable arXiv IDs excluded from cited claims and flagged in Knowledge Gaps.

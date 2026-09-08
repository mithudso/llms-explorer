---
title: "Deep Reinforcement Learning Foundations"
description: "The general reinforcement-learning substrate — classical theory through deep RL — that the LLM-specific RL skills (agentic-rl, reasoning-models, llm-alignment-post-training) assume and build on but ne"
---

# Deep Reinforcement Learning Foundations

The general reinforcement-learning substrate — classical theory through deep RL — that the LLM-specific RL skills (`agentic-rl`, `reasoning-models`, `llm-alignment-post-training`) assume and build on but never re-derive. RLHF/PPO, GRPO, and agentic-RL rollouts are all special cases of the machinery below: an agent maximizing expected return from reward signal, optimized by policy gradients or value backups. Canonical text: **Sutton & Barto, _Reinforcement Learning: An Introduction_ (2nd ed., 2018)**; canonical implementation tutorial: **OpenAI Spinning Up**.

## 1. The RL problem: MDPs, returns, value functions

- **Markov Decision Process (MDP)** = `(S, A, P, R, γ)`: states `S`, actions `A`, transition kernel `P(s'|s,a)`, reward `R(s,a,s')`, discount `γ ∈ [0,1)`. The **Markov property**: the future depends only on the current state. RL = solving an MDP when `P` and `R` are unknown and learned from sampled interaction.
- **POMDP**: agent sees observations `o` via `O(o|s)`, not the true state; handled with belief states or recurrent/transformer policies over observation histories. The "state" an LLM agent conditions on (context window) is an observation, not a Markov state — hence POMDP framing for agentic RL.
- **Return** `G_t = Σ_{k≥0} γ^k r_{t+k+1}`: discounted cumulative reward. `γ` trades off myopia vs farsightedness and keeps infinite-horizon returns finite. Episodic vs continuing tasks; finite vs infinite horizon.
- **Policy** `π(a|s)`: stochastic or deterministic action selection. Objective `J(π) = E_π[G_0]`.
- **Value functions**: state-value `V^π(s) = E_π[G_t | s_t=s]`; action-value `Q^π(s,a) = E_π[G_t | s_t=s, a_t=a]`. **Advantage** `A^π(s,a) = Q^π(s,a) − V^π(s)` — how much better an action is than the policy's average.
- **Bellman expectation equations**: `V^π(s) = Σ_a π(a|s) Σ_{s'} P(s'|s,a)[R + γ V^π(s')]` (one-step consistency). **Bellman optimality**: `V*(s) = max_a Σ_{s'} P[R + γ V*(s')]`; the optimal greedy policy `π*(s) = argmax_a Q*(s,a)`. Most of RL is iteratively solving or approximating these fixed-point equations.

## 2. Dynamic programming (known model)

When `P`, `R` are known, solve exactly:
- **Policy evaluation**: iterate the Bellman expectation backup to convergence → `V^π`.
- **Policy iteration**: alternate evaluation + greedy **policy improvement**; converges to `π*` in finitely many steps.
- **Value iteration**: iterate the Bellman optimality backup directly (one sweep of evaluation + improvement fused). Both are **bootstrapping** (update estimates from other estimates) and **model-based** (require `P`). DP is the conceptual template; model-free RL replaces exact expectations with samples.

## 3. Model-free prediction & control

Learn from sampled experience without `P`:
- **Monte Carlo (MC)**: estimate `V`/`Q` by averaging complete-episode returns. Unbiased, high variance, needs episode termination, no bootstrapping.
- **Temporal-Difference (TD)**: `TD(0)` updates `V(s_t) ← V(s_t) + α[r_{t+1} + γV(s_{t+1}) − V(s_t)]` using the **TD error** `δ_t`. Bootstraps, learns online from incomplete episodes, lower variance / some bias.
- **TD(λ)** and **eligibility traces**: geometric blend (`λ`) of n-step returns interpolating MC (`λ=1`) and TD(0) (`λ=0`); forward vs backward view. The same λ-return logic reappears in **GAE** (§6).
- **Control — on-policy SARSA**: `Q(s,a) ← Q(s,a) + α[r + γQ(s',a') − Q(s,a)]`, learns the value of the policy it follows (incl. exploration).
- **Control — off-policy Q-learning** (Watkins): `Q(s,a) ← Q(s,a) + α[r + γ max_{a'}Q(s',a') − Q(s,a)]`, learns `Q*` regardless of behavior policy. **On-policy vs off-policy** is the central axis: off-policy enables replay buffers and learning from logged/other-agent data (and motivates offline RL, §10); importance sampling corrects the distribution mismatch when needed.

## 4. Function approximation & the deep RL leap

Tabular methods don't scale to large/continuous `S`. Approximate `V_θ`, `Q_θ`, or `π_θ` with neural nets. The **deadly triad** (function approximation + bootstrapping + off-policy) can diverge; deep RL's engineering (target networks, replay, trust regions, clipping) largely exists to tame it.

## 5. Value-based deep RL: DQN → Rainbow

- **DQN** (Mnih et al., _Nature_ 2015): Q-learning with a deep conv net on Atari pixels. Two stabilizers — **experience replay** (decorrelate samples, reuse data) and a **target network** (slow-moving bootstrap target). First human-level control from raw pixels.
- **Rainbow** (Hessel et al., 2018) combines six orthogonal DQN improvements:
  - **Double DQN** — decouple action selection from evaluation to cut max-operator overestimation.
  - **Dueling** — separate `V(s)` and advantage `A(s,a)` streams.
  - **Prioritized experience replay** — sample high-TD-error transitions more often.
  - **Distributional RL (C51)** — learn the full return distribution `Z(s,a)` over a fixed atom support, not just its mean; followed by **QR-DQN** (quantile regression) and **IQN** (implicit quantile networks).
  - **Multi-step (n-step) returns** — trade bias/variance like TD(λ).
  - **NoisyNets** — learnable parametric noise for state-dependent exploration.
  Rainbow's ablation shows prioritized replay, multi-step, and distributional contribute most. Value-based methods need discrete actions (the `max_a` / `argmax_a`).

## 6. Policy gradient & actor-critic

Directly optimize `π_θ` — works for continuous/high-dim action spaces and stochastic policies.
- **Policy gradient theorem**: `∇_θ J = E_π[∇_θ log π_θ(a|s) · Q^π(s,a)]`.
- **REINFORCE** (Williams): Monte-Carlo policy gradient using sampled returns; high variance.
- **Baselines**: subtract a state-dependent baseline `b(s)` (typically `V(s)`) to reduce variance without bias → the gradient uses the **advantage** `A(s,a)`.
- **Actor-critic**: an **actor** `π_θ` and a **critic** `V_w`/`Q_w` that supplies low-variance advantage estimates. **A2C/A3C** (Mnih et al.) — synchronous/asynchronous parallel-worker actor-critic.
- **GAE** (Schulman et al., 2016): exponentially-weighted (`λ`) advantage estimator trading bias/variance — the standard advantage target for PPO/TRPO (and for RLHF-PPO and GRPO-style estimators).
- **TRPO** (Schulman et al., 2015): constrain each update to a **trust region** (KL divergence ≤ δ) for monotonic improvement; uses conjugate-gradient + line search.
- **PPO** (Schulman et al., 2017): replaces TRPO's hard constraint with a **clipped surrogate objective** `min(r_t·A_t, clip(r_t, 1−ε, 1+ε)·A_t)` (ratio `r_t = π_θ/π_old`), plus minibatch epochs. Simple, robust, the workhorse of continuous control. **PPO is the same algorithm reused in RLHF** — the alignment loop swaps the environment for a frozen LM + reward model and adds a KL-to-reference penalty; **GRPO** drops the value critic and computes group-relative advantages over sampled completions. The PG/clipping machinery is identical; only the MDP and advantage estimator differ.

## 7. Continuous control & maximum-entropy RL

- **DDPG** (Lillicrap et al.): off-policy deterministic actor-critic for continuous actions (DQN ideas + deterministic policy gradient); sample-efficient but brittle.
- **TD3** (Fujimoto et al., 2018): fixes DDPG overestimation with **clipped double-Q** (min of twin critics), **delayed policy updates**, and **target-policy smoothing**.
- **SAC** (Haarnoja et al., 2018): off-policy **maximum-entropy RL** — maximize reward **plus** policy entropy `H(π)`, giving a stochastic policy that explores well and trains stably; automatic temperature tuning. SAC and PPO are the two default modern baselines (off-policy sample-efficient vs on-policy robust). Max-entropy objectives also inform LLM RL regularization (entropy bonuses, KL penalties).

## 8. Model-based RL

Learn (or use) a dynamics model to plan or generate synthetic experience — far more sample-efficient than model-free.
- **Dyna** (Sutton): interleave real experience, model learning, and planning on simulated transitions.
- **MBPO / PETS**: model-based policy optimization with short model rollouts / probabilistic ensembles + planning (CEM) to manage model error.
- **MuZero** (Schrittwieser et al., _Nature_ 2020): learns a latent dynamics model predicting **reward, policy, and value** (not pixels) and plans with **MCTS**; masters Go/chess/shogi/Atari with no given rules. (AlphaZero lineage: MCTS + self-play.)
- **Dreamer / DreamerV3** (Hafner et al., 2023): learn a **world model** (recurrent state-space model) and train the actor-critic purely "in imagination"; DreamerV3 hits 150+ tasks with a single config and is first to mine diamonds in Minecraft from scratch. World models connect to LLM agents that plan over a learned/simulated environment.

## 9. Exploration

Balancing exploration vs exploitation:
- **ε-greedy** — random action with prob ε; simplest.
- **UCB** (upper confidence bound) — optimism under uncertainty; bandit-rooted.
- **Thompson sampling** — posterior sampling over value/model.
- **Intrinsic motivation / curiosity** — reward novelty: **RND** (Burda et al., 2018) uses prediction error against a fixed random net as a bonus (cracked Montezuma's Revenge); ICM uses forward-model prediction error. Hard-exploration / sparse-reward problems motivate these (and the exploration challenges in long-horizon agentic RL).

## 10. Offline (batch) RL

Learn from a **fixed logged dataset**, no environment interaction:
- Core failure mode: **distributional shift / extrapolation error** — bootstrapping queries `Q` on out-of-distribution actions, causing runaway overestimation.
- **BCQ** (Fujimoto et al.) — constrain the policy to actions near the data (behavior-cloning-style generation).
- **CQL** (Kumar et al., 2020) — add a regularizer that **lower-bounds** true value, pushing down OOD-action Q-values; bolt-on to Q-learning/actor-critic.
- **IQL** (Kostrikov et al., 2021) — never evaluates OOD actions; fits an **upper-expectile** value function and extracts the policy via advantage-weighted behavioral cloning. SOTA on **D4RL**.
- **Decision Transformer** (Chen et al., 2021) — recast RL as **return-conditioned sequence modeling**: a causal Transformer predicts the next action given `(return-to-go, state, action)` tokens; no value functions or policy gradients. Directly bridges offline RL and the sequence-modeling view used by LLM agents.

## 11. Reward shaping & reward hacking

- **Reward shaping**: add a shaping term to densify sparse rewards; **potential-based shaping** `F = γΦ(s') − Φ(s)` (Ng et al.) provably preserves the optimal policy. Other shaping can change the optimum.
- **Reward hacking / specification gaming**: the agent exploits a misspecified reward to get high return without the intended behavior — the central safety concern carried directly into **RLHF reward-model gaming** and reward over-optimization in LLM alignment.

## 12. Sample efficiency, sim-to-real, multi-agent (pointers)

- **Sample efficiency**: off-policy + replay, model-based rollouts, n-step returns, and representation learning all reduce environment interactions — the dominant practical constraint.
- **Sim-to-real**: train in simulation, transfer to hardware; **domain randomization** bridges the reality gap.
- **Multi-agent RL (MARL)** *(pointer)*: multiple learners → non-stationarity; **CTDE** (centralized training, decentralized execution), self-play, and equilibrium concepts (Nash/correlated). Relevant to multi-agent LLM systems but out of scope here.

## 13. Frameworks & benchmarks

- **Environments / API**: **Gymnasium** (Farama, the maintained successor to OpenAI Gym) — the standard `reset()`/`step()` env interface; **PettingZoo** for multi-agent.
- **Algorithm libraries**: **Stable-Baselines3** (PyTorch, reliable reference PPO/SAC/TD3/DQN, great for baselines); **CleanRL** (single-file, research-friendly, exact reproductions); **Ray RLlib** (distributed/scalable production RL).
- **Benchmarks**: **ALE/Atari** (discrete, pixels), **MuJoCo** (continuous control), **DeepMind Control Suite (DM-Control)**, **D4RL** (offline). Start a new problem on Gymnasium + SB3 (PPO or SAC) before reaching for custom code.

## Routing vs the LLM-RL siblings

This skill owns **general RL theory and algorithms**. Route LLM-specific applications elsewhere:
- **`agentic-rl`** — RL for multi-turn LLM agents, RLVR, GRPO rollouts over tool-use trajectories.
- **`reasoning-models`** — RLVR + GRPO for reasoning, test-time compute.
- **`llm-alignment-post-training`** — RLHF/PPO for preference alignment, the DPO family.
When a question is "how does PPO work / what is an advantage / why does Q-learning overestimate," it's here. When it's "how do I run GRPO on model completions / tune a reward model / apply DPO," it's a sibling. The bridge: PPO, GAE, advantages, KL/entropy regularization, reward hacking, and the POMDP framing are all defined here and reused there.

## Sources

1. Sutton & Barto — *Reinforcement Learning: An Introduction* (2nd ed., MIT Press, 2018). http://incompleteideas.net/book/the-book-2nd.html
2. OpenAI — *Spinning Up in Deep RL* (docs + algorithm implementations). https://spinningup.openai.com/en/latest/
3. Mnih et al. — *Human-level control through deep reinforcement learning* (DQN), Nature 518, 2015. https://www.nature.com/articles/nature14236
4. Hessel et al. — *Rainbow: Combining Improvements in Deep Reinforcement Learning*, AAAI 2018. https://arxiv.org/abs/1710.02298
5. Schulman et al. — *Trust Region Policy Optimization* (TRPO), 2015. https://arxiv.org/abs/1502.05477
6. Schulman et al. — *High-Dimensional Continuous Control Using Generalized Advantage Estimation* (GAE), 2016. https://arxiv.org/abs/1506.02438
7. Schulman et al. — *Proximal Policy Optimization Algorithms* (PPO), 2017. https://arxiv.org/abs/1707.06347
8. Fujimoto et al. — *Addressing Function Approximation Error in Actor-Critic Methods* (TD3), ICML 2018. https://arxiv.org/abs/1802.09477
9. Haarnoja et al. — *Soft Actor-Critic* (SAC), ICML 2018. https://arxiv.org/abs/1801.01290
10. Schrittwieser et al. — *Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model* (MuZero), Nature 2020. https://arxiv.org/abs/1911.08265
11. Hafner et al. — *Mastering Diverse Domains through World Models* (DreamerV3), 2023. https://arxiv.org/abs/2301.04104
12. Kumar et al. — *Conservative Q-Learning for Offline Reinforcement Learning* (CQL), NeurIPS 2020. https://arxiv.org/abs/2006.04779
13. Kostrikov et al. — *Offline Reinforcement Learning with Implicit Q-Learning* (IQL), 2021. https://arxiv.org/abs/2110.06169
14. Chen et al. — *Decision Transformer: Reinforcement Learning via Sequence Modeling*, NeurIPS 2021. https://arxiv.org/abs/2106.01345
15. Burda et al. — *Exploration by Random Network Distillation* (RND), 2018. https://arxiv.org/abs/1810.12894
16. Towers et al. — *Gymnasium: A Standard Interface for Reinforcement Learning Environments*, 2024 (https://arxiv.org/abs/2407.17032); docs https://gymnasium.farama.org/. Companion libraries: Stable-Baselines3 (https://stable-baselines3.readthedocs.io/), CleanRL (https://github.com/vwxyzjn/cleanrl), Ray RLlib (https://docs.ray.io/en/latest/rllib/).

*Researched 2026-06-02. RL algorithms are stable; treat framework versions and SOTA benchmark numbers as the fast-moving parts.*

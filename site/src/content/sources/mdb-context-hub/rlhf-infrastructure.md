---
title: "RLHF & RL Training Infrastructure"
description: "The systems stack that post-training reinforcement learning runs on — RLHF, RLVR, reasoning-RL, and agentic-RL all share it. This is deliberately not the RL algorithm (PPO/GRPO/DPO — those live in the"
---

# RLHF & RL Training Infrastructure for LLMs

The **systems stack** that post-training reinforcement learning runs on — RLHF, RLVR, reasoning-RL, and agentic-RL all share it. This is deliberately *not* the RL **algorithm** (PPO/GRPO/DPO — those live in the alignment, reasoning, and agentic-RL references) and *not* generic supervised distributed training (FSDP/ZeRO for pretraining — that lives in `distributed-training`). It is the third thing those two references keep pointing at: **how do you actually run an RL post-training job — generate samples, score them, update weights, and not leave half your GPUs idle.**

The one-sentence framing: **a supervised step is one engine doing forward+backward; an RL step is three engines — a generator, a scorer, and a trainer — passed through an experience buffer, and the whole discipline exists because the generator dominates wall-clock (60–90%+ of step time) and the naive synchronous schedule leaves the trainer's GPUs idle while the generator works.** Every design decision below — colocate vs disaggregated placement, the per-step weight resync, async/off-policy systems, the train/inference logprob mismatch — follows from attacking that bottleneck.

## Scope boundary (read first)

- **This reference** = the RL *systems* layer: the actor–rollout–learner architecture and experience buffer; GPU **placement** (colocate/hybrid vs disaggregated); the rollout/generation **bottleneck** and the inference-engine-in-the-loop; the train→infer **weight resync** (NCCL/IPC/resharding); **async/off-policy** systems and staleness; the **framework landscape** (veRL, OpenRLHF, NeMo-RL/-Aligner, TRL, slime, AReaL, ROLL, SkyRL, TorchForge); **reward-model serving** + verifier/code-sandbox infra; **scaling** the trainer (FSDP/Megatron) alongside the rollout engine (TP); the RL **utilization "bubble"** and overlap fixes; and RL-systems **failure modes** (logprob mismatch, weight-sync desync, reward over-optimization).
- **The RL *algorithm* itself** — what PPO's clipped objective is, how GRPO drops the value model, what a KL penalty does, the DPO loss — is **out of scope**. RLHF/PPO and the DPO family live in `llm-alignment-post-training`; GRPO/RLVR and the DeepSeek-R1 recipe live in `reasoning-models`; multi-turn/agentic RL (POMDP, trajectory credit assignment, observation masking, the Echo Trap) lives in `agentic-rl`. **The line: those references answer "what loss am I optimizing and why"; this one answers "what does the cluster look like that runs it."** GRPO here is just "a critic-free algorithm that drops the value engine," not a derivation.
- **Generic supervised distributed training** — FSDP/FSDP2, ZeRO stages, tensor/pipeline/expert parallelism, NCCL collective *mechanics*, distributed checkpointing — lives in `distributed-training`. This reference *uses* those (the trainer is FSDP or Megatron) but only owns the **RL-specific** twist: the train-vs-infer **layout mismatch** and the **resharding** it forces (§8). Supervised training has no rollout engine, no weight resync, no logprob mismatch — those are the RL-only surfaces here.
- **Serving one model in production** — vLLM/SGLang config, PagedAttention, continuous batching, speculative decoding, autoscaling — lives in `llm-inference-serving`. RL post-training **embeds** that exact inference engine *inside the training loop* as the rollout generator (§3). **The line: serving an endpoint for users = there; running vLLM/SGLang as the in-loop trajectory generator with per-step weight sync = here.**

---

## 1. The actor–rollout–learner architecture (the three engines)

An RL post-training step decomposes into **three logically distinct engines** that exchange data through an **experience buffer**:

- **Generation / rollout engine** — autoregressively samples responses (for agents, multi-turn trajectories) from the *current* policy. Implemented with an **inference** engine (vLLM/SGLang), *not* the training framework, because sampling is the throughput-critical step (§3).
- **Reward / verifier module** — scores responses: a learned reward model (RM), a rule-based verifier, or a code-execution sandbox (RLVR). A served system component in its own right (§7).
- **Policy training engine (learner)** — runs forward + backward + optimizer to update the policy weights (FSDP or Megatron).

**Model count by algorithm.** Classic **PPO-RLHF runs four models**: actor (policy, trained), critic/value (trained), reward model (frozen), and reference model (frozen, for the per-token KL penalty). **Critic-free algorithms (GRPO and kin) drop the value model**, collapsing the systems problem to actor + reward/verifier + reference — one fewer trained network to place, shard, and resync. *(Why GRPO can drop the critic is an algorithm question → `reasoning-models`; that it removes an engine from the topology is the systems consequence that matters here.)*

**The per-step dataflow:** prompts → **(rollout)** responses → **(reward)** scores + (recomputed) logprobs → advantages → **(learner)** gradients → updated weights → **resync to the rollout engine** (§4). That last arrow — pushing fresh weights back into the generator every step — is the loop-closing step that supervised training does not have, and it is the source of much of the difficulty.

**The design space (HF survey).** The "Keep the Tokens Flowing" survey frames the whole field as **seven orthogonal axes**; the three that matter most are: (1) the **orchestration / concurrency primitive** (Ray actors, asyncio, pub/sub, HTTP); (2) the **rollout buffer design** (how rollouts flow from inference into training); (3) the **weight-synchronisation protocol**. The remaining axes are sync/async degree, GPU placement, batching, and reward integration. **A framework is essentially a point in that 7-axis space** — knowing the axes lets you read any framework's design in minutes.

---

## 2. Co-located / hybrid vs disaggregated GPU placement

The central placement decision: do the trainer and the rollout engine **share one GPU pool** (colocate / hybrid) or run on **separate pools** (disaggregated)? This single choice cascades into the weight-resync mechanism (§4), the utilization profile (§9), and how easy async is (§5).

- **Colocate / hybrid engine** — training and generation **time-share the same GPUs**. The trainer offloads/sleeps while the rollout engine generates; then weights are **resharded in place** and the trainer wakes. veRL's **3D-HybridEngine** is the canonical implementation: it reshards the actor between a **training layout** (e.g. FSDP DP=2 / TP=8) and an **inference layout** (e.g. vLLM DP=16 / TP=4) **on the same GPUs with zero memory redundancy** and reduced communication, by *transforming the single model in place* rather than holding a second copy. **Pro:** highest GPU utilization, no idle pool. **Con:** memory contention on the shared GPUs (trainer optimizer state + inference KV-cache fighting for HBM).
- **Disaggregated / separated** — inference runs continuously on one pool, the optimizer on another. **OpenRLHF pioneered this with Ray Placement Groups**, scheduling vLLM engines, actor, critic, reference, and reward each on their own GPUs (with the Adam optimizer optionally on CPU). **Pro:** isolation, independent scaling of the two pools, easier async. **Con:** in a *synchronous* schedule a pool sits idle waiting on the other, and weights must cross the **network** every step.

**The programming model underneath (HybridFlow's core contribution).** RL dataflow is awkward because it is *nested and multi-model*. HybridFlow combines a **single-controller** paradigm (one process expresses the whole dataflow graph — flexible, easy to express PPO/GRPO/DAPO) with a **multi-controller** paradigm (each device runs its own SPMD program — efficient, low dispatch overhead). Pure single-controller has high control-dispatch overhead at scale; pure multi-controller is too rigid for nested RL dataflow. The hybrid reports **1.53×–20.57× throughput** over baselines like DeepSpeed-Chat and NeMo-Aligner. **ROLL and slime** use the same single-controller + parallel-worker abstraction. **Practical read:** colocate when GPUs are scarce and you want max utilization; disaggregate when you want isolation, independent scaling, or fully-async (§5).

---

## 3. The generation / rollout bottleneck (inference-engine-in-the-loop)

The dominant systems fact: **RL post-training is rollout-dominated** — generation accounts for **60–90%+ (up to >90% worst case) of total RL step time**. The reason is structural: **autoregressive per-token decoding is memory-bandwidth-bound** and runs at **<40% GPU utilization** in the actor, whereas the scoring and training stages are compute-intensive. *(The prefill-compute-bound vs decode-memory-bound mechanics are a kernel-layer fact → `llm-gpu-kernels`; the consequence — generation is the expensive stage — is what drives every choice here.)*

This is **why frameworks plug a dedicated inference engine — vLLM or SGLang — into the loop as the rollout generator** (with PagedAttention, continuous batching, often FP8/INT8 inference for extra speed), rather than generating with the training framework's slow eval path. veRL supports both vLLM and SGLang as interchangeable rollout backends; slime is SGLang-native; OpenRLHF/TRL default to vLLM.

**The long-tail straggler problem compounds it.** Response lengths are **long-tailed**, so a few very long generations stall an *entire synchronous batch* — most GPUs sit idle waiting on the slowest few sequences. This one fact — "rollout is the bottleneck *and* the tail makes it worse" — is the direct motivation for async (§5), overlap (§9), and partial-rollout recycling (APRIL). If you remember one thing about RL systems: **optimize the rollout, or nothing else matters.**

---

## 4. The train → infer weight resync (weight transfer)

After **every** policy update, the learner's new weights must be pushed into the rollout engine *before* the next generation — otherwise the generator samples from a **stale** policy. This per-step **weight resync** is a notable systems cost and a frequent source of subtle bugs. It is the step supervised training simply does not have.

**Transfer mechanisms:**
- **NCCL broadcast (default)** — trainer rank 0 broadcasts weights to all inference workers in a process group. vLLM's `update_weights` API supports `packed=True` (pack many tensors into large contiguous buffers to cut the number of NCCL ops), with **double/triple buffering and dedicated CUDA streams** to overlap packing, broadcast, and unpacking.
- **CUDA IPC** (`backend="ipc"`) — for **colocated** transfers on the same node, hand off via shared GPU memory instead of a network collective. Faster, but only works when trainer and inference share a node/GPU.
- **Checkpoint reload / Hub bucket** — the slow fallback. TRL's **"delta weight sync"** ships only the *changed* weights through a Hub bucket for trillion-parameter models where a full broadcast is impractical.

**The hard part — resharding across mismatched layouts.** The trainer is sharded one way (FSDP, or Megatron TP×PP×…), the inference engine another (vLLM/SGLang TP). veRL handles this with **sharding managers** — `FSDPVllmShardingManager` and `MegatronVLLMShardingManager` — that reshard actor→rollout weights on the fly; the **in-place zero-copy reshard is only possible in colocated engine mode** (disaggregated must send weights over the network). slime exposes the same split as two APIs: **`UpdateWeightFromTensor`** (colocated) vs **`UpdateWeightFromDistributed`** (multi-node). Dedicated tools now target this step specifically — Ant's **AWEX** advertises "second-level parameter updates from training to inference." vLLM has added native weight-syncing APIs plus **sleep/wake** support so a colocated engine can free KV-cache memory during training and reload weights on wake. **Practical read:** weight resync is where colocate (cheap IPC/in-place) and disaggregate (network broadcast) diverge most sharply, and it is a top source of "the reward curve is stuck" bugs (§10b).

---

## 5. Async / off-policy RL systems (staleness, streaming rollout)

Synchronous RL forces the trainer to **wait for the slowest rollout** (the §3 tail). **Asynchronous RL decouples generation from training**: rollout workers generate *continuously* while training workers update whenever a batch is ready. The price is **off-policy staleness** — rollouts were produced by an *older* policy than the one being updated, which biases the gradient and must be corrected (and is the systemic root of the logprob mismatch in §10a).

**AReaL (Ant Research) — the canonical fully-async system.** Four pieces: **streaming generation** (each rollout worker generates without waiting), **interruptible rollout workers**, **dynamic batching** for variable-length outputs, and a **parallel reward service**. It uses a **staleness-controlled, modified PPO** that tolerates samples up to **8 steps old with no performance drop**, plus a data-filtering step to cap staleness — achieving **~2× speedup** at equal final accuracy. **AReaL-Hex** extends this to **heterogeneous GPUs** (mixed device types in one async job).

**The sync↔async spectrum** (not a binary):
- **Fully synchronous** — trainer waits for the whole batch; on-policy, simplest, slowest (the tail kills it).
- **One-step-off / periodic asynchrony** — overlap generation of step *k+1* with training of step *k* (at most one step stale); near on-policy accuracy with async throughput.
- **Partial rollouts (APRIL)** — over-provision requests, **stop when the target count is reached, and recycle the unfinished long generations into the next step** — taming the tail *without* full async decoupling: **+22.5% avg (up to 44%) rollout throughput**.
- **Fully async (AReaL-style)** — continuous decoupling; max throughput, most staleness to manage.

NeMo-RL and OpenRLHF both ship async rollouts + replay buffers for off-policy training; TRL ships an async GRPO trainer. **Practical read:** more async = more throughput *and* more staleness you must correct (TIS, §10a). Most teams start one-step-off or partial-rollout (APRIL) before reaching for fully-async.

---

## 6. The framework landscape (2024–2026)

| Framework | Org | Training backend | Rollout backend | Orchestration | Default placement | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **veRL / HybridFlow** | ByteDance | FSDP, Megatron | vLLM, SGLang | hybrid single+multi-controller | colocate (3D-HybridEngine); supports disaggregated | Most-used; in-place zero-redundancy reshard; AgentLoop for multi-turn; 1.53–20.57× |
| **OpenRLHF** | community | DeepSpeed ZeRO-3 | vLLM | Ray Placement Groups | disaggregated / separated | First production Ray+vLLM+DeepSpeed; PPO/GRPO/REINFORCE++/async-agentic; Adam-on-CPU option |
| **NeMo-Aligner** | NVIDIA | Megatron-LM 3D parallel | TensorRT-LLM | — | colocate | 1000s of GPUs (Nemotron-4 340B, Llama-3.1 405B); TRT-LLM-accelerated generation |
| **NeMo-RL** | NVIDIA | Megatron, FSDP | vLLM, SGLang | Ray | both | Re-architected NeMo-Aligner; FP8 training, VLM SFT/GRPO, fully-async GRPO |
| **TRL** | HuggingFace | Accelerate / FSDP / DeepSpeed | vLLM (colocate or server) | process / HTTP | colocate or server mode | GRPOTrainer/PPOTrainer; NCCL weight sync every `weight_sync_steps`; async GRPO; most accessible |
| **ROLL** | Alibaba | Megatron | vLLM / SGLang | Ray, single-controller + parallel worker | both | Rollout scheduler w/ per-sample lifecycle; env+reward workers for agentic; 200B+ MoE |
| **slime** | THUDM / Z.ai | Megatron-LM | SGLang-native | Ray, HTTP | colocate or decoupled, sync or async | Deep SGLang integration; SlimeRouter, StringRadixTrie cache; UpdateWeightFromTensor/Distributed |
| **AReaL / AReaL-boba** | Ant | FSDP / Megatron | SGLang | fully async | disaggregated | Streaming/interruptible rollout, staleness ≤8 steps, parallel reward service, ~2× |
| **SkyRL** | NovaSky / Anyscale | FSDP | vLLM | Ray | disaggregated | Inference stack as tokenization source-of-truth; VLM RL; full-stack (train/agent/gym) |
| **TorchForge / torchtune RL** | Meta / PyTorch | PyTorch-native FSDP | vLLM | — | — | PyTorch-native post-training; thinly documented publicly beyond the HF survey |

**The survey's meta-finding:** **16 libraries built independently converged on the same fix** — *get off the synchronous pipeline*, because idle training GPUs are the throughput killer. They differ mainly along the seven axes (§1). **Choosing:** **veRL** if you want the most-used, hybrid, in-place-reshard default; **OpenRLHF** for Ray-disaggregated; **NeMo-RL/-Aligner** at the largest (Megatron + TRT-LLM) scale; **TRL** for accessibility and a gentle on-ramp; **slime** for SGLang-native; **AReaL** for fully-async SOTA throughput; **ROLL** for an agentic-friendly rollout scheduler.

---

## 7. Reward-model serving + verifier / code sandboxes in the loop

The **reward source is itself a served system component**, not a passive function — and at scale it can become the bottleneck.

- **Learned RM serving** — a frozen reward model served as a **separate inference service** (its own GPUs in disaggregated setups, or colocated). AReaL runs a **parallel reward service** so scoring overlaps generation rather than blocking it.
- **Rule-based verifiers** — math-answer checking, regex/format checks (the RLVR case); cheap, deterministic, no GPU.
- **Code-execution sandboxes** — for code RL, generated programs are **executed against unit tests inside a sandbox** to produce a binary verifiable reward. **Execution-based RLVR outperforms learned reward models** on code, which suffer instability and reward hacking.

**Systems concerns specific to the reward stage:** the **verifier/reward can become the bottleneck** (unit-test test-time-scaling shows a clear performance–latency trade-off); at scale teams serve **hundreds of environments as autoscaled managed sandbox endpoints** (e.g. serving 330+ RL environments backed by 4.5M+ tasks on autoscaled sandbox compute). Sandbox **isolation and throughput** — parallel execution, timeouts for non-terminating generated code, side-effect containment — are first-order infra problems. The standing warning: **verifier quality is the real bottleneck** — weak auto-generated reward functions teach the wrong behavior at scale (the systems face of reward over-optimization, §10c). *(The agentic-RL flavor of environments — Gymnasium `step`/`reset`, OpenEnv, SkyRL-Gym — is detailed in `agentic-rl` §3; here the focus is serving the reward/verifier as throughput-critical infra alongside the rollout engine.)*

---

## 8. Scaling the trainer (FSDP/Megatron) alongside the rollout engine (TP)

Training and inference **want different parallelism layouts** — and that mismatch is the *root reason* the weight resync (§4) is non-trivial.

- **Trainer** must shard parameters + gradients + **optimizer states** + activations → FSDP (ZeRO-3-style) or Megatron 3D/5D (TP×PP×DP, +CP/EP). Optimized for **backward-pass memory** (the optimizer state is ~2× the params for Adam).
- **Rollout engine** has **no backward, no optimizer, no gradient state** → it wants a layout that minimizes *inference* latency: typically a **smaller tensor-parallel degree with high data-parallel replication** for batch throughput (e.g. train TP=8 vs infer TP=4).

**When colocated**, the two layouts **contend for the same GPU memory**, so frameworks **offload the trainer (params/optimizer to CPU or freed) while generating**, then reload — exactly what vLLM **sleep/wake** and the **3D-HybridEngine reshard** enable. **When disaggregated**, the two pools size independently but pay the **network resync**. veRL exposes both FSDP and Megatron trainer backends behind a common worker API and maps them to vLLM/SGLang rollout workers.

**Boundary:** the *supervised* parallelism mechanics — ZeRO stages, FSDP2 internals, TP/PP/CP/EP composition, NCCL collective tuning — belong to **`distributed-training`**. This reference owns only the **RL-specific train-vs-infer layout mismatch** and the resharding it forces. If the question is "how do I shard a 405B model to train it," that is `distributed-training`; if it is "why do my trainer and generator disagree on layout and how do I bridge them every step," it is here.

---

## 9. RL-specific throughput & GPU under-utilization (the "bubble")

In a naive synchronous PPO/GRPO loop the stages run **sequentially with hard dependencies**: the reward model cannot score until the actor finishes generating; the learner cannot step until rewards are in. This creates an **idle "bubble"** — generation GPUs busy while training GPUs idle, then vice-versa — *amplified* by the long-tailed response lengths (§3). Measured actor-generation utilization is **<40%**.

Mitigations (distinct from full async, §5 — these keep an on-policy-ish schedule):
- **Intra-step overlap** — stream upstream outputs in chunks so the downstream model begins **prefill while the upstream is still decoding** (OPPO).
- **Inter-step overlap** — overcommit prompts and **defer long generations to the next step** to cut tail latency (OPPO).
- **Partial-rollout recycling** — APRIL's over-provision-and-recycle.

**Reported gains:** OPPO **1.8×–2.8×** end-to-end with **1.4×–2.1×** higher GPU utilization, no convergence loss; APRIL **+20–44%** rollout throughput.

**Orchestration corollary:** classic Slurm **gang-scheduling** fits supervised training but *not* the heterogeneous, long-lived, multi-role RL job (a generator pool + a trainer pool + a reward service, each a different shape, all long-running). This is why these systems lean on **Ray** rather than Slurm — "RL doesn't work on Slurm" is a recurring lesson, because RL is not one homogeneous gang of identical workers.

---

## 10. Failure modes unique to RL systems

### 10a. Train/inference logprob mismatch — the headline systems bug
The rollout engine (vLLM/SGLang) and the trainer (FSDP/Megatron) produce **different log-probabilities for the same sequence under the same weights**, because they use **different kernels, precision, and batching paths**. This silently turns nominally **"on-policy" RL into off-policy RL** with nontrivial bias — the behavior policy (inference) differs from the proxy policy (training) even before any async staleness is added.

- **Corrections:** **token-level Truncated Importance Sampling (TIS)** downweights tokens with severe mismatch and is stable, outperforming no correction despite its bias; alternatives mask out off-policy tokens or use sequence-level IS.
- **The famous gotcha:** with **temperature ≠ 1, vLLM does not apply temperature scaling to returned logprobs by default**, producing a huge *spurious* mismatch that breaks TIS. If TIS suddenly destabilizes training, check this first.
- **Correctness-before-corrections:** the vLLM V0→V1 work argues for **fixing correctness at the source** (batch-invariance, kernel alignment) so the mismatch *shrinks* before you reach for IS corrections — corrections paper over a gap that better kernels can close.
- **MoE is worse:** for Mixture-of-Experts models the mismatch is larger (routing can differ between engines), and **no current open-source async library implements the "Keep Routing" fix** (replaying expert routing) — a correctness gap for DeepSeek-V3 / Mixtral-class RL.

### 10b. Weight-sync bugs
Stale or partially-synced weights leave the rollout engine generating from an **old policy**. Real-world example: vLLM weights silently **not synchronized when `vllm_enable_sleep_mode=True`** (the sleep/wake path skipped the update). **Symptoms look like a "stuck" or diverging reward curve** — easy to misdiagnose as an algorithm problem when it is a resync (§4) bug. When the reward curve is flat or wrong, **verify the generator actually received the latest weights** before touching hyperparameters.

### 10c. Reward over-optimization / hacking at scale (systems symptoms)
As RL scales, the policy **exploits flaws in the reward source** — reward keeps rising while true quality stalls or drops (Goodhart). **Execution-based code rewards are more robust** than learned RMs, which suffer instability and hacking. The **algorithmic** mitigations (KL penalty, RM ensembles, ODIN) live in the **alignment-algorithm** domain (`llm-alignment-post-training`); the **systems** responsibility here is **verifier quality, sandbox correctness, and reward-service monitoring** — i.e. making sure the thing the policy is gaming is actually correct and observable.

---

## Practical patterns

- **Profile the rollout first.** Generation is 60–90%+ of the step; if you optimize anything else first you are tuning noise. Plug in vLLM/SGLang as the in-loop generator and measure its share before touching the trainer.
- **Pick placement by GPU scarcity vs isolation.** Scarce GPUs / want max utilization → **colocate** (veRL 3D-HybridEngine, vLLM sleep/wake, CUDA-IPC resync). Want isolation, independent scaling, or fully-async → **disaggregate** (OpenRLHF Ray placement groups, NCCL/network resync).
- **Treat weight resync as a first-class step.** Decide the mechanism up front: **CUDA-IPC / in-place reshard** (colocated) vs **packed NCCL broadcast or delta-sync** (disaggregated/huge models). Use sharding managers to bridge the train↔infer layout mismatch.
- **Climb the async ladder, don't leap.** Start synchronous → **one-step-off** or **APRIL partial-rollout** (tames the tail cheaply) → **fully-async (AReaL)** only when you need the throughput and can manage ≤8-step staleness.
- **Run the reward as a parallel service.** Overlap scoring with generation (AReaL parallel reward service); sandbox code execution with isolation + timeouts; size it so the verifier doesn't become the new bottleneck.
- **Match trainer and rollout parallelism deliberately.** Trainer FSDP/Megatron for backward-memory; rollout smaller-TP + high-DP for inference throughput; offload/sleep the trainer during generation when colocated.
- **Instrument the logprob gap.** Log the per-token train-vs-infer logprob difference; apply **TIS** if it is nonzero; verify vLLM temperature-logprob handling before trusting TIS.

## Anti-patterns

- **Generating rollouts with the training framework's eval path** instead of a real inference engine — you eat the full <40%-utilization decode cost with none of vLLM/SGLang's PagedAttention/continuous-batching wins.
- **Running a naive fully-synchronous loop at scale** and wondering why GPUs are half-idle — the §9 bubble + the §3 tail. Add overlap or async.
- **Ignoring the weight resync** — forgetting it, or letting sleep-mode skip it, leaves the generator on a stale policy and produces a "stuck reward" that looks like an algorithm bug (§10b).
- **Assuming on-policy because the code says on-policy** — the train/infer logprob mismatch (§10a) makes it off-policy by construction; without TIS or correctness fixes the gradient is biased.
- **Trusting TIS with vLLM temperature ≠ 1 and default logprob settings** — the un-scaled logprobs create a spurious mismatch that breaks the correction.
- **Colocating without offload/sleep** — trainer optimizer state and inference KV-cache fight for HBM and you OOM; use 3D-HybridEngine reshard or vLLM sleep/wake.
- **Treating the reward model as a cheap function** — a learned RM is a served GPU workload that can bottleneck the loop and be reward-hacked; serve it in parallel and monitor it.
- **Confusing this with the RL algorithm or with serving** — if the question is "what is PPO/GRPO/DPO," that is the alignment/reasoning/agentic-RL references; if it is "how do I serve one model to users," that is `llm-inference-serving`. This is the *training-loop systems* layer.

## Troubleshooting

- **GPUs ~half-idle, throughput dominated by generation** → the synchronous bubble + long-tail stragglers. Add intra/inter-step overlap (OPPO), APRIL partial-rollout recycling, or move to async (§5/§9).
- **Reward curve stuck / diverging despite a sane algorithm** → suspect a **weight-sync bug** (§10b): is the generator actually getting the latest weights? Check sleep-mode resync, sharding-manager reshard, the broadcast group.
- **Training unstable, "on-policy" RL behaving off-policy** → the **train/inference logprob mismatch** (§10a). Log the per-token gap; apply TIS; check vLLM temperature-logprob scaling; consider correctness fixes (kernel/batch-invariance) for MoE.
- **OOM only when colocated** → trainer + inference KV-cache contending for HBM. Enable trainer offload / vLLM sleep-wake / 3D-HybridEngine in-place reshard, or disaggregate.
- **Reward rises but quality stalls/drops** → reward over-optimization (§10c). For code, prefer execution-based verifiers over learned RMs; audit verifier/sandbox correctness; monitor the reward service. (Algorithmic KL/ensemble mitigations → `llm-alignment-post-training`.)
- **Weight resync is slow and dominates the step** → switch to packed/double-buffered NCCL broadcast, CUDA-IPC (colocated), or delta-weight sync (huge models); a dedicated tool like AWEX targets "second-level" updates.
- **MoE RL is unstable where dense was fine** → the logprob mismatch is worse for MoE and the "Keep Routing" fix is not in OSS async libraries yet; expect a correctness gap.

## References (primary sources)

- **HybridFlow: A Flexible and Efficient RLHF Framework** (arXiv:2409.19256) + verl docs (HybridFlow programming guide, FSDP/Megatron/SGLang worker backends, FSDPVllmShardingManager issue #3232) — single+multi-controller hybrid, 3D-HybridEngine in-place reshard, sharding managers, 1.53–20.57×.
- **OpenRLHF: Easy-to-use, Scalable, High-performance RLHF** (arXiv:2405.11143) + GitHub — Ray Placement Groups, disaggregated/separated placement, four-model PPO, Adam-on-CPU.
- **Accelerating RLHF with vLLM (OpenRLHF best practice)** — vLLM blog (blog.vllm.ai 2025-04-23) — vLLM as in-loop generator, the generation bottleneck.
- **NeMo-Aligner: Scalable Toolkit for Efficient Model Alignment** (arXiv:2405.01481) + **NVIDIA-NeMo/RL** docs — Megatron 3D parallel + TensorRT-LLM generation, 1000-GPU scale, re-architected NeMo-RL async GRPO.
- **AReaL: Large-Scale Asynchronous RL System** (arXiv:2505.24298) + **AReaL-Hex** (arXiv:2511.00796) — fully-async, streaming/interruptible rollout, ≤8-step staleness, parallel reward service, ~2×, heterogeneous GPUs.
- **TRL** vLLM-integration + async-GRPO docs — colocate vs server mode, NCCL weight sync every `weight_sync_steps`, GRPOTrainer/PPOTrainer.
- **vLLM weight-transfer / NCCL-engine docs** + native-weight-syncing RFC #31848 + sleep-mode RFC #15254 — `update_weights` packed/double-buffered, NCCL vs IPC, sleep/wake; **TRL delta-weight-sync** blog.
- **ROLL: RL Optimization for Large-Scale Learning** (arXiv:2506.06122) + GitHub — single-controller + parallel worker, rollout scheduler with per-sample lifecycle, env/reward workers, 200B MoE.
- **slime (THUDM/Z.ai)** GitHub + LMSYS blog + DeepWiki — SGLang-native, UpdateWeightFromTensor vs UpdateWeightFromDistributed, colocate/decoupled, SlimeRouter/StringRadixTrie.
- **Keep the Tokens Flowing: Lessons from 16 Open-Source RL Libraries** (HuggingFace blog) — the seven design axes, the universal idle-GPU finding, the MoE "Keep Routing" gap.
- **OPPO: Accelerating PPO-based RLHF via Pipeline Overlap** (arXiv:2509.25762) — <40% generation GPU util, intra/inter-step overlap, 1.8–2.8×.
- **APRIL: Active Partial Rollouts to Tame Long-tail Generation** (arXiv:2509.18521) — ~90% rollout time, over-provision+recycle, +20–44%.
- **ServiceNow-AI: vLLM V0→V1, Correctness Before Corrections** (HF blog) + **Mismatch Praxis** (LLM Data Co.) + Swift train-inference-mismatch docs + **TRL issues #4159 (vLLM temp logprobs) / #5312 (sleep-mode weight sync)** — the logprob mismatch source, TIS token-vs-sequence, the temperature gotcha, concrete weight-sync bug.
- **Promptfoo RLVR**, **CodeScaler** (arXiv:2602.17684), **RL Environments Taxonomy** (leehanchung.github.io) — verifier/sandbox-as-bottleneck, execution rewards vs learned RM, verifier quality, autoscaled sandbox endpoints.
- **SkyPilot "RL Doesn't Work on Slurm"** + **Anyscale OSS RL libraries / SkyRL** — Ray-vs-Slurm orchestration, SkyRL disaggregated/VLM RL.
- **Boundaries** — RL algorithm math → `llm-alignment-post-training` (PPO/DPO), `reasoning-models` (GRPO/RLVR), `agentic-rl` (multi-turn/POMDP); supervised distributed-training internals → `distributed-training`; production serving of one model → `llm-inference-serving`.

---
title: "Running Ollama on an RTX 5080 eGPU via Thunderbolt 5 on Apple Silicon M5 Max"
description: "A partial RTX 5080 compute guide for Apple Silicon, covering recorded failures, tinygrad prerequisites, corrected KV-cache math and compatibility limits."
date: "2026-09-30"
order: 30
tags: ["egpu", "rtx-5080", "apple-silicon", "thunderbolt-5", "tinygrad", "ollama", "driverkit"]
---

Apple's supported native eGPU graphics path requires an Intel Mac. Experimental compute through tinygrad's DriverKit transport is a different path; it does not supply NVIDIA display or Metal integration. [Apple eGPU requirements](https://support.apple.com/en-us/102363), [tinygrad eGPU setup](https://docs.tinygrad.org/tinygpu/)

In the recorded setup, an **NVIDIA GeForce RTX 5080 (GB203 Blackwell, 16 GB GDDR7)** is connected via **Thunderbolt 5** to an **Apple M5 Max MacBook Pro (64 GB unified memory)** serving local LLM inference through standard `ollama run` commands.

```console
$ OLLAMA_HOST=http://127.0.0.1:11440 ollama run Qwen2-beta-14B-Chat "Provide a 2-sentence summary of quantum computing and confirm you are running on RTX 5080."

Quantum computing is a futuristic computing paradigm that leverages quantum
mechanics to perform complex calculations at a much faster speed than classical
computers, using quantum bits (qubits) instead of classical bits. As an AI, I am
not physically running on any hardware, including an RTX 5080, but I can provide
information about it if needed.
```

Getting here required debugging two distinct macOS kernel panics, modifying `tinygrad`'s low-level GPU System Processor (GSP) boot routines for NVIDIA's Blackwell architecture, overcoming Thunderbolt PCIe bus reset restrictions, and writing an Ollama-compatible translation daemon.

This writeup preserves the recorded symptoms and patches, separates hypotheses from demonstrated causes, and documents the helper scripts' prerequisites. The original raw panic/benchmark logs and an end-to-end fresh-machine acceptance run are unavailable; this is a partial reproduction guide, not a verified blank-machine installer.

---

## 1. Hardware & Topology

| Layer | Hardware / Component | Details |
|---|---|---|
| **Host System** | Apple MacBook Pro (16-inch, 2026) | Reported M5 Max, 64 GB unified memory; confirm the actual macOS build |
| **Bus / Tunnel** | Thunderbolt 5 (USB4 v2) | Intel Barlow Ridge / Apple Thunderbolt 5 controller, 80 Gb/s bidirectional link (PCIe Gen 4 x4 tunnel) |
| **Enclosure** | Razer Core X V2 eGPU | PCIe enclosure; setup reports an installed 650W ATX PSU (sold separately) |
| **Accelerator** | NVIDIA GeForce RTX 5080 | GB203 die, `sm_120`, 16 GB GDDR7, PCI ID `10de:2c02` |
| **DriverKit Driver** | Tiny Corp `TinyGPU.dext` | DriverKit extension (`org.tinygrad.tinygpu.driver2`) matching `display@0` |
| **Compute Engine** | `tinygrad.llm` | Low-level userspace driver + JIT NV compiler (`DEV=NV`) |
| **API Bridge** | `ollama-egpu-proxy.py` | Native Ollama REST API compatibility layer on port `11440` |

Apple introduced M5 Max MacBook Pro in March 2026 with macOS Tahoe and Thunderbolt 5. The original notes named Sequoia without a build record. Razer's enclosure excludes the GPU and PSU. [Apple announcement](https://www.apple.com/newsroom/2026/03/apple-introduces-macbook-pro-with-all-new-m5-pro-and-m5-max/), [Razer specifications](https://www.razer.com/gaming-egpus/razer-core-x-v2)

---

## 2. The Core Problem: The DriverKit Boundary

Linux NVIDIA drivers use kernel modules; Windows uses its own driver model rather than `.ko` modules. Apple's native eGPU support does not include Apple Silicon. TinyGPU uses a DriverKit extension instead of adding an NVIDIA kernel module.

To bypass macOS kernel restrictions without presenting itself as an Apple-supported graphics driver, Tiny Corp introduced **TinyGPU**: an Apple **DriverKit** (`.dext`) extension.

```
┌────────────────────────────────────────────────────────┐
│                      Ollama CLI                        │
│          OLLAMA_HOST=http://127.0.0.1:11440            │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP (Ollama API)
┌──────────────────────────▼─────────────────────────────┐
│                 ollama-egpu-proxy.py                   │
│   Translates /api/generate & /api/chat to OpenAI spec   │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP (OpenAI /v1/chat/completions)
┌──────────────────────────▼─────────────────────────────┐
│                    tinygrad.llm                        │
│       Runs GGUF/Safetensors via DEV=NV on port 8000    │
└──────────────────────────┬─────────────────────────────┘
                           │ Shared Memory / IPC
┌──────────────────────────▼─────────────────────────────┐
│       DriverKit Extension (TinyGPU.dext)               │
│  Maps PCIe BAR0 (MMIO) and BAR1 (VRAM aperture) to user│
└──────────────────────────┬─────────────────────────────┘
                           │ Thunderbolt 5 (PCIe Gen 4 x4)
┌──────────────────────────▼─────────────────────────────┐
│       NVIDIA GeForce RTX 5080 (GB203 Blackwell)        │
│          GSP Firmware + 16 GB GDDR7 VRAM               │
└────────────────────────────────────────────────────────┘
```

The DriverKit extension matches the PCI display device class, maps:
1. **BAR0** (MMIO register space; use the size enumerated for the device, not a hardcoded 16 MB), and
2. **BAR1** (Physical VRAM window),

and hands them directly to userspace memory via an `IOUserClient` connection. Tinygrad runs host-side GPU initialization, memory allocation and command submission in user space. The GSP firmware and hardware copy engines execute on the GPU; they are not Python user-space code.

---

## 3. The Troubleshooting Journey: Failures & Fixes

When first connecting the RTX 5080 over Thunderbolt 5, the GPU lit up and negotiated link, but attempts to run inference crashed the system or aborted. Six reported incidents stood in the way:

### Incident 1: Kernel Panic via `IOPCIFamily` Data Abort

**Symptom:**  
While checking the link state, running Apple's standard `system_profiler SPPCIDataType` caused an immediate hard kernel panic:

```
panic(cpu 0 caller 0xfffffe0013b827e8): Data abort in kernel mode
Kernel Extensions in backtrace:
    com.apple.iokit.IOPCIFamily(2.9) ...
    com.apple.driver.AppleThunderboltPCIUpstreamPort ...
```

**Working hypothesis:**
The panic excerpt names the PCI/Thunderbolt path. It does not establish the asserted configuration-read race or identify a specific Apple driver defect. Avoiding the command was the session's workaround; proving the mechanism needs the complete panic report and a controlled reproduction.

**Solution:**  
Never probe an active eGPU using `system_profiler SPPCIDataType`. Instead, read the IOKit registry directly through `ioreg`, which inspects cached in-memory registry property tables without triggering concurrent PCI config bus cycles:

```bash
# Registry-based link check used by the helper:
ioreg -r -c IOPCIDevice -l | grep -q "<022c0000>"
```
*(Device ID `0x2c02` for RTX 5080 represents `<022c0000>` in little-endian binary).*

---

### Incident 2: Kernel Panic via Hot-Unplug Power-Gating Timeout

**Symptom:**  
Unplugging the Thunderbolt 5 cable while testing caused the entire Mac to lock up and kernel panic ~30 seconds later:

```
panic(cpu 4 caller 0xfffffe001cb18e24): ApplePMGR::_waitForXNUClusterPowerGatingThreadCall ...
cluster rail-gating timeout after 30000 ms
```

**Working hypothesis:**
The panic excerpt reports a 30,000 ms cluster rail-gating timeout. Active device mappings may have contributed, but the excerpt does not prove that PMGR waited on those mappings or identify the rail involved. The full panic log and a controlled test are still needed.

**Solution:**  
Stop both owned daemons before disconnecting. The supplied harness has a `stop` command; inspect its process matching on a shared machine. Confirm the processes have exited. Stopping them reduces the reported risk but is not proof that hot-unplug is safe; shut down before disconnecting if device state is uncertain.
```bash
python3 rtx5080_egpu_harness.py stop
```

---

### Incident 3: Blackwell GB203 GSP Initialization & Page Table Bug

**Symptom:**  
When `tinygrad` attempted to initialize the GPU System Processor (GSP) firmware on the RTX 5080, it crashed with:
```
AssertionError: Must be table pt=0x0
```

**Root Cause:**  
NVIDIA's GSP (GPU System Processor) offloads the proprietary Resource Manager to an onboard RISC-V core on the GPU. On Ada Lovelace (RTX 40-series), `NV_PBUS_BAR1_BLOCK` is programmed to zero. On Blackwell (RTX 50-series), the register layout shifted:
1. `NV_VIRTUAL_FUNCTION_PRIV_BAR1_BLOCK` threw exceptions on non-virtualized Blackwell hardware.
2. The GSP firmware leaves residual state in the physical root page table in VRAM, causing tinygrad's MMU validator to assert that page table entries were non-zero.

**Fix:**  
We patched `tinygrad/runtime/support/nv/ip.py`:
- Wrap BAR1 register writes in `contextlib.suppress(Exception)`.
- Explicitly zero out the physical root page table in VRAM immediately following the GSP init event:

```python
# tinygrad/runtime/support/nv/ip.py
if not self.nvdev.fmc_boot: 
    self.nvdev.NV_PBUS_BAR1_BLOCK.write(mode=0, target=0, ptr=0)
else:
    with contextlib.suppress(Exception): 
        self.nvdev.NV_VIRTUAL_FUNCTION_PRIV_BAR1_BLOCK.write(mode=0, target=0, ptr=0)
    with contextlib.suppress(Exception): 
        self.nvdev.NV_VIRTUAL_FUNCTION_PRIV_FUNC_BAR1_BLOCK_LOW_ADDR.write(mode=0, target=0, ptr=0)
    # Zero physical VRAM root page table after GSP handoff:
    self.nvdev.vram[self.nvdev.mm.root_page_table.paddr : self.nvdev.mm.root_page_table.paddr + 0x1000] = bytes(0x1000)
```

---

### Incident 4: Thunderbolt Bus Resets Drop the PCIe Tunnel

**Symptom:**  
On bare-metal x86 Linux systems, tinygrad can reset the GPU between script invocations by issuing a Secondary Bus Reset (SBR) over the PCIe bridge. In this setup, an SBR was reported to cause the Thunderbolt PCIe controller to report `IOPCIDeviceDeadOnRestore = Yes`, permanently severing the tunnel until a physical cable reconnect.

**Fix:**  
We patched `tinygrad/runtime/support/nv/nvdev.py` to prevent bus resets when operating over DriverKit:
```python
# tinygrad/runtime/support/nv/nvdev.py
if self.reg("NV_PFB_PRI_MMU_WPR2_ADDR_HI").read() != 0 and not isinstance(self.pci_dev, RemotePCIDevice):
    self.pci_dev.reset()
```

**Architecture Implication:**  
The reported second-run failure followed locked WPR2 state and an unusable reset path. That does not establish that every GPU, macOS release and tinygrad revision behaves the same way.

The solution is to **run a single, persistent background daemon** (`tinygrad.llm --serve 8000`) that boots the GSP once and holds the hardware state open across all subsequent queries.

---

### Incident 5: Docker Container Thrashing (`JITBEAM=2`)

**Symptom:**  
Launching the server initially caused macOS to freeze as ~189 simultaneous Docker containers spawned, saturating the host CPU, according to the setup notes. The raw process trace was not retained.

**Root Cause:**  
A debugging script had exported `JITBEAM=2`. In `tinygrad`, beam search attempts to optimize kernel execution time by compiling dozens of parallel assembly permutations inside isolated containerized environments.

**Fix:**  
Unset `JITBEAM` for this reproduction to avoid the reported search explosion. That does not remove the NV compiler prerequisite: tinygrad's macOS NV setup requires Docker Desktop and `extra/setup_nvcc_osx.sh`. Compilation times depend on kernels, cache state and revision; the 1.5-second figure has no raw trace here. [tinygrad setup](https://docs.tinygrad.org/tinygpu/)

---

### Incident 6: GGUF Tokenizer & RoPE Theta KeyErrors

**Symptom:**  
Loading modern GGUF models like Qwen2 or Llama 3 caused crashes:
`KeyError: 'qwen2.rope.freq_base'` or `KeyError: 'tokenizer.ggml.pre'`.

**Fix:**  
The recorded workaround patched `tinygrad/llm/model.py` and `tinygrad/llm/cli.py` with these fallbacks:
```python
# tinygrad/llm/model.py
rope_theta=kv.get(f'{arch}.rope.freq_base', 1000000.0 if 'qwen' in arch else 10000.0)

# tinygrad/llm/cli.py
pre = kv.get("tokenizer.ggml.pre", "qwen2" if "qwen" in kv.get("general.architecture", "") else "llama3")
```

This is a workaround for the recorded checkpoint, not a general model-loading fix.
The defaults apply only when a metadata key is missing; `kv.get` keeps a supplied value.
Do not apply the missing-RoPE fallback unchanged to Llama 3: its reference implementation
uses `rope_theta = 500000`, while the non-Qwen default above is `10000`. Recover missing
RoPE and tokenizer metadata from the specific checkpoint configuration, or reject the
checkpoint; removing a `KeyError` does not prove inference correctness.
[Meta Llama 3 reference](https://github.com/meta-llama/llama3/blob/main/llama/model.py)

---

## 4. The Bridge: Emulating Ollama

`tinygrad.llm` exposes an OpenAI-compatible endpoint on port `8000` (`/v1/chat/completions`). However, tools like Ollama CLI, Open WebUI, and local agent orchestrators expect the native Ollama REST protocol on `/api/tags`, `/api/generate`, `/api/chat`, and `/api/show`.

To make the RTX 5080 eGPU a bridge for selected Ollama operations, we developed [`ollama-egpu-proxy.py`](/downloads/egpu/ollama-egpu-proxy.py), running on port `11440` (avoiding default 11434 and any conflicting local Ollama services).

Key features of the proxy:
- **Streaming & Non-Streaming support**: Seamlessly converts OpenAI Server-Sent Events (SSE) into Ollama newline-delimited JSON chunks (`{"response": "...", "done": false}`).
- **Model Metadata**: Handles `POST /api/show`; inspect whether returned metadata describes the loaded checkpoint. The inspected version included fixed values, so these responses are not independent measurements.
- **Health Checks**: Implements `HEAD /` and `GET /` returning `Ollama is running` for CLI probes.
- **Model Catalog**: Supplies `/api/tags` and `/api/ps` responses for the served model. The inspected values include placeholders; they do not prove active VRAM residency.

The proxy is changing alongside this review. These observations describe the inspected September 30 version. The current proxy also contains an Anthropic Messages text adapter; it strips non-text
content blocks and does not establish agent tool-call support. New endpoint implementations
need separate protocol and inference acceptance checks; a health response alone does not prove tool support, accurate token timings or GPU execution.

---

## 5. Recorded Performance & Evidence Limits

The setup notes report the following results. Raw transport and allocation traces are unavailable, so these are recorded observations rather than independently reproduced benchmarks:

1. **Thunderbolt 5 Link Throughput:**  
   The Razer Core X V2 negotiated a full USB4 v2 / TB5 connection at **80 Gb/s**.  
   Transferring the reported 7.62 GiB Qwen2-14B model weights into RTX 5080 GDDR7 VRAM was reported at **7.0 GB/s** and approximately **1.1 seconds**. The units and timing boundary are not documented well enough to certify a sustained Thunderbolt payload benchmark.

2. **Inference Latency:**  
   Prompt evaluation on Blackwell `sm_120` runs with zero host CPU offload. Generation for 14B Q4 context runs fluidly, completely bypassing macOS unified memory contention.

3. **Memory Footprint:**  
   - The default blob is 8,179,322,304 bytes (about 7.62 GiB on disk).
   - Its calculated 4096-token FP16 KV cache is 3.125 GiB (§6).
   - Weight allocation, compiler scratch space and runtime overhead need measurement; the original 8.8 GB total is inconsistent with this cache estimate.

---

## 6. Context Window Scaling & KV Cache Math

Because the RTX 5080 features 16 GB of physical GDDR7 VRAM, how far can the context window scale before out-of-memory (OOM)?

For the helper's default `Qwen2-beta-14B-Chat` GGUF blob, static metadata inspection gives 40 layers, 40 attention heads, 40 KV heads and embedding width 5120. The head dimension is 128. This is multi-head attention, not the 48-layer/8-KV-head GQA configuration originally assumed. The default blob hash is `de0334402b975e19dd48eb43a13f7534772fb5b4a054447f8f6a861b87ec5799`.

For an FP16 cache with those dimensions:
$$\text{Bytes per token} = 2 \times 40 \times 40 \times 128 \times 2 = 819{,}200\text{ bytes} = 800\text{ KiB}$$

| Context window | Blob size (weight-allocation proxy) | Calculated KV cache | Combined estimate before runtime overhead | Implication on a 16 GB card |
|---|---|---|---|---|
| 4,096 | 7.62 GiB | 3.125 GiB | 10.74 GiB | Plausible; verify actual allocation |
| 8,192 | 7.62 GiB | 6.25 GiB | 13.87 GiB | Tight; measure scratch-space headroom |
| 16,384 | 7.62 GiB | 12.5 GiB | 20.12 GiB | Does not fit this estimate |
| 32,768 | 7.62 GiB | 25 GiB | 32.62 GiB | Does not fit this estimate |

Disk blob size is not an exact GPU allocation measurement. Cache dtype, layout and allocator behavior also matter. A smaller GQA checkpoint can have a much smaller cache; derive the budget from that checkpoint's metadata and supported context, rather than from parameter count alone.

Start the supplied default with a 4096-token context and verify residency before increasing it:
```bash
python3 rtx5080_egpu_harness.py stop
python3 rtx5080_egpu_harness.py serve --context 4096
```

---

## 7. Agent Harnesses & CLI Compatibility

The dual-port architecture exposes both OpenAI and Ollama protocols simultaneously:

### A. ChatGPT CLI & OpenAI SDK (`OPENAI_BASE_URL`)
`tinygrad.llm` on port `8000` is natively OpenAI-compatible (`/v1/chat/completions`). Clients configured for Chat Completions can use that endpoint. This does not imply Responses API or agent-tool compatibility:
```bash
export OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
export OPENAI_API_BASE="http://127.0.0.1:8000/v1"
export OPENAI_API_KEY="dummy"

# Launch ChatGPT interactive CLI connected to RTX 5080
chatgpt
```

### B. Codex and other coding agents
Modern Codex uses the Responses API; a Chat Completions endpoint alone is insufficient. A provider configuration or protocol adapter must support the installed client's API, streaming and tools. Merely setting `OPENAI_BASE_URL` is not an end-to-end compatibility test. [Codex provider configuration](https://developers.openai.com/codex/config-advanced/)

### C. AGY (Antigravity CLI & SDK)
This article has no verified AGY provider configuration or successful tool-call trace for this backend. Do not assume its build honors Ollama/OpenAI environment variables. Consult that client's provider settings and test text, streaming and a real tool cycle before using it for agent work.

### D. Aider CLI
Aider documents both Ollama and OpenAI-compatible provider settings. These commands illustrate routing; the served model still needs an editing/tool-workflow acceptance test. [Aider Ollama settings](https://aider.chat/docs/llms/ollama.html), [OpenAI-compatible settings](https://aider.chat/docs/llms/openai-compat.html)
```bash
# Via Ollama bridge (port 11440):
OLLAMA_HOST=http://127.0.0.1:11440 aider --model ollama/Qwen2-beta-14B-Chat

# Or direct OpenAI backend (port 8000):
aider --openai-api-base http://127.0.0.1:8000/v1 --openai-api-key none --model openai/Qwen2-beta-14B-Chat
```

### E. Claude Code CLI adapter
Claude Code uses Anthropic's Messages protocol. An adapter such as LiteLLM may translate protocols, but the original command did not demonstrate a successful Claude Code tool cycle. Text completion is insufficient: tool schemas, tool results, streaming and prompt size must all work. The default checkpoint's calculated 16k cache does not fit this card, so the original 16k+ recommendation is withdrawn. This integration remains unverified.

---

## 8. Evaluating `/dr` Deep Research on the RTX 5080: Three Workflows Compared

To stress-test the stack in realistic agentic development, we executed the global AI hub's `/dr` (deep-research-to-skill) pipeline on a real frontier concept: **"16 GB VRAM residency budgeting (weights + KV cache)"** across three distinct operational modes:

### Benchmark & Diagnostic Results

| Metric / Dimension | Method 1: Interactive Pipeline | Method 2: Local RTX 5080 eGPU Offload | Method 3: Automated Research Queue |
|---|---|---|---|
| **Driver / Backend** | Host Agent (`dr_run.py`) | Local `tinygrad.llm` (Port 8000, `DEV=NV`) | Queue Daemon (`process-research-queue`) |
| **Prefill Speed** | N/A (Cloud Orchestration) | **34 tokens/sec** | N/A |
| **Generation Throughput** | ~60 tokens/sec | **7.0 tokens/sec** sustained (14B Q4) | Asynchronous batch |
| **Claim Schema Validation** | Passed (`claims: 3, sources: 4`) | Passed (`claims: 2, sources: 3`) | Passed (`tree.json` injected) |
| **Cloud Token Cost** | Standard cloud API | No metered completion API in local path; full workflow cost unmeasured | Cost unmeasured |
| **Tree Integration** | Node created, 1 alias consumed | Claims merged into tree node | Queue marked `[x]` |

### Diagnostic Findings

1. **Schema compliance (limited evidence)**:
   - When given strict JSON schema instructions, the local Qwen2-14B model on the RTX 5080 generated syntactically flawless claims JSON (`weight-quantization-footprints.json`).
   - `dr_run.py concept-done` checks structured submission requirements. The saved manifest records `claim_gate: off`; it does not prove source entailment, factual accuracy or first-attempt success.

2. **Throughput vs. Privacy Trade-Off (Diagnostic)**:
   - **Local Inference Latency**: Generating a 147-token structured claims payload on the RTX 5080 reportedly required 87.31 seconds: about 1.68 output tokens/s over that wall-clock interval. The 7 tokens/s decode figure uses another timing boundary and is not directly comparable. No trace isolates the delay to DriverKit or JIT. Local generation keeps that request on the local path; the research workflow still uses web retrieval and may use cloud orchestration.
   - **Optimization Strategy**: For high-volume research saturation, a smaller model may improve throughput and memory headroom. `Qwen2.5-Coder-7B` is a 7B example, not an 8B model; neither a fourfold speedup nor its maximum context was measured here.

3. **Autonomous Lifecycle**:
   - The combined stack successfully installed a brand-new skill (`~/dev/skills/vram-residency-budgeting/SKILL.md`), registered it in `~/.global-ai-hub/registry.db` (72 entries), and updated the 3D concept tree.

---

## 9. How to Switch Models

The service accepts paths and repository identifiers only for architectures, quantization types and tokenizers supported by the installed tinygrad revision. Fitting the weights in VRAM is necessary but insufficient; include KV cache and runtime headroom. The filenames below are examples to validate, not a promise that every GGUF/Safetensors model works.

### Method A: Use Existing Ollama Model Blobs
Find the blob hash in `~/.ollama/models/manifests`:
```bash
cat ~/.ollama/models/manifests/registry.ollama.ai/library/qwen2.5/14b | grep -A 2 "image.model"
```
Restart the service with the blob:
```bash
pkill -f tinygrad.llm
ollama-egpu ~/.ollama/models/blobs/sha256-<hash>
```

### Method B: Direct Hugging Face ID or Local File
```bash
pkill -f tinygrad.llm
ollama-egpu Qwen/Qwen2.5-7B-Instruct
# or
ollama-egpu ~/models/llama-3.2-3b-instruct-q8_0.gguf
```

---

## 10. Downloadable Scripts & Source Code

All scripts created during this setup are available directly for download:

| Script / Artifact | Description | Direct Download |
|---|---|---|
| `rtx5080_egpu_harness.py` | Partial bootstrap and daemon/benchmark helper; requires DriverKit, NV compiler setup and a compatible checkout | [Download rtx5080_egpu_harness.py](/downloads/egpu/rtx5080_egpu_harness.py) |
| `chatgpt` | Standalone interactive ChatGPT CLI connected to RTX 5080 backend with streaming | [Download chatgpt](/downloads/egpu/chatgpt) |
| `ollama-egpu` | Shell orchestrator: link detection, daemon management, port routing | [Download ollama-egpu](/downloads/egpu/ollama-egpu) |
| `ollama-egpu-proxy.py` | Python Ollama-to-tinygrad REST API bridge (port 11440) | [Download ollama-egpu-proxy.py](/downloads/egpu/ollama-egpu-proxy.py) |
| `tinygpu-blackwell-gsp.patch` | Git patch for `tinygrad` covering Blackwell GSP boot, page tables, and Qwen2 RoPE fixes | [Download tinygpu-blackwell-gsp.patch](/downloads/egpu/tinygpu-blackwell-gsp.patch) |

### Quickstart Option 1: All-In-One Automated Harness

Before using the harness, install and approve TinyGPU, install Docker Desktop, and run tinygrad's NV compiler setup for macOS. See the [upstream procedure](https://docs.tinygrad.org/tinygpu/). Have Python, Git, a supported model blob and a compatible tinygrad revision available.

The [`rtx5080_egpu_harness.py`](/downloads/egpu/rtx5080_egpu_harness.py) helper checks the link, clones tinygrad, attempts the patch, prepares a virtualenv and launches daemons. It does not install all prerequisites or pin an upstream revision. Its patch-failure branch can print a skip message; inspect the patch result and stop on an unexplained mismatch. A fresh-machine end-to-end run has not been verified.

```bash
# 1. Download harness
curl -fsSL -O https://llms-explorer.com/downloads/egpu/rtx5080_egpu_harness.py
chmod +x rtx5080_egpu_harness.py

# 2. Automated bootstrap (hardware probe, tinygrad clone, patch, virtualenv)
python3 rtx5080_egpu_harness.py bootstrap

# 3. Start background daemons (tinygrad.llm on 8000 + Ollama proxy on 11440)
python3 rtx5080_egpu_harness.py serve

# 4. Run test inference or benchmarks directly
python3 rtx5080_egpu_harness.py run "Provide a 2-sentence summary of quantum computing."
python3 rtx5080_egpu_harness.py benchmark --tokens 128

# 5. Stop owned services before disconnecting; panic prevention is not established
python3 rtx5080_egpu_harness.py stop
```

### Quickstart Option 2: Manual Script Installation

This option assumes the same DriverKit/Docker/NVCC prerequisites and a prepared tinygrad
virtualenv. Use a compatible checkout, review the patch before applying it, and put
`~/.local/bin` on `PATH`. The shell helper does not unset `JITBEAM`; unset it before launch.

```bash
# 1. Clone and patch tinygrad
git clone https://github.com/tinygrad/tinygrad.git ~/tinygrad
cd ~/tinygrad
curl -O https://llms-explorer.com/downloads/egpu/tinygpu-blackwell-gsp.patch
git apply tinygpu-blackwell-gsp.patch

# 2. Download helper scripts to ~/.local/bin
mkdir -p ~/.local/bin
curl -o ~/.local/bin/ollama-egpu https://llms-explorer.com/downloads/egpu/ollama-egpu
curl -o ~/.local/bin/ollama-egpu-proxy.py https://llms-explorer.com/downloads/egpu/ollama-egpu-proxy.py
curl -o ~/.local/bin/rtx5080-harness https://llms-explorer.com/downloads/egpu/rtx5080_egpu_harness.py
chmod +x ~/.local/bin/ollama-egpu ~/.local/bin/ollama-egpu-proxy.py ~/.local/bin/rtx5080-harness

# 3. Launch service
unset JITBEAM
ollama-egpu

# 4. Use with Ollama CLI
export OLLAMA_HOST=http://127.0.0.1:11440
ollama list
ollama run Qwen2-beta-14B-Chat
```

---

## Conclusion

External GPUs on Apple Silicon are far from plug-and-play, but they are no longer impossible. By treating DriverKit as a raw PCIe transport and implementing user space hardware initialization, modern NVIDIA GPUs—including the newest Blackwell RTX 5080—can live alongside Apple Silicon, giving Mac developers access to dedicated NVIDIA hardware through tinygrad's NV backend; this does not provide general CUDA application compatibility without giving up the macOS desktop.

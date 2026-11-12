# /sko devops-linux-internals — 2026-11-11

| Iter | High | Medium | Low | Action |
|---|---|---|---|---|
| 1 | 0 | 4 | 1 | applied scoped repairs |
| 2 | 0 | 0 | 1 | author recheck; blind review pending |

Hygiene: final entrypoint byte checks clean; whitespace fixes excluded from severity totals.
Pre-lint: 1 final Low heuristic findings; strict YAML parse passed.

| Pass | Finding | Level | Action taken |
|---|---|---|---|
| F | No repository-owned behavior or trigger evaluation files. (`evals/evals.json and evals/trigger-eval.json (absent at baseline)`) | Medium | Add three realistic cases and derive trigger projection from the scoped replay corpus. |
| P | Missing applicable llms discovery and source-verification guidance. (`SKILL.md: no size-first/source-verification section`) | Medium | Add a size-first lookup section; preserve direct-script operations and raw-capture ordering. |
| A | The referenced CUDA-build spoke is absent from the routing table. (`Routing rule: eGPU overlap, CUDA build/install stack spoke above`) | Medium | State the kernel/driver vs LLM-runtime boundary without naming an absent spoke. |
| N | The routing card has no concrete whenToUse examples. (`SKILL.md frontmatter: whenToUse absent at baseline`) | Medium | Add three realistic one-line user phrasings spanning the owned intents. |

eval: predicted (author frontmatter-only judgments; Claude activation harness unavailable under quota; no installed source hidden).

| Metric | Result | Target | Pass? |
|---|---|---|---|
| should-trigger rate | 10/10 | ≥ 9/10 | yes, predicted |
| false-positive rate | 0/10 | ≤ 1/10 | yes, predicted |

Unified diff preview (source entrypoint; capped at 80 lines):
```diff
--- baseline/SKILL.md
+++ .claude/skills/devops-linux-internals/SKILL.md
@@ -2,11 +2,24 @@
 name: devops-linux-internals
 description: >-
   Linux kernel & OS-internals sub-hub (devops family). TRIGGER: Linux kernel architecture, boot/init, memory & NUMA, storage & filesystems, virtualization/KVM, io_uring async I/O, cgroups v2 & namespaces, sandboxing & confinement, immutable/atomic Linux, Linux privilege model (LSM/SELinux/capabilities); Thunderbolt/USB4 eGPU on Linux ('fallen off the bus'/Xid 79, PCIe hotplug BAR windows, NVIDIA open modules/GSP on Blackwell, bolt/IOMMU, PCIe ASPM/AER/D3cold, eGPU hot-unplug, TB firmware/regression, PCIe link retrain, eGPU power/PSU/thermals, hybrid iGPU+eGPU, TB5/OCuLink topologies, NUC BIOS, eGPU benchmarking, suspend/resume, health monitoring/recovery, idle power, remote recovery, reproducible setup). SKIP: sysadmin/systemd/packaging/shell/host-networking → devops-linux-admin; containers/k8s/CI-CD/IaC → devops-containers-cicd; logging/tracing/metrics/eBPF/perf → devops-observability; LLM serving/runtime/model choice on an eGPU → ai-llm-model-layer; Mac eGPU → mac-egpu-compute.
-version: "1.2.0"
-updated: "2026-09-25"
+version: "1.3.0"
+updated: "2026-11-11"
 origin: local
-model: claude-opus-4-8
+model: claude-opus-5-5
 effort: high
+whenToUse:
+  - "Diagnose an NVIDIA Linux eGPU that reports Xid 79 or fallen off the bus."
+  - "Explain Linux cgroups v2, namespaces and kernel isolation."
+  - "Investigate PCIe BAR allocation or Thunderbolt authorization on Linux."
+related_skills:
+  - "devops-linux-admin"
+  - "devops-containers-cicd"
+  - "devops-observability"
+  - "ai-llm-model-layer"
+  - "mac-egpu-compute"
+category: custom
+metadata:
+  changelog_ref: references/CHANGELOG.md
 ---

 # devops-linux-internals
@@ -14,6 +27,15 @@
 Linux kernel & OS-internals sub-hub (devops family).

 This hub routes to on-demand reference files under `references/`. See each spoke for depth.
+
+## Look for llms files first
+
+Before reading the Linux subsystem or source repository raw, locate its llms files. If the repo is available, step 4 sets the order.
+1. Check the subject's `llms.txt`, its docs site's `/llms.txt`, or matching packs under `~/.global-ai-hub/skills.llms/` and `~/.global-ai-hub/llms-concepts/`; use available hub keyword/search tools as discovery leads.
+2. Run `wc -c` first (or inspect a remote size header). Read a file whole only when it fits; otherwise search it.
+3. Use `llms-facts.txt` and `llms-sitemap.txt` for lookups. Treat `llms-small.txt` as a map, not a fact store.
+4. If you have the repo, search its code before opening llms files. Verify each fact you act on against the authoritative file and line.
+5. Index and llms hits are leads. Confirm them against readable source text before acting.

 ## Sub-skill routing table

@@ -53,7 +75,7 @@

 ## Routing rule: eGPU overlap with ai-llm-model-layer

-Both hubs carry Linux eGPU material. Kernel, PCIe, driver, Thunderbolt/USB4 and boot mechanics (fallen off the bus, BAR/bridge windows, NVIDIA open modules/GSP, bolt/IOMMU, ASPM/AER/D3cold, hot-unplug, firmware hygiene) stay here. LLM-serving, runtime-choice, quantization and model-picking questions for a Linux eGPU go to `ai-llm-model-layer` (its `references/linux-egpu-blackwell-llm.md`). The CUDA build/install stack spoke above is the boundary: build and driver-floor problems here, which model or runtime to run there. The Blackwell sm_120 LLM inference stack (CUDA/driver floors, llama.cpp, Ollama, PyTorch and vLLM matrix, tunnel cost in load time) lives in `ai-llm-model-layer` as `references/blackwell-sm120-llm-inference-stack-linux.md`.
+Both hubs carry Linux eGPU material. Kernel, PCIe, driver, Thunderbolt/USB4 and boot mechanics (fallen off the bus, BAR/bridge windows, NVIDIA open modules/GSP, bolt/IOMMU, ASPM/AER/D3cold, hot-unplug, firmware hygiene) stay here. LLM-serving, runtime-choice, quantization and model-picking questions for a Linux eGPU go to `ai-llm-model-layer` (its `references/linux-egpu-blackwell-llm.md`). Kernel-module build and driver-floor problems stay here; LLM runtime builds, model choice and serving stay in `ai-llm-model-layer`. The Blackwell sm_120 LLM inference stack (CUDA/driver floors, llama.cpp, Ollama, PyTorch and vLLM matrix, tunnel cost in load time) lives in `ai-llm-model-layer` as `references/blackwell-sm120-llm-inference-stack-linux.md`.

 <!-- cross-hub-map -->
 ## Cross-hub map — where every devops topic lives
```

```diff
--- baseline/evals/evals.json
+++ .claude/skills/devops-linux-internals/evals/evals.json
@@ -0,0 +1,118 @@
+{
+  "skill_name": "devops-linux-internals",
+  "schema_version": "1.0",
+  "evaluation_scope": "Static instruction-contract checks for realistic functional scenarios. Output behavior and side effects require an isolated execution follow-up; none are claimed here.",
+  "evals": [
+    {
+      "id": 1,
+      "name": "bus-failure",
+      "prompt": "The Linux Thunderbolt NVIDIA GPU reports Xid 79. Explain the next evidence to gather; make no device changes.",
+      "expected_output": "Read the fallen-off-bus reference; keep kernel/PCIe diagnostics distinct from LLM serving choices.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "right-spoke",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/linux-nvidia-egpu-fallen-off-bus-diagnosis.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "runtime-deferral",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "LLM runtime builds, model choice and serving stay in",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
+      ]
+    },
+    {
+      "id": 2,
+      "name": "kernel-isolation",
+      "prompt": "Compare Linux namespaces, cgroups v2 and seccomp for this workload.",
+      "expected_output": "Read the resource/isolation and confinement references before synthesizing the comparison.",
+      "files": [],
+      "assertions": [
+        {
+          "name": "cgroups",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/linux-cgroups-namespaces.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        },
+        {
+          "name": "confinement",
+          "type": "deterministic",
+          "check": "The final instruction file contains the scenario policy named by this assertion.",
+          "static_check": {
+            "path": "SKILL.md",
+            "regex": "references/linux-sandboxing-confinement.md",
+            "flags": [
+              "IGNORECASE",
+              "DOTALL"
+            ],
+            "scope": "instruction-contract"
+          }
+        }
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/evals/trigger-eval.json
+++ .claude/skills/devops-linux-internals/evals/trigger-eval.json
@@ -0,0 +1,82 @@
+[
+  {
+    "query": "My Linux NVIDIA eGPU reports Xid 79 and fallen off the bus; explain the diagnostic path.",
+    "should_trigger": true
+  },
+  {
+    "query": "Why does the Thunderbolt GPU have an unusable PCIe BAR?",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain cgroups v2 and namespaces for process isolation.",
+    "should_trigger": true
+  },
+  {
+    "query": "How does Linux reclaim memory on a NUMA system?",
+    "should_trigger": true
+  },
+  {
+    "query": "Compare ext4 and XFS writeback and durability semantics.",
+    "should_trigger": true
+  },
+  {
+    "query": "Walk me through Linux kernel scheduling and EEVDF.",
+    "should_trigger": true
+  },
+  {
+    "query": "How do seccomp and Landlock constrain an untrusted process?",
+    "should_trigger": true
+  },
+  {
+    "query": "Explain io_uring submission and completion rings.",
+    "should_trigger": true
+  },
+  {
+    "query": "What happens to a headless Thunderbolt eGPU across suspend and resume?",
+    "should_trigger": true
+  },
+  {
+    "query": "Diagnose early-boot Thunderbolt authorization and NVIDIA driver loading.",
+    "should_trigger": true
+  },
+  {
+    "query": "Write a systemd unit for my ordinary web server.",
+    "should_trigger": false
+  },
+  {
+    "query": "Configure Kubernetes service networking.",
+    "should_trigger": false
+  },
+  {
+    "query": "Pick an LLM and quantization for my Linux eGPU.",
+    "should_trigger": false
+  },
+  {
+    "query": "Build a Grafana dashboard for application traces.",
+    "should_trigger": false
+  },
+  {
+    "query": "Set up an Apple Silicon external GPU.",
+    "should_trigger": false
+  },
+  {
+    "query": "Write a bash script that rotates logs.",
+    "should_trigger": false
+  },
+  {
+    "query": "Build a GitHub Actions deployment pipeline.",
+    "should_trigger": false
+  },
+  {
+    "query": "Tune a MongoDB compound index.",
+    "should_trigger": false
+  },
+  {
+    "query": "Design a React settings page.",
+    "should_trigger": false
+  },
... diff truncated at 80 lines; complete bytes bound by SHA-256 in JSON.
```

```diff
--- baseline/references/CHANGELOG.md
+++ .claude/skills/devops-linux-internals/references/CHANGELOG.md
@@ -0,0 +1,3 @@
+# Changelog
+
+2026-11-11 sko v1.2.0->v1.3.0 — Pass H predicted 10/10->10/10 pos, 0/10->0/10 false positives; 4 Medium findings fixed in reviewed scope; global sync and blind review deferred.
```

| Eval | Result | Level | Files present? |
|---|---|---|---|
| trigger | pos 10/10; false-positive 0/10 | predicted | trigger-eval.json yes |
| behavior | 6/6 instruction assertions; 3/3 cases | static, instruction-contract only | evals.json yes |

No functional scenario output was generated. Static policy presence does not prove runtime behavior.

index-discovery: degraded (local keyword referrers 1; paused semantic services; no ranking scores inferred).

| Location | Kind | Before-hash | Action | After-hash |
|---|---|---|---|---|
| .claude/skills/devops-linux-internals/SKILL.md | canonical (explicit repository target) | 34fd209c624d | audited and changed in isolated worktree | 597c7503c9e2 |
| $HOME/.claude/skills/devops-linux-internals/SKILL.md | installed copy | 5ba11290d911 | report only; preserve divergence; root-coordinated ownership review | 5ba11290d911 |
| $HOME/.global-ai-hub/skills/devops-linux-internals/SKILL.md | installed copy | 5ba11290d911 | report only; preserve divergence; root-coordinated ownership review | 5ba11290d911 |

llms-first: added; size-first and source-verification checks retained.

| Skill | Verdict | Indexed description matches file? | Surfaces for own intent? | Surplus stale rows |
|---|---|---|---|---|
| devops-linux-internals | unverified/deferred (--no-sync) | no exact unprefixed row match; payload format not assumed | not run; paused | not inferred |

prose-index: operator paused; worker did not start it.
index: root-coordinated; worker made no generated-index writes.
degraded: semantic discovery, global routing/parity and fresh blind gate remain unverified; exit DEGRADED.
model: claude-opus-5-5 · effort: high (tier: flagship; heuristic). ID source: live models overview receipt; effort source: current effort documentation.

Snapshot & rollback: `cp "$PRIVATE_WORKER_STATE/devops-linux-internals/baseline/SKILL.md" ".claude/skills/devops-linux-internals/SKILL.md"`. Private preimages include every baseline target file.
Telemetry: per-pass rows retained in private worker state; no shared ledger modified.

4 Medium findings addressed across 2 author iterations (profile: standard); registry rebuild skipped --no-sync; routing unverified; exit DEGRADED pending independent/global gates.

Modified sections: frontmatter routing/model/version metadata; Look for llms files first.

A-P dispositions:

| Pass | Disposition |
|---|---|
| A | Reviewed entrypoint correctness and operative supporting files; fixed anchored contradictions/broken pointers. Large unchanged reference facts are not independently revalidated. |
| B | Reviewed claimed scope, stage ordering and output promises; preserved research evidence/budget/STOP boundaries. |
| C | Strict YAML parsed with duplicate-key rejection; checked target-local introduced links and hub table file existence. |
| D | Reviewed procedural clarity and concrete examples; retained domain terms and source-qualified claims. |
| E | Applied only scoped routing/progressive-disclosure repairs; retained author workflow and purpose. |
| F | Created three realistic functional scenario cases; static instruction-contract checks ran at 6/6. Scenario outputs were not executed. |
| G | Manifest parsed, version/date updated, advisory model provenance recorded; no claim that prior model IDs are invalid. |
| H | 20-query corpus replay/generated first, projection derived afterward; author predictions 10/10 positive, 0/10 false positives. No measured activation. |
| I | Local keyword/referrer discovery and explicit peer boundaries reviewed. Global semantic ranking/collision rates remain unverified because services are paused. |
| J | Description 992 characters; body estimate 2520 tokens. Within budgets. |
| K | No exact banned terms outside code; retained Low stylistic/domain-density heuristics where no behavioral defect is anchored. |
| L | Deterministic entrypoint whitespace/control-character checks passed; git diff --check passed for owned paths. Unchanged source reference bodies were preserved. |
| M | Description states capability and carries TRIGGER/SKIP; trigger surface narrowed where anchored collisions or buried triggers existed. |
| N | Concrete whenToUse examples and named resolvable peer routes checked against local files/manifests. No new dangling target-local routes. |
| O | No peer writes: other owners are active; missing reciprocal edges and installed-wrapper drift are handed to root. Existing target-side deferrals retained. |
| P | Added size-first llms discovery with source verification and repo-code authority. |

Read coverage: Read completely across full output plus targeted continuation spans; final changed spans re-read. Strict parser/lint also re-read final bytes.
Supporting files read in full: none; entrypoint routes/existence checked.
Unread supporting files: references/asus-nuc15-pro-firmware-for-thunderbolt-egpu-linux.md, references/egpu-health-monitoring-and-automated-recovery-linux.md, references/egpu-hot-unplug-pciehp-safety-linux.md, references/egpu-idle-power-and-energy-accounting-linux.md, references/egpu-power-enclosure-and-thermals-linux.md, references/egpu-reproducible-bringup-and-drift-detection-linux.md, references/egpu-suspend-resume-and-sleep-states-linux.md, references/egpu-unattended-remote-recovery-and-out-of-band-linux.md, references/hybrid-graphics-igpu-plus-nvidia-egpu-headless-linux.md, references/immutable-atomic-linux.md, references/io-uring-async-io.md, references/linux-boot-init.md, references/linux-cgroups-namespaces.md, references/linux-egpu-hotplug-boot-orchestration.md, references/linux-kernel-architecture.md, references/linux-mac-privilege.md, references/linux-memory-numa.md, references/linux-nvidia-egpu-fallen-off-bus-diagnosis.md, references/linux-pcie-hotplug-bar-allocation.md, references/linux-sandboxing-confinement.md, references/linux-storage-filesystems.md, references/linux-virtualization.md, references/measuring-a-thunderbolt-egpu-bandwidth-and-inference-linux.md, references/nvidia-gsp-fsp-boot-diagnostics-blackwell-linux.md, references/nvidia-open-kernel-modules-blackwell-linux.md, references/pcie-link-training-speed-width-thunderbolt-egpu-linux.md, references/pcie-power-management-aer-dpc-egpu-linux.md, references/thunderbolt-boot-authorization-and-nvidia-cdi-linux.md, references/thunderbolt-firmware-and-kernel-regression-hygiene-linux.md, references/thunderbolt-usb4-pcie-tunnel-bolt-iommu-linux.md, references/thunderbolt5-barlow-ridge-and-oculink-egpu-topologies-linux.md.

Static regression checks:

| Check | Baseline | Final | Level |
|---|---|---|---|
| absent-build-spoke-removed | false | true | static instruction check |

<details><summary>Trigger queries (predicted)</summary>

| Query | Expected | Predicted | Pass? |
|---|---|---|---|
| My Linux NVIDIA eGPU reports Xid 79 and fallen off the bus; explain the diagnostic path. | trigger | trigger | true |
| Why does the Thunderbolt GPU have an unusable PCIe BAR? | trigger | trigger | true |
| Explain cgroups v2 and namespaces for process isolation. | trigger | trigger | true |
| How does Linux reclaim memory on a NUMA system? | trigger | trigger | true |
| Compare ext4 and XFS writeback and durability semantics. | trigger | trigger | true |
| Walk me through Linux kernel scheduling and EEVDF. | trigger | trigger | true |
| How do seccomp and Landlock constrain an untrusted process? | trigger | trigger | true |
| Explain io_uring submission and completion rings. | trigger | trigger | true |
| What happens to a headless Thunderbolt eGPU across suspend and resume? | trigger | trigger | true |
| Diagnose early-boot Thunderbolt authorization and NVIDIA driver loading. | trigger | trigger | true |
| Write a systemd unit for my ordinary web server. | skip | skip | true |
| Configure Kubernetes service networking. | skip | skip | true |
| Pick an LLM and quantization for my Linux eGPU. | skip | skip | true |
| Build a Grafana dashboard for application traces. | skip | skip | true |
| Set up an Apple Silicon external GPU. | skip | skip | true |
| Write a bash script that rotates logs. | skip | skip | true |
| Build a GitHub Actions deployment pipeline. | skip | skip | true |
| Tune a MongoDB compound index. | skip | skip | true |
| Design a React settings page. | skip | skip | true |
| Compare vLLM and Ollama serving throughput on this eGPU. | skip | skip | true |

</details>

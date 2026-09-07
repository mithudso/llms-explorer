# AI Red-Teaming & Security-Testing Tooling for LLM Apps (2024-2026): Research Report
*Generated: 2026-05-31 | Sources: 28 | Overall confidence: High*

## Overview

AI red-teaming is the **offensive testing discipline** for LLM and generative-AI applications: systematically generating adversarial inputs to find where a model or app *fails in ways we don't want* (jailbreaks, prompt injection, data/system-prompt exfiltration, harmful-content generation, insecure tool use), then feeding those findings back into fixes and regression tests. It is distinct from runtime guardrails/defense (input/output filters, dual-LLM/CaMeL), which are the *defensive* counterpart and are covered by the existing `agent-reliability-guardrails` reference — this report focuses on the **testing tooling and methodology** and cross-references the defensive layer where relevant.

By 2025-2026 the field has matured from ad-hoc manual probing into a tooled discipline with: (1) open-source scanners and frameworks (Garak, PyRIT, promptfoo, Giskard, Purple Llama); (2) standardized benchmarks (HarmBench, JailbreakBench, AdvBench, AgentDojo); (3) automated attack-generation algorithms (GCG, PAIR, TAP, Crescendo, many-shot); (4) commercial continuous red-teaming platforms (Lakera/Cisco, Mindgard, HiddenLayer, Robust Intelligence/Cisco AI Defense); and (5) governance/process frameworks (OWASP LLM Top 10 2025, OWASP GenAI Red Teaming Guide, MITRE ATLAS, NIST AI RMF). The dominant consensus lesson is that **automation augments but does not replace human red-teamers**, and that **red-teaming must be continuous, not one-off** ([Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2025/01/13/3-takeaways-from-red-teaming-100-generative-ai-products/); [Mend.io](https://www.mend.io/blog/llm-red-teaming-threats-testing-best-practices/)).

---

## 1. AI Red-Teaming as a Discipline (offensive testing) — *Confidence: High*

- **Definition & posture.** Red-teaming starts by defining a **threat model**: a description of the AI system, the relevant vulnerabilities, and the contexts in which they arise, including human interactions ([CSET Georgetown](https://cset.georgetown.edu/article/ai-red-teaming-design-threat-models-and-tools/)). It is offensive *testing*, distinct from blue-team runtime defenses.
- **Manual vs automated.** Automated tools (PyRIT, Garak, commercial platforms) excel at systematic coverage and regression testing but **cannot match human creativity** in discovering novel attacks; manual expert testing remains essential ([Mend.io](https://www.mend.io/blog/llm-red-teaming-threats-testing-best-practices/); [Vectra](https://www.vectra.ai/topics/ai-red-teaming)). Microsoft's own framing: PyRIT "is not a replacement for manual red teaming... it augments an AI red teamer's existing domain expertise and automates the tedious tasks" ([Microsoft Security Blog, 2024](https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/)).
- **Continuous red-teaming.** The 2025-2026 shift is toward **continuous adversarial testing** run regularly in staging or production monitoring, rather than periodic one-shot engagements ([Ajith Prabhakar playbook](https://ajithp.com/2025/07/13/red-teaming-large-language-models-playbook/); [Mindgard](https://mindgard.ai/blog/what-is-ai-red-teaming)). Regression testing after fixes is treated as mandatory, not optional ([Mend.io](https://www.mend.io/blog/llm-red-teaming-threats-testing-best-practices/)).
- **Microsoft's lessons from 100 products.** Eight key lessons include: start from **downstream impact** rather than attack mechanics; **prompt engineering often outperforms gradient-based attacks** in practice; and red-teaming **cannot be replaced by safety benchmarks**. Their AIRT ontology models a finding as: an *Actor* conducts an *Attack* leveraging *TTPs* to exploit a *Weakness* in a *System*, creating an *Impact* ([Lessons From Red Teaming 100 Generative AI Products, arXiv 2501.07238](https://arxiv.org/pdf/2501.07238); [Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2025/01/13/3-takeaways-from-red-teaming-100-generative-ai-products/)).

---

## 2. Tooling Landscape: Scanners vs Frameworks — *Confidence: High*

The landscape splits into **scanners** (run a fixed/curated battery of probes, give a vulnerability report) and **frameworks** (composable building blocks you script your own attacks with). The major open-source tools:

| Tool | Type | What it does | License/Owner |
|---|---|---|---|
| **Garak** | Scanner | LLM vulnerability scanner — "Nessus for LLMs" | Apache 2.0 / NVIDIA |
| **PyRIT** | Framework | Composable orchestration toolkit for adaptive attacks | MIT / Microsoft |
| **promptfoo** | Scanner + eval framework | Eval + red-team CLI/library with CI/CD | Open source / promptfoo |
| **Giskard** | Scanner | LLM/RAG scan for vulns + quality issues | Apache 2.0 / Giskard |
| **Purple Llama** | Models + benchmarks | Llama Guard, Prompt Guard, CyberSecEval | Meta |

### Garak (NVIDIA) — *the leading open-source LLM vulnerability scanner*
- Name = "**Generative AI Red-teaming & Assessment Kit**." Developed Spring 2023 by Prof. Leon Derczynski; homed at NVIDIA as an open-source project with long-term support since Nov 2024 ([Wikipedia](https://en.wikipedia.org/wiki/Garak_(software)); [GitHub](https://github.com/NVIDIA/garak)).
- **Five-component plugin architecture**: *Probes* (generate adversarial interactions), *Detectors* (identify failure modes in responses), *Generators* (interface to model platforms — OpenAI, HuggingFace, Bedrock, etc.), *Harnesses* (orchestrate the workflow; default `probewise`), and *Evaluators* (produce findings reports) ([Garak README](https://raw.githubusercontent.com/NVIDIA/garak/main/README.md)).
- **20+ probe modules** covering prompt injection (encoding-based, structural), DAN-family jailbreaks, encoding/Base64 guardrail bypass, data leakage, package/dependency hallucination, toxicity, malware generation, XSS via LLM output, and glitch tokens. Notable modules: `encoding`, `dan`, `promptinject`, `malwaregen`, `realtoxicityprompts` ([Garak README](https://raw.githubusercontent.com/NVIDIA/garak/main/README.md); [Databricks blog](https://www.databricks.com/blog/ai-security-action-applying-nvidias-garak-llms-databricks)).
- **CLI-driven**: `garak --target_type openai --target_name <model> --probes encoding`. License **Apache 2.0** ([Garak README](https://raw.githubusercontent.com/NVIDIA/garak/main/README.md)).

### Microsoft PyRIT — *automation framework, "Metasploit for LLMs"*
- **PyRIT = Python Risk Identification Toolkit.** Released Feb 2024 ([Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/); [The Hacker News](https://thehackernews.com/2024/02/microsoft-releases-pyrit-red-teaming.html)).
- **Four core components**: *Targets* (the AI under test), *Converters* (transform/obfuscate prompts before sending), *Scorers* (evaluate whether responses are harmful), *Orchestrators* (manage multi-turn conversation flow). It is **adaptive** — it changes tactics based on the system's response and generates the next input until the goal is reached ([Medium deep dive](https://medium.com/@xsankalp13/automating-ai-red-teaming-with-microsoft-pyrit-a-deep-dive-ce18d0bd8d44); [ToxSec](https://www.toxsec.com/p/pyrit-ai-red-teaming)).
- In one Copilot exercise, Microsoft generated several thousand malicious prompts and scored outputs "**in hours instead of weeks**." Now integrated into **Azure AI Foundry's AI Red Teaming Agent** ([Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/); [Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent)).

### promptfoo — *eval + red-team, CI-native*
- CLI/library for evaluating and red-teaming LLM apps, **runs 100% locally**; used by OpenAI and Anthropic and 156 of the Fortune 500 ([GitHub](https://github.com/promptfoo/promptfoo); [Promptfoo docs](https://www.promptfoo.dev/docs/red-team/)).
- Built-in vulnerability scanner covering **50+ vulnerability types** and OWASP LLM Top 10, with presets aligned to **NIST AI RMF, OWASP LLM Top 10, and MITRE ATLAS** ([Promptfoo MITRE ATLAS](https://www.promptfoo.dev/docs/red-team/mitre-atlas/); [Promptfoo config](https://www.promptfoo.dev/docs/red-team/configuration/)).
- **CI/CD integration**: can automatically fail builds if AI components regress or become vulnerable — the canonical "red-team-in-CI" pattern ([Promptfoo CI/CD](https://www.promptfoo.dev/docs/integrations/ci-cd/)).

### Giskard — *open-source scan for security + quality*
- Apache-2.0 Python library that auto-detects security vulns (prompt injection, data leakage) **and** quality issues (hallucination, bias, sycophancy) in LLMs, RAG systems, and classic ML ([Giskard docs](https://docs.giskard.ai/en/latest/knowledge/llm_vulnerabilities/index.html); [Giskard site](https://www.giskard.ai/)).
- Uses a mixture of predefined examples, heuristics, and **LLM-assisted detectors (GPT-4-based)**; notable for **sycophancy testing** to surface hallucination without ground truth ([Giskard docs](https://docs.giskard.ai/en/latest/reference/scan/llm_detectors.html); [HuggingFace blog](https://huggingface.co/blog/JMJM/giskard-llm-testing-and-debugging-hf)).

### Meta Purple Llama — *guardrail models + the offensive benchmark*
- A toolset spanning **Llama Guard** (input/output content moderation classifier), **Prompt Guard** (mDeBERTa-based classifier for jailbreaks + indirect injection), and **CyberSecEval** ([GitHub](https://github.com/meta-llama/PurpleLlama); [Meta Prompt Guard overview](https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/prompt_guard/overview)).
- *For the testing angle*, **CyberSecEval** is the key piece: a benchmark of an LLM's propensity to (a) generate insecure code and (b) comply with cyberattack assistance. **CyberSecEval 3** added visual prompt-injection tests, spear-phishing capability tests, and autonomous offensive cyber-operations tests ([CyberSecEval paper, arXiv 2312.04724](https://arxiv.org/html/2312.04724v1); [Meta AI research](https://ai.meta.com/research/publications/purple-llama-cyberseceval-a-benchmark-for-evaluating-the-cybersecurity-risks-of-large-language-models/)). (Llama Guard / Prompt Guard themselves are *defensive* — cross-reference `agent-reliability-guardrails`.)

---

## 3. Attack Taxonomy — *Confidence: High*

- **Direct vs indirect prompt injection.** *Direct* injection (often conflated with jailbreaking) is when a user's input overrides/reveals the system prompt. *Indirect* injection smuggles malicious instructions via untrusted content the model ingests (RAG docs, web pages, files, tool outputs) — here the **attacker is not the user** but a third party poisoning the data channel ([OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/); [Greshake et al., arXiv 2302.12173 — the foundational indirect-injection paper](https://arxiv.org/abs/2302.12173); [CrowdStrike](https://www.crowdstrike.com/en-us/cybersecurity-101/cyberattacks/prompt-injection/)).
- **Jailbreak families.** Documented families include **DAN ("Do Anything Now")** roleplay/dual-persona, generic roleplay/persona-escalation and "admin" status, **payload splitting**, **obfuscation/encoding** (Base64, multilingual injection, hiding in code comments), and **multi-turn gradual escalation** ([ToxSec DAN](https://www.toxsec.com/p/dan-prompts-for-guardrail-bypass); [OnSecurity](https://onsecurity.io/article/llm-jailbreaks-explained-how-to-test-different-attacks/); [Astra guide](https://www.getastra.com/blog/ai-security/prompt-injection-attacks/)).
- **Many-shot jailbreaking (Anthropic, 2024).** Prompt the model with hundreds-to-thousands of in-context examples of undesirable behavior, then ask the harmful question; effectiveness follows a **power law** with shot count and is newly feasible due to long context windows ([Anthropic Many-Shot paper PDF](https://www-cdn.anthropic.com/af5633c94ed2beb282f6a53c595eb437e8e7b630/Many_Shot_Jailbreaking__2024_04_02_0936.pdf); [Prompt Security explainer](https://prompt.security/blog/many-shot-jailbreaking-a-new-llm-vulnerability)).
- **Crescendo (multi-turn).** A seemingly benign multi-turn attack that exploits the model's tendency to follow patterns and focus on its own recent output; reaches up to **100% ASR** on many tasks and beats prior SOTA by 29-71% on AdvBench subsets ([Crescendo paper, arXiv 2404.01833](https://arxiv.org/abs/2404.01833); [Crescendo site](https://crescendo-the-multiturn-jailbreak.github.io/)).
- **Data / system-prompt exfiltration.** A successful injection in a tool-enabled app can exfiltrate data directly via tools (e.g., writing to a public GitHub repo, DNS exfil, markdown-image rendering) — this is **LLM02 Sensitive Information Disclosure** and **LLM07 System Prompt Leakage** in OWASP 2025 ([CrowdStrike indirect-injection blog](https://www.crowdstrike.com/en-us/blog/indirect-prompt-injection-attacks-hidden-ai-risks/); [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).
- **The lethal trifecta (cross-ref to guardrails).** Simon Willison's June 2025 framing: an agent is structurally insecure when it combines **(1) access to private data, (2) exposure to untrusted content, and (3) the ability to communicate externally** — a single poisoned input can then exfiltrate data with no traditional code vuln. As a *testing* target this maps directly to indirect-injection + tool-poisoning test cases; the *defensive* mitigation is covered by `agent-reliability-guardrails` ([Simon Willison](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/); [Promptfoo lethal-trifecta testing](https://www.promptfoo.dev/blog/lethal-trifecta-testing/); [HiddenLayer](https://www.hiddenlayer.com/research/the-lethal-trifecta-and-how-to-defend/)).

---

## 4. Automated Attack Generation — *Confidence: High*

- **GCG (Greedy Coordinate Gradient).** Token-level, *white-box* — optimizes an adversarial suffix via greedy coordinate gradient descent to force affirmative ("Sure, here is…") outputs. High success but **orders of magnitude more queries** than search-based methods; suffixes can transfer across models ([Tree of Attacks paper comparison, arXiv 2312.02119](https://arxiv.org/html/2312.02119v3); [EmergentMind GCG+PAIR](https://www.emergentmind.com/topics/gcg-pair)).
- **PAIR (Prompt Automatic Iterative Refinement).** Uses an **attacker LLM** steered by meta-prompts to iteratively refine semantically coherent adversarial prompts — *black-box*, query-efficient ([TAP paper](https://arxiv.org/html/2312.02119v3)).
- **TAP (Tree of Attacks with Pruning).** Black-box; an attacker LLM **iteratively refines a tree of candidate prompts with pruning**. Against GPT-4o it finds jailbreaks for **16% more prompts than PAIR with 60% fewer queries**. This is the algorithm Robust Intelligence/Cisco productized for algorithmic red-teaming ([TAP paper, arXiv 2312.02119](https://arxiv.org/pdf/2312.02119); [Cisco/Robust Intelligence](https://www.cisco.com/site/us/en/products/security/ai-defense/robust-intelligence-is-part-of-cisco/index.html)).
- **Red-teamer LLMs & fuzzing.** The common modern pattern is an **attacker/red-teamer LLM** that generates, mutates, and scores attacks in a loop — the core of PyRIT orchestrators, TAP, PAIR, and Crescendo automation ("Crescendomation"). Hybrid **GCG+PAIR** combines gradient suffixes with semantic refinement for up to **+33pp ASR** over single-strategy ([EmergentMind](https://www.emergentmind.com/topics/gcg-pair); [Crescendo paper](https://arxiv.org/abs/2404.01833)).

---

## 5. Benchmarks & Datasets — *Confidence: High*

- **AdvBench** (Zou et al., 2023) — the original harmful-behaviors/harmful-strings dataset introduced with GCG; now a component of later benchmarks ([JailbreakBench paper, arXiv 2404.01318](https://arxiv.org/pdf/2404.01318)).
- **HarmBench** (Center for AI Safety, 2024) — standardized evaluation framework for **automated red-teaming and robust refusal**, broader topic coverage including copyright and multimodal ([JailbreakBench paper](https://arxiv.org/pdf/2404.01318)).
- **JailbreakBench** (NeurIPS 2024) — open robustness benchmark: 100 harmful + 100 benign behaviors across 10 categories aligned to OpenAI usage policies, a **validated jailbreak classifier**, an artifact repository, and a **public leaderboard** for attacks and defenses ([JailbreakBench GitHub](https://github.com/JailbreakBench/jailbreakbench); [paper, arXiv 2404.01318](https://arxiv.org/pdf/2404.01318)).
- **AgentDojo** (2024) — the key benchmark for **tool-use / agent injection**: a dynamic environment with **97 realistic tasks and 629 security test cases** across banking, Slack, travel, and workspace domains; metrics are benign utility, utility-under-attack, and attack success rate. Used by US/UK AISI to demonstrate Claude 3.5 Sonnet's injection vulnerability ([AgentDojo paper, arXiv 2406.13352](https://arxiv.org/html/2406.13352v3); [AgentDojo site](https://agentdojo.spylab.ai/)).
- **OWASP LLM Top 10 (2025) as a testing checklist.** Functions as a structured 10-category test plan for any production LLM deployment ([Mend.io 2025 guide](https://www.mend.io/blog/2025-owasp-top-10-for-llm-applications-a-quick-guide/)): **LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data & Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector & Embedding Weaknesses, LLM09 Misinformation, LLM10 Unbounded Consumption** ([OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/); [Oligo](https://www.oligo.security/academy/owasp-top-10-llm-updated-2025-examples-and-mitigation-strategies)).

---

## 6. AI Firewalls / Runtime-Defense Products from the Testing Angle — *Confidence: High*

These are defensive products, but each ships a **red-team/testing** capability or dataset relevant to offensive testing:

- **Lakera — Gandalf & Lakera Red.** *Gandalf* is a gamified prompt-injection challenge (extract a secret password through 7-8 escalating defense levels); it has drawn **1M+ players and 80M+ adversarial prompts** that feed Lakera's threat intel. **Lakera Red** runs automated attack simulations against LLM apps pre-production. Lakera (incl. Guard, Red, Gandalf dataset) was **acquired by Cisco in 2025** ([Lakera "Who is Gandalf"](https://www.lakera.ai/blog/who-is-gandalf); [Lakera prompt-injection guide](https://www.lakera.ai/blog/guide-to-prompt-injection)).
- **Robust Intelligence → Cisco AI Defense.** Robust Intelligence (Harvard spinout, founded 2019) built what it calls the **first algorithmic red-teaming solution**, using **TAP** to jailbreak LLMs in seconds rather than weeks of human effort. Acquired by Cisco Oct 2024; now powers **Cisco AI Defense "AI Validation"** ([Cisco](https://www.cisco.com/site/us/en/products/security/ai-defense/robust-intelligence-is-part-of-cisco/index.html); [Cisco blog](https://blogs.cisco.com/ai/robust-intelligence-now-part-of-cisco-recognized-as-a-2024-gartner-cool-vendor-for-ai-security)).
- **Mindgard.** Automated AI red-teaming / **DAST-AI** platform for LLMs, agents, multimodal; Lancaster University spinout (2022), recognized in the OWASP GenAI Security Solutions Landscape; emphasizes **continuous** red-teaming ([Mindgard](https://mindgard.ai/automated-ai-red-teaming); [Mindgard/S&P Global](https://mindgard.ai/resources/analyst-report-s-p-global-market-intelligence)).
- **HiddenLayer & Prompt Guard.** HiddenLayer's AISec platform focuses on ML model protection and threat intel; Meta's **Prompt Guard** classifier is the open-source guardrail you *test against* ([Mend.io top-6 services](https://www.mend.io/blog/best-ai-red-teaming-services-top-6-services/); [Meta Prompt Guard](https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/prompt_guard/overview)).

---

## 7. Process: Scoping, CI, Reporting, and Framework Mapping — *Confidence: High*

- **OWASP GenAI Red Teaming Guide (Jan 2025)** structures red-teaming into **four phases**: (1) **model evaluation** (provenance, data pipelines), (2) **implementation testing** (guardrails in place), (3) **infrastructure/system assessment** (deployed exploitable components), and (4) **runtime behavior analysis** (business processes and multi-component interactions in production) ([OWASP GenAI Red Teaming Guide](https://genai.owasp.org/resource/genai-red-teaming-guide/); [ResilientCyber walkthrough](https://www.resilientcyber.io/p/implementing-genai-red-teaming-the); [CSO Online](https://www.csoonline.com/article/3844225/how-owasps-guide-to-generative-ai-red-teaming-can-help-teams-build-a-proactive-approach.html)).
- **Three governance frameworks, three lifecycle phases.** The standard mapping: **OWASP LLM Top 10** for the development/secure-coding phase, **MITRE ATLAS** for operations/threat-modeling/detection, **NIST AI RMF** (Govern/Map/Measure/Manage) for governance/compliance — they **complement, not compete** ([Straiker](https://www.straiker.ai/blog/comparing-ai-security-frameworks-owasp-csa-nist-and-mitre); [Medium — Elias Silva](https://medium.com/@esilvalabh/security-architecture-for-a-genai-tool-implementation-applying-the-nist-ai-rmf-map-measure-39617e189ffe)).
- **MITRE ATLAS scale.** As of the **Nov 2025 v5.1.0** update: **16 tactics, 84 techniques, 32 mitigations, 42 case studies**, with continued additions of agentic-AI techniques into 2026 ([Vectra](https://www.vectra.ai/topics/mitre-atlas); [Repello](https://repello.ai/blog/mitre-atlas-framework)). OWASP published a first-ever **Red Teaming Landscape** in 2026 alongside separate LLM/GenAI and agentic-AI landscapes ([Straiker](https://www.straiker.ai/blog/comparing-ai-security-frameworks-owasp-csa-nist-and-mitre)).
- **Red-team in CI + reporting.** promptfoo is the reference implementation: run the red-team suite in CI/CD and **fail the build** on regression, with reports mapped to OWASP/NIST/ATLAS ([Promptfoo CI/CD](https://www.promptfoo.dev/docs/integrations/ci-cd/)). Best-practice reporting documents every scenario with **goals, prompts, model versions, and observed behaviors** as reproducible test cases ([Ajith Prabhakar playbook](https://ajithp.com/2025/07/13/red-teaming-large-language-models-playbook/)).

---

## 8. Anti-Patterns — *Confidence: High*

- **One-off red-teaming.** Treating red-teaming as a single pre-launch event; models, prompts, and threat landscape drift, so testing must be **continuous** ([Mindgard](https://mindgard.ai/blog/what-is-ai-red-teaming); [Mend.io](https://www.mend.io/blog/llm-red-teaming-threats-testing-best-practices/)).
- **Testing only direct injection.** Ignoring **indirect injection / tool-poisoning** (RAG docs, web content, tool outputs) — the highest-impact agentic attack surface and the core of the lethal trifecta ([Greshake et al.](https://arxiv.org/abs/2302.12173); [AgentDojo](https://agentdojo.spylab.ai/)).
- **No regression after fixes.** Failing to re-run the attack that found a bug after patching; "**regression testing is not optional in AI security**" ([Mend.io](https://www.mend.io/blog/llm-red-teaming-threats-testing-best-practices/)).
- **Treating benchmarks as a substitute for red-teaming.** Microsoft explicitly warns against the idea that **safety benchmarks can replace red-teaming** — benchmarks measure known behaviors; red-teaming finds novel failures ([Lessons From Red Teaming 100, arXiv 2501.07238](https://arxiv.org/pdf/2501.07238)).
- **Over-relying on gradient attacks.** In real products, **prompt engineering often outperforms gradient-based attacks** (GCG-style) and is far cheaper; teams that fixate on academic white-box attacks miss the easy wins ([Microsoft Security Blog](https://www.microsoft.com/en-us/security/blog/2025/01/13/3-takeaways-from-red-teaming-100-generative-ai-products/)).
- **Automation-only.** Assuming an automated scanner is sufficient; it cannot match human creativity for novel attacks ([Vectra](https://www.vectra.ai/topics/ai-red-teaming); [Microsoft, 2024](https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/)).

---

## 9. Suggested Child Sub-Concepts (6-10 future concepts)

1. **Open-source red-team scanners** — Garak, Giskard, promptfoo red-team (scanner-vs-framework, probe/detector architecture, CI integration).
2. **Adversarial attack-generation algorithms** — GCG, PAIR, TAP, fuzzing, red-teamer LLMs (white-box vs black-box, query efficiency, transferability).
3. **Jailbreak families & prompt-injection taxonomy (offensive)** — DAN/roleplay, payload splitting, encoding, many-shot, Crescendo; direct vs indirect; exfiltration patterns.
4. **Agent / tool-use injection testing** — AgentDojo, indirect injection, tool-poisoning, lethal-trifecta test cases (cross-ref guardrails).
5. **Red-team benchmarks & datasets** — AdvBench, HarmBench, JailbreakBench, CyberSecEval; leaderboards and validated classifiers.
6. **PyRIT & orchestration frameworks** — Targets/Converters/Scorers/Orchestrators, adaptive multi-turn automation, Azure AI Foundry Red Teaming Agent.
7. **Red-team process & governance mapping** — OWASP GenAI Red Teaming Guide 4 phases, OWASP LLM Top 10 as test plan, MITRE ATLAS, NIST AI RMF; red-team-in-CI and reporting.
8. **Commercial continuous red-teaming platforms** — Lakera/Gandalf, Cisco AI Defense (Robust Intelligence), Mindgard, HiddenLayer (DAST-AI, algorithmic red-teaming).

---

## Knowledge Gaps

- **Quantitative tool comparisons** (precision/recall of Garak vs promptfoo vs Giskard detectors on a common suite) are scarce in public sources — vendor claims dominate; treat comparative effectiveness as **Low confidence**.
- **Robust Intelligence post-acquisition specifics** beyond the TAP-based algorithmic red-teaming and "AI Validation" branding are thin in public sources.
- **Multimodal and voice red-teaming tooling** (image/audio injection) is emerging (CyberSecEval 3 visual injection; ATLAS agentic additions) but tooling maturity is unclear — flagged as a frontier, not a settled area.

---

## Sources

1. [NVIDIA/garak GitHub](https://github.com/NVIDIA/garak) — the LLM vulnerability scanner repo.
2. [Garak README (raw)](https://raw.githubusercontent.com/NVIDIA/garak/main/README.md) — architecture, probes, CLI, Apache-2.0 license.
3. [Garak (software) — Wikipedia](https://en.wikipedia.org/wiki/Garak_(software)) — history, ownership, recognition.
4. [Databricks — Applying Garak](https://www.databricks.com/blog/ai-security-action-applying-nvidias-garak-llms-databricks) — probe categories in practice.
5. [Microsoft Security Blog — Announcing PyRIT (2024)](https://www.microsoft.com/en-us/security/blog/2024/02/22/announcing-microsofts-open-automation-framework-to-red-team-generative-ai-systems/) — PyRIT launch, augments-not-replaces framing.
6. [The Hacker News — Microsoft releases PyRIT](https://thehackernews.com/2024/02/microsoft-releases-pyrit-red-teaming.html) — overview.
7. [Medium — Automating AI Red Teaming with PyRIT](https://medium.com/@xsankalp13/automating-ai-red-teaming-with-microsoft-pyrit-a-deep-dive-ce18d0bd8d44) — Targets/Converters/Scorers/Orchestrators.
8. [Microsoft Learn — AI Red Teaming Agent (Foundry)](https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent) — PyRIT in Azure AI Foundry.
9. [Promptfoo — LLM red teaming docs](https://www.promptfoo.dev/docs/red-team/) — scanner scope, 50+ vuln types.
10. [promptfoo/promptfoo GitHub](https://github.com/promptfoo/promptfoo) — used by OpenAI/Anthropic, CI/CD.
11. [Promptfoo — CI/CD integration](https://www.promptfoo.dev/docs/integrations/ci-cd/) — fail builds on regression.
12. [Promptfoo — MITRE ATLAS preset](https://www.promptfoo.dev/docs/red-team/mitre-atlas/) — framework mapping.
13. [Promptfoo — testing the lethal trifecta](https://www.promptfoo.dev/blog/lethal-trifecta-testing/) — trifecta as test cases.
14. [Giskard — LLM vulnerabilities docs](https://docs.giskard.ai/en/latest/knowledge/llm_vulnerabilities/index.html) — scan categories.
15. [Giskard — LLM detectors reference](https://docs.giskard.ai/en/latest/reference/scan/llm_detectors.html) — sycophancy/hallucination detectors.
16. [meta-llama/PurpleLlama GitHub](https://github.com/meta-llama/PurpleLlama) — Llama Guard, Prompt Guard, CyberSecEval.
17. [Meta — Prompt Guard overview](https://meta-llama.github.io/PurpleLlama/CyberSecEval/docs/prompt_guard/overview) — jailbreak + indirect-injection classifier.
18. [CyberSecEval paper (arXiv 2312.04724)](https://arxiv.org/html/2312.04724v1) — secure-coding + cyberattack-compliance benchmark.
19. [Tree of Attacks paper (arXiv 2312.02119)](https://arxiv.org/pdf/2312.02119) — TAP vs PAIR vs GCG comparison.
20. [Crescendo paper (arXiv 2404.01833)](https://arxiv.org/abs/2404.01833) — multi-turn jailbreak.
21. [Anthropic — Many-Shot Jailbreaking (PDF)](https://www-cdn.anthropic.com/af5633c94ed2beb282f6a53c595eb437e8e7b630/Many_Shot_Jailbreaking__2024_04_02_0936.pdf) — power-law many-shot attack.
22. [Greshake et al. — Indirect Prompt Injection (arXiv 2302.12173)](https://arxiv.org/abs/2302.12173) — foundational indirect-injection paper.
23. [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) — direct/indirect taxonomy, exfiltration.
24. [Mend.io — 2025 OWASP Top 10 for LLM Apps](https://www.mend.io/blog/2025-owasp-top-10-for-llm-applications-a-quick-guide/) — full 2025 list.
25. [JailbreakBench (arXiv 2404.01318)](https://arxiv.org/pdf/2404.01318) — benchmark, classifier, leaderboard; AdvBench/HarmBench lineage.
26. [JailbreakBench GitHub](https://github.com/JailbreakBench/jailbreakbench) — dataset & repo.
27. [AgentDojo paper (arXiv 2406.13352)](https://arxiv.org/html/2406.13352v3) — agent/tool-use injection benchmark.
28. [AgentDojo site](https://agentdojo.spylab.ai/) — leaderboard, 97 tasks / 629 security cases.
29. [Lakera — Who is Gandalf](https://www.lakera.ai/blog/who-is-gandalf) — Gandalf game, Lakera Red, Cisco acquisition.
30. [Lakera — Guide to prompt injection](https://www.lakera.ai/blog/guide-to-prompt-injection) — attack taxonomy.
31. [Cisco — Robust Intelligence is part of Cisco](https://www.cisco.com/site/us/en/products/security/ai-defense/robust-intelligence-is-part-of-cisco/index.html) — algorithmic red-teaming, TAP, AI Validation.
32. [Microsoft Security Blog — 3 takeaways from red-teaming 100 GenAI products](https://www.microsoft.com/en-us/security/blog/2025/01/13/3-takeaways-from-red-teaming-100-generative-ai-products/) — eight lessons summary.
33. [Lessons From Red Teaming 100 Generative AI Products (arXiv 2501.07238)](https://arxiv.org/pdf/2501.07238) — AIRT ontology, benchmarks-not-a-substitute.
34. [Simon Willison — The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) — trifecta definition.
35. [OWASP — GenAI Red Teaming Guide](https://genai.owasp.org/resource/genai-red-teaming-guide/) — four-phase methodology.
36. [ResilientCyber — Implementing GenAI Red Teaming the OWASP way](https://www.resilientcyber.io/p/implementing-genai-red-teaming-the) — phase walkthrough.
37. [Vectra — MITRE ATLAS](https://www.vectra.ai/topics/mitre-atlas) — ATLAS tactics/techniques, v5.1.0 scale.
38. [Straiker — Comparing OWASP, CSA, NIST, MITRE](https://www.straiker.ai/blog/comparing-ai-security-frameworks-owasp-csa-nist-and-mitre) — framework complementarity, 2026 OWASP landscapes.
39. [Mend.io — LLM red teaming best practices](https://www.mend.io/blog/llm-red-teaming-threats-testing-best-practices/) — continuous/regression, anti-patterns.
40. [Ajith Prabhakar — Red Teaming LLMs playbook](https://ajithp.com/2025/07/13/red-teaming-large-language-models-playbook/) — reporting, reproducible cases.
41. [Mindgard — What is AI red teaming (2026)](https://mindgard.ai/blog/what-is-ai-red-teaming) — continuous red-teaming, platform.
42. [CSET Georgetown — AI Red-Teaming Design](https://cset.georgetown.edu/article/ai-red-teaming-design-threat-models-and-tools/) — threat-model-first methodology.
43. [Vectra — AI red teaming tools/frameworks](https://www.vectra.ai/topics/ai-red-teaming) — manual-vs-automated.
44. [CrowdStrike — Prompt Injection taxonomy](https://www.crowdstrike.com/en-us/cybersecurity-101/cyberattacks/prompt-injection/) — IM/PT taxonomy, exfiltration.
45. [ToxSec — DAN & roleplay prompts](https://www.toxsec.com/p/dan-prompts-for-guardrail-bypass) — jailbreak families.
46. [Mend.io — Top 6 AI red teaming services](https://www.mend.io/blog/best-ai-red-teaming-services-top-6-services/) — commercial platform landscape.

## Methodology

Searched 12 queries across web and news using the WebSearch/WebFetch fallback (firecrawl/exa MCPs unavailable in this thread; per skill guidance, source-count target raised ~50%). Deep-read primary sources: Garak README, OWASP LLM01:2025, OWASP GenAI Red Teaming Guide, and arXiv papers (TAP, Crescendo, JailbreakBench, AgentDojo, Many-Shot, Greshake indirect-injection, Microsoft "100 products"). Sub-questions investigated: (1) discipline & manual-vs-automated & continuous; (2) tooling landscape scanner-vs-framework (Garak/PyRIT/promptfoo/Giskard/Purple Llama); (3) attack taxonomy (direct/indirect injection, jailbreak families, exfiltration, lethal trifecta); (4) automated attack generation (GCG/PAIR/TAP/red-teamer LLMs); (5) benchmarks/datasets (AdvBench/HarmBench/JailbreakBench/AgentDojo/OWASP-as-checklist); (6) AI-firewall products from the testing angle (Lakera/Gandalf, Robust Intelligence/Cisco, Mindgard, HiddenLayer); (7) process & framework mapping (OWASP guide 4 phases, ATLAS, NIST AI RMF, red-team-in-CI); (8) anti-patterns. **Injection guard honored:** all fetched web content treated as data, not instructions; no adversarial-instruction pages encountered.

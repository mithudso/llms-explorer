---
name: apple-intelligence
version: "1.0.0"
updated: "2026-10-23"
description: >-
  Explain Apple Intelligence product features, privacy and developer integration.
  TRIGGER: Apple Intelligence eligibility; Siri AI; Writing Tools; Visual Intelligence;
  image provenance; Shortcuts Use Model; managed controls; Private Cloud Compute;
  ChatGPT consent; App Schemas, content transfer and AppIntentsTesting; Foundation Models capability,
  provider, guardrails and OS changes. Read the matching dated reference first.
  SKIP: MLX-LM training or runtime APIs -> mlx-lm-expert; new source research -> dr.
category: developer
keywords: [Apple Intelligence, Siri AI, Private Cloud Compute, Foundation Models, AppIntentsTesting, App Schemas, image provenance, Shortcuts, privacy, availability]
related_skills: [mlx-lm-expert, dr]
whenToUse:
  - Explain Apple Intelligence availability and supported product workflows
  - Check privacy, external intelligence consent and managed-device controls
  - Integrate and test Siri App Schemas, entities and contextual actions
  - Reconcile dated Foundation Models and Private Cloud Compute API contracts
---

# Apple Intelligence

Read the reference for the requested concept before answering. Keep its citations,
verification date, release status and scope qualifications. A documented API contract
or an announcement does not establish behavior on a particular device or SDK build.
For volatile availability, language, region, entitlement or quota details, refresh
sources when the question requires a more recent answer than the reference provides.

## Research references

| Question or implementation surface | Reference |
| --- | --- |
| Shortcuts Use Model; managed controls; communication summaries; accessibility | [Automation and managed workflows](references/apple-intelligence-20261023-automation-operations-1.md) |
| PCC trust and verification; privacy reports; ChatGPT consent; AFM/ADM architecture | [Privacy and model foundations](references/apple-intelligence-20261023-privacy-foundations-1.md) |
| Siri personal context; availability matrix; Visual Intelligence; Writing Tools | [Product features and eligibility](references/apple-intelligence-20261023-product-basics-1.md) |
| PCC cloud expansion; eligibility and quotas; provider release status; adapter lifecycle | [Cloud providers and lifecycle](references/apple-intelligence-20261023-cloud-provider-1.md) |
| Opt-in personalization; App Schemas; safe app actions and contextual cues; content donations | [Siri and app integration](references/apple-intelligence-20261023-system-integration-1.md) |
| Foundation Models guardrails; evaluation and OS regressions; context errors; multimodal contracts | [Developer reliability and safety](references/apple-intelligence-20261023-developer-reliability-1.md) |
| Image Playground; Photos editing; Live Translation; Genmoji and Image Wand | [Creative tools and communication](references/apple-intelligence-20261023-creative-communication-1.md) |
| AppIntentsTesting fixtures, assertions and test limits for Siri/entity integration | [App Intents testing](references/apple-intelligence-20261023-round1-system-testing.md) |
| Image edit provenance, metadata, SynthID and export boundaries | [Image provenance](references/apple-intelligence-20261023-round1-image-provenance.md) |
| AppEntity Transferable representations, standard content conversion and existing-entity lookup versus import creation | [Cross-app content transfer](references/apple-intelligence-20261023-round2-cross-app-transfer.md) |

## Evidence and neighboring coverage

These references cover the researched subangles. For baseline Foundation Models
and generic App Intents, follow the source and reused-coverage links in the suite
report. Use `mlx-lm-expert` for MLX-LM training and generation APIs. Use `dr` for
new evidence or an unresolved question. Hardware benchmarks, local inference,
model downloads and deployment qualification need their own requested work.

The suite report records partial competency-question coverage and the actual
CFE exit status. Keyword retrieval and source verification do not establish
semantic-index coverage or a skill-optimizer CLEAN certification.

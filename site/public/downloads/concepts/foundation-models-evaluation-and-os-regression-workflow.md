<!-- llms-explorer concept facts · https://llms-explorer.com/tree/foundation-models-evaluation-and-os-regression-workflow/ · pack 2026-10-23 · ~1820 tokens -->

# Foundation Models evaluation and OS regression workflow

> Source-anchored research for Foundation Models evaluation and OS regression workflow. Run status: COMPLETED.

Parent: [Apple Foundation Models framework](https://llms-explorer.com/tree/apple-foundation-models-framework/) · 5 facets · 20 facts · page: https://llms-explorer.com/tree/foundation-models-evaluation-and-os-regression-workflow/

## How it works

- Apple says it periodically updates the on-device SystemLanguageModel with OS releases and recommends testing prompts against new model versions, comparing outputs, and versioning prompts when behavior changes. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel.md)
- Swift Testing’s EvaluationTrait records evaluation results as test attachments; Xcode stores these results in test reports, and an independent implementation documents the native .xcevalresult attachment format. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/evaluations.md)
- Do not accept a passing aggregate alone: inspect per-sample failures and category-level results because the same aggregate can hide a collapsed fixture distribution or a newly failing subgroup. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)
- Apple’s prompt-update guidance says to record the prior model’s prompt output, compare it with output from the new model, and version prompts when behavior needs to differ; an app can select a prompt version using OS availability checks. (high confidence) (verified as of 2026-08-06) — [source](https://developer.apple.com/documentation/foundationmodels/updating-prompts-for-new-model-versions.md)

## How-to and procedures

- Use code-based evaluators for measurable response properties and model-judge evaluators for subjective qualities; Apple says judge scores should correlate with human review, and its WWDC example shows that a broad judging rubric can approve output that humans consider unhelpful. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)

## Problems, failure modes and limitations

- Apple’s Evaluations framework provides type-safe Swift APIs to run an intelligence-powered feature against samples, score responses with metrics from pass/fail checks to model-judge scoring, and aggregate results. (high confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/documentation/evaluations.md)
- Build a small, reviewed evaluation set with categories for typical, boundary, and failure inputs; Apple documents manually written seed samples and synthetic expansion, while an independent implementation guide recommends trusting the reviewed seed before growing it. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)

## Comparisons and alternatives

- Use deterministic evaluators for objectively measurable properties and model judges for qualitative criteria; compare judge scores with human ratings because a judge is another probabilistic system rather than an objective oracle. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)

## Facts and statements

- In a June 2026 forum answer, an Apple Frameworks Engineer said there was no model-pinning or model-version-retrieval API at that time and recommended Evaluations to catch regressions as the system model changes across OS updates. (high confidence) — [source](https://developer.apple.com/forums/thread/833642)
- Compare control and experimental runs on the same fixtures, change one variable at a time, and inspect individual responses as well as aggregate metrics before carrying a change forward. (high confidence) — [source](https://developer-rno.apple.com/videos/play/wwdc2026/335/)
- Evaluations measure model-driven output quality and do not replace conventional deterministic tests for application state transitions, persistence, permissions, or writes. (high confidence) — [source](https://3nsofts.com/guides/foundation-models/testing-ai-features-evaluations-framework-ios-27)
- As checked on 2026-10-23, Xcode 27 is generally released and Apple’s Evaluations Markdown metadata lists Xcode 27 and OS 27 availability floors, while an independent API guide labels the framework Beta; the exact per-symbol maturity state remains unresolved. (medium confidence) (verified as of 2026-10-23) — [source](https://developer.apple.com/news/releases/)
- Apple’s Evaluations framework measures an app’s intelligence-powered feature against samples with developer-defined metrics and aggregates the results; Apple presents it for comparing prompt strategies, tracking quality over time, and catching regressions before release. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)
- Apple’s documented evaluation workflow defines the feature code as the subject, supplies ModelSample inputs, applies Metric and Evaluator measurements, aggregates metrics, and runs the evaluation through Swift Testing with the .evaluates trait. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)
- Apple recommends categorized datasets that represent the full range of real-world use for a feature; its documentation also describes generating synthetic samples to expand a smaller manually written set. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)
- Apple’s Xcode evaluation report exposes per-sample prompts, measurements, and full model responses; Swift Testing runs can also carry configuration notes that make later comparisons easier to interpret. (high confidence) — [source](https://developer.apple.com/documentation/evaluations.md)
- Apple’s June 2026 Foundation Models update notes say that updating to OS 27 changes the on-device model and direct developers to test prompts with the new model; the notes make the same recommendation for the OS 26.4 model change. (high confidence) (verified as of 2026-08-06) — [source](https://developer.apple.com/documentation/updates/foundationmodels.md)
- For interpretable release comparisons, run control and candidate changes against the same dataset, record app commit, prompt and model configuration, OS and SDK, locale, and dataset version, then inspect category-level movement as well as the aggregate score. (medium confidence) — [source](https://3nsofts.com/insights/ai-evaluations-ios-release-readiness)
- A fixed regression set supports apples-to-apples comparisons but does not establish generalization by itself: Google’s evaluation guidance warns that tuning against fixed nightly cases can overfit and recommends a separate release exam with unseen inputs, while Apple recommends samples spanning real-world usage. (high confidence) — [source](https://developer.chrome.com/docs/ai/evals/run)
- A model judge should not be the sole release authority: 3nsofts recommends checking judge rationales and comparing scores with human labels on held-out examples, consistent with Apple’s guidance to correlate model-judge scores with human review. (medium confidence) — [source](https://3nsofts.com/insights/ai-evaluations-ios-release-readiness)

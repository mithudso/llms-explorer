# Research stopping and citation entailment

Research date: 2026-10-22. Parent task: concept knowledge strategy research, TASK-816.

Both concepts completed six genuine deepening passes and stopped at the skill's default cap. Both verdicts are **BUDGET_EXHAUSTED**. Neither met the two-consecutive-passes-below-5% rule. The final research files contain 19 stopping claims and 20 entailment claims. Their independent promotion gate belongs to the parent run; schema validation alone does not establish support.

## Verified project baseline

The installed rabbithole workflow already requires atomic claims, semantic novelty accounting, distinct budget and saturation outcomes, and primary-source deepening. Its novelty denominator is the accumulated claim count after a pass. See `.agents/skills/rabbithole/references/saturation.md` and `references/depth-passes.md`.

The current gate already binds selected full canonical statements to exact evidence spans in pinned source snapshots. It rejects altered text, stale inputs, missing judgments, and unresolved dissent. This is an existing strength; the research does not justify replacing that identity contract.

The important coverage gap remains current. `scripts/research_gate.py:37`, `claim_rows`, enumerates only `document['claims']`. `scripts/research_artifact.py:32`, `build`, preserves the other document fields, but enriches and verifies evidence identities only inside the claim list. Hash binding protects auxiliary prose against later changes; it does not judge its factual assertions. The prior incident record, [the auxiliary-prose verification gap, KNOW-796](https://app.stele-ai.dev/p/llms-explorer-9d1wd/nodes/KNOW-796), describes a corrected structured claim whose inference remained in a disagreement note. That record changed the priority here: assess assertion coverage across reader prose before adding another structured-claim verifier.

No retrieval, model, storage, gate, or embedding changes were implemented in this work.

## Marginal evidence gain research stopping

**IN:** the decision to stop acquiring evidence inside one scoped concept; novelty units, prospective stopping rules, uncertainty, and validation failures. **OUT:** designing a full systematic-review protocol, optimizing general active-learning classifiers, claiming complete open-web coverage, or implementing a new production rule.

In plain terms, low recent yield is an observation about the searches already attempted. A completeness claim asks how much relevant material remains unseen. The two need different evidence. Callaghan and Müller-Hansen's finite-pool method tests a chosen recall target using random residual sampling without replacement. Its hypergeometric model concerns a known candidate pool. [Statistical stopping criteria](https://link.springer.com/article/10.1186/s13643-020-01521-4).

Guest, Namey, and Chen instead compare new themes in an observation run with themes in a specified initial base. They explicitly reject a probability guarantee from the threshold. Their method and the installed skill therefore have different denominators, units, and interpretations; importing a numerical threshold does not import a confidence guarantee. [Thematic saturation method](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0232076).

The evidence developed along several distinct lines. The 2017 code-versus-meaning study found that recognizing the range of issues could precede understanding their dimensions. In its 25-interview dataset, code saturation occurred at nine interviews. Some conceptual codes reached meaning saturation at interviews 16–24; other codes reached it earlier, and one conceptual code never reached it. The independent gate caught and corrected an overbroad reading of the abstract headline. These are study results, not proposed paper or web-search quotas. [Hennink, Kaiser, and Marconi](https://pmc.ncbi.nlm.nih.gov/articles/PMC9359070/).

In 2024, SAFE combined random initialization, active screening, model switching, and quality checks. It describes its numerical examples as adaptable, and reports no direct comparison against other heuristics. [SAFE](https://link.springer.com/article/10.1186/s13643-024-02502-7). A separate commentary requires explicit uncertainty and evaluation across algorithms and datasets when stopping is used to claim achieved recall. [Stopping-criteria commentary](https://link.springer.com/article/10.1186/s13643-024-02699-7). These approaches have different evidentiary ambitions; this dossier does not manufacture a single consensus cutoff.

The 2026 Repke evaluation examined 223 screening simulations over 81 datasets. CMH met its set recall targets in those experiments, often conservatively. The authors disclose that evaluation co-author Müller-Hansen also co-authored CMH. This is useful later evidence, with an authorship dependency that prevents treating it as wholly independent replication. [Repke and colleagues](https://onlinelibrary.wiley.com/doi/full/10.1002/cesm.70068).

**Project inference:** retain the current rule as an observable workflow stop, and report its scope and remaining gaps. Test whether a fixed-base novelty denominator, explicit mechanism-gap tracking, and a different final search angle improve decisions before changing defaults. A large inventory mathematically lowers `new / total` for a fixed number of new facts; that fact alone says nothing about whether the new fact changes a recommendation. Use a statistical residual audit only after freezing the candidate pool and stating its sampling assumptions. Do not extend its result to the entire web.

Likely failure modes to test include repeated searches within one citation lineage, duplicate phrasing counted as novelty, a corpus dominated by easy common facts, missing counterexamples despite a low average yield, and stopping because a budget ended. The last is a legitimate resource decision and needs its own verdict.

## Citation entailment for generated research prose

**IN:** whether factual assertions in generated research prose follow from their identified evidence; coverage of extracted claims, context, partial support, and verification failures. **OUT:** training an entailment model, a full causal-interpretability program, redesigning the retrieval stack, or changing production gates.

AIS asks whether a statement is attributable to identified source material, with context and time used to interpret the statement. Source trust is a separate evaluation. Thus an exact citation can accurately represent a mistaken source. [AIS](https://arxiv.org/html/2112.12870v2). ALCE checks full statement support from the cited passages together and separately evaluates irrelevant citations. It does not demand a minimal citation set. Its automatic precision calculation can penalize legitimate partial support when other citations cover the same information. [ALCE](https://aclanthology.org/2023.emnlp-main.398.pdf).

FActScore's 2023 contribution was a fine-grained supported-fact fraction. Its authors explicitly separate that precision from information coverage and state limits for nuanced or conflicting material. A high supported fraction can accompany an answer that omits useful facts. [FActScore](https://aclanthology.org/2023.emnlp-main.741.pdf).

The later literature exposes two further layers. Wallat and colleagues define citation faithfulness as causal influence in addition to support correctness. Their intervention experiments are preliminary, and the paper identifies assumptions requiring stronger controls; this review does not use its headline percentage as a project-wide estimate. [Citation faithfulness](https://arxiv.org/html/2412.18004v1). DnDScore keeps the fact being judged distinct from the context needed to interpret it. Adding contextual facts can otherwise repeat evidence or change the verification target. [DnDScore](https://aclanthology.org/2025.emnlp-main.1205.pdf).

Atomic extraction is not automatically beneficial. A separate analysis identifies omission, excessive splitting, ambiguity, and meaning alteration as downstream failure mechanisms. [Decomposition Dilemmas](https://aclanthology.org/2025.naacl-long.320.pdf). Claimify's evaluation measures coverage of individual verifiable elements and permits abstention when context cannot resolve competing interpretations; its reported local evaluation does not establish accuracy on this project. [Claimify](https://aclanthology.org/2025.acl-long.348.pdf). WiCE further distinguishes partial support and retains alternative sufficient evidence sets. [WiCE](https://arxiv.org/html/2303.01432v2).

**Project inference:** measure three separate coverage questions: whether the rendered prose's factual assertions entered the canonical inventory, whether selected claims have semantic support, and whether the answer covers the requested problem. Preserve full conditions, versions, quantifiers, and temporal context when matching prose to claims. A prose extractor should not invent a sharper claim than the author wrote. Treat an unsupported assertion, an ambiguous assertion, and an explicitly marked project inference differently.

The present exact-span contract should remain the provenance anchor. Before adding multi-passage semantics, first measure how often legitimate project claims require several evidence fragments, and whether a longer existing span already supplies the context. Causal attribution research is a separate future investigation; support verification remains valuable even when it does not prove how a generator internally used a source.

## Actual pass curve

Pass 0 supplied three local baseline claims per concept. The table includes these seeded claims in the accumulated denominator, as required by the skill. The canonical literature files exclude the six local baseline claims. Private ledgers map each accepted claim ID to its exact final text, literal searches, sources read, rejected restatements, and mechanism gaps. A renewed productive angle legitimately raises the curve; these are measured claim counts, not a fitted decline.

| Deepening pass | Stopping: new / accumulated | Novelty | Entailment: new / accumulated | Novelty |
|---|---:|---:|---:|---:|
| 1 | 3 / 6 | 50.0% | 3 / 6 | 50.0% |
| 2 | 3 / 9 | 33.3% | 7 / 13 | 53.8% |
| 3 | 4 / 13 | 30.8% | 2 / 15 | 13.3% |
| 4 | 4 / 17 | 23.5% | 4 / 19 | 21.1% |
| 5 | 2 / 19 | 10.5% | 2 / 21 | 9.5% |
| 6 | 3 / 22 | 13.6% | 2 / 23 | 8.7% |

**Stopping:** 22 inventory claims, including three project baselines; 19 literature claims. **Entailment:** 23 inventory claims, including three project baselines; 20 literature claims. Both remain above 5% at the cap. One or two additional passes could still pay off on sequential calibration and temporal/conditional assertion coverage. The remaining work is recorded, not described as saturated.

The source library searches returned unrelated material and supplied no useful primary-source baseline. All final URLs received exact library lookups before opening. There are six stopping sources from four original origin groups and eight entailment sources from eight original research teams. Hosting several papers at ACL or arXiv neither makes them one origin nor proves independence; the private origin file records the actual research-team basis. Claims with one URL use `low` confidence under the current schema even when the source is a primary paper.

## Proposed controlled experiments

All numbers below are proposed experimental choices, not measured outcomes. Preserve current canonical artifacts and embeddings throughout the experiments.

| Experiment | Controlled comparison | Measurements | Adoption condition |
|---|---|---|---|
| Research stopping replay | Freeze sources and model configuration for 12 varied concepts. Compare a fixed budget, the existing novelty rule, and a fixed-base rule with explicit mechanism-gap checks. Keep independent continuation passes hidden until each proposed stop. | Supported unique claims per minute and model cost; late decision-changing findings; missing counterexamples; reference-inventory recall with its incompleteness stated. Randomize order and blind adjudication. | Adopt a change only if held-out runs reduce serious late discoveries at an acceptable additional cost. Keep the existing rule if the change adds cost without a useful improvement. |
| Auxiliary-prose coverage | On 150 sampled or deliberately modified reader sentences, compare today's structured-only gate, a renderer restricted to supported canonical assertions, and an auxiliary-prose assertion extractor. Include summaries and disagreement notes. | Assertion-extraction precision and recall against two human reviewers; unsupported assertions escaping; false publication blocks; review time; preservation of caveats and inference labels. | Prefer the smallest change that closes measured coverage gaps while retaining existing claim and snapshot bindings. |
| Entailment boundaries | Reuse the same claims and frozen evidence. Vary compound versus carefully decomposed statements, full contextual spans versus short snippets, and one versus complementary passages. Include partial support, conflicting sources, negation, versions, and missing time qualifiers. | False support, false rejection, reviewer agreement, evidence-set sufficiency, and changes caused solely by extraction. Score completeness separately. | Extend evidence handling only when meaningful legitimate claims are rejected by the baseline and the extension does not materially increase false support. |

Measure costs independently for discovery, extraction, verification, and rendering. Reuse the same source snapshots for comparisons so retrieval differences do not masquerade as better reasoning. Reserve a holdout before tuning thresholds. Treat published benchmark results and local measurements as separate evidence.

The expected value is a testable reduction in unsupported or misleading published assertions and better justification for research spend. Neither benefit has been measured here. The practical first experiment is auxiliary-prose coverage because the repository contains a concrete observed incident. A prompt-only manual review of summaries and disagreements can precede any schema migration; an implementation decision should follow the measured error distribution.

The recommended architecture implication is to retain immutable evidence and canonical claim identities, then make generated factual prose traceable to those claims or explicitly reviewed new assertions. Keep policy recommendations marked as project inferences. Version any extractor, judge prompt, novelty decision, and experiment dataset so results can be reproduced and a proposed change can be abandoned without re-embedding or altering historical artifacts.

## Remaining research queue and receipts

Adjacent concepts queued rather than absorbed: decision value of information, living-review refresh triggers, causal citation faithfulness, and evidence-set ranking for human verification. Within the present concepts, unresolved questions include repeated-look calibration, rare but decisive findings, temporal ambiguity, assertion extraction across bullet-list context, and multi-passage judge disagreement.

The authored dossier is a public synthesis; private acquisition bodies and raw logs are not copied into it. Private evidence remains under `/private/tmp/llmsx-strategy-816/quality/`:

- `source-manifest.json` and `source-origins.json`: final reviewed URLs and origin dependencies.
- `marginal-evidence-gain-research-stopping.json` and `citation-entailment-for-generated-research-prose.json`: final DR claims; both passed `claims-check`, with `recorded: false` at handoff.
- `marginal-stopping-passes.json` and `citation-entailment-passes.json`: scoped Pass 0 baselines and six-pass claim ledgers.
- `raw-web-rounds-1-2.json` and `raw-web-rounds-3-6.json`: acquisition attempts, including failed fetches and scout-only results.

The parent run owns source ingestion, canonical recording, independent claim validation, rendering, finish, and generated-site refresh. A completed dossier and a budget-stop verdict do not substitute for those persistence steps.

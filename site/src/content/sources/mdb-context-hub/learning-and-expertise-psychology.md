---
title: "Learning &amp; Expertise Psychology"
description: "The science of how durable skill and knowledge are actually built — and the uncomfortable headline that organizes the whole field: the activities that feel like learning are usually not, and the activ"
---

# Learning & Expertise Psychology

The science of how durable skill and knowledge are actually built — and the uncomfortable headline that organizes the whole field: **the activities that feel like learning are usually not, and the activities that feel unproductive usually are.** Rereading and highlighting feel smooth and confident; they mostly build *fluency*, not memory. Self-testing, spacing, and interleaving feel slow and error-prone; they build durable, transferable mastery. This gap between the *feeling* of learning and the *fact* of learning is the central practical problem you are solving — for customers in a training session and for yourself building expertise.

**Two audiences, one science.** Every technique below carries an **Enablement note** (designing customer/technical training that survives the drive home) and a **Self note** (the operator deliberately getting better at their own craft). Same evidence, two applications.

**Use this skill to** decide how to structure a workshop, lab, or onboarding path; diagnose why a training "didn't land"; design a customer's ramp so they retain it; build your own deliberate-practice plan; or settle an evidence question ("are learning styles real?", "is the 10,000-hour rule true?", "should I reread or self-test?").

## Scope and boundaries

| You need… | Use |
| --- | --- |
| The learning **science** — load, retrieval, spacing, transfer, expertise | **this skill** |
| How to **write** the tutorial / how-to / reference / KB article (Diátaxis, prose, headings, structure) | `technical-writing-craft` (owns tutorial/how-to writing — `references/tutorial-writing.md`; it cites "cognitive load 7±2" in passing, this skill owns the underlying science — cross-reference) |
| **Motivation** to learn, building the *habit* of practice, driving adoption/engagement over time | `behavior-change-psychology` (SDT, Fogg B=MAP, habit loops, goal-setting) |
| Rolling out an enablement **program** as a TAM deliverable (success plan, EBR/QBR, scoping) | `tam-expertise` |
| Cognitive **biases** / judgment & decision-making (anchoring, framing, prospect theory, debiasing) | `behavioral-decision-making` |
| **Trust in / reliance on AI tools**, automation bias, calibrated reliance on a model | `human-ai-interaction-psychology` |

The clean line: **learning-and-expertise-psychology** = the science of building skill and memory. **behavior-change-psychology** = the science of getting someone to *want to* and *keep* doing it. A real enablement plan usually needs both — design the learning here, design the motivation/habit there.

---

## 1. Cognitive Load Theory (Sweller) — the load budget

Working memory is tiny and fragile (classically Miller's **7±2** chunks, 1956; revised down to **~4** by Cowan, 2001; structured by Baddeley's multi-component model). Long-term memory is effectively unlimited and stores **schemas** — chunked patterns that let an expert treat many elements as one. Learning *is* schema construction, and instruction has to respect the working-memory bottleneck while it happens (Sweller; [Cognitive load — Wikipedia](https://en.wikipedia.org/wiki/Cognitive_load); [The Decision Lab](https://thedecisionlab.com/reference-guide/psychology/cognitive-load-theory)).

**Three loads to manage:**
- **Intrinsic load** — the inherent complexity of the material *for this learner*. Driven by **element interactivity**: how many pieces must be held in mind *simultaneously* because they interact ([Springer, Educ. Psych. Review](https://link.springer.com/article/10.1007/s10648-010-9128-5)). A list of CLI flags is low-interactivity (learn one at a time); designing a sharding key is high-interactivity (data distribution, query patterns, cardinality, and growth all interact at once).
- **Extraneous load** — load imposed by *how* you present it, unrelated to learning. The waste you cut: clutter, hunting for information, decorative complexity.
- **Germane load** — the productive effort that actually builds schemas. You want learner effort spent here.

**The effects that fall out of CLT** (each is a concrete design lever):
- **Worked-example effect** — for novices, studying a fully worked solution beats struggling through an equivalent unsolved problem. Free working memory to see the *pattern* rather than burning it on means-ends search.
- **Expertise-reversal effect** — the single most important boundary condition in this skill. Support that helps a novice (detailed worked examples, step-by-step scaffolds) becomes *useless or actively harmful* for someone who already has the schema; the now-redundant guidance is itself extraneous load ([eLearning Industry](https://elearningindustry.com/cognitive-load-element-interactivity-and-reversal-effect)). **What helps a beginner hurts an expert.**
- **Split-attention effect** — when a diagram and the text explaining it are separated (forcing the eye to jump and hold), integrate them physically: labels *on* the diagram, not in a distant legend.
- **Modality effect** — narrate a complex diagram (spoken audio + visual) rather than captioning it (visual + visual); this spreads load across two channels (ties to dual coding, §6).
- **Redundancy effect** — the trap that catches well-meaning trainers: presenting the *same* information two ways at once (reading on-screen text aloud verbatim, or annotating self-explanatory visuals) *adds* load instead of helping. More is not better.

> *Active debate:* a 2023 *British Journal of Educational Psychology* special issue continues to question whether "germane load" is a distinct, measurable construct. The intrinsic/extraneous distinction and the effects above are well-established and decades-replicated; treat "germane load" as a useful design intent rather than a precisely measured quantity.

**Enablement note.** Match support to expertise and *fade it*. Open a new topic with worked examples and a guided lab; withdraw scaffolding as competence grows. Don't run your power-users through the beginner walkthrough — expertise reversal means you're wasting their time and adding load. Strip extraneous load: one idea per slide, integrated labels, no decorative slides, no reading bullets aloud.

**Self note.** When a topic feels overwhelming, it's usually high element interactivity, not low ability — break it into lower-interactivity sub-skills and master them before combining. As a novice in a new domain, *deliberately study worked examples* (read excellent PRs, annotated configs, model write-ups) before grinding from scratch; the struggle-first instinct is inefficient early.

---

## 2. Retrieval practice / the testing effect — the strongest lever

Retrieving information from memory strengthens it far more than re-exposure does. **Roediger & Karpicke (2006)**, *The Power of Testing Memory*: on delayed tests (days to weeks out), learners who *tested themselves* outperformed those who *restudied* — and the advantage **grows with delay**, even though restudy looks better on an immediate test ([PDF, WUSTL](http://psychnet.wustl.edu/memory/wp-content/uploads/2018/04/Roediger-Karpicke-2006_PPS.pdf)). The act of reconstructing a memory is what consolidates it. This is one of the most replicated findings in cognitive psychology.

**Karpicke & Blunt (2011)**, *Science*: retrieval practice produced *more meaningful learning* than elaborate concept-mapping — including on inference questions, and even when the final test was itself creating a concept map ([Science](https://www.science.org/doi/10.1126/science.1199327)). Retrieval isn't just for rote facts; it builds understanding.

**Generation effect** (Slamecka & Graf, 1978): information you *produce* (fill the blank, derive the answer, predict the output) is retained better than the same information read passively.

**Enablement note.** Build retrieval *into* every asset, not just the final exam. Open each session with low-stakes recall of the last one ("before we start — what does a write concern of `majority` actually guarantee?"). End modules with a "close the docs and rebuild it" task. Make labs require recall, not copy-paste. Frame quizzing as a *learning tool*, not judgment — the value is the retrieval attempt, not the score.

**Self note.** After reading docs, an RFC, or a postmortem, shut it and write what you remember from memory before checking — that closed-book reconstruction is the learning event; passive rereading mostly produces the illusion of fluency (§7). Flashcards, the Feynman technique (explain it as if teaching), and "predict the output before you run it" are all retrieval. A failed retrieval attempt *followed by feedback* still beats restudy.

---

## 3. Spacing / distributed practice & the forgetting curve

**Ebbinghaus (1885)** measured his own memory for nonsense syllables and produced the **forgetting curve**: retention drops steeply then flattens — roughly ~50% of novel meaningless material gone within an hour, ~70% within a day. The curve was **successfully replicated** by Murre & Dros (2015) ([Forgetting curve — Wikipedia](https://en.wikipedia.org/wiki/Forgetting_curve)). *Caveats:* a single subject (himself) and meaningless material, so don't treat the exact percentages as a schedule for meaningful, connected content — the popular "review at exactly these intervals" framing overstates its precision ([Carl Hendrick critique](https://carlhendrick.substack.com/p/why-the-forgetting-curve-is-not-as)).

**Spacing beats massing.** **Cepeda et al. (2006)** meta-analyzed 839 assessments across 317 experiments: distributing study across sessions reliably beats cramming the same total time into one ([PDF](https://augmentingcognition.com/assets/Cepeda2006.pdf)). The crucial nuance: the **optimal gap scales with how long you need to remember** — the further out the test, the longer the ideal inter-study interval. Practical heuristic from this line of work: **space reviews at roughly 10–20% of the target retention interval** (need it in a week → review ~daily; need it in a year → review ~monthly).

**Spaced-repetition systems** operationalize expanding intervals: the **Leitner** box system (move a card to a longer-interval box on success, back to a short one on failure) and the **SM-2** algorithm (SuperMemo, adopted by **Anki**) schedule the next review just before predicted forgetting.

**Enablement note.** A one-day "firehose" bootcamp is the *worst* schedule the science describes — it maximizes forgetting. Distribute enablement across weeks: shorter sessions with deliberate gaps, each opening with spaced recall of prior material. Plant a follow-up touchpoint (office hours, a 2-week "rebuild the cluster from scratch" lab) precisely to force a spaced retrieval.

**Self note.** Study a hard topic in short sessions across days, not one marathon — same hours, far better retention. Use Anki (or a Leitner deck) for durable factual scaffolding (error codes, CLI syntax, API surfaces) so working memory is free for the genuinely hard interactive parts. Revisit a skill *just as it starts to fade* — that's the highest-yield moment to practice it.

---

## 4. Interleaving vs blocking

**Blocked** practice does all of topic A, then all of B, then C (AAA BBB CCC). **Interleaved** practice mixes them (ABC BCA CAB). **Rohrer & Taylor (2007)** had students practice math either way: interleaving *worsened* practice-session accuracy (60% vs 89% blocked) but **improved a delayed test a week later** — and the classroom replications (Rohrer et al. 2014, 2015) held up ([Rohrer guide PDF](http://uweb.cas.usf.edu/~drohrer/pdfs/Interleaved_Mathematics_Practice_Guide.pdf)). Blocking looks better *during* practice and is worse *for keeps* — the same feeling-vs-fact trap.

Interleaving bundles two mechanisms: different *kinds* of problem are mixed (so the learner must first **choose** the right approach — the skill that matters in the real world, where problems don't arrive pre-labeled), and same-kind problems are automatically **spaced** (§3).

**Discriminative-contrast hypothesis:** interleaving works partly by juxtaposing categories so learners notice the **differences between** them (Kang & Pashler; Birnbaum et al. 2013, [Springer Mem. & Cog.](https://link.springer.com/article/10.3758/s13421-012-0272-7)). A 2021 systematic review argues spacing and interleaving rest on *distinct* theoretical bases ([Educ. Psych. Review 2021](https://link.springer.com/article/10.1007/s10648-021-09613-w)). **Boundary condition:** interleaving helps most when the categories are **confusable** (easy to mix up); for unrelated material the benefit shrinks or reverses.

**Enablement note.** After teaching several related-but-confusable things (index types; consistency levels; when to shard vs scale up), don't drill them one block at a time — mix them in a practice set so learners practice *diagnosing which applies*. That mirrors the real task: a customer never says "this is a sharding problem," they describe a symptom.

**Self note.** When practicing a family of confusable skills (SQL window functions, regex constructs, design patterns), shuffle them rather than grinding one type to fluency before moving on. It'll feel worse and slower — that's the desirable difficulty working. Mixed problem sets and randomized drills beat sorted ones for transfer.

---

## 5. Desirable difficulties (Bjork) — the unifying frame

**Robert & Elizabeth Bjork** coined **desirable difficulties** (1994): conditions that *slow* acquisition often *speed* long-term retention and transfer ([UNH/Bjork PDF](https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-introducing-desirable-difficulties-into-practice-and-instruction-bjork-and-bjork.pdf)). The canonical four are exactly the techniques above: **spacing, interleaving, retrieval/testing, and varying the conditions of practice.** This is the umbrella that explains *why* §§2–4 all work and all feel bad while working.

**The mechanism — New Theory of Disuse** (Bjork & Bjork, 1992): every memory has two independent strengths.
- **Storage strength** — how deeply the memory is woven into what you already know. It (essentially) only ever *increases*.
- **Retrieval strength** — how accessible it is *right now*. It fluctuates and decays with disuse.

The key dynamic: **the lower retrieval strength is when you successfully retrieve, the larger the gain in storage strength** ([Learning Scientists](https://www.learningscientists.org/blog/2016/5/10-1)). Easy, fluent retrieval (right after studying) barely strengthens storage; effortful retrieval (after a gap, mixed in with other material) strengthens it a lot. Difficulty is desirable *because* struggle-then-success is what builds durable storage.

**The critical qualifier — when difficulty is *un*desirable.** A difficulty only helps if the learner can actually *overcome* it. For someone lacking the prerequisite knowledge to succeed, the same difficulty just produces failure and load (this is exactly the **expertise-reversal effect**, §1, viewed from the learner's side). Calibrate difficulty to the **edge of current ability** — hard enough to require effort, not so hard that retrieval fails outright.

**Enablement / Self note.** When you (or a customer) complain that a method "feels inefficient" or "I keep getting it wrong in practice," that's often the *signal it's working*, not a reason to abandon it — provided success is achievable. Reserve the easy, fluent, blocked, massed approach only for the very first exposure to genuinely novel material; switch to desirable difficulties as soon as the learner can succeed at them.

---

## 6. Elaboration, dual coding, self-explanation

**Dual coding theory** (Paivio, 1971/1986): cognition runs two interconnected channels — **verbal** and **nonverbal/imagery**. Pairing a relevant picture with words gives memory two routes to the same idea, and memory for images exceeds memory for words (the "picture superiority effect") ([Dual-coding — Wikipedia](https://en.wikipedia.org/wiki/Dual-coding_theory)). **Two cautions:** (a) this means *complementary* visual + verbal, NOT "match a visual learner" — see the learning-styles myth (§10); (b) it is NOT the **redundancy** trap (§1) of duplicating the *same* info in two simultaneous streams. A good architecture diagram + spoken narration: dual coding. On-screen paragraph read aloud verbatim: redundancy.

**Self-explanation effect** (Chi et al.): learners who explain *to themselves* why a step is true learn far more.
- Chi et al. (1989, *Cognitive Science*): students who spontaneously self-explained worked physics examples vastly out-learned those who didn't.
- Chi et al. (1994): *merely prompting* eighth-graders to explain each line of a biology text aloud produced larger pre→post gains, with the "high explainers" understanding most ([PDF](https://andymatuschak.org/files/papers/Chi%20et%20al%20-%201994%20-%20Eliciting%20self-explanations%20improves%20understanding.pdf)). Self-explanation can be *induced*, not just observed.

**Elaboration / elaborative interrogation** — asking and answering "*why* is this true? how does it connect to what I already know?" — integrates new material with existing schemas (rated *moderate*-utility by Dunlosky, §10).

**Enablement note.** Pair every architecture/data-flow concept with a clean visual *and* a verbal account (dual coding) — never a wall of bullets read aloud. Build self-explanation prompts into labs: "before you run this, explain why this index will/won't be used." Ask "why" and "how does this connect to what you saw yesterday," not just "what."

**Self note.** When studying a worked example (an exemplary PR, a reference architecture), pause at each step and explain *why it's there* before reading on — that's the highest-yield way to learn from examples. Sketch a diagram of a system as you learn it; the act of externalizing into the visual channel both encodes it and surfaces the gaps you can't yet draw.

---

## 7. Metacognition — the illusion of fluency

Learners are systematically bad at judging their own learning, and they reliably steer toward the *wrong* strategies as a result. **Judgments of learning (JOLs)** — predictions of future recall — are poorly calibrated, especially in one direction.

**The illusion of fluency / illusion of competence** (Koriat & Bjork): material that is *easy to process right now* (a re-read page, a highlighted passage, a just-watched demo) feels well-learned and earns a high JOL — but **current fluency is a weak predictor of future recall** ([structural-learning](https://www.structural-learning.com/post/fluency-illusions-students-think-they-know)). This is *the* reason people choose rereading (smooth, confident) over self-testing (effortful, error-revealing): they're optimizing for the feeling, not the outcome. **Koriat's cue-utilization framework** explains it — JOLs lean on experiential cues like fluency and familiarity, which are unreliable proxies for actual memory strength.

**Stability bias** (Kornell & Bjork): people behave as if memory is static — overestimating what they'll still know later and underestimating how much *more* studying would help. **Foresight bias** (Koriat & Bjork): judging while the answer is in front of you (or right after studying) badly overestimates later *unaided* recall.

**Dunning–Kruger — use with care.** The pop framing ("incompetent people are wildly, uniquely overconfident") is contested; a substantial part of the classic chart is a statistical artifact (regression to the mean plus a general better-than-average tendency). Don't lean on a strong DK claim as established fact.

**Why this is the linchpin.** Fluency illusions are what make customers say "yeah, I've got it" right before they forget it, and what make *you* abandon the effortful methods that actually work. The fix is to **replace the feeling of knowing with a test of knowing.**

**Enablement note.** Don't trust nods, "makes sense," or smooth demo-watching as evidence of learning — they're fluency signals. Insert frequent low-stakes retrieval to give *both* of you accurate signal on what actually stuck. Warn learners explicitly that re-watching a recording feels productive but mostly builds fluency; a closed-book rebuild is the real check.

**Self note.** Distrust "I understand this" after reading — prove it with a closed-book retrieval or by teaching it. Calibrate: predict your quiz/recall score, then check the gap. Treat smoothness as a *warning*, not a green light: if learning feels effortless, you're probably not building durable memory.

---

## 8. Deliberate practice & expertise (Ericsson) — and the 10,000-hour critique

**Ericsson, Krampe & Tesch-Römer (1993)** defined **deliberate practice**: a *highly structured* activity whose explicit goal is to improve performance, operating at the **edge of current ability**, with **immediate feedback** and **focused repetition** of the weak component — not merely "doing the activity a lot" ([Royal Society Open Science replication](https://royalsocietypublishing.org/doi/10.1098/rsos.190327)). Mere experience plateaus; deliberate practice is what keeps driving improvement.

**Expertise is chunked pattern recognition, and it's domain-specific.** Chase & Simon (1973): chess masters massively out-recall novices for *real* game positions but are *no better* for *random* ones — their advantage is recognizing meaningful patterns (chunks) stored in long-term memory, not superior general memory. Expertise doesn't transfer across domains; it's built schema by schema.

**The 10,000-hour rule is overstated.** That figure was popularized by Gladwell, not claimed by Ericsson. **Macnamara et al. (2014)** meta-analysis (88 studies) found deliberate practice explained only **~26% of performance variance in games, 21% in music, 18% in sports, 4% in education, and <1% in professions** ([Princeton summary](https://www.princeton.edu/news/2014/07/03/becoming-expert-takes-more-practice)). Practice is necessary and important but **far from the whole story** — starting age, working memory, coaching quality, and task predictability all matter. A 2019 re-analysis of Ericsson's own violinist data also failed to reproduce the original effect size. (Ericsson disputed Macnamara's looser definition of "practice"; the honest synthesis: *quality* of practice matters more than a magic hour count, and practice alone doesn't fully determine expertise.)

**The durable, actionable core:** edge-of-ability tasks + immediate feedback + focused repetition on the specific weakness. That mechanism is solid; the hour count is folklore.

**Enablement note.** Move customers up a difficulty ramp (don't leave them in the comfortable zone or drop them off a cliff), and engineer **immediate, specific feedback** into labs — automated checks, instant "here's why that query is slow," not feedback a week later. Target practice at the *specific* sub-skill a customer is weak on rather than re-covering what they already do well.

**Self note.** Don't just *do* the work and expect to improve — that plateaus. Pick the specific weak sub-skill, design a focused drill at the edge of your ability, and get tight feedback loops (code review, a mentor, automated tests, replaying your own decisions against outcomes). Reflect after the rep: what specifically went wrong and what will you change. Forget the hour count; optimize the *quality* and *targeting* of practice.

---

## 9. Adult learning: andragogy & Bloom's revised taxonomy

**Knowles' andragogy** — six assumptions about adult learners ([helpfulprofessor](https://helpfulprofessor.com/principles-of-andragogy/)):
1. **Need to know** — adults want to know *why* before they invest.
2. **Self-concept** — they see themselves as self-directing, not dependent.
3. **Experience** — their prior experience is a learning *resource* (and sometimes a bias to surface).
4. **Readiness** — tied to real-life tasks and roles, not an abstract syllabus.
5. **Orientation** — **problem-centered**, not subject-centered: they want to solve *their* problem, now.
6. **Motivation** — driven more by internal payoffs (mastery, competence) than external ones.

*Critiques:* the assumptions arguably describe good practice for *all* learners (a "distinction without a difference" from pedagogy), and the model reflects a Western, individualistic, middle-class frame that fits collectivist or low-literacy contexts poorly ([Wiley, New Directions 2024](https://onlinelibrary.wiley.com/doi/full/10.1002/ace.20546)). Treat andragogy as a **design lens / heuristic**, not a tested causal theory.

**Bloom's revised taxonomy** (Anderson & Krathwohl, 2001) — six cognitive-process levels: **Remember → Understand → Apply → Analyze → Evaluate → Create**, crossed with a knowledge dimension (factual / conceptual / procedural / metacognitive) ([Krathwohl 2002 overview PDF](https://cmapspublic2.ihmc.us/rid=1Q2PTM7HL-26LTFBX-9YN8/Krathwohl%202002.pdf)). Use it as a **leveling tool**: write each learning objective with an action verb at the *intended* level, then make sure your practice and assessment hit that level. The classic failure is teaching/testing at *Remember* ("list the index types") when the real goal is *Apply* or *Analyze* ("given this workload, choose and justify an index").

**Enablement note.** Lead every module with the *why* and a real problem the customer actually has (andragogy 1, 4, 5); use their existing stack/experience as the worked example. Pitch objectives at the Bloom level that matches the job — most technical enablement should land at Apply/Analyze, so labs and checks must require *doing and deciding*, not reciting.

**Self note.** When learning something new, anchor it to a real problem you have right now (your own readiness/orientation) — it sticks better than abstract study. Be honest about which Bloom level you've actually reached: being able to *recall* a pattern (Remember) is not being able to *choose and apply* it under pressure (Apply/Analyze). Push your practice up the taxonomy deliberately.

---

## 10. The practitioner consensus — and the myths

**Dunlosky et al. (2013)**, *Improving Students' Learning With Effective Learning Techniques* (*Psychological Science in the Public Interest*) rated 10 common techniques by utility ([full PDF](https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf); [AFT summary](https://www.aft.org/ae/fall2013/dunlosky)):

| Utility | Technique |
| --- | --- |
| **High** | **Practice testing** (retrieval), **distributed practice** (spacing) |
| **Moderate** | Elaborative interrogation, self-explanation, interleaved practice |
| **Low** | Summarization, **highlighting/underlining**, keyword mnemonics, imagery-for-text, **rereading** |

The punchline: **the most popular student strategies — rereading and highlighting — are the weakest**, and the two highest-utility techniques are the two that feel hardest. **Make It Stick** (Brown, Roediger & McDaniel, 2014) is the well-grounded trade-book popularization of this evidence.

**Learning styles are a myth.** **Pashler, McDaniel, Rohrer & Bjork (2008)** reviewed the evidence for the **meshing hypothesis** (that matching instruction to a learner's preferred "style" — visual/auditory/kinesthetic, VARK — improves learning) and found **no adequate support**; later work (Nancekivell et al. 2020) shows it persists as a stubborn neuromyth ([APS journal](https://journals.sagepub.com/doi/10.1111/j.1539-6053.2009.01038.x)). People *have* preferences; teaching to them doesn't improve outcomes. **Design for the content's best modality** (a map is visual, a dialogue is auditory) and use **dual coding** (§6) — never "she's a visual learner, give her diagrams."

**Enablement / Self note.** If you do one thing with this skill: **swap rereading for self-testing and cramming for spacing.** And when someone proposes building training around learner "styles," redirect that energy to retrieval, spacing, and worked examples — it's where the evidence actually is.

---

## Quick-reference: design / diagnose checklist

When **designing** training or a personal learning plan:
- [ ] **Retrieval** built in throughout (not just a final test)? (§2)
- [ ] Sessions **spaced** across time, not massed into one firehose? (§3)
- [ ] Confusable topics **interleaved** so learners practice choosing? (§4)
- [ ] Support **matched to expertise** — worked examples for novices, faded for experts (no expertise reversal)? (§1)
- [ ] **Extraneous load** stripped (one idea per slide, integrated visuals, no read-aloud bullets)? (§1)
- [ ] Concepts **dual-coded** (visual + verbal, complementary not redundant)? (§6)
- [ ] **Self-explanation** prompts in the labs? (§6)
- [ ] **Immediate, specific feedback** at the edge of ability? (§8)
- [ ] Objectives leveled with **Bloom** to the right cognitive demand (usually Apply/Analyze, not Remember)? (§9)
- [ ] Led with the **"why" and a real problem** (andragogy)? (§9)

When **diagnosing** "the training didn't stick":
- Was it **massed** (one big session) instead of spaced? → §3
- Was it **passive** (watch/read) with no retrieval? → §2, §7
- Did learners *feel* confident but fail later? → illusion of fluency; you trusted nods over tests. → §7
- Were experts forced through novice scaffolding (or novices dropped into expert-level difficulty)? → expertise reversal / undesirable difficulty. → §1, §5
- Was everything **blocked** so learners never practiced *choosing* the right approach? → §4

## Anti-patterns

- **The firehose bootcamp** — cramming everything into one day. Worst possible schedule; maximizes forgetting. → space it (§3).
- **Trusting fluency** — taking "makes sense" / smooth demos / nodding as evidence of learning. → test it (§2, §7).
- **Lecture-only / passive** — no retrieval, no doing. Builds fluency, not memory. → §2.
- **Same deck for novices and experts** — expertise reversal wastes experts' time and overloads novices. → tier and fade support (§1).
- **Block-drilling confusable topics** — looks efficient, kills transfer and the discrimination skill. → interleave (§4).
- **Redundant dual-channel** — reading on-screen text aloud verbatim; narrating self-explanatory visuals. *Adds* load. → §1, §6.
- **Designing for "learning styles"** — no evidence; opportunity cost vs real techniques. → design for content modality + dual coding (§6, §10).
- **Counting hours** — treating 10,000 hours (or any total) as the goal instead of edge-of-ability practice with feedback. → §8.
- **Bloom-level mismatch** — teaching/testing at Remember when the job needs Apply/Analyze. → §9.

## References

Primary sources, meta-analyses, and authoritative syntheses:

1. **Sweller, J.** — Cognitive Load Theory; intrinsic/extraneous/germane load, element interactivity, worked-example & expertise-reversal effects. Overviews: [Cognitive load (Wikipedia)](https://en.wikipedia.org/wiki/Cognitive_load), [The Decision Lab](https://thedecisionlab.com/reference-guide/psychology/cognitive-load-theory), [element interactivity & load (Springer, Educ. Psych. Review)](https://link.springer.com/article/10.1007/s10648-010-9128-5), [expertise-reversal & redundancy (eLearning Industry)](https://elearningindustry.com/cognitive-load-element-interactivity-and-reversal-effect).
2. **Roediger, H. L., & Karpicke, J. D. (2006).** *The Power of Testing Memory.* Perspectives on Psychological Science, 1(3), 181–210. [PDF (WUSTL)](http://psychnet.wustl.edu/memory/wp-content/uploads/2018/04/Roediger-Karpicke-2006_PPS.pdf).
3. **Karpicke, J. D., & Blunt, J. R. (2011).** *Retrieval Practice Produces More Learning than Elaborative Studying with Concept Mapping.* Science, 331(6018), 772–775. [Science](https://www.science.org/doi/10.1126/science.1199327).
4. **Cepeda, N. J., et al. (2006).** *Distributed Practice in Verbal Recall Tasks: A Review and Quantitative Synthesis.* Psychological Bulletin. [PDF](https://augmentingcognition.com/assets/Cepeda2006.pdf). Spacing scaled to retention interval.
5. **Ebbinghaus, H. (1885)** forgetting curve; replicated by **Murre & Dros (2015)**. [Forgetting curve (Wikipedia)](https://en.wikipedia.org/wiki/Forgetting_curve); [precision critique (Hendrick)](https://carlhendrick.substack.com/p/why-the-forgetting-curve-is-not-as).
6. **Rohrer, D., & Taylor, K. (2007)** & Rohrer et al. (2014/2015) — interleaved mathematics practice. [Rohrer interleaving guide (PDF)](http://uweb.cas.usf.edu/~drohrer/pdfs/Interleaved_Mathematics_Practice_Guide.pdf).
7. **Discriminative-contrast hypothesis** — Birnbaum et al. (2013), [Memory & Cognition (Springer)](https://link.springer.com/article/10.3758/s13421-012-0272-7); spacing vs interleaving distinct bases, [Educ. Psych. Review (2021)](https://link.springer.com/article/10.1007/s10648-021-09613-w).
8. **Bjork, R. A., & Bjork, E. L.** — desirable difficulties; New Theory of Disuse (storage vs retrieval strength, 1992). [Bjork & Bjork, "Introducing Desirable Difficulties" (UNH PDF)](https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-introducing-desirable-difficulties-into-practice-and-instruction-bjork-and-bjork.pdf); [storage vs retrieval strength (Learning Scientists)](https://www.learningscientists.org/blog/2016/5/10-1).
9. **Paivio, A. (1971/1986)** — dual coding theory. [Dual-coding theory (Wikipedia)](https://en.wikipedia.org/wiki/Dual-coding_theory).
10. **Chi, M. T. H., et al. (1989, 1994)** — self-explanation effect. [Chi et al. 1994, "Eliciting self-explanations improves understanding" (PDF)](https://andymatuschak.org/files/papers/Chi%20et%20al%20-%201994%20-%20Eliciting%20self-explanations%20improves%20understanding.pdf).
11. **Koriat, A., & Bjork, R. A.** — illusion of fluency, JOLs, foresight/stability bias. [Fluency illusions (structural-learning)](https://www.structural-learning.com/post/fluency-illusions-students-think-they-know).
12. **Ericsson, K. A., Krampe, R. T., & Tesch-Römer, C. (1993)** — deliberate practice; revisited by **Macnamara, Hambrick, & Oswald (2014)** meta-analysis. [1993 replication & re-analysis (Royal Society Open Science)](https://royalsocietypublishing.org/doi/10.1098/rsos.190327); [Macnamara 2014 summary (Princeton)](https://www.princeton.edu/news/2014/07/03/becoming-expert-takes-more-practice). **Chase & Simon (1973)** expert chunking.
13. **Knowles, M.** — andragogy & critiques. [Six principles (helpfulprofessor)](https://helpfulprofessor.com/principles-of-andragogy/); [critique (Wiley, New Directions 2024)](https://onlinelibrary.wiley.com/doi/full/10.1002/ace.20546).
14. **Anderson, L. W., & Krathwohl, D. R. (2001)** — revised Bloom's taxonomy. [Krathwohl 2002 overview (PDF)](https://cmapspublic2.ihmc.us/rid=1Q2PTM7HL-26LTFBX-9YN8/Krathwohl%202002.pdf).
15. **Dunlosky, J., et al. (2013).** *Improving Students' Learning With Effective Learning Techniques.* Psychological Science in the Public Interest, 14(1), 4–58. [Full PDF](https://www.whz.de/fileadmin/lehre/hochschuldidaktik/docs/dunloskiimprovingstudentlearning.pdf); [AFT summary](https://www.aft.org/ae/fall2013/dunlosky). **Brown, Roediger & McDaniel (2014)**, *Make It Stick*.
16. **Pashler, H., McDaniel, M., Rohrer, D., & Bjork, R. (2008).** *Learning Styles: Concepts and Evidence.* PSPI. [APS journal](https://journals.sagepub.com/doi/10.1111/j.1539-6053.2009.01038.x). The meshing hypothesis is unsupported.

---

## Embedded reusable prompt: enablement-design / learning-plan review

Use this to apply the science to a concrete training plan, workshop, lab, or personal learning goal. Fill the brackets and run it.

```
You are an applied learning scientist. Using the evidence base in learning-and-expertise-psychology
(Cognitive Load Theory, retrieval practice, spacing, interleaving, desirable difficulties, dual
coding, self-explanation, metacognition/illusion of fluency, deliberate practice, andragogy,
Bloom's revised taxonomy, Dunlosky 2013), review the following.

CONTEXT
- Audience & prior expertise (novice / intermediate / expert): [....]
- What they must be able to DO afterward (the real on-the-job task): [....]
- Current plan / format / schedule: [....]
- Constraints (time, async vs live, single session vs multi-touch): [....]

PRODUCE
1. Bloom level check — what cognitive level does the goal actually require (usually Apply/Analyze),
   and does the current plan teach & assess at that level? Flag any Remember-level mismatch.
2. Cognitive load — is support matched to expertise (worked examples for novices, faded for experts;
   no expertise-reversal)? Where is extraneous load (clutter, split attention, redundant read-aloud)
   that should be cut?
3. Desirable difficulties — concrete edits to add RETRIEVAL (not just a final test), SPACING (break
   the firehose into spaced touchpoints), and INTERLEAVING (mix confusable topics so learners
   practice choosing). Note where the plan is currently passive, massed, or blocked.
4. Dual coding & self-explanation — where to pair visual+verbal (complementary, not redundant) and
   add "explain why before you act" prompts.
5. Feedback & deliberate practice — is feedback immediate and specific, targeting the weak sub-skill
   at the edge of ability?
6. Fluency-illusion guardrails — how will you (and they) get TRUE signal on retention rather than
   trusting nods / smooth demos? Add low-stakes recall checkpoints.
7. Myth check — is anything built on learning styles or an hour-count goal? Redirect to evidence-based
   techniques.

Output a prioritized, specific edit list (highest learning-impact first). Cite the relevant principle
(e.g., "spacing — Cepeda 2006") for each recommendation. Be concrete, not generic.
```

**Self-development variant:** replace CONTEXT with *"Skill I'm building: [...]; my current level: [...]; how I currently practice: [...]"* and ask the same model to design a deliberate-practice plan — edge-of-ability drills, a spaced + interleaved schedule, retrieval/self-explanation routines, feedback loops, and fluency-illusion guardrails (predict-then-check calibration).

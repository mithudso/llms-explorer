"""Topics, coverage and gaps over a pool of units.

This is the module that answers component 19's actual promise: *give it an
arbitrary amount of loosely related material and it produces the most
comprehensive coverage that material supports.* "Most comprehensive" has to be a
number or it is marketing, so this module defines one, and defines it so that it
behaves the way the promise implies:

* **Breadth pays.** Adding material about something the corpus did not previously
  discuss creates a topic where there was none, and the score rises.
* **Depth pays.** Adding material about something already present thickens an
  existing topic — more units, more independent sources, a definition where
  there was only assertion — and the score rises.
* **Noise does not pay.** Adding a near-duplicate of what is already there is
  merged upstream in :mod:`llmsx.units` and moves nothing. Adding a page of
  boilerplate creates terms that appear once, in one source, and the term-level
  weighting discounts them toward zero.
* **Nothing is rewarded for being unsourced.** Every quantity below counts
  *distinct sources*, never units alone, so one verbose document cannot fake the
  corroboration that two documents agreeing represents.

Mechanically it is TF-IDF over unit tokens, phrase seeding from real headings,
nearest-seed assignment, then agglomeration of seeds that turned out to be the
same topic. No embeddings, no model, no dependency — the same reasoning
:mod:`llmsx.units` records. A metered pass can improve topic *names* and
reassign genuinely ambiguous units later; it cannot be required to get a result,
because the free tier has to produce one.

The vocabulary of the report is deliberately the lint rubric's: a topic under
threshold is a **gap** with a severity, so the coverage report and the llms
findings report speak the same language to the same reader.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .ingest import slugify
from .units import STOPWORDS, Unit, UnitPool

# --- the thresholds a gap is measured against ---------------------------------
#
# Component 02 §6 already states the editorial rule the wizard shows a user:
# "each section needs >= 3 facts and >= 1 definition". These are that rule, as
# numbers, plus the source-diversity floor this module adds.

#: A topic with fewer units than this is not a topic; it is a stray heading.
MIN_TOPIC_UNITS = 3
#: Below this a topic asserts things without ever saying what they are.
MIN_TOPIC_DEFINITIONS = 1
#: Below this a topic is one document's opinion, not the corpus's.
MIN_TOPIC_SOURCES = 2
#: A topic bigger than this is doing two jobs and should be split.
MAX_TOPIC_UNITS = 120
#: Below this many distinct sources the corpus is too small for its score to be
#: read as anything but "these few documents are well organised". `analyse`
#: emits a gap saying so rather than letting the headline number imply more.
MIN_CORPUS_SOURCES = 5

#: Seeds whose token sets overlap by at least this are the same topic.
SEED_MERGE_JACCARD = 0.55
#: A heading repeated across at least this share of the corpus's documents is a
#: *template* heading — "Purpose", "3. Inputs → outputs", "Open questions" — not
#: a subject. Seeding on one is actively harmful: the units beneath it in twenty
#: documents are about twenty different things, and the resulting "topic" is a
#: filing cabinet drawer rather than a subject. Only applied once the corpus is
#: big enough for the share to mean something.
TEMPLATE_HEADING_SHARE = 0.30
MIN_DOCS_FOR_TEMPLATE_TEST = 5
#: A unit scoring below this against every seed is unassigned — an honest
#: "nothing here covers it" rather than a forced fit into the nearest topic.
MIN_ASSIGN_SCORE = 0.02

#: Weight of the three things a topic can be strong at, in `Topic.depth`.
DEPTH_WEIGHTS: Mapping[str, float] = {"units": 0.4, "sources": 0.35, "kinds": 0.25}
#: Where each component of `Topic.depth` saturates. Set well above the `MIN_*`
#: floors on purpose: the floors say "this is not broken", the targets say "this
#: is genuinely well covered", and a score that reached 1.00 at the floor would
#: tell a reader nothing about the difference.
DEPTH_TARGETS: Mapping[str, int] = {"units": 20, "sources": 6, "kinds": 6}

_PHRASE_SPLIT_RE = re.compile(r"[^\w+#.]+")
#: Leading enumeration on a heading: "4. ", "P2 ", "Step 3 — ", "12) ".
_ENUMERATION_RE = re.compile(
    r"^\s*(?:(?:step|task|part|pass|section|appendix)\s+)?[A-Za-z]?\d{1,3}[.):\s]+\s*",
    re.IGNORECASE,
)


def strip_enumeration(heading: str) -> str:
    """``"4. Reading an index"`` → ``"Reading an index"``.

    The number is the document's own ordering, not part of the subject, and
    leaving it in produces topic slugs like ``4-reading-an-index`` that sort by
    an accident of where the heading happened to appear.
    """
    stripped = _ENUMERATION_RE.sub("", heading).strip()
    return stripped or heading.strip()


# --- vocabulary ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Term:
    """One vocabulary term of the corpus, with the evidence behind it."""

    term: str
    #: Units mentioning it.
    frequency: int
    #: Distinct sources mentioning it — the number that resists one loud document.
    sources: int
    #: tf-idf weight; high means "distinctive here", not merely "common here".
    weight: float

    @property
    def corroborated(self) -> bool:
        return self.sources >= MIN_TOPIC_SOURCES


def build_vocabulary(pool: UnitPool) -> dict[str, Term]:
    """Every content term in the pool, weighted by tf-idf and source spread.

    The IDF is over *units*, not documents, because a corpus of loosely related
    material has wildly uneven document sizes and a per-document IDF would let
    one long file dominate the vocabulary of everything.
    """
    total = max(len(pool.units), 1)
    frequency: Counter[str] = Counter()
    sources: defaultdict[str, set[str]] = defaultdict(set)
    for unit in pool.units:
        for token in unit.tokens:
            frequency[token] += 1
            sources[token].add(unit.source)
    out: dict[str, Term] = {}
    for token, count in frequency.items():
        idf = math.log(total / count) + 1.0
        out[token] = Term(term=token, frequency=count, sources=len(sources[token]),
                          weight=count * idf / total)
    return out


def _unit_weights(unit: Unit, vocabulary: Mapping[str, Term]) -> dict[str, float]:
    """The unit as a sparse tf-idf vector, L2-normalised.

    Normalising matters: without it a long unit outscores a short one against
    every seed simply for having more tokens, and every topic fills up with the
    corpus's longest paragraphs.
    """
    weights = {t: vocabulary[t].weight for t in unit.tokens if t in vocabulary}
    norm = math.sqrt(sum(w * w for w in weights.values())) or 1.0
    return {t: w / norm for t, w in weights.items()}


# --- topics ---------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Topic:
    """A cluster of units the corpus talks about as one subject."""

    slug: str
    name: str
    #: The terms that define it, most distinctive first.
    terms: Sequence[str]
    units: Sequence[Unit]
    #: Headings that seeded it, kept so a reader can see where the name came from.
    seeds: Sequence[str] = field(default_factory=tuple)

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(u.source for u in self.units))

    @property
    def kinds(self) -> set[str]:
        return {u.type for u in self.units}

    def count(self, type_: str) -> int:
        return sum(1 for u in self.units if u.type == type_)

    @property
    def depth(self) -> float:
        """0–1: how well supported this topic is.

        Three components, each saturating: enough units, enough independent
        sources, enough *kinds* of unit. The third is what separates a topic
        that is genuinely covered — it has a definition, some facts, something
        actionable — from one that is twelve restatements of a single claim.
        """
        units = min(len(self.units) / DEPTH_TARGETS["units"], 1.0)
        sources = min(len(self.sources) / DEPTH_TARGETS["sources"], 1.0)
        kinds = min(len(self.kinds) / DEPTH_TARGETS["kinds"], 1.0)
        return round(
            units * DEPTH_WEIGHTS["units"]
            + sources * DEPTH_WEIGHTS["sources"]
            + kinds * DEPTH_WEIGHTS["kinds"],
            4,
        )


def _seed_phrases(pool: UnitPool,
                  vocabulary: Mapping[str, Term]) -> list[tuple[str, frozenset[str]]]:
    """Candidate topics: the corpus's own headings, then its distinctive terms.

    Headings first because a heading is the author telling us a subject exists,
    which is better evidence than any statistic. Terms fill in the subjects that
    are discussed everywhere but titled nowhere — the usual shape of notes.
    """
    heading_counts: Counter[str] = Counter()
    heading_sources: defaultdict[str, set[str]] = defaultdict(set)
    documents: set[str] = set()
    for unit in pool.units:
        documents.add(unit.source)
        if unit.heading:
            name = strip_enumeration(unit.heading)
            heading_counts[name] += 1
            heading_sources[name].add(unit.source)

    # The template test: a heading that shows up across a large share of the
    # corpus's documents is the documents' skeleton, not one of their subjects.
    template_floor = (
        len(documents) * TEMPLATE_HEADING_SHARE
        if len(documents) >= MIN_DOCS_FOR_TEMPLATE_TEST
        else float("inf")
    )

    seeds: list[tuple[str, frozenset[str]]] = []
    seen: set[frozenset[str]] = set()
    for heading, count in heading_counts.most_common():
        if len(heading_sources[heading]) >= template_floor:
            continue
        tokens = frozenset(
            t.lower() for t in _PHRASE_SPLIT_RE.split(heading)
            if len(t) > 2 and t.lower() not in STOPWORDS
        ) & set(vocabulary)
        if not tokens or tokens in seen or count < 2:
            continue
        seen.add(tokens)
        seeds.append((heading.strip(), tokens))

    # Distinctive, corroborated terms that no heading already covers.
    covered = frozenset().union(*(t for _, t in seeds)) if seeds else frozenset()
    ranked = sorted(
        (t for t in vocabulary.values() if t.corroborated and t.frequency >= MIN_TOPIC_UNITS),
        key=lambda t: (-t.weight, t.term),
    )
    for term in ranked:
        if term.term in covered:
            continue
        tokens = frozenset({term.term})
        if tokens in seen:
            continue
        seen.add(tokens)
        seeds.append((term.term, tokens))
    return seeds


def _merge_seeds(seeds: Sequence[tuple[str, frozenset[str]]]
                 ) -> list[tuple[str, frozenset[str], list[str]]]:
    """Collapse seeds whose token sets are effectively the same subject."""
    merged: list[tuple[str, set[str], list[str]]] = []
    for name, tokens in seeds:
        for n, (existing_name, existing_tokens, names) in enumerate(merged):
            union = tokens | existing_tokens
            if union and len(tokens & existing_tokens) / len(union) >= SEED_MERGE_JACCARD:
                merged[n] = (existing_name, existing_tokens | tokens, [*names, name])
                break
        else:
            merged.append((name, set(tokens), [name]))
    return [(name, frozenset(tokens), names) for name, tokens, names in merged]


def _name_topic(seed_name: str, terms: Sequence[str]) -> str:
    """A human-readable topic name.

    A heading seed keeps its heading — the author already named it. A term seed
    is titled from its two strongest terms, which reads as a subject rather than
    a keyword.
    """
    seed_name = strip_enumeration(seed_name)
    if " " in seed_name or seed_name.istitle():
        return seed_name
    head = [t for t in terms[:2]]
    return " ".join(word.capitalize() if word.islower() else word for word in head) or seed_name


def build_topics(pool: UnitPool, *, max_topics: int = 40) -> tuple[list[Topic], list[Unit]]:
    """Cluster the pool into topics. Returns ``(topics, unassigned)``.

    ``unassigned`` is deliberately returned rather than swept into an "other"
    bucket: it is the honest measure of how much of the material the topic model
    could not place, and component 19's report prints it.
    """
    if not pool.units:
        return [], []
    vocabulary = build_vocabulary(pool)
    seeds = _merge_seeds(_seed_phrases(pool, vocabulary))[:max_topics]
    if not seeds:
        return [], list(pool.units)

    seed_vectors: list[dict[str, float]] = []
    for _, tokens, _ in seeds:
        weights = {t: vocabulary[t].weight for t in tokens if t in vocabulary}
        norm = math.sqrt(sum(w * w for w in weights.values())) or 1.0
        seed_vectors.append({t: w / norm for t, w in weights.items()})

    buckets: list[list[Unit]] = [[] for _ in seeds]
    unassigned: list[Unit] = []
    for unit in pool.units:
        weights = _unit_weights(unit, vocabulary)
        best, best_score = -1, 0.0
        for n, vector in enumerate(seed_vectors):
            score = sum(w * vector.get(t, 0.0) for t, w in weights.items())
            if score > best_score:
                best, best_score = n, score
        if best < 0 or best_score < MIN_ASSIGN_SCORE:
            unassigned.append(unit)
        else:
            buckets[best].append(unit)

    topics: list[Topic] = []
    used_slugs: set[str] = set()
    for (seed_name, tokens, names), units in zip(seeds, buckets, strict=True):
        if not units:
            continue
        ranked = sorted(tokens, key=lambda t: (-vocabulary[t].weight, t))
        name = _name_topic(seed_name, ranked)
        slug = slugify(name) or f"topic-{len(topics) + 1}"
        while slug in used_slugs:
            slug = f"{slug}-{len(used_slugs)}"
        used_slugs.add(slug)
        topics.append(Topic(slug=slug, name=name, terms=tuple(ranked[:12]),
                            units=tuple(units), seeds=tuple(names)))

    topics.sort(key=lambda t: (-len(t.units), t.name))
    return topics, unassigned


# --- the report -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Gap:
    """A place the corpus is thin, in the findings vocabulary of the lint rubric."""

    topic: str
    kind: str
    severity: str
    message: str
    #: What would close it, phrased as material to add rather than a code fix.
    remedy: str


@dataclass(frozen=True, slots=True)
class CoverageReport:
    """What the corpus covers, how well, and where it is thin."""

    topics: Sequence[Topic]
    unassigned: Sequence[Unit]
    gaps: Sequence[Gap]
    vocabulary_size: int
    #: Fraction of weighted vocabulary represented in at least one topic.
    breadth: float
    #: Mean topic depth, weighted by topic size.
    depth: float
    #: The headline number. See :func:`score`.
    comprehensiveness: float
    sources: int
    units: int

    @property
    def high_gaps(self) -> list[Gap]:
        return [g for g in self.gaps if g.severity == "high"]

    def as_dict(self) -> dict[str, object]:
        return {
            "comprehensiveness": self.comprehensiveness,
            "breadth": self.breadth,
            "depth": self.depth,
            "units": self.units,
            "sources": self.sources,
            "vocabulary": self.vocabulary_size,
            "unassigned": len(self.unassigned),
            "topics": [
                {"slug": t.slug, "name": t.name, "units": len(t.units),
                 "sources": len(t.sources), "kinds": sorted(t.kinds),
                 "depth": t.depth, "terms": list(t.terms)}
                for t in self.topics
            ],
            "gaps": [
                {"topic": g.topic, "kind": g.kind, "severity": g.severity,
                 "message": g.message, "remedy": g.remedy}
                for g in self.gaps
            ],
        }


def _gaps_for(topic: Topic) -> list[Gap]:
    out: list[Gap] = []
    if len(topic.units) < MIN_TOPIC_UNITS:
        out.append(Gap(topic.slug, "thin", "high",
                       f"{len(topic.units)} units, under the {MIN_TOPIC_UNITS} floor",
                       "add material on this subject, or fold it into a neighbour"))
    if topic.count("definition") < MIN_TOPIC_DEFINITIONS:
        out.append(Gap(topic.slug, "undefined", "medium",
                       "nothing in this topic says what its subject is",
                       "add a sentence of the form 'X is …' to any source"))
    if len(topic.sources) < MIN_TOPIC_SOURCES:
        out.append(Gap(topic.slug, "single-source", "medium",
                       f"only {len(topic.sources)} source covers this",
                       "add a second, independent document on the subject"))
    if len(topic.units) > MAX_TOPIC_UNITS:
        out.append(Gap(topic.slug, "oversized", "low",
                       f"{len(topic.units)} units is two subjects in one topic",
                       "split it, or narrow the terms that define it"))
    if not topic.kinds & {"fact", "parameter", "snippet"}:
        out.append(Gap(topic.slug, "unevidenced", "low",
                       "no facts, parameters or snippets — assertion only",
                       "add a number, a parameter table or an example"))
    return out


def score(topics: Sequence[Topic], unassigned: Sequence[Unit],
          vocabulary: Mapping[str, Term]) -> tuple[float, float, float]:
    """``(comprehensiveness, breadth, depth)``, each 0–1.

    *Breadth* is the share of the corpus's **weighted vocabulary** that appears
    in a unit some topic actually placed. Weighted by tf-idf, so a term used
    once in one source cannot drag the number down as far as a term the corpus
    is built around; measured over placed units rather than over topic term
    lists, because the term list is a label and the units are the coverage.
    Unplaced units are exactly what this misses, which is the honest way for
    them to cost something.

    *Depth* is the mean of :attr:`Topic.depth` weighted by topic size, so a
    corpus of many thin topics does not read as well covered as one with the
    same number of units concentrated where they corroborate each other.

    *Comprehensiveness* is the geometric mean of breadth, depth and a third
    factor the other two barely see: **placement**, the share of units a topic
    could actually claim. Placement is not a restatement of breadth — a unit
    that fits no topic usually shares its vocabulary with units that do, so
    breadth stays high while a quarter of the material sits in no file anybody
    will read. They are two different deficiencies and both are worth naming.

    Geometric rather than arithmetic on all three, on purpose: breadth with no
    depth is a keyword list, depth with no breadth is one essay, and either with
    no placement is a well-organised minority of what was uploaded. Nothing
    should be able to score well by being excellent at one third of the job.
    """
    if not topics:
        return 0.0, 0.0, 0.0
    total_weight = sum(t.weight for t in vocabulary.values()) or 1.0
    covered: set[str] = set()
    for topic in topics:
        for unit in topic.units:
            covered |= unit.tokens
    breadth = sum(vocabulary[t].weight for t in covered if t in vocabulary) / total_weight

    unit_total = sum(len(t.units) for t in topics) or 1
    depth = sum(t.depth * len(t.units) for t in topics) / unit_total
    placement = unit_total / (unit_total + len(unassigned))

    product = max(breadth, 0.0) * max(depth, 0.0) * max(placement, 0.0)
    comprehensiveness = product ** (1 / 3)
    return round(comprehensiveness, 4), round(breadth, 4), round(depth, 4)


def analyse(pool: UnitPool, *, max_topics: int = 40) -> CoverageReport:
    """The full coverage report for a unit pool."""
    vocabulary = build_vocabulary(pool)
    topics, unassigned = build_topics(pool, max_topics=max_topics)
    gaps = [gap for topic in topics for gap in _gaps_for(topic)]
    # Comprehensiveness is coverage *of the supplied material*, not of the
    # subject as it exists in the world — a corpus of three notes can score well
    # by being three notes that are fully organised. Left unsaid, that number is
    # read as the second thing. So a small corpus says so, in the report, next to
    # the score, every time.
    if pool.sources and len(pool.sources) < MIN_CORPUS_SOURCES:
        gaps.append(Gap("*", "small-corpus", "medium",
                        f"{len(pool.sources)} sources: the score measures how well this "
                        "material is covered, not how well the subject is",
                        f"add material from at least {MIN_CORPUS_SOURCES} independent "
                        "documents before reading the score as a subject verdict"))
    if unassigned and topics:
        share = len(unassigned) / (len(unassigned) + sum(len(t.units) for t in topics))
        if share >= 0.25:
            gaps.append(Gap("*", "unplaced", "medium",
                            f"{len(unassigned)} units ({share:.0%}) fit no topic",
                            "the material may be too heterogeneous; raise max_topics "
                            "or split the corpus"))
    comprehensiveness, breadth, depth = score(topics, unassigned, vocabulary)
    return CoverageReport(
        topics=tuple(topics), unassigned=tuple(unassigned), gaps=tuple(gaps),
        vocabulary_size=len(vocabulary), breadth=breadth, depth=depth,
        comprehensiveness=comprehensiveness,
        sources=len(pool.sources), units=len(pool.units),
    )


__all__ = [
    "DEPTH_TARGETS",
    "DEPTH_WEIGHTS",
    "MAX_TOPIC_UNITS",
    "MIN_ASSIGN_SCORE",
    "MIN_CORPUS_SOURCES",
    "MIN_TOPIC_DEFINITIONS",
    "MIN_TOPIC_SOURCES",
    "MIN_TOPIC_UNITS",
    "SEED_MERGE_JACCARD",
    "TEMPLATE_HEADING_SHARE",
    "CoverageReport",
    "Gap",
    "Term",
    "Topic",
    "analyse",
    "build_topics",
    "build_vocabulary",
    "score",
    "strip_enumeration",
]

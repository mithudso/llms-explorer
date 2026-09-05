"""Topics out to delineated markdown files — one per topic, or grouped into categories.

This is the deliverable behind component 19's plainest promise: throw documents
at it and get back *useful, delineated, structured markdown files on specific
topics, or divided into categories*. Everything upstream computed what the
corpus says; this module decides what the files look like.

Three properties the layout holds to, none of them cosmetic:

1. **Every line is anchored.** A unit is written as its text followed by the URL
   and heading it came from. That is the same grammar the llms facts file uses
   (``- [type] text — url#anchor``), so a reader who follows a line lands on the
   sentence in the original, and a lint pass over the output can check it.
2. **Sections are unit kinds, in reading order.** Definitions first, because a
   reader needs to know what a thing is before what is true of it; then facts,
   parameters, actionables, snippets, questions, problems, ideas, quotes,
   statements. Order is fixed in :data:`SECTION_ORDER` rather than being
   whatever the type happened to be encountered in.
3. **The index tells the truth about coverage.** The generated ``README.md``
   carries the depth of each topic and the gap list — including the topics the
   corpus barely covers. A catalogue that lists only the strong topics is how a
   reader ends up trusting a thin file.

Categories exist because forty topic files is a directory nobody reads. Grouping
is agglomerative over topic term overlap: topics that share vocabulary end up in
the same category, the category is named from the terms its members actually
share, and a category of one is left as a top-level file rather than a folder
containing a single thing.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .coverage import CoverageReport, Topic
from .ingest import slugify
from .tokens import estimate
from .units import Unit

#: Reading order of the per-topic sections. Rule 2 of the module docstring.
SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("definition", "Definitions"),
    ("concept", "Concepts"),
    ("fact", "Facts"),
    ("parameter", "Parameters and fields"),
    ("actionable", "How to"),
    ("snippet", "Examples"),
    ("change", "Changes"),
    ("problem", "Problems and failure modes"),
    ("question", "Open questions"),
    ("idea", "Ideas"),
    ("quote", "Quotes"),
    ("statement", "Notes"),
)

#: Topics sharing at least this share of their terms land in one category.
CATEGORY_MERGE_JACCARD = 0.18
#: Below this many topics, categories are noise; the flat layout is used.
MIN_TOPICS_FOR_CATEGORIES = 6


@dataclass(frozen=True, slots=True)
class OutputFile:
    """One generated file: a relative path and its whole text.

    Returned rather than written, so the same function serves the CLI (which
    writes to disk), the API (which streams a zip or a JSON body) and the tests
    (which assert on text without a temporary directory).
    """

    path: str
    text: str

    @property
    def tokens(self) -> int:
        return estimate(self.text)

    @property
    def bytes(self) -> int:
        return len(self.text.encode("utf-8"))


@dataclass(frozen=True, slots=True)
class Category:
    """A group of topics that share vocabulary."""

    slug: str
    name: str
    topics: Sequence[Topic]
    shared_terms: Sequence[str] = field(default_factory=tuple)

    @property
    def units(self) -> int:
        return sum(len(t.units) for t in self.topics)


def _fmt_unit(unit: Unit) -> str:
    """One unit as an anchored markdown line, facts-file grammar.

    A snippet keeps its fence and puts the source underneath: inlining a code
    block into a bullet destroys the indentation the code depends on.
    """
    if unit.type == "snippet":
        lang = unit.language or ""
        label = unit.heading or unit.document
        return f"```{lang}\n{unit.text}\n```\n\n<sub>Source: [{label}]({unit.url})</sub>"
    text = unit.text.rstrip(" .") if unit.text.endswith("..") else unit.text
    return f"- {text} — [{unit.heading or unit.document}]({unit.url})"


def _section(units: Sequence[Unit], title: str) -> list[str]:
    if not units:
        return []
    out = [f"## {title}", ""]
    for unit in units:
        out.append(_fmt_unit(unit))
        out.append("")
    return out


def render_topic(topic: Topic, report: CoverageReport, *, generated: str) -> str:
    """One topic as a standalone markdown document."""
    gaps = [g for g in report.gaps if g.topic == topic.slug]
    lines = [
        f"# {topic.name}",
        "",
        f"{len(topic.units)} units from {len(topic.sources)} "
        f"source{'s' if len(topic.sources) != 1 else ''}; "
        f"depth {topic.depth:.2f}. Generated {generated}.",
        "",
    ]
    if topic.terms:
        lines += [f"**Vocabulary:** {', '.join(topic.terms)}", ""]
    if gaps:
        lines += ["> **Coverage gaps in this topic**", ">"]
        lines += [f"> - _{g.severity}_ — {g.message}. {g.remedy}." for g in gaps]
        lines += [""]
    for type_, title in SECTION_ORDER:
        lines += _section([u for u in topic.units if u.type == type_], title)
    lines += ["## Sources", ""]
    lines += [f"- {source}" for source in topic.sources]
    lines += [""]
    return "\n".join(lines).rstrip() + "\n"


def _shared_terms(topics: Sequence[Topic]) -> list[str]:
    """Terms more than one member topic uses, most widely shared first."""
    counts: dict[str, int] = {}
    for topic in topics:
        for term in topic.terms:
            counts[term] = counts.get(term, 0) + 1
    return [t for t, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])) if n > 1]


def build_categories(topics: Sequence[Topic]) -> list[Category]:
    """Group topics that share vocabulary. One-topic groups stay ungrouped.

    Agglomerative and greedy, in topic-size order: the biggest topic anchors a
    category and smaller ones join the first category they overlap enough with.
    Deterministic because the input order is deterministic, which matters more
    here than finding an optimal partition nobody would notice.
    """
    groups: list[list[Topic]] = []
    for topic in topics:
        terms = frozenset(topic.terms)
        for group in groups:
            group_terms = frozenset(t for member in group for t in member.terms)
            union = terms | group_terms
            if union and len(terms & group_terms) / len(union) >= CATEGORY_MERGE_JACCARD:
                group.append(topic)
                break
        else:
            groups.append([topic])

    out: list[Category] = []
    used: set[str] = set()
    for group in groups:
        shared = _shared_terms(group)
        name = (" and ".join(t.capitalize() for t in shared[:2]) if shared
                else group[0].name)
        slug = slugify(name) or f"category-{len(out) + 1}"
        while slug in used:
            slug = f"{slug}-{len(used)}"
        used.add(slug)
        out.append(Category(slug=slug, name=name, topics=tuple(group),
                            shared_terms=tuple(shared[:8])))
    out.sort(key=lambda c: (-c.units, c.name))
    return out


def _readme(report: CoverageReport, layout: Mapping[str, str], *, subject: str,
            generated: str, categories: Sequence[Category] | None) -> str:
    """The index: what is here, how well covered, and what is thin."""
    lines = [
        f"# {subject}",
        "",
        f"{report.units} knowledge units from {report.sources} sources, organised into "
        f"{len(report.topics)} topics"
        + (f" across {len(categories)} categories" if categories else "")
        + f". Generated {generated}.",
        "",
        "## Coverage",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Comprehensiveness | {report.comprehensiveness:.2f} |",
        f"| Breadth (vocabulary covered) | {report.breadth:.2f} |",
        f"| Depth (mean, size-weighted) | {report.depth:.2f} |",
        f"| Units placed | {report.units - len(report.unassigned)} of {report.units} |",
        f"| Distinct sources | {report.sources} |",
        f"| Vocabulary terms | {report.vocabulary_size} |",
        "",
    ]
    if categories:
        for category in categories:
            lines += [f"## {category.name}", ""]
            if category.shared_terms:
                lines += [f"_Shared vocabulary: {', '.join(category.shared_terms)}._", ""]
            lines += ["| Topic | Units | Sources | Depth |", "|---|---|---|---|"]
            for topic in category.topics:
                lines.append(
                    f"| [{topic.name}]({layout[topic.slug]}) | {len(topic.units)} "
                    f"| {len(topic.sources)} | {topic.depth:.2f} |"
                )
            lines.append("")
    else:
        lines += ["## Topics", "", "| Topic | Units | Sources | Depth |", "|---|---|---|---|"]
        for topic in report.topics:
            lines.append(
                f"| [{topic.name}]({layout[topic.slug]}) | {len(topic.units)} "
                f"| {len(topic.sources)} | {topic.depth:.2f} |"
            )
        lines.append("")

    if report.gaps:
        lines += ["## Gaps", "",
                  "What this corpus does not yet cover well. Adding material that "
                  "closes one of these raises the comprehensiveness score; adding "
                  "more of what is already here does not.", "",
                  "| Severity | Topic | Gap | What would close it |", "|---|---|---|---|"]
        for gap in sorted(report.gaps, key=lambda g: ("high", "medium", "low").index(g.severity)):
            lines.append(f"| {gap.severity} | {gap.topic} | {gap.message} | {gap.remedy} |")
        lines.append("")
    if report.unassigned:
        lines += [
            f"## Unplaced ({len(report.unassigned)})", "",
            "Units no topic could claim. They are listed rather than discarded: "
            "material that fits nothing is either a subject the corpus has only "
            "one sentence of, or evidence the corpus is really two corpora.", "",
        ]
        lines += [_fmt_unit(u) for u in report.unassigned[:50]]
        if len(report.unassigned) > 50:
            lines.append(f"\n_…and {len(report.unassigned) - 50} more._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def organize(report: CoverageReport, *, subject: str = "Corpus",
             categorise: bool | None = None,
             generated: str | None = None) -> list[OutputFile]:
    """The whole organised set: one file per topic plus an index.

    ``categorise=None`` decides by size — categories below
    :data:`MIN_TOPICS_FOR_CATEGORIES` topics are more structure than the reader
    gains. Pass ``True`` or ``False`` to force it.
    """
    stamp = generated or dt.datetime.now(dt.UTC).date().isoformat()
    if not report.topics:
        return [OutputFile("README.md", _readme(report, {}, subject=subject,
                                                generated=stamp, categories=None))]

    use_categories = (len(report.topics) >= MIN_TOPICS_FOR_CATEGORIES
                      if categorise is None else categorise)
    categories = build_categories(report.topics) if use_categories else None
    if categories is not None and len(categories) < 2:
        # One category is the flat layout with an extra directory level.
        categories = None

    layout: dict[str, str] = {}
    files: list[OutputFile] = []
    if categories is None:
        for n, topic in enumerate(report.topics, start=1):
            path = f"{n:02d}-{topic.slug}.md"
            layout[topic.slug] = path
            files.append(OutputFile(path, render_topic(topic, report, generated=stamp)))
    else:
        for category in categories:
            for n, topic in enumerate(category.topics, start=1):
                path = f"{category.slug}/{n:02d}-{topic.slug}.md"
                layout[topic.slug] = path
                files.append(OutputFile(path, render_topic(topic, report, generated=stamp)))

    files.insert(0, OutputFile("README.md", _readme(report, layout, subject=subject,
                                                    generated=stamp, categories=categories)))
    return files


__all__ = [
    "CATEGORY_MERGE_JACCARD",
    "MIN_TOPICS_FOR_CATEGORIES",
    "SECTION_ORDER",
    "Category",
    "OutputFile",
    "build_categories",
    "organize",
    "render_topic",
]

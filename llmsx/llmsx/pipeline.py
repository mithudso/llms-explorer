"""One call, end to end: materials in, organised markdown and an llms family out.

Every surface runs the same function. The CLI's ``llmsx corpus``, the API's
``POST /api/corpus``, and the six client libraries all reduce to :func:`run`,
so a result obtained one way is byte-identical to the same result obtained
another. That is not tidiness for its own sake — it is what makes "try it free
on the site, then automate it with the library" an honest offer.

The budget is checked **before** any work, against the estimated token size of
the input, and the refusal names the numbers. Component 19 §8: the free tier's
ceiling is a property of the request, not something discovered halfway through.

Nothing here calls a model. The pipeline's four stages — ingest, extract,
analyse, render — are deterministic, which is why the free tier can exist at
all. :data:`MODEL_STAGES` names the three places a metered pass would attach if
the caller has paid for one, and the ``model`` hook takes it. Passing no hook
produces a complete result; that is the design, not a degraded mode.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

from . import coverage as coverage_mod
from . import family as family_mod
from . import organize as organize_mod
from . import units as units_mod
from .ingest import Corpus, Dropped, Material, build_corpus
from .organize import OutputFile
from .tokens import Budget, BudgetExceeded, estimate_all

#: Where a paid model pass attaches. Named so the seam is documented rather than
#: implied, and so a caller can ask which stages their plan would improve.
MODEL_STAGES: tuple[tuple[str, str], ...] = (
    ("classify", "reclassify the units the deterministic rules called `statement`"),
    ("name", "rename topics from their content rather than their strongest terms"),
    ("polish", "rewrite unit text into standalone sentences that read without context"),
)

#: A hook is given the stage name and the working value, and returns a new one.
ModelHook = Callable[[str, object], object]


@dataclass(frozen=True, slots=True)
class Result:
    """Everything one run produced."""

    subject: str
    corpus: Corpus
    pool: units_mod.UnitPool
    report: coverage_mod.CoverageReport
    #: The organised per-topic markdown files, plus their README index.
    organized: Sequence[OutputFile]
    #: The llms family and its manifest.
    family: family_mod.Family
    #: Tokens the input was measured at, and the budget it was measured against.
    input_tokens: int = 0
    budget: int | None = None
    generated: str = ""
    dropped: Sequence[Dropped] = field(default_factory=tuple)

    @property
    def files(self) -> list[OutputFile]:
        """Every file, family first, then the organised topics.

        Family first because a reader opening the archive should meet the index
        before forty topic files.
        """
        return [*self.family.files, *self.organized]

    @property
    def comprehensiveness(self) -> float:
        return self.report.comprehensiveness

    def summary(self) -> dict[str, object]:
        """The JSON body every surface returns alongside the files."""
        return {
            "subject": self.subject,
            "generated": self.generated,
            "input_tokens": self.input_tokens,
            "budget": self.budget,
            "pages": len(self.corpus.pages),
            "units": len(self.pool.units),
            "merged_duplicates": self.pool.merged,
            "sources": self.report.sources,
            "coverage": self.report.as_dict(),
            "dropped": [{"name": d.name, "reason": d.reason, "detail": d.detail}
                        for d in self.dropped],
            "files": [{"path": f.path, "bytes": f.bytes, "tokens": f.tokens}
                      for f in self.files],
            "manifest": self.family.manifest,
        }


def measure(materials: Sequence[Material]) -> int:
    """The token size of the input, by the declared estimator.

    Measured on the raw material rather than on the pages ingestion produces:
    the caller is billed for what they sent, and a conversion that happens to
    shrink an HTML file should not silently change what a request costs.
    """
    return estimate_all(m.text for m in materials)


def run(materials: Iterable[Material], *, subject: str = "Corpus",
        corpus_id: str = "corpus", budget: Budget | None = None,
        max_topics: int = 40, categorise: bool | None = None,
        small_budget: int = family_mod.SMALL_TOKEN_BUDGET,
        with_vocabulary: bool = True, generated: str | None = None,
        model: ModelHook | None = None) -> Result:
    """Materials → organised markdown + an llms family.

    Raises :class:`llmsx.tokens.BudgetExceeded` before doing any work if the
    input is larger than ``budget``.
    """
    items = list(materials)
    input_tokens = measure(items)
    ceiling = budget or Budget(None)
    ceiling.check(input_tokens)

    stamp = generated or dt.datetime.now(dt.UTC).date().isoformat()

    corpus = build_corpus(items, corpus_id=corpus_id)
    pool = units_mod.extract(corpus)
    if model is not None:
        pool = model("classify", pool)                        # type: ignore[assignment]

    report = coverage_mod.analyse(pool, max_topics=max_topics)
    if model is not None:
        report = model("name", report)                        # type: ignore[assignment]

    organized = organize_mod.organize(report, subject=subject, categorise=categorise,
                                      generated=stamp)
    layout = {
        topic.slug: path
        for topic in report.topics
        for path in [next((f.path for f in organized
                           if f.path.endswith(f"-{topic.slug}.md")), "")]
        if path
    }
    family = family_mod.build_family(corpus, pool, report, subject=subject,
                                     generated=stamp, small_budget=small_budget,
                                     layout=layout, with_vocabulary=with_vocabulary)

    return Result(subject=subject, corpus=corpus, pool=pool, report=report,
                  organized=tuple(organized), family=family,
                  input_tokens=input_tokens, budget=ceiling.limit,
                  generated=stamp, dropped=corpus.dropped)


def preview(materials: Iterable[Material], *, subject: str = "Corpus",
            max_topics: int = 40) -> dict[str, object]:
    """What a run *would* produce, without rendering any file.

    The wizard's Detect and Skeleton steps (component 02 §2) call this: the
    caller gets the topic list, the coverage numbers and the gaps to edit before
    spending anything. It is a strict prefix of :func:`run`, so a preview that
    looks right cannot be followed by a run that organises differently.
    """
    items = list(materials)
    corpus = build_corpus(items, corpus_id="preview")
    pool = units_mod.extract(corpus)
    report = coverage_mod.analyse(pool, max_topics=max_topics)
    return {
        "subject": subject,
        "input_tokens": measure(items),
        "pages": len(corpus.pages),
        "units": len(pool.units),
        "coverage": report.as_dict(),
        "dropped": [{"name": d.name, "reason": d.reason, "detail": d.detail}
                    for d in corpus.dropped],
    }


__all__ = [
    "MODEL_STAGES",
    "Budget",
    "BudgetExceeded",
    "Material",
    "ModelHook",
    "Result",
    "measure",
    "preview",
    "run",
]

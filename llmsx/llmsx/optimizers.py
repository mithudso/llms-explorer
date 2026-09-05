"""The optimizer catalogue of component 18 §7, as data.

Nine convergence-loop optimizers exist in this estate and, before this module,
no single place named them: the router SKILL.md routes between eight for an
agent, and nothing published the set to a human, a client library or an HTTP
caller. :data:`CATALOGUE` is that publication, and every surface reads it —
`site/tools/gen_optimizers.py` writes the pages' JSON from it, the API's
``GET /api/optimizers`` serves it, `llmsx optimizers` prints it, and the six
client libraries fetch it.

**The document is the authority.** Seven fields of every record —
``id``, ``name``, ``alias``, ``passes``, ``hosted``, ``gate``, ``domain`` — are
transcribed from the table in `docs/site/components/18-optimizer-catalogue.md`
§7, and `tests/test_optimizers.py` re-parses that table and fails the build if
the two ever disagree. It is the same drift guard 15 §5 and `api/plans.py` use,
for the same reason: a table a human edits and a table a program reads should
not be allowed to diverge quietly.

The other three fields are this module's alone, because they are not limits or
counts that belong in a comparison table: ``skill`` (the SKILL.md a reader
should open), ``artifacts`` (the concrete file kinds, for a router matching on
extension) and ``summary`` (a paragraph of this repo's own prose — never a copy
of the skill's body, which has one canonical home).

``hosted`` is the field to be careful with. It means *this platform runs the
loop for you*, and it is true for exactly one optimizer today. A hosted record
must name a ``surface`` route that the site actually builds; :func:`validate`
enforces that pairing at import, so the catalogue cannot advertise a product
that does not exist.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass, field

#: Where an agent-only optimizer's skill lives. Named, never republished.
SKILL_HOME = "~/.claude/skills"

#: The router that dispatches between the agent-side siblings.
ROUTER_SKILL = "skills/deep-optimizer-router-SKILL.md"


class UnknownOptimizer(KeyError):
    """An id that is not in :data:`CATALOGUE`.

    An error rather than ``None`` so a typo in a route or a client surfaces as a
    404 with the bad id named, not as an empty catalogue page.
    """


@dataclass(frozen=True, slots=True)
class Optimizer:
    """One row of 18 §7, plus the three fields §7 does not carry."""

    id: str
    name: str
    alias: str
    passes: int
    hosted: bool
    gate: str
    domain: str
    skill: str
    summary: str
    artifacts: Sequence[str] = field(default_factory=tuple)
    #: The route that runs the loop, for a hosted optimizer. ``None`` otherwise.
    surface: str | None = None

    @property
    def route(self) -> str:
        """This optimizer's page on the site."""
        return f"/optimizers/{self.id}/"

    def as_dict(self) -> dict[str, object]:
        """The JSON record of 18 §3, with the derived route included.

        ``artifacts`` becomes a list because a tuple is not JSON, and callers
        that round-trip through the API should get the same type either way.
        """
        record = asdict(self)
        record["artifacts"] = list(self.artifacts)
        record["route"] = self.route
        return record


#: 18 §7, transcribed, hosted first — the order §6 asks the catalogue page for.
CATALOGUE: tuple[Optimizer, ...] = (
    Optimizer(
        id="ldo",
        name="llms deep optimizer",
        alias="/ldo",
        passes=16,
        hosted=True,
        gate="llms_lint.py deterministic gate; FTS5 keyword, vector and "
             "agent-usability probes",
        domain="llms.txt, llms-full.txt, llms-small.txt, llms-facts.txt, family "
               "indexes, topical llms files",
        skill="llms-deep-optimizer",
        artifacts=("llms.txt", "llms-full.txt", "llms-small.txt", "llms-facts.txt",
                   "llms-vocabulary.txt", "manifest.json"),
        surface="/create/",
        summary=(
            "Audits an llms file — or a whole <stem>.llms/ family — against the "
            "59-attribute rubric, applies every safe fix, and re-audits until the "
            "family lints clean. Sixteen passes cover structure, links, "
            "descriptions, the size ladder, the full-file grammar, facts anchors "
            "and their truth, provenance, serving headers, and live keyword, "
            "vector and agent-usability probes. Its corpus mode takes an "
            "arbitrary pile of loosely related material and builds the family "
            "with the widest coverage of it that the material supports."
        ),
    ),
    Optimizer(
        id="cdo",
        name="code deep optimizer",
        alias="/cdo",
        passes=18,
        hosted=False,
        gate="build, lint and test verify gate; regressions backed out",
        domain="source files and whole repositories, any language",
        skill="code-deep-optimizer",
        artifacts=(".py", ".ts", ".js", ".go", ".rs", ".java", ".swift"),
        summary=(
            "Detects the languages, frameworks and domains in a file or repo, "
            "activates the matching reviewer skills, runs an eighteen-pass audit, "
            "applies every Medium-or-higher fix in place, and verifies with the "
            "project's own build, lint and tests — backing out anything that "
            "regresses them — until no Medium-or-higher finding survives."
        ),
    ),
    Optimizer(
        id="ddo",
        name="document deep optimizer",
        alias="/ddo",
        passes=15,
        hosted=False,
        gate="blind re-audit and a human-voice pass",
        domain="prose documents: specs, RFCs, runbooks, KB articles",
        skill="document-critique",
        artifacts=(".md", ".rst", ".txt"),
        summary=(
            "Fifteen passes over a prose document: purpose and audience fit, "
            "structure, technical accuracy, plain language, voice and tone, "
            "source verification, terminology consistency, and the removal of "
            "generator artifacts. Every Medium-or-higher fix is applied in place "
            "and the result is re-audited blind."
        ),
    ),
    Optimizer(
        id="pdo",
        name="prompt deep optimizer",
        alias="/pdo",
        passes=16,
        hosted=False,
        gate="injection guard and an optimization-algorithm pick",
        domain="production prompts shipped in code",
        skill="prompt-deep-optimizer",
        artifacts=("system prompt", "agent instruction block", "tool template"),
        summary=(
            "For a prompt that lives in code and runs repeatedly, not a one-off "
            "question. Sixteen passes in five parallel bundles, every "
            "Medium-or-higher fix applied, looped to convergence — and a "
            "recommendation of which training-data-driven algorithm to reach for "
            "next, or an honest 'structural only' when there is no training data."
        ),
    ),
    Optimizer(
        id="sko",
        name="skill optimizer",
        alias="/sko",
        passes=15,
        hosted=False,
        gate="trigger eval and a hub registry sync",
        domain="SKILL.md files",
        skill="skill-optimizer",
        artifacts=("SKILL.md",),
        summary=(
            "Fifteen passes over one skill file, ending in a trigger-accuracy "
            "eval — does the description fire on the cases it should and stay "
            "quiet on the cases it should not — and a sync of the improved file "
            "back to the registry other agents route from."
        ),
    ),
    Optimizer(
        id="dqo",
        name="deep query optimizer",
        alias="/dqo",
        passes=12,
        hosted=False,
        gate="EXPLAIN / EXPLAIN ANALYZE; plan improved, result set unchanged",
        domain="SQL queries and files, Postgres MySQL SQLite SQL Server",
        skill="deep-query-optimizer",
        artifacts=(".sql",),
        summary=(
            "Detects the dialect, then audits sargability, index design, joins "
            "and N+1, predicate logic, projection, pagination and the plan "
            "itself. Rewrites are applied and then verified against EXPLAIN: a "
            "rewrite that does not improve the plan, or changes the result set, "
            "is backed out. Recommends the index DDL it would need."
        ),
    ),
    Optimizer(
        id="deso",
        name="design deep optimizer",
        alias="/deso",
        passes=11,
        hosted=False,
        gate="re-render, contrast and axe verification",
        domain="graphic, brand and UI/UX screens",
        skill="design-deep-optimizer",
        artifacts=(".png", ".jpg", ".svg", ".html", ".css"),
        summary=(
            "Eleven passes over a screen or brand asset: hierarchy, gestalt, "
            "typography, colour, usability heuristics, WCAG, affective trust, "
            "measurable aesthetics, brand parity and a hallucination guard. Where "
            "the design is code-backed the fixes are applied and verified by "
            "re-rendering and re-checking contrast; an image or a spec gets "
            "findings only."
        ),
    ),
    Optimizer(
        id="dso",
        name="deep strategy optimizer",
        alias="/dso",
        passes=19,
        hosted=False,
        gate="project test suite and a figure-verification gate",
        domain="trading strategies, their cards and backtests",
        skill="deep-strategy-optimizer",
        artifacts=("strategy card", "backtest"),
        summary=(
            "Nineteen passes over a strategy and the research that measured it: "
            "simulation integrity (lookahead, cost path, accounting, data), "
            "statistical honesty (protocol grade, multiple-testing burden, "
            "evidence floor, degeneracy), claim provenance and economics. The "
            "expected outcome of its optional promotion step is no promotion."
        ),
    ),
    Optimizer(
        id="dmqo",
        name="deep MongoDB MQL optimizer",
        alias="/dmqo",
        passes=14,
        hosted=False,
        gate="explain verified; index recommendations",
        domain="MongoDB find queries and aggregation pipelines",
        skill="mongodb-expert (references/deep-mongodb-mql-query-optimizer.md)",
        artifacts=("find query", "aggregation pipeline"),
        summary=(
            "The MQL sibling of dqo: stage ordering, index usage, $lookup and "
            "$graphLookup shape, projection and paging over MongoDB find queries "
            "and aggregation pipelines, verified against explain output rather "
            "than asserted."
        ),
    ),
)

#: By id, for the O(1) lookups every surface does.
BY_ID: Mapping[str, Optimizer] = {o.id: o for o in CATALOGUE}


def validate(catalogue: Sequence[Optimizer] = CATALOGUE) -> None:
    """Refuse a catalogue that could mislead a reader. Called at import.

    Three invariants, each of which has cost somebody something somewhere:

    * ids are unique and slug-safe, because the id is a URL segment and an API
      path segment and a duplicate would shadow a page;
    * ``alias`` is ``"/" + id``, which is what lets a reader who knows the slash
      command find the page without a lookup table;
    * ``hosted`` implies ``surface``. 18 §10: an optimistically hosted record is
      the one dishonest field this table could carry.
    """
    seen: set[str] = set()
    for o in catalogue:
        if not o.id or not o.id.isalnum() or not o.id.islower():
            raise AssertionError(f"optimizer id {o.id!r} is not a lowercase slug")
        if o.id in seen:
            raise AssertionError(f"duplicate optimizer id {o.id!r}")
        seen.add(o.id)
        if o.alias != f"/{o.id}":
            raise AssertionError(f"{o.id}: alias {o.alias!r} is not /{o.id}")
        if o.passes <= 0:
            raise AssertionError(f"{o.id}: a convergence loop has passes")
        if o.hosted and not o.surface:
            raise AssertionError(f"{o.id}: hosted with no surface to run it on")
        if o.surface and not o.hosted:
            raise AssertionError(f"{o.id}: names a surface but is not hosted")


validate()


def all_optimizers() -> tuple[Optimizer, ...]:
    """The whole catalogue, hosted first."""
    return CATALOGUE


def get(optimizer_id: str) -> Optimizer:
    """One optimizer, or :class:`UnknownOptimizer` — never a silent default."""
    try:
        return BY_ID[optimizer_id]
    except KeyError:
        raise UnknownOptimizer(optimizer_id) from None


def hosted() -> Iterator[Optimizer]:
    """The optimizers this platform actually runs."""
    return (o for o in CATALOGUE if o.hosted)


def as_records() -> list[dict[str, object]]:
    """The catalogue as the JSON list of 18 §3."""
    return [o.as_dict() for o in CATALOGUE]


__all__ = [
    "BY_ID",
    "CATALOGUE",
    "ROUTER_SKILL",
    "SKILL_HOME",
    "Optimizer",
    "UnknownOptimizer",
    "all_optimizers",
    "as_records",
    "get",
    "hosted",
    "validate",
]

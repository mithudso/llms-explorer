"""Merge-back proposals, the publish gate and the 05 §4 precedence ladder.

Authority: component `05-conceptual-vs-proprietary.md` §4 (the ladder, the
conflict record), §5 (the surface), §7 (`proposals`, `moderation`), §9 (the
acceptance bar) and §10 (submissions are data), plus master §9 (the
publish/contribute gate is ``llms_lint.py check`` with zero High findings and a
provenance banner present).

The module owns three separable things, in the order a proposal meets them:

1. **The public tree as a file.** Master §4 settles it: a tree is a *file copy*,
   not a patch model, and there is exactly one writer (master principle 5). So a
   merge is read → apply → validate → atomic replace, and every write is guarded
   by the sha it expected to overwrite. A proposal that raced another writer is
   refused (:class:`TreeMoved`), never blindly applied. Where that file *is*, and
   how it is read and written, belongs to `explorer_api.trees`: a fork's
   ``forked_from_sha`` and a proposal's ``tree_sha`` are the same identity, and
   two locators would eventually disagree about which file it names.

2. **The lint gate.** ``llms_lint.check`` is imported from the hub and called,
   never reimplemented — the hub is read-only to this service. A High finding, or
   a missing provenance banner, auto-rejects the proposal *with the findings
   attached*, so the contributor sees the verdict (05 §2) instead of a shrug.

3. **The precedence ladder.** Six rungs, evaluated in order, first difference
   wins; anything that survives all six is a tie and goes to a human. The ladder
   is deliberately **total** (05 §9): every conflict resolves to a named rung or
   to the queue, and there is no third outcome in which a unit is silently
   dropped. :func:`conflict_record` emits §4's record shape verbatim so the
   `resolve` job can append it to ``conflicts.jsonl`` unchanged.

Two decisions worth stating because they are security, not style:

* **Submissions are data, never instructions.** Every free-text field a
  contributor controls goes through the hub's steering regexes at intake
  (05 §10); a hit is refused at the door and never enters the queue, where a
  moderator's assistant might read it as an instruction.
* **Artifacts are named by id, not by path.** The gate lints files this service
  already owns rows for, so no request can point the linter — or the merge — at
  a path outside the caller's own store.

Moderators are an environment allow-list (:data:`MODERATOR_ENV`) rather than a
column, because `users` is Task 2's file and this task does not edit it. The
identity is the *verified* email, so an unverified address cannot claim the
role. When 15 grows a role column this function is the only thing that moves.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models as m, trees

# --- the hub, imported read-only ---------------------------------------------

#: Where the hub's scripts are looked for. Same order as `trees.py`'s locator —
#: the vendored snapshot first, because it is what CI has and what the site
#: published — so both modules always import the *same* hub code.
_HUB_ENV = "HUB_SCRIPTS"


def _hub_scripts() -> Path:
    """The directory holding ``llms_lint.py``."""
    candidates: list[Path] = []
    if raw := os.environ.get(_HUB_ENV):
        candidates.append(Path(raw).expanduser())
    # `api/explorer_api/moderation.py` → repo root → the vendored snapshot.
    candidates.append(Path(__file__).resolve().parents[2] / "hub" / "scripts")
    candidates.append(
        Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub")).expanduser()
        / "scripts"
    )
    for candidate in candidates:
        if (candidate / "llms_lint.py").is_file():
            return candidate
    raise RuntimeError(
        "the hub's scripts were not found; looked in "
        + ", ".join(str(c) for c in candidates)
        + f" (set {_HUB_ENV})"
    )


_HUB_SCRIPTS = _hub_scripts()
if str(_HUB_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_HUB_SCRIPTS))

import llms_lint as _llms_lint  # noqa: E402 — after the sys.path insert above


# --- errors ------------------------------------------------------------------


class ModerationError(RuntimeError):
    """Base for everything a route turns into a status code."""


class StaleTree(ModerationError):
    """The diff was taken against a public tree that has since moved (409)."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected, self.actual = expected, actual
        super().__init__(
            f"the proposal was written against tree sha {expected}, but the public "
            f"tree is now {actual}; rebase the diff onto {actual} and resubmit"
        )


class TreeMoved(StaleTree):
    """The public tree changed between queueing and the merge (409)."""


class InvalidPatch(ModerationError):
    """The patch is not a patch, or does not apply (422)."""


class BrokenTree(ModerationError):
    """Applying the patch would leave the public tree structurally broken (422)."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = list(problems)
        super().__init__(
            "the merge would break the public tree: " + "; ".join(self.problems)
        )


class SteeringDetected(ModerationError):
    """A submitted field tries to instruct the model reading it (422)."""

    def __init__(self, hits: Sequence[str]) -> None:
        self.hits = list(hits)
        super().__init__(
            "steering text is not accepted in a proposal (05 §10): " + "; ".join(self.hits)
        )


class UnknownArtifact(ModerationError):
    """An artifact id that is not this user's (404 — never 403, which confirms it)."""


class ProposalNotFound(ModerationError):
    """No such proposal, for this caller (404)."""


class AlreadyDecided(ModerationError):
    """The proposal already carries a verdict (409)."""


class NotAModerator(ModerationError):
    """The caller may not decide proposals (403)."""


class InvalidUnit(ValueError):
    """A unit the ladder refuses to score — no source is never queued (05 §6)."""


# --- who may decide ----------------------------------------------------------

#: Comma-separated verified emails. Environment, never a file in the repo.
MODERATOR_ENV = "EXPLORER_MODERATOR_EMAILS"


def moderator_emails() -> frozenset[str]:
    """The allow-list, read at call time so a change needs no redeploy."""
    raw = os.environ.get(MODERATOR_ENV, "")
    return frozenset(part.strip().lower() for part in raw.split(",") if part.strip())


def is_moderator(user: m.User) -> bool:
    """True when ``user`` may accept or reject. Unverified email never qualifies."""
    if not user.email or not user.email_verified:
        return False
    return user.email.strip().lower() in moderator_emails()


# --- the public tree as a file ----------------------------------------------
#
# One owner: `explorer_api.trees` (Task 9) locates, reads and writes tree files,
# and `forked_from_sha` there and `tree_sha` here are the *same* identity — the
# sha256 of the public file's bytes. Re-deriving either of those separately is
# how a fork and a merge end up talking about two different files.


def public_tree_path() -> Path:
    """The public `tree.json` — whatever `trees.py` says it is."""
    return trees.public_tree_path()


def sha_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_tree(path: Path) -> tuple[list[dict], str]:
    """``(nodes, sha)``. The sha is over the bytes on disk, so it is exactly
    what a later write must still find there."""
    if not Path(path).is_file():
        # `trees.read_nodes` answers `[]` for a missing file; merging a patch
        # into an empty tree because the file vanished is worse than failing.
        raise ModerationError(f"the public tree is missing: {path}")
    return list(trees.read_nodes(Path(path))), trees.sha_of(Path(path))


def write_tree(path: Path, nodes: Sequence[Mapping[str, Any]], *, expected_sha: str) -> str:
    """Replace the tree atomically, refusing if another writer got there first."""
    _, actual = read_tree(path)
    if actual != expected_sha:
        raise TreeMoved(expected_sha, actual)
    trees.write_nodes(Path(path), [dict(n) for n in nodes])
    return trees.sha_of(Path(path))


# --- patches -----------------------------------------------------------------

PATCH_OPS = ("add", "update", "remove")
#: A merge-back diff is a handful of nodes, not a tree rewrite. The cap is what
#: keeps a submission from turning into an unbounded merge a moderator cannot read.
MAX_OPS = 200


def apply_patch(
    nodes: Sequence[Mapping[str, Any]], patch: Mapping[str, Any]
) -> list[dict]:
    """Apply ``patch`` to ``nodes``, returning a new list. Never mutates its input.

    Structural validity is *not* checked here — that is :func:`validate_nodes`,
    run at merge time, so a proposal that dangles a parent still reaches a human
    with its problem named rather than being swallowed at submission.
    """
    if not isinstance(patch, Mapping):
        raise InvalidPatch("the patch must be an object with an `ops` list")
    ops = patch.get("ops")
    if not isinstance(ops, list) or not ops:
        raise InvalidPatch("the patch must carry a non-empty `ops` list")
    if len(ops) > MAX_OPS:
        raise InvalidPatch(f"a patch may carry at most {MAX_OPS} ops (got {len(ops)})")

    out = copy.deepcopy(list(nodes))
    index = {n.get("concept"): n for n in out if n.get("concept")}
    for position, op in enumerate(ops):
        if not isinstance(op, Mapping) or op.get("op") not in PATCH_OPS:
            raise InvalidPatch(f"op {position}: `op` must be one of {', '.join(PATCH_OPS)}")
        kind = op["op"]
        node = op.get("node")
        if kind == "add":
            if not isinstance(node, Mapping) or not node.get("concept"):
                raise InvalidPatch(f"op {position}: `add` needs a node with a concept")
            concept = str(node["concept"])
            if concept in index:
                raise InvalidPatch(f"op {position}: `{concept}` already exists — use update")
            fresh = dict(node)
            out.append(fresh)
            index[concept] = fresh
        elif kind == "update":
            concept = str(op.get("concept") or (node or {}).get("concept") or "")
            if concept not in index:
                raise InvalidPatch(f"op {position}: `{concept}` has no node to update")
            if not isinstance(node, Mapping):
                raise InvalidPatch(f"op {position}: `update` needs a node object")
            if node.get("concept") not in (None, concept):
                # A rename relinks every child by name; it is remove + add, and a
                # moderator should see it as such rather than as a field edit.
                raise InvalidPatch(f"op {position}: an update may not rename `{concept}`")
            index[concept].update({k: v for k, v in node.items() if k != "concept"})
        else:  # remove
            concept = str(op.get("concept") or "")
            if concept not in index:
                raise InvalidPatch(f"op {position}: `{concept}` has no node to remove")
            out = [n for n in out if n.get("concept") != concept]
            del index[concept]
    return out


#: `validate()` also reports a node whose `skillId` is installed nowhere. That is
#: a property of the box, not of the tree, and it must not block a merge here.
_SKILL_PROBLEM = "is not installed"


def validate_nodes(nodes: Sequence[Mapping[str, Any]]) -> list[str]:
    """Structural link problems, from the hub's own validator."""
    tree = trees.concept_tree().ConceptTree(copy.deepcopy(list(nodes)))
    return [p for p in tree.validate() if not p.endswith(_SKILL_PROBLEM)]


# --- submissions are data (05 §10) -------------------------------------------


def scan_for_steering(*texts: str | None) -> list[str]:
    """Lines that read as instructions to the model, using the hub's regexes."""
    hits: list[str] = []
    for text in texts:
        for line in (text or "").splitlines():
            if _llms_lint._steer_hit(line) is not None:
                hits.append(line.strip()[:120])
    return hits


# --- the lint gate (master §9) ------------------------------------------------

#: The finding that says a file has no provenance banner. Master §9 requires the
#: banner as well as zero High findings, so this one medium is blocking too.
PROVENANCE_FINDING = ("P9", "P1")
SEVERITIES = ("high", "medium", "low", "hygiene", "na")


@dataclass(frozen=True)
class LintReport:
    """What the gate found, and whether it opens."""

    passed: bool
    counts: dict[str, int]
    findings: list[dict]
    blocking: list[dict]
    files: list[str]

    def as_json(self) -> dict:
        return {
            "passed": self.passed,
            "counts": self.counts,
            "findings": self.findings,
            "blocking": self.blocking,
            "files": self.files,
        }


def _blocking(finding: Mapping[str, Any]) -> bool:
    if finding.get("severity") == "high":
        return True
    return (finding.get("pass"), finding.get("attr")) == PROVENANCE_FINDING


def lint_gate(paths: Iterable[Path]) -> LintReport:
    """Run `llms_lint.check` over every artifact and decide whether to publish."""
    findings: list[dict] = []
    files: list[str] = []
    for path in paths:
        files.append(str(path))
        if not Path(path).is_file():
            # A file the gate cannot read is a failure, never a pass by absence.
            findings.append(
                {
                    "file": str(path), "pass": "P0", "attr": "I6", "severity": "high",
                    "line": 0, "fixable": False,
                    "msg": f"artifact file is missing: {path}",
                }
            )
            continue
        result = _llms_lint.check(Path(path))
        for finding in result["findings"]:
            findings.append({"file": str(path), **dict(finding)})
    counts = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        severity = str(finding.get("severity", "na"))
        counts[severity] = counts.get(severity, 0) + 1
    blocking = [f for f in findings if _blocking(f)]
    return LintReport(
        passed=not blocking, counts=counts, findings=findings,
        blocking=blocking, files=files,
    )


# --- the 05 §4 precedence ladder ---------------------------------------------

#: Rung 1, best first. "spec/standard" is one level in the spoke's table, so the
#: two share a rank; anything unknown ranks below every named grade.
GRADE_ORDER: tuple[str, ...] = (
    "spec", "standard", "vendor", "measurement", "secondary", "blog",
)
GRADE_RANK: Mapping[str, int] = {
    "spec": 0, "standard": 0, "vendor": 1, "measurement": 2, "secondary": 3, "blog": 4,
}
UNKNOWN_GRADE_RANK = max(GRADE_RANK.values()) + 1

#: The ladder, in order. First rung with a difference decides; surviving all six
#: is a tie, which is the queue (05 §4's last row).
RUNGS: tuple[str, ...] = (
    "grade", "corroboration", "recency", "sense", "evals", "scope",
)


@dataclass(frozen=True)
class Unit:
    """A fact unit as the ladder sees it (05 §7's fields)."""

    id: str
    claim_key: str
    text: str = ""
    source: str | None = None
    grade: str = "blog"
    also: tuple[str, ...] = ()
    verified_as_of: dt.date | None = None
    sense: str | None = None
    answers: frozenset[str] = frozenset()
    scope: Mapping[str, str] = field(default_factory=dict)
    superseded_by: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Unit:
        """Accepts the facts-file spelling (``verified-as-of``) and the Python one."""
        def pick(*names: str, default: Any = None) -> Any:
            for name in names:
                if name in data and data[name] is not None:
                    return data[name]
            return default

        raw_date = pick("verified_as_of", "verified-as-of")
        if isinstance(raw_date, str):
            raw_date = dt.date.fromisoformat(raw_date)
        return cls(
            id=str(data["id"]),
            claim_key=str(data["claim_key"]),
            text=str(pick("text", default="")),
            source=pick("source"),
            grade=str(pick("grade", default="blog")).lower(),
            also=tuple(pick("also", default=()) or ()),
            verified_as_of=raw_date,
            sense=pick("sense"),
            answers=frozenset(pick("answers", default=()) or ()),
            scope=dict(pick("scope", default={}) or {}),
            superseded_by=pick("superseded_by", "superseded-by"),
        )

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "claim_key": self.claim_key,
            "text": self.text,
            "source": self.source,
            "grade": self.grade,
            "also": list(self.also),
            "verified-as-of": self.verified_as_of.isoformat() if self.verified_as_of else None,
            "sense": self.sense,
            "answers": sorted(self.answers),
            "scope": dict(self.scope),
            "superseded_by": self.superseded_by,
        }

    # -- rung inputs ----------------------------------------------------------

    @property
    def grade_rank(self) -> int:
        return GRADE_RANK.get(self.grade, UNKNOWN_GRADE_RANK)

    @property
    def corroboration(self) -> int:
        """Independent sources, deduplicated — "citation chains collapse to one"."""
        return len({a for a in self.also if a and a != self.source})


@dataclass(frozen=True)
class Verdict:
    """The ladder's answer: a winner at a named rung, or a tie for a human."""

    challenger: Unit
    incumbent: Unit
    rung: str | None
    scores: dict[str, dict[str, Any]]
    winner: Unit | None = None
    loser: Unit | None = None

    @property
    def tie(self) -> bool:
        return self.winner is None

    @property
    def claim_key(self) -> str:
        return self.challenger.claim_key


def _cmp(a: Any, b: Any) -> int:
    """1 when ``a`` beats ``b``, -1 when ``b`` beats ``a``, 0 when neither does."""
    if a == b:
        return 0
    return 1 if a > b else -1


def _rung_grade(a: Unit, b: Unit, _ctx: Mapping[str, Any]) -> int:
    return _cmp(b.grade_rank, a.grade_rank)  # a *lower* rank is a better source


def _rung_corroboration(a: Unit, b: Unit, _ctx: Mapping[str, Any]) -> int:
    return _cmp(a.corroboration, b.corroboration)


def _rung_recency(a: Unit, b: Unit, _ctx: Mapping[str, Any]) -> int:
    # A unit with no re-fetch stamp cannot win this rung; a date bump alone is
    # not evidence (05 §4 rung 3), so the field is written only by a re-fetch.
    if a.verified_as_of is None and b.verified_as_of is None:
        return 0
    if a.verified_as_of is None:
        return -1
    if b.verified_as_of is None:
        return 1
    return _cmp(a.verified_as_of, b.verified_as_of)


def _rung_sense(a: Unit, b: Unit, ctx: Mapping[str, Any]) -> int:
    canonical = ctx.get("canonical_sense")
    if not canonical:
        return 0
    return _cmp(a.sense == canonical, b.sense == canonical)


def _rung_evals(a: Unit, b: Unit, _ctx: Mapping[str, Any]) -> int:
    # "answered P12 questions the loser did not" — a strict superset. Two units
    # that each answer something the other misses do not settle this rung.
    if a.answers > b.answers:
        return 1
    if b.answers > a.answers:
        return -1
    return 0


def _rung_scope(a: Unit, b: Unit, _ctx: Mapping[str, Any]) -> int:
    """Narrower beats broader — a refinement of the same scope, not a different one."""
    a_items, b_items = set(a.scope.items()), set(b.scope.items())
    if a_items > b_items:
        return 1
    if b_items > a_items:
        return -1
    return 0


_RUNG_FUNCS = {
    "grade": _rung_grade,
    "corroboration": _rung_corroboration,
    "recency": _rung_recency,
    "sense": _rung_sense,
    "evals": _rung_evals,
    "scope": _rung_scope,
}


def _rung_scores(unit: Unit) -> dict[str, Any]:
    return {
        "grade": unit.grade_rank,
        "corroboration": unit.corroboration,
        "recency": unit.verified_as_of.isoformat() if unit.verified_as_of else None,
        "sense": unit.sense,
        "evals": sorted(unit.answers),
        "scope": dict(unit.scope),
    }


def resolve_conflict(
    challenger: Unit, incumbent: Unit, *, canonical_sense: str | None = None
) -> Verdict:
    """Score two conflicting units on the ladder (05 §4).

    Total by construction: the result is a winner at exactly one named rung, or
    a tie destined for the moderation queue. There is no path on which a unit is
    dropped without a record.
    """
    for unit in (challenger, incumbent):
        if not unit.source:
            raise InvalidUnit(
                f"unit {unit.id} has no source; a submission without one is "
                "rejected at intake and never queued (05 §6)"
            )
    ctx = {"canonical_sense": canonical_sense}
    a_scores, b_scores = _rung_scores(challenger), _rung_scores(incumbent)
    scores = {
        rung: {"challenger": a_scores[rung], "incumbent": b_scores[rung]}
        for rung in RUNGS
    }
    for rung in RUNGS:
        decision = _RUNG_FUNCS[rung](challenger, incumbent, ctx)
        if decision:
            winner, loser = (
                (challenger, incumbent) if decision > 0 else (incumbent, challenger)
            )
            return Verdict(challenger, incumbent, rung, scores, winner, loser)
    return Verdict(challenger, incumbent, None, scores)


def conflict_record(
    verdict: Verdict,
    *,
    concept: str,
    resolver: str = "ladder",
    note: str | None = None,
    prior_winner_id: str | None = None,
    now: dt.datetime | None = None,
) -> dict:
    """05 §4's `conflicts.jsonl` line, ready to append verbatim."""
    stamp = (now or dt.datetime.now(dt.UTC)).isoformat()
    return {
        "concept": concept,
        "claim_key": verdict.claim_key,
        "winner_id": verdict.winner.id if verdict.winner else None,
        "loser_ids": [verdict.loser.id] if verdict.loser else [],
        "contenders": [verdict.challenger.id, verdict.incumbent.id],
        "rung": verdict.rung,
        "scores": verdict.scores,
        "resolved_at": stamp,
        "resolver": resolver,
        "note": note,
        "prior_winner_id": prior_winner_id,
    }


def mark_superseded(loser: Unit, winner_id: str) -> dict:
    """The loser's line, keeping its source and gaining `superseded_by` (05 §4)."""
    return {**loser.as_dict(), "superseded_by": winner_id}


# --- proposals ----------------------------------------------------------------

AUTO_REJECT_NOTE = "auto-rejected by the lint gate (master §9)"
MAX_SUMMARY_LEN = 2000


async def _artifacts_for(
    session: AsyncSession, user: m.User, artifact_ids: Sequence[str]
) -> list[m.Artifact]:
    """The caller's own artifacts. Anything else is a 404, so ids stay unguessable."""
    if not artifact_ids:
        return []
    rows = (
        await session.execute(
            select(m.Artifact).where(
                m.Artifact.id.in_(list(artifact_ids)),
                m.Artifact.owner_user_id == user.id,
            )
        )
    ).scalars().all()
    found = {row.id for row in rows}
    missing = [aid for aid in artifact_ids if aid not in found]
    if missing:
        raise UnknownArtifact(f"no such artifact: {', '.join(missing)}")
    order = {aid: i for i, aid in enumerate(artifact_ids)}
    return sorted(rows, key=lambda row: order[row.id])


async def submit(
    session: AsyncSession,
    user: m.User,
    *,
    tree_sha: str,
    patch: Mapping[str, Any],
    artifact_ids: Sequence[str] = (),
    summary: str | None = None,
) -> tuple[m.Proposal, LintReport]:
    """Queue a merge-back proposal, or auto-reject it at the gate.

    Order matters: intake scan, then the sha, then the patch, then the gate.
    Nothing is written until all four have had their say, so a refused
    submission leaves no row behind for a moderator to wade through.
    """
    if hits := scan_for_steering(summary, json.dumps(patch)):
        raise SteeringDetected(hits)
    if summary and len(summary) > MAX_SUMMARY_LEN:
        raise InvalidPatch(f"summary must be at most {MAX_SUMMARY_LEN} characters")

    nodes, current_sha = read_tree(public_tree_path())
    if tree_sha != current_sha:
        raise StaleTree(tree_sha, current_sha)
    apply_patch(nodes, patch)  # a patch that cannot apply is refused now, not later

    artifacts = await _artifacts_for(session, user, list(artifact_ids))
    report = lint_gate(Path(a.path) for a in artifacts)

    tree_id = (
        await session.execute(
            select(m.Tree.id).where(m.Tree.user_id == user.id).order_by(m.Tree.created_at)
        )
    ).scalars().first()

    proposal = m.Proposal(
        user_id=user.id,
        tree_id=tree_id,
        tree_sha=current_sha,
        patch_json=dict(patch),
        summary=summary,
        status="proposed" if report.passed else "rejected",
        lint_json=report.as_json(),
    )
    session.add(proposal)
    await session.flush()

    item = m.ModerationItem(
        subject_kind="proposal",
        subject_id=proposal.id,
        state="pending" if report.passed else "rejected",
        findings_json={} if report.passed else {"lint": report.as_json()},
        note=None if report.passed else AUTO_REJECT_NOTE,
        # No `decided_by_user_id`: the gate is a rule, not a person.
        decided_at=None if report.passed else dt.datetime.now(dt.UTC),
    )
    session.add(item)
    await session.flush()
    return proposal, report


async def get_for_user(
    session: AsyncSession, user: m.User, proposal_id: str
) -> m.Proposal | None:
    """One proposal, if it is the caller's or the caller moderates."""
    proposal = await session.get(m.Proposal, proposal_id)
    if proposal is None:
        return None
    if proposal.user_id != user.id and not is_moderator(user):
        return None
    return proposal


async def list_for_user(
    session: AsyncSession, user: m.User, *, limit: int = 100
) -> list[m.Proposal]:
    rows = await session.execute(
        select(m.Proposal)
        .where(m.Proposal.user_id == user.id)
        .order_by(m.Proposal.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars().all())


async def queue(
    session: AsyncSession, user: m.User, *, limit: int = 100
) -> list[m.Proposal]:
    """The pending queue, oldest first — 8a's 48 h clock runs from the head."""
    if not is_moderator(user):
        raise NotAModerator("only a moderator may read the queue")
    rows = await session.execute(
        select(m.Proposal)
        .join(m.ModerationItem, m.ModerationItem.subject_id == m.Proposal.id)
        .where(
            m.ModerationItem.subject_kind == "proposal",
            m.ModerationItem.state == "pending",
        )
        .order_by(m.ModerationItem.created_at)
        .limit(limit)
    )
    return list(rows.scalars().all())


async def _item_for(session: AsyncSession, proposal: m.Proposal) -> m.ModerationItem | None:
    rows = await session.execute(
        select(m.ModerationItem).where(
            m.ModerationItem.subject_kind == "proposal",
            m.ModerationItem.subject_id == proposal.id,
        )
    )
    return rows.scalars().first()


async def decide(
    session: AsyncSession,
    moderator: m.User,
    proposal_id: str,
    *,
    accept: bool,
    note: str | None = None,
) -> m.Proposal:
    """Accept (merging into the public tree) or reject, recording who decided.

    The merge is the only path in this service that writes the public tree, and
    it writes it exactly once: guarded by the sha the proposal was queued
    against, validated after the patch is applied, replaced atomically.
    """
    if not is_moderator(moderator):
        raise NotAModerator("only a moderator may decide a proposal")
    if hits := scan_for_steering(note):
        raise SteeringDetected(hits)

    proposal = await session.get(m.Proposal, proposal_id)
    if proposal is None:
        raise ProposalNotFound(f"no such proposal: {proposal_id}")
    if proposal.status != "proposed":
        raise AlreadyDecided(
            f"proposal {proposal.id} was already {proposal.status}; a second "
            "decision would merge it twice"
        )

    if accept:
        path = public_tree_path()
        nodes, current_sha = read_tree(path)
        if current_sha != proposal.tree_sha:
            raise TreeMoved(proposal.tree_sha, current_sha)
        merged = apply_patch(nodes, proposal.patch_json)
        if problems := validate_nodes(merged):
            raise BrokenTree(problems)
        write_tree(path, merged, expected_sha=current_sha)

    now = dt.datetime.now(dt.UTC)
    proposal.status = "merged" if accept else "rejected"
    proposal.moderator_user_id = moderator.id
    proposal.decided_at = now

    item = await _item_for(session, proposal)
    if item is None:  # a proposal always has one; heal rather than lose the record
        item = m.ModerationItem(subject_kind="proposal", subject_id=proposal.id)
        session.add(item)
    item.state = "approved" if accept else "rejected"
    item.decided_by_user_id = moderator.id
    item.decided_at = now
    if note is not None:
        item.note = note
    await session.flush()
    return proposal


def public_view(proposal: m.Proposal) -> dict:
    """A proposal as its author and a moderator may see it."""
    return {
        "id": proposal.id,
        "user_id": proposal.user_id,
        "tree_id": proposal.tree_id,
        "tree_sha": proposal.tree_sha,
        "patch": proposal.patch_json,
        "summary": proposal.summary,
        "status": proposal.status,
        "lint": proposal.lint_json,
        "moderator_user_id": proposal.moderator_user_id,
        "decided_at": proposal.decided_at,
        "created_at": proposal.created_at,
    }


__all__ = [
    "AUTO_REJECT_NOTE",
    "AlreadyDecided",
    "BrokenTree",
    "GRADE_ORDER",
    "GRADE_RANK",
    "InvalidPatch",
    "InvalidUnit",
    "LintReport",
    "MODERATOR_ENV",
    "ModerationError",
    "NotAModerator",
    "PROVENANCE_FINDING",
    "ProposalNotFound",
    "RUNGS",
    "StaleTree",
    "SteeringDetected",
    "TreeMoved",
    "Unit",
    "UnknownArtifact",
    "Verdict",
    "apply_patch",
    "conflict_record",
    "decide",
    "get_for_user",
    "is_moderator",
    "lint_gate",
    "list_for_user",
    "mark_superseded",
    "moderator_emails",
    "public_tree_path",
    "public_view",
    "queue",
    "read_tree",
    "resolve_conflict",
    "scan_for_steering",
    "sha_of",
    "submit",
    "validate_nodes",
    "write_tree",
]

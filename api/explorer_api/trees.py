"""Private concept-tree forks.

Authority: master §4 (`trees(user_id, forked_from_sha, updated_at)` — *"a file
copy, not a patch model"*), component 09 §7, and 15 §5 for the per-plan
allowance (free 1, starter 3, pro 20).

Four decisions this module makes explicit, because each is load-bearing:

**1. A fork is a byte-for-byte copy of the public file, plus a sha.**
`concept_tree.py` reads a flat JSON list from a path and knows nothing about
users, so the cheapest correct private tree is a second file. ``forked_from_sha``
is sha256 over the *public file's bytes* at the moment of the copy — which is
what lets Task 10 refuse a merge-back proposal taken from a stale base (409)
without storing a patch chain nobody would be able to replay.

**2. The hub is read-only here.** ``concept_tree`` is imported from the vendored
``hub/scripts`` (CI) or ``$HUB_DIR/scripts`` (the box) and only its pure
functions are used — loading, saving and validating an explicit path. Nothing
in this module writes anywhere inside the hub tree.

**3. A slug is a path component, so it is validated as one.** :data:`SLUG_RE`
is an allow-list; a slug that is not in it never reaches the filesystem. Paths
are then *composed*, never resolved from user input, so ``..`` cannot appear in
one even in principle.

**4. Validation separates structure from environment.** ``ConceptTree.validate``
reports two very different things: links that dangle (a real defect in the
user's tree) and ``skillId``s that are not installed *on this machine* — which
says nothing about the tree and would differ between the box and CI. The first
are :attr:`Validation.problems` and decide ``ok``; the second are
:attr:`Validation.warnings` and never fail a tree.

Enforcement of the allowance is *not* here: it is
:func:`explorer_api.ledger.check_quota`, the single place a limit is applied.
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import ledger, models as m

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .settings import Settings

#: The private tree every account gets first. `/api/trees/me/validate` in the
#: plan's route table is this slug, not a magic word.
DEFAULT_SLUG = "me"

#: The two things `GET /api/tree?tree=` can name.
PUBLIC = "public"
MINE = "me"

#: The 15 §5 quota this module spends. Named once so the 402 and the check
#: cannot drift apart.
QUOTA_FEATURE = "private_trees"

#: A slug is a directory name. Lowercase, digits and hyphens only, and never
#: empty — so no slug can contain a separator, a dot segment or a NUL, and the
#: composed path is inside `stores_root` by construction.
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

#: Where a user's trees live under `stores_root`, beside (not inside) the
#: per-user docset store: `stores/<user_id>/trees/<slug>/tree.json`.
TREES_DIR = "trees"
TREE_FILE = "tree.json"

#: The file name `concept_tree.py` gives a tree's sidecars. A private tree has
#: its own directory so those can exist beside it later without a second root.
QUEUE_FILE = "RESEARCH_QUEUE.md"
STATE_FILE = "research_state.json"

#: Findings from `ConceptTree.validate()` that describe this *machine* rather
#: than the tree: a node naming a skill that is not installed here.
_SKILL_FINDING = re.compile(r"skillId '.*' is not installed")


class TreeError(RuntimeError):
    """Base for everything this module refuses to do."""


class InvalidSlug(TreeError, ValueError):
    """A slug that is not a safe single path component."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(
            f"invalid tree slug {slug!r}: lowercase letters, digits and hyphens "
            "only, 1-64 characters, starting with a letter or digit"
        )


class TreeExists(TreeError):
    """That slug is already forked. Re-forking would discard the user's edits."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(
            f"tree {slug!r} already exists; fork under a different slug rather "
            "than overwriting the edits already in it"
        )


class TreeNotFound(TreeError):
    """No such tree for this account — which is also the answer for someone
    else's tree, so the slug space cannot be enumerated."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"no tree {slug!r} for this account")


class QuotaExceeded(TreeError):
    """The plan's private-tree allowance is spent."""

    def __init__(self, verdict: ledger.QuotaVerdict) -> None:
        self.verdict = verdict
        super().__init__(
            f"the {verdict.tier} plan allows {verdict.limit} private tree(s)"
        )


class PublicTreeMissing(TreeError):
    """Neither the vendored snapshot nor the hub has a public `tree.json`."""


# --- the hub, read-only ------------------------------------------------------


def _repo_root() -> Path:
    # explorer_api/trees.py -> explorer_api -> api -> <repo>
    return Path(__file__).resolve().parents[2]


def _hub_dir() -> Path:
    return Path(os.environ.get("HUB_DIR", Path.home() / ".global-ai-hub")).expanduser()


def _candidate_script_dirs() -> tuple[Path, ...]:
    """Vendored copy first: it is the one CI has and the one the site builds
    from, so a test run never depends on the machine's live hub."""
    return (_repo_root() / "hub" / "scripts", _hub_dir() / "scripts")


@lru_cache(maxsize=1)
def concept_tree() -> ModuleType:
    """The hub's ``concept_tree`` module, imported read-only.

    Cached because the import mutates ``sys.path``; doing it once keeps that
    to a single entry no matter how many requests are served.
    """
    for directory in _candidate_script_dirs():
        if (directory / "concept_tree.py").is_file():
            if str(directory) not in sys.path:
                sys.path.insert(0, str(directory))
            break
    import concept_tree as module  # noqa: PLC0415 - located above, deliberately late

    return module


def public_tree_path() -> Path:
    """The public `tree.json`.

    ``EXPLORER_PUBLIC_TREE`` wins (a deployment may pin it), then the vendored
    snapshot in the repo, then the live hub. The vendored copy is preferred over
    the hub so the API serves exactly what the site published.
    """
    override = os.environ.get("EXPLORER_PUBLIC_TREE")
    if override:
        return Path(override).expanduser()
    for root in (_repo_root(), _hub_dir()):
        candidate = root / "concept-tree" / TREE_FILE
        if candidate.is_file():
            return candidate
    raise PublicTreeMissing(
        "no public concept-tree/tree.json found in the repo or the hub; set "
        "EXPLORER_PUBLIC_TREE to point at one"
    )


# --- reading and writing a tree file -----------------------------------------


def sha_of(path: Path) -> str:
    """sha256 of the file's bytes — the identity Task 10 compares against."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_sha() -> str:
    return sha_of(public_tree_path())


def public_nodes() -> list[dict[str, Any]]:
    return read_nodes(public_tree_path())


def read_nodes(path: Path) -> list[dict[str, Any]]:
    """The flat node list at ``path``.

    ``concept_tree.load_nodes`` accepts both shapes the hub has used (a bare
    list, or ``{"nodes": [...]}``) and returns ``[]`` for a missing file — the
    latter is why callers check existence themselves rather than reading an
    empty tree and calling it valid.
    """
    return concept_tree().load_nodes(path)


def write_nodes(path: Path, nodes: list[dict[str, Any]]) -> None:
    """Write ``nodes`` atomically, in the hub's own format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    concept_tree().save_nodes(nodes, path)


# --- paths -------------------------------------------------------------------


def check_slug(slug: str) -> str:
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        raise InvalidSlug(slug)
    return slug


def tree_dir(settings: Settings, user_id: str, slug: str = DEFAULT_SLUG) -> Path:
    """`<stores_root>/<user_id>/trees/<slug>/` — composed, never resolved."""
    return settings.stores_root / user_id / TREES_DIR / check_slug(slug)


def tree_path(settings: Settings, user_id: str, slug: str = DEFAULT_SLUG) -> Path:
    return tree_dir(settings, user_id, slug) / TREE_FILE


def relative_path(user_id: str, slug: str = DEFAULT_SLUG) -> str:
    """What goes in ``trees.path``: root-relative, so moving ``stores_root``
    (a different box, a restore) does not invalidate every row."""
    return f"{user_id}/{TREES_DIR}/{check_slug(slug)}/{TREE_FILE}"


def resolve_path(settings: Settings, tree: m.Tree) -> Path:
    """The file for a stored row. Derived from the row's ids, not from its
    ``path`` string, so a bad value in the column can never redirect a read."""
    return tree_path(settings, tree.user_id, tree.slug)


def load_nodes(settings: Settings, tree: m.Tree) -> list[dict[str, Any]]:
    path = resolve_path(settings, tree)
    if not path.is_file():
        raise TreeNotFound(tree.slug)
    return read_nodes(path)


def save_nodes(settings: Settings, tree: m.Tree, nodes: list[dict[str, Any]]) -> None:
    write_nodes(resolve_path(settings, tree), nodes)


# --- the rows ----------------------------------------------------------------


async def list_for_user(session: AsyncSession, user: m.User) -> list[m.Tree]:
    rows = await session.execute(
        select(m.Tree).where(m.Tree.user_id == user.id).order_by(m.Tree.created_at)
    )
    return list(rows.scalars().all())


async def get(
    session: AsyncSession, user: m.User, slug: str = DEFAULT_SLUG
) -> m.Tree | None:
    """This user's tree, or ``None``. Scoped by ``user_id`` in the query itself,
    so there is no path where another account's row is fetched and then checked."""
    try:
        check_slug(slug)
    except InvalidSlug:
        return None
    rows = await session.execute(
        select(m.Tree).where(m.Tree.user_id == user.id, m.Tree.slug == slug)
    )
    return rows.scalars().first()


async def fork(
    session: AsyncSession,
    user: m.User,
    *,
    settings: Settings,
    slug: str = DEFAULT_SLUG,
) -> m.Tree:
    """Copy the public tree into ``user``'s store and record the row.

    Order matters: the owner's row is locked, the quota is checked, the row is
    written, then the file is copied. The lock is not decoration — the quota is
    a ``count(*)`` over ``trees``, and under ``READ COMMITTED`` two concurrent
    forks would otherwise both count zero and both be allowed. Locking
    ``users`` for the transaction serialises forks per account and nothing
    else. The file copy comes last, so a copy that fails leaves no row: the
    caller has not committed yet.
    """
    check_slug(slug)
    if await get(session, user, slug) is not None:
        raise TreeExists(slug)

    # Serialise this account's forks against each other before counting them.
    await session.execute(
        select(m.User.id).where(m.User.id == user.id).with_for_update()
    )
    verdict = await ledger.check_quota(session, user, QUOTA_FEATURE)
    if not verdict.allowed:
        raise QuotaExceeded(verdict)

    source = public_tree_path()
    row = m.Tree(
        user_id=user.id,
        slug=slug,
        forked_from_sha=sha_of(source),
        path=relative_path(user.id, slug),
    )
    session.add(row)
    await session.flush()

    # A byte-for-byte copy (master §4), not a re-serialisation: the sha above
    # must describe exactly what is now in the private file.
    destination = tree_path(settings, user.id, slug)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    return row


# --- validation --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Validation:
    """What `concept_tree.py validate` found, split by what it means."""

    #: Structural defects in *this* tree: dangling parents, one-way parent/child
    #: links, duplicate concepts, shared slugs.
    problems: list[str] = field(default_factory=list)
    #: Findings about the machine, not the tree (a skill that is not installed
    #: here). Reported, never fatal — they differ between the box and CI.
    warnings: list[str] = field(default_factory=list)
    node_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "problems": list(self.problems),
                "warnings": list(self.warnings), "node_count": self.node_count}


def validate_path(path: Path) -> Validation:
    """Run the hub's own validator over one tree file.

    The queue and research-state paths are pointed inside the tree's own
    directory: they are hub run-state, and a private tree must never read (or
    be influenced by) the hub's.
    """
    tree = concept_tree().ConceptTree.load(
        path, path.parent / QUEUE_FILE, path.parent / STATE_FILE
    )
    problems, warnings = [], []
    for finding in tree.validate():
        (warnings if _SKILL_FINDING.search(finding) else problems).append(finding)
    return Validation(problems=problems, warnings=warnings, node_count=len(tree.nodes))


def validate(settings: Settings, tree: m.Tree) -> Validation:
    path = resolve_path(settings, tree)
    if not path.is_file():
        raise TreeNotFound(tree.slug)
    return validate_path(path)


# --- serialisation -----------------------------------------------------------


def public_view(tree: m.Tree, *, node_count: int | None = None) -> dict[str, Any]:
    """A tree row as its owner may see it. An allow-list: no column added later
    can leak into a response by accident."""
    view: dict[str, Any] = {
        "id": tree.id,
        "slug": tree.slug,
        "forked_from_sha": tree.forked_from_sha,
        "path": tree.path,
        "created_at": tree.created_at,
        "updated_at": tree.updated_at,
    }
    if node_count is not None:
        view["node_count"] = node_count
    return view


__all__ = [
    "DEFAULT_SLUG",
    "MINE",
    "PUBLIC",
    "QUOTA_FEATURE",
    "SLUG_RE",
    "InvalidSlug",
    "PublicTreeMissing",
    "QuotaExceeded",
    "TreeError",
    "TreeExists",
    "TreeNotFound",
    "Validation",
    "check_slug",
    "concept_tree",
    "fork",
    "get",
    "list_for_user",
    "load_nodes",
    "public_nodes",
    "public_sha",
    "public_tree_path",
    "public_view",
    "read_nodes",
    "relative_path",
    "resolve_path",
    "save_nodes",
    "sha_of",
    "tree_dir",
    "tree_path",
    "validate",
    "validate_path",
    "write_nodes",
]

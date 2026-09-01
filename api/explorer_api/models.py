"""The tables.

Authority: `docs/site/00-platform-design.md` §4 (core entities, job/ledger
shapes), component 15 §3 (the ledger contract) and §7 (accounts, billing),
component 13 §7 (`api_keys`), component 09 §7 (private trees) and component
05 §7 (`proposals`, `moderation`). Where a spoke and the master disagree the
master wins — it says so itself.

Three rules from the plan's Global Constraints are enforced *in the database*,
not merely in Python, because a bug here costs money or leaks data:

* **Money is `numeric(12,6)`** everywhere and reaches Python as ``Decimal``.
  :data:`Money` is the only money type; nothing declares its own.
* **The ledger is append-only.** :data:`LEDGER_APPEND_ONLY_DDL` installs a
  ``BEFORE UPDATE OR DELETE`` trigger that raises. A correction is a new row.
* **`job_events` is a replayable stream.** ``unique(job_id, seq)`` is what makes
  SSE `Last-Event-ID` resume exact rather than best-effort (master §5).

Vocabulary values (job kinds, artifact kinds, scopes, ledger components) are
`CHECK` constraints over text rather than native enums: the lists are owned by
the design docs and grow task by task, and widening a CHECK is a one-line
migration where widening a PostgreSQL enum is not.
"""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import (
    DDL,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# --- shared column types -----------------------------------------------------

#: Money. Global constraint: `numeric(12,6)` in Postgres, `Decimal` in Python,
#: never float — six decimals is a tenth of a micro-dollar, below any real price.
Money = Numeric(12, 6, asdecimal=True)

MONEY_SCALE = 6
MONEY_PRECISION = 12

Timestamp = DateTime(timezone=True)


def new_id(prefix: str) -> str:
    """`led_9f2c…` — prefixed ids, as component 15 §3's ledger row shows them."""
    return f"{prefix}_{uuid.uuid4().hex}"


def _id(prefix: str) -> Mapped[str]:
    return mapped_column(Text, primary_key=True, default=lambda: new_id(prefix))


def _one_of(column: str, values: tuple[str, ...], name: str) -> CheckConstraint:
    joined = ", ".join(f"'{v}'" for v in values)
    return CheckConstraint(f"{column} IN ({joined})", name=name)


# --- vocabularies (owned by the design docs) ---------------------------------

#: Master §4 / 15 §5.
PLAN_IDS = ("free", "starter", "pro")
#: 15 §2 — `read` reads, `run` is metered, `publish` goes through moderation.
KEY_SCOPES = ("read", "run", "publish")
#: Master §4.
JOB_KINDS = (
    "lint", "optimize", "notes", "topical", "abstract", "pack", "deepen", "research",
    "family", "resolve", "index", "benchmark", "probe", "publish",
)
#: Master §5 lifecycle, plus `held` for the open-circuit-breaker hold (master §7).
JOB_STATUSES = ("created", "queued", "running", "held", "done", "failed", "cancelled")
#: Master §4 — the SSE source.
JOB_EVENT_KINDS = ("stage", "iteration", "findings", "tokens", "log")
#: Master §4 "Artifact kinds every surface accepts".
ARTIFACT_KINDS = (
    "index", "family", "full", "small", "facts", "split-root", "vocabulary",
    "concept-pack",
)
#: 15 §3 — "every component that spends; 10 writes none".
LEDGER_COMPONENTS = ("01", "02", "05", "06", "07", "08", "13", "16", "17")
#: 15 §3.
LEDGER_KINDS = ("input", "output", "embedding", "storage_mb_month")
#: 05 §7 / master §4.
PROPOSAL_STATUSES = ("proposed", "merged", "rejected")
MODERATION_STATES = ("pending", "approved", "rejected")
MODERATION_SUBJECTS = ("proposal", "contribution", "artifact")
#: Stripe's subscription states, as the webhook (Task 6) reports them.
SUBSCRIPTION_STATES = (
    "incomplete", "incomplete_expired", "trialing", "active", "past_due",
    "canceled", "unpaid", "paused",
)
OAUTH_PROVIDERS = ("github", "google")


# --- accounts ----------------------------------------------------------------


class User(Base):
    """15 §7 `users(id, email, created, org_id)`; `org_id` is reserved, not used."""

    __tablename__ = "users"

    id: Mapped[str] = _id("usr")
    #: Only ever an address a provider *proved*. A claimed-but-unproven address
    #: lives in :attr:`pending_email`, so an unverified sign-up can never be the
    #: row a later verified sign-in merges into.
    email: Mapped[str | None] = mapped_column(Text, unique=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False,
                                                 server_default="false")
    #: What the account *says* its address is, before anything proved it (a
    #: passkey sign-up types it into an unauthenticated request body). Not
    #: unique, never merged on, and never returned as the account's email.
    pending_email: Mapped[str | None] = mapped_column(Text)
    #: Bumped to invalidate every session token already issued for this account
    #: ("sign out everywhere"). The signed cookie carries the epoch it was
    #: minted at; a stale one is refused.
    session_epoch: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    #: 15 §5's ``overage`` is "opt-in" on the paid plans — this is the opt. Without
    #: it a balance at or below zero is a hard stop (master §7).
    overage_opt_in: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(Text)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"), default="free", server_default="free"
    )
    #: Orgs/teams are 15 §2's "later"; the column is reserved so the migration
    #: that adds them does not have to rewrite `users`.
    org_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)

    plan: Mapped[Plan] = relationship(back_populates="users", lazy="raise")


class Passkey(Base):
    """15 §7 `auth_passkeys` — WebAuthn credentials (Task 3 uses them)."""

    __tablename__ = "auth_passkeys"

    id: Mapped[str] = _id("pk")
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    credential_id: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    public_key: Mapped[bytes] = mapped_column(LargeBinary)
    sign_count: Mapped[int] = mapped_column(BIGINT, default=0, server_default="0")
    transports: Mapped[list | None] = mapped_column(JSONB)
    aaguid: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    last_used_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)


class OAuthAccount(Base):
    """15 §7 `auth_oauth`. `unique(provider, provider_account_id)` is what stops
    a second sign-in from the same GitHub account creating a second user."""

    __tablename__ = "auth_oauth"
    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id",
                         name="uq_auth_oauth_provider_provider_account_id"),
        _one_of("provider", OAUTH_PROVIDERS, "auth_oauth_provider"),
    )

    id: Mapped[str] = _id("oa")
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(32))
    provider_account_id: Mapped[str] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False,
                                                 server_default="false")
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    last_used_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)


class ApiKey(Base):
    """13 §7 `api_keys(id, user_id, prefix, hash, scopes[], created, last_used, revoked)`.

    The plaintext is never here: `prefix` is the non-secret lookup half and
    `hash` is Argon2id over the secret half (Task 4 owns the hashing).
    """

    __tablename__ = "api_keys"
    __table_args__ = (
        CheckConstraint("scopes <@ ARRAY['read','run','publish']::text[]",
                        name="ck_api_keys_scopes"),
        CheckConstraint("array_length(scopes, 1) >= 1", name="ck_api_keys_scopes_nonempty"),
    )

    id: Mapped[str] = _id("key")
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str | None] = mapped_column(Text)
    #: Indexed and unique: authentication is one lookup by prefix, then one
    #: Argon2 verify — never a scan over every hash.
    prefix: Mapped[str] = mapped_column(Text, unique=True, index=True)
    hash: Mapped[str] = mapped_column(Text)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    #: 15 §10 key-leak response: a per-key daily spend cap.
    max_usd_day: Mapped[Decimal | None] = mapped_column(Money)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    last_used_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)


# --- plans, subscriptions, credits, prices -----------------------------------


class Plan(Base):
    """15 §5 as a row. `api/plans.py` (Task 5) is the authority for the numbers;
    this table is where they are persisted and joined from."""

    __tablename__ = "plans"
    __table_args__ = (_one_of("id", PLAN_IDS, "plans_id"),)

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    price_usd: Mapped[Decimal] = mapped_column(Money, server_default="0")
    included_credit_usd: Mapped[Decimal] = mapped_column(Money, server_default="0")
    #: The 15 §5 feature table, as data — no threshold is written inline in a route.
    quotas: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    stripe_price_id: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, server_default="0")
    active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    users: Mapped[list[User]] = relationship(back_populates="plan", lazy="raise")


class Subscription(Base):
    """15 §7 `subscriptions(user_id, plan_id, stripe_sub_id, state, period_*)`."""

    __tablename__ = "subscriptions"
    __table_args__ = (_one_of("state", SUBSCRIPTION_STATES, "subscriptions_state"),)

    id: Mapped[str] = _id("sub")
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"))
    stripe_customer_id: Mapped[str | None] = mapped_column(Text, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text, unique=True)
    state: Mapped[str] = mapped_column(String(24))
    #: 15 §5: a cancellation downgrades at period end, not immediately (Task 6).
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    period_start: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    period_end: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


class Credit(Base):
    """15 §7 `credits(user_id, balance_usd, updated)` — one row per user."""

    __tablename__ = "credits"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    balance_usd: Mapped[Decimal] = mapped_column(Money, server_default="0")
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


class CreditGrant(Base):
    """One invoice's included credit, claimed exactly once.

    ``stripe_events`` dedupes on the *event* id, which only stops a byte-identical
    redelivery. Stripe emits more than one event for the same invoice routinely (a
    dashboard "Resend", a re-subscribed endpoint, an account-level plus a Connect
    delivery), and each of those carries a fresh event id. The invoice id is the
    thing that must be idempotent, so it is this table's primary key: the grant
    happens only for the delivery that wins the insert.
    """

    __tablename__ = "credit_grants"

    #: Stripe's invoice id (`in_…`). The primary key *is* the idempotency.
    invoice_id: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    subscription_id: Mapped[str | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL")
    )
    amount_usd: Mapped[Decimal] = mapped_column(Money)
    granted_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())


class Price(Base):
    """15 §7 `prices(model, kind, unit_cost_usd, price_usd, effective_from)`.

    Owner-tunable in Postgres, per 15 §3 — the price list is data, so a margin
    change is an insert, not a deploy.
    """

    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("model", "kind", "effective_from",
                         name="uq_prices_model_kind_effective_from"),
        _one_of("kind", LEDGER_KINDS, "prices_kind"),
    )

    id: Mapped[str] = _id("prc")
    model: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(24))
    unit_cost_usd: Mapped[Decimal] = mapped_column(Money)
    price_usd: Mapped[Decimal] = mapped_column(Money)
    effective_from: Mapped[dt.date] = mapped_column(Date, server_default=func.current_date())
    note: Mapped[str | None] = mapped_column(Text)


# --- the ledger --------------------------------------------------------------


class LedgerEntry(Base):
    """15 §3, verbatim: the contract every metered component writes.

    No `updated_at`: rows are never touched after insert. The trigger below
    enforces that in the database, so a future route cannot quietly rewrite
    history through the ORM.
    """

    __tablename__ = "ledger"
    __table_args__ = (
        _one_of("component", LEDGER_COMPONENTS, "ledger_component"),
        _one_of("kind", LEDGER_KINDS, "ledger_kind"),
        CheckConstraint("units >= 0", name="ck_ledger_units_non_negative"),
        Index("ix_ledger_user_id_at", "user_id", "at"),
        #: The per-key daily spend cap sums over exactly this.
        Index("ix_ledger_api_key_id_at", "api_key_id", "at"),
        Index("ix_ledger_client_ip_at", "client_ip", "at"),
    )

    id: Mapped[str] = _id("led")
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    #: The MCP call this row belongs to, when the spend came through the gateway
    #: rather than a job (13 §7 `mcp_calls` is the source; 15 §3 names the field).
    call_id: Mapped[str | None] = mapped_column(Text)
    #: The key that spent this, when the spend came through the gateway. It is
    #: what makes 15 §10's per-key `max_usd_day` cap answerable from one query.
    #: `SET NULL` because a key is revoked, never deleted — but a future purge
    #: must not take the ledger row with it.
    api_key_id: Mapped[str | None] = mapped_column(
        ForeignKey("api_keys.id", ondelete="SET NULL"), index=True
    )
    #: The caller's address, so 15 §9's free-tier ceilings can be enforced "per
    #: user **and** per IP". Text rather than `inet`: the gateway also records
    #: "unknown" when there is no address to record.
    client_ip: Mapped[str | None] = mapped_column(Text)
    component: Mapped[str] = mapped_column(String(2))
    model: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(24))
    units: Mapped[int] = mapped_column(BIGINT)
    unit_cost_usd: Mapped[Decimal] = mapped_column(Money)
    price_usd: Mapped[Decimal] = mapped_column(Money)
    billable: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    #: `polish|bulk|verify|query` (15 §3) — and why a row is not billable, which
    #: is how a failed verify gate explains itself (master §5, 15 §8).
    reason: Mapped[str | None] = mapped_column(Text)
    at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())


#: Append-only, enforced by the database. `RAISE EXCEPTION` aborts the statement,
#: so an UPDATE or DELETE fails the transaction rather than silently doing nothing.
#:
#: One statement per element: asyncpg prepares every statement it is given and
#: refuses a script, so this can never be a single semicolon-joined string.
LEDGER_APPEND_ONLY_SQL: tuple[str, ...] = (
    """
    CREATE OR REPLACE FUNCTION ledger_is_append_only() RETURNS trigger AS $fn$
    BEGIN
        IF TG_OP = 'TRUNCATE' THEN
            RAISE EXCEPTION
                'ledger is append-only: TRUNCATE refused; record correcting rows instead'
                USING ERRCODE = 'restrict_violation';
        END IF;
        RAISE EXCEPTION
            'ledger is append-only: % refused on row %; record a correcting row instead',
            TG_OP, OLD.id
            USING ERRCODE = 'restrict_violation';
    END;
    $fn$ LANGUAGE plpgsql
    """,
    "DROP TRIGGER IF EXISTS ledger_append_only ON ledger",
    """
    CREATE TRIGGER ledger_append_only
        BEFORE UPDATE OR DELETE ON ledger
        FOR EACH ROW EXECUTE FUNCTION ledger_is_append_only()
    """,
    # A row-level trigger cannot fire for TRUNCATE — it is a statement-level,
    # DDL-ish operation — so "append-only" without this one is erasable in a
    # single statement by anything holding the table.
    "DROP TRIGGER IF EXISTS ledger_append_only_truncate ON ledger",
    """
    CREATE TRIGGER ledger_append_only_truncate
        BEFORE TRUNCATE ON ledger
        FOR EACH STATEMENT EXECUTE FUNCTION ledger_is_append_only()
    """,
)

LEDGER_APPEND_ONLY_DROP_SQL: tuple[str, ...] = (
    "DROP TRIGGER IF EXISTS ledger_append_only ON ledger",
    "DROP TRIGGER IF EXISTS ledger_append_only_truncate ON ledger",
    "DROP FUNCTION IF EXISTS ledger_is_append_only()",
)

# Attach to metadata creation too, so any path that builds the schema without
# Alembic (a scratch database, a future test helper) still gets the guarantee.
for _statement in LEDGER_APPEND_ONLY_SQL:
    event.listen(
        LedgerEntry.__table__,
        "after_create",
        DDL(_statement).execute_if(dialect="postgresql"),
    )


# --- jobs --------------------------------------------------------------------


class Job(Base):
    """Master §4/§5. One `jobs` table for every component — the master forbids
    parallel job tables and a second status route."""

    __tablename__ = "jobs"
    __table_args__ = (
        _one_of("kind", JOB_KINDS, "jobs_kind"),
        _one_of("status", JOB_STATUSES, "jobs_status"),
        CheckConstraint("attempts >= 0", name="ck_jobs_attempts_non_negative"),
        Index("ix_jobs_status_lease_expires", "status", "lease_expires"),
        #: Master §5 idempotency: same user + input hash + params within 24 h
        #: returns the prior job. The index is what makes that lookup cheap.
        Index("ix_jobs_user_id_input_hash", "user_id", "input_hash"),
    )

    id: Mapped[str] = _id("job")
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(24))
    input_ref: Mapped[str | None] = mapped_column(Text)
    input_hash: Mapped[str | None] = mapped_column(Text)
    params: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    status: Mapped[str] = mapped_column(String(16), default="created",
                                        server_default="created")
    budget_usd: Mapped[Decimal | None] = mapped_column(Money)
    estimate_usd: Mapped[Decimal | None] = mapped_column(Money)
    # --- lease, so the reaper can requeue an expired one (master §5) ---
    worker: Mapped[str | None] = mapped_column(Text)
    lease_expires: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_heartbeat: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    # --- outcome ---
    started_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    finished_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    cost_tokens: Mapped[int] = mapped_column(BIGINT, default=0, server_default="0")
    cost_usd: Mapped[Decimal] = mapped_column(Money, server_default="0")
    artifact_ref: Mapped[str | None] = mapped_column(Text)
    log_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


class JobEvent(Base):
    """Master §4/§5 — the SSE source. `unique(job_id, seq)` makes `Last-Event-ID`
    resume exact: an event is identified by its sequence, and a sequence never
    means two things."""

    __tablename__ = "job_events"
    __table_args__ = (
        UniqueConstraint("job_id", "seq", name="uq_job_events_job_id_seq"),
        _one_of("kind", JOB_EVENT_KINDS, "job_events_kind"),
        CheckConstraint("seq >= 1", name="ck_job_events_seq_positive"),
    )

    id: Mapped[str] = _id("jev")
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer)
    ts: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    kind: Mapped[str] = mapped_column(String(16))
    payload: Mapped[dict] = mapped_column(JSONB, server_default="{}")


# --- artifacts, trees, governance --------------------------------------------


class Artifact(Base):
    """Master §4 `Artifact(id, owner[user|public], kind, path, manifest_json,
    lint_summary_json, published_at)`."""

    __tablename__ = "artifacts"
    __table_args__ = (
        _one_of("kind", ARTIFACT_KINDS, "artifacts_kind"),
        _one_of("visibility", ("public", "private"), "artifacts_visibility"),
        #: A private artifact without an owner would be unreachable and
        #: unaccountable; `/u/<user>/…` needs the owner to authorise a read.
        CheckConstraint(
            "(visibility = 'public' AND owner_user_id IS NULL) "
            "OR (visibility = 'private' AND owner_user_id IS NOT NULL)",
            name="ck_artifacts_private_has_owner",
        ),
    )

    id: Mapped[str] = _id("art")
    owner_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    visibility: Mapped[str] = mapped_column(String(8), default="public",
                                            server_default="public")
    kind: Mapped[str] = mapped_column(String(24))
    slug: Mapped[str] = mapped_column(Text, index=True)
    path: Mapped[str] = mapped_column(Text)
    manifest_json: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    lint_summary_json: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"))
    published_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


class Tree(Base):
    """Master §4 / 09 §7 `trees(user_id, forked_from_sha, updated_at)` — a
    listing row only. The file at `path` stays the truth so `concept_tree.py`
    works unchanged; `slug` exists because the plan quota is per tree
    (free 1, starter 3, pro 20), not per user."""

    __tablename__ = "trees"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_trees_user_id_slug"),)

    id: Mapped[str] = _id("tree")
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(Text, default="me", server_default="me")
    forked_from_sha: Mapped[str] = mapped_column(Text)
    path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


class Proposal(Base):
    """Master §4 / 05 §7 — a merge-back proposal from a private tree."""

    __tablename__ = "proposals"
    __table_args__ = (_one_of("status", PROPOSAL_STATUSES, "proposals_status"),)

    id: Mapped[str] = _id("prop")
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    tree_id: Mapped[str | None] = mapped_column(ForeignKey("trees.id", ondelete="SET NULL"))
    #: The public sha the diff was taken against — a stale one is a 409 (Task 10).
    tree_sha: Mapped[str] = mapped_column(Text)
    patch_json: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="proposed",
                                        server_default="proposed")
    #: The lint gate's findings, kept with the proposal so an auto-rejection can
    #: show its reasons (master §9).
    lint_json: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    moderator_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


class ModerationItem(Base):
    """05 §7 `moderation` — the queue, over proposals and contributions alike,
    so 8a's 48 h turnaround is measured in one place."""

    __tablename__ = "moderation"
    __table_args__ = (
        _one_of("subject_kind", MODERATION_SUBJECTS, "moderation_subject_kind"),
        _one_of("state", MODERATION_STATES, "moderation_state"),
        UniqueConstraint("subject_kind", "subject_id",
                         name="uq_moderation_subject_kind_subject_id"),
        Index("ix_moderation_state_created_at", "state", "created_at"),
    )

    id: Mapped[str] = _id("mod")
    subject_kind: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), default="pending",
                                       server_default="pending")
    assignee_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    findings_json: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        Timestamp, server_default=func.now(), onupdate=func.now()
    )


# --- billing plumbing --------------------------------------------------------


class Subscriber(Base):
    """Blog change-notice mailing list. Not part of the master plan's numbered
    components — a small standalone subsystem: an email address, a double
    opt-in confirmation, and a one-click unsubscribe token.

    Double opt-in (``confirmed_at`` starts ``NULL``) rather than "subscribed on
    submit": an address the submitter does not own must never start receiving
    mail. Only rows with ``confirmed_at IS NOT NULL`` and
    ``unsubscribed_at IS NULL`` are notified (see ``notify.py``).
    """

    __tablename__ = "subscribers"

    id: Mapped[str] = _id("nsub")
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    #: Consumed once, by `GET /api/subscribers/confirm`.
    confirm_token: Mapped[str] = mapped_column(Text, unique=True)
    confirmed_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    #: Never rotated once minted, so the link mailed at signup keeps working
    #: for as long as the row exists — an unsubscribe link that expired would
    #: leave someone unable to opt back out.
    unsubscribe_token: Mapped[str] = mapped_column(Text, unique=True)
    unsubscribed_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    created_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())


class StripeEvent(Base):
    """15 §7 `stripe_events(id, type, payload, processed_at)`.

    The primary key is Stripe's own event id: recording it *before* acting is
    what makes a replayed webhook a no-op (15 §9, Task 6).
    """

    __tablename__ = "stripe_events"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    received_at: Mapped[dt.datetime] = mapped_column(Timestamp, server_default=func.now())
    processed_at: Mapped[dt.datetime | None] = mapped_column(Timestamp)
    error: Mapped[str | None] = mapped_column(Text)


__all__ = [
    "ARTIFACT_KINDS",
    "JOB_EVENT_KINDS",
    "JOB_KINDS",
    "JOB_STATUSES",
    "KEY_SCOPES",
    "LEDGER_APPEND_ONLY_DROP_SQL",
    "LEDGER_APPEND_ONLY_SQL",
    "LEDGER_COMPONENTS",
    "LEDGER_KINDS",
    "MODERATION_STATES",
    "MODERATION_SUBJECTS",
    "OAUTH_PROVIDERS",
    "PLAN_IDS",
    "PROPOSAL_STATUSES",
    "SUBSCRIPTION_STATES",
    "ApiKey",
    "Artifact",
    "Base",
    "Credit",
    "CreditGrant",
    "Job",
    "JobEvent",
    "LedgerEntry",
    "ModerationItem",
    "Money",
    "OAuthAccount",
    "Passkey",
    "Plan",
    "Price",
    "Proposal",
    "StripeEvent",
    "Subscriber",
    "Subscription",
    "Tree",
    "User",
    "new_id",
]

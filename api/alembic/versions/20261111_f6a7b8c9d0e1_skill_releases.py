"""Private owner-namespaced skill releases and explicit sharing grants."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "skill_releases",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("release_sha256", sa.String(64), nullable=False),
        sa.Column("manifest", postgresql.JSONB(), nullable=False),
        sa.Column("bundle", sa.LargeBinary(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "name", "version", name="uq_skill_release_version"),
        sa.CheckConstraint("size_bytes > 0 AND size_bytes <= 6291456", name="skill_release_size"),
    )
    op.create_index("ix_skill_releases_user_created", "skill_releases", ["user_id", "created_at"])
    op.execute(
        "CREATE INDEX ix_skill_releases_search ON skill_releases USING gin (to_tsvector('simple', search_text))"
    )
    op.create_table(
        "skill_release_grants",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "release_id",
            sa.Text(),
            sa.ForeignKey("skill_releases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("release_id", "user_id", name="uq_skill_release_grant"),
    )
    op.create_index("ix_skill_release_grants_user_id", "skill_release_grants", ["user_id"])
    op.execute("""
      CREATE FUNCTION refuse_skill_release_update() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RAISE EXCEPTION 'skill release content is immutable'; END; $$;
    """)
    op.execute("""CREATE TRIGGER skill_release_immutable BEFORE UPDATE ON skill_releases
      FOR EACH ROW EXECUTE FUNCTION refuse_skill_release_update()""")


def downgrade():
    op.drop_table("skill_release_grants")
    op.drop_table("skill_releases")
    op.execute("DROP FUNCTION refuse_skill_release_update()")

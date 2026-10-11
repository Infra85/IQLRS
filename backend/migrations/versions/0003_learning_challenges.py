"""Add curriculum activity workspaces and immutable attempts; preserve legacy tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0003_learning_challenges"
down_revision = "0002_hardware_jobs"
branch_labels = None
depends_on = None


def upgrade():
    for name in ["challenge_workspaces", "challenge_attempts"]:
        shared = [
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                UUID(as_uuid=True),
                sa.ForeignKey("users.user_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("challenge_id", sa.String(80), nullable=False),
            sa.Column("version", sa.Integer, nullable=False),
            sa.Column("revision", UUID(as_uuid=True), nullable=False),
            sa.Column("fingerprint", sa.String(64), nullable=False),
            sa.Column("circuit", JSONB, nullable=False),
            sa.Column("prediction", JSONB, nullable=False),
            sa.Column("hints_used", sa.Integer, nullable=False),
        ]
        if name == "challenge_workspaces":
            extra = [
                sa.Column("execution", JSONB),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
                sa.UniqueConstraint("user_id", "challenge_id"),
            ]
        else:
            extra = [
                sa.Column("module_id", sa.Integer, nullable=False),
                sa.Column("number", sa.Integer, nullable=False),
                sa.Column("simulation", JSONB),
                sa.Column("result", JSONB, nullable=False),
                sa.Column("passed", sa.Boolean, nullable=False),
                sa.Column("score", sa.Integer, nullable=False),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("completed_at", sa.DateTime(timezone=True)),
                sa.UniqueConstraint("user_id", "challenge_id", "revision"),
                sa.UniqueConstraint("user_id", "challenge_id", "number"),
            ]
        op.create_table(name, *shared, *extra)
        op.create_index("ix_" + name + "_user_id", name, ["user_id"])


def downgrade():
    op.drop_table("challenge_attempts")
    op.drop_table("challenge_workspaces")

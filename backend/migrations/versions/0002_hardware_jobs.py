"""Add durable hardware jobs to the existing version-1 schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0002_hardware_jobs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "hardware_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(80), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("provider_job_id", sa.String(512)),
        sa.Column("device_id", sa.String(512), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("shots", sa.Integer, nullable=False),
        sa.Column("circuit", JSONB, nullable=False),
        sa.Column("execution_metadata", JSONB, nullable=False),
        sa.Column("result", JSONB),
        sa.Column("failure", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("polled_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "idempotency_key"),
        sa.CheckConstraint("shots > 0"),
    )
    op.create_index("ix_hardware_jobs_user_id", "hardware_jobs", ["user_id"])
    op.create_index("ix_hardware_jobs_created_at", "hardware_jobs", ["created_at"])


def downgrade():
    op.drop_table("hardware_jobs")

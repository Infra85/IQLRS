"""Add lesson acknowledgements and resume cursor without changing legacy progress."""

from alembic import op

revision = "0004_lesson_journey"
down_revision = "0003_learning_challenges"
branch_labels = None
depends_on = None


def upgrade():
    # Fresh/legacy bootstrap creates this existing table from current metadata.
    op.execute("ALTER TABLE module_progress ADD COLUMN IF NOT EXISTS journey JSONB")


def downgrade():
    op.drop_column("module_progress", "journey")

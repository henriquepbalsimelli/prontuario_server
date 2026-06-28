"""add notes to consultation

Revision ID: 20260627_0010
Revises: 20260626_0009
Create Date: 2026-06-27 10:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260627_0010"
down_revision: str | None = "20260626_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("consultation", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("consultation", "notes")

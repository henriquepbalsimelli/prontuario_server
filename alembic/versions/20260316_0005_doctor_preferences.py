"""add preferences to doctor

Revision ID: 20260316_0005
Revises: 20260303_0004
Create Date: 2026-03-16 10:30:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260316_0005"
down_revision: str | None = "20260303_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "doctor",
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("doctor", "preferences", server_default=None)


def downgrade() -> None:
    op.drop_column("doctor", "preferences")

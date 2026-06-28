"""add consultation scheduling fields

Revision ID: 20260624_0007
Revises: 20260604_0006
Create Date: 2026-06-24 00:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260624_0007"
down_revision: str | None = "20260604_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "consultation",
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "consultation",
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("consultation", sa.Column("status", sa.String(length=30), nullable=True))
    op.create_index(
        "ix_consultation_doctor_scheduled_start_at",
        "consultation",
        ["doctor_id", "scheduled_start_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_consultation_doctor_scheduled_start_at", table_name="consultation")
    op.drop_column("consultation", "status")
    op.drop_column("consultation", "scheduled_end_at")
    op.drop_column("consultation", "scheduled_start_at")

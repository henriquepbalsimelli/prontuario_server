"""add prd1 consultation and patient core fields

Revision ID: 20260626_0008
Revises: 20260624_0007
Create Date: 2026-06-26 00:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260626_0008"
down_revision: str | None = "20260624_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patient", sa.Column("medical_history", sa.Text(), nullable=True))
    op.add_column("consultation", sa.Column("diagnosis", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("consultation", "diagnosis")
    op.drop_column("patient", "medical_history")

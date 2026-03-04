"""add request_id to audit log

Revision ID: 20260303_0004
Revises: 20260303_0003
Create Date: 2026-03-03 08:45:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260303_0004"
down_revision: str | None = "20260303_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("request_id", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_log", "request_id")

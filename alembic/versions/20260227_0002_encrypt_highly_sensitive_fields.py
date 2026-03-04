"""encrypt highly sensitive fields

Revision ID: 20260227_0002
Revises: 20260226_0001
Create Date: 2026-02-27 11:20:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260227_0002"
down_revision: str | None = "20260226_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "audit_log",
        "before_state",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        postgresql_using="before_state::text",
        existing_nullable=True,
    )
    op.alter_column(
        "audit_log",
        "after_state",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        postgresql_using="after_state::text",
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "audit_log",
        "after_state",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="after_state::jsonb",
        existing_nullable=True,
    )
    op.alter_column(
        "audit_log",
        "before_state",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="before_state::jsonb",
        existing_nullable=True,
    )

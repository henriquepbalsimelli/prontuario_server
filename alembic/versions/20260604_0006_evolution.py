"""add evolution table

Revision ID: 20260604_0006
Revises: 20260316_0005
Create Date: 2026-06-04 12:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260604_0006"
down_revision: str | None = "20260316_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evolution",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "consultation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("consultation.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("origin_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_evolution_doctor_id", "evolution", ["doctor_id"], unique=False)
    op.create_index("ix_evolution_patient_id", "evolution", ["patient_id"], unique=False)
    op.create_index("ix_evolution_consultation_id", "evolution", ["consultation_id"], unique=False)
    op.create_index(
        "ix_evolution_doctor_patient_occurred_at",
        "evolution",
        ["doctor_id", "patient_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_evolution_doctor_patient_occurred_at", table_name="evolution")
    op.drop_index("ix_evolution_consultation_id", table_name="evolution")
    op.drop_index("ix_evolution_patient_id", table_name="evolution")
    op.drop_index("ix_evolution_doctor_id", table_name="evolution")
    op.drop_table("evolution")

"""add medical history snapshots

Revision ID: 20260628_0011
Revises: 20260627_0010
Create Date: 2026-06-28 12:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260628_0011"
down_revision: str | None = "20260627_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patient_continuous_medication",
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_pcm_consultation_id_consultation",
        "patient_continuous_medication",
        "consultation",
        ["consultation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_patient_continuous_medication_consultation_id",
        "patient_continuous_medication",
        ["consultation_id"],
        unique=False,
    )

    op.create_table(
        "patient_medical_history",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), server_onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultation.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_medical_history_doctor_id", "patient_medical_history", ["doctor_id"], unique=False)
    op.create_index("ix_patient_medical_history_patient_id", "patient_medical_history", ["patient_id"], unique=False)
    op.create_index("ix_patient_medical_history_consultation_id", "patient_medical_history", ["consultation_id"], unique=False)
    op.create_index("ix_pmh_doctor_patient", "patient_medical_history", ["doctor_id", "patient_id"], unique=False)
    op.create_index(
        "ix_pmh_doctor_patient_consultation",
        "patient_medical_history",
        ["doctor_id", "patient_id", "consultation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pmh_doctor_patient_consultation", table_name="patient_medical_history")
    op.drop_index("ix_pmh_doctor_patient", table_name="patient_medical_history")
    op.drop_index("ix_patient_medical_history_consultation_id", table_name="patient_medical_history")
    op.drop_index("ix_patient_medical_history_patient_id", table_name="patient_medical_history")
    op.drop_index("ix_patient_medical_history_doctor_id", table_name="patient_medical_history")
    op.drop_table("patient_medical_history")

    op.drop_index("ix_patient_continuous_medication_consultation_id", table_name="patient_continuous_medication")
    op.drop_constraint("fk_pcm_consultation_id_consultation", "patient_continuous_medication", type_="foreignkey")
    op.drop_column("patient_continuous_medication", "consultation_id")

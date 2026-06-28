"""add prd1 remaining entities

Revision ID: 20260626_0009
Revises: 20260626_0008
Create Date: 2026-06-26 00:01:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260626_0009"
down_revision: str | None = "20260626_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patient_continuous_medication",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("dosage", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), server_onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_continuous_medication_doctor_id", "patient_continuous_medication", ["doctor_id"], unique=False)
    op.create_index("ix_patient_continuous_medication_patient_id", "patient_continuous_medication", ["patient_id"], unique=False)
    op.create_index("ix_pcm_doctor_patient", "patient_continuous_medication", ["doctor_id", "patient_id"], unique=False)
    op.create_index("ix_pcm_doctor_patient_status", "patient_continuous_medication", ["doctor_id", "patient_id", "status"], unique=False)

    op.create_table(
        "exam",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("exam_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="requested"),
        sa.Column("result_notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), server_onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultation.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exam_doctor_id", "exam", ["doctor_id"], unique=False)
    op.create_index("ix_exam_patient_id", "exam", ["patient_id"], unique=False)
    op.create_index("ix_exam_consultation_id", "exam", ["consultation_id"], unique=False)
    op.create_index("ix_exam_doctor_patient", "exam", ["doctor_id", "patient_id"], unique=False)
    op.create_index("ix_exam_doctor_patient_date", "exam", ["doctor_id", "patient_id", "exam_date"], unique=False)

    op.create_table(
        "procedure",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("procedure_date", sa.Date(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), server_onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultation.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_procedure_doctor_id", "procedure", ["doctor_id"], unique=False)
    op.create_index("ix_procedure_patient_id", "procedure", ["patient_id"], unique=False)
    op.create_index("ix_procedure_consultation_id", "procedure", ["consultation_id"], unique=False)
    op.create_index("ix_procedure_doctor_patient", "procedure", ["doctor_id", "patient_id"], unique=False)
    op.create_index("ix_procedure_doctor_patient_date", "procedure", ["doctor_id", "patient_id", "procedure_date"], unique=False)

    op.create_table(
        "doctor_template",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), server_onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_template_doctor_id", "doctor_template", ["doctor_id"], unique=False)
    op.create_index("ix_doctor_template_doctor_type", "doctor_template", ["doctor_id", "type"], unique=False)

    op.create_table(
        "text_document",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), server_onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultation.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["doctor_template.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_text_document_doctor_id", "text_document", ["doctor_id"], unique=False)
    op.create_index("ix_text_document_patient_id", "text_document", ["patient_id"], unique=False)
    op.create_index("ix_text_document_consultation_id", "text_document", ["consultation_id"], unique=False)
    op.create_index("ix_text_document_template_id", "text_document", ["template_id"], unique=False)
    op.create_index("ix_text_document_doctor_patient", "text_document", ["doctor_id", "patient_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_text_document_doctor_patient", table_name="text_document")
    op.drop_index("ix_text_document_template_id", table_name="text_document")
    op.drop_index("ix_text_document_consultation_id", table_name="text_document")
    op.drop_index("ix_text_document_patient_id", table_name="text_document")
    op.drop_index("ix_text_document_doctor_id", table_name="text_document")
    op.drop_table("text_document")

    op.drop_index("ix_doctor_template_doctor_type", table_name="doctor_template")
    op.drop_index("ix_doctor_template_doctor_id", table_name="doctor_template")
    op.drop_table("doctor_template")

    op.drop_index("ix_procedure_doctor_patient_date", table_name="procedure")
    op.drop_index("ix_procedure_doctor_patient", table_name="procedure")
    op.drop_index("ix_procedure_consultation_id", table_name="procedure")
    op.drop_index("ix_procedure_patient_id", table_name="procedure")
    op.drop_index("ix_procedure_doctor_id", table_name="procedure")
    op.drop_table("procedure")

    op.drop_index("ix_exam_doctor_patient_date", table_name="exam")
    op.drop_index("ix_exam_doctor_patient", table_name="exam")
    op.drop_index("ix_exam_consultation_id", table_name="exam")
    op.drop_index("ix_exam_patient_id", table_name="exam")
    op.drop_index("ix_exam_doctor_id", table_name="exam")
    op.drop_table("exam")

    op.drop_index("ix_pcm_doctor_patient_status", table_name="patient_continuous_medication")
    op.drop_index("ix_pcm_doctor_patient", table_name="patient_continuous_medication")
    op.drop_index("ix_patient_continuous_medication_patient_id", table_name="patient_continuous_medication")
    op.drop_index("ix_patient_continuous_medication_doctor_id", table_name="patient_continuous_medication")
    op.drop_table("patient_continuous_medication")

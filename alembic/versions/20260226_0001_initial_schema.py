"""initial schema

Revision ID: 20260226_0001
Revises:
Create Date: 2026-02-26 09:00:00

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260226_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "doctor",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_doctor_email", "doctor", ["email"], unique=True)

    op.create_table(
        "disease",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("cid10", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "medication",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("active_principle", sa.String(length=255), nullable=True),
        sa.Column("form", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "patient",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=30), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_patient_doctor_id", "patient", ["doctor_id"], unique=False)
    op.create_index("ix_patient_doctor_created_at", "patient", ["doctor_id", "created_at"], unique=False)

    op.create_table(
        "consultation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consultation_date", sa.Date(), nullable=True),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("physical_exam", sa.Text(), nullable=True),
        sa.Column("conduct", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_consultation_doctor_id", "consultation", ["doctor_id"], unique=False)
    op.create_index("ix_consultation_patient_id", "consultation", ["patient_id"], unique=False)
    op.create_index("ix_consultation_doctor_created_at", "consultation", ["doctor_id", "created_at"], unique=False)

    op.create_table(
        "image",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("consultation.id", ondelete="SET NULL"), nullable=True),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=True),
        sa.Column("body_region", sa.String(length=120), nullable=True),
        sa.Column("coord_x", sa.Float(), nullable=True),
        sa.Column("coord_y", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_image_doctor_id", "image", ["doctor_id"], unique=False)
    op.create_index("ix_image_patient_id", "image", ["patient_id"], unique=False)
    op.create_index("ix_image_consultation_id", "image", ["consultation_id"], unique=False)
    op.create_index("ix_image_doctor_created_at", "image", ["doctor_id", "created_at"], unique=False)

    op.create_table(
        "lesion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctor.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patient.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("body_region", sa.String(length=120), nullable=True),
        sa.Column("coord_x", sa.Float(), nullable=True),
        sa.Column("coord_y", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lesion_doctor_id", "lesion", ["doctor_id"], unique=False)
    op.create_index("ix_lesion_patient_id", "lesion", ["patient_id"], unique=False)
    op.create_index("ix_lesion_doctor_created_at", "lesion", ["doctor_id", "created_at"], unique=False)

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_log_doctor_id", "audit_log", ["doctor_id"], unique=False)
    op.create_index("ix_audit_log_doctor_created_at", "audit_log", ["doctor_id", "created_at"], unique=False)

    op.create_table(
        "domain_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("processed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_domain_event_processed", "domain_event", ["processed"], unique=False)
    op.create_index("ix_domain_event_created_at", "domain_event", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_domain_event_created_at", table_name="domain_event")
    op.drop_index("ix_domain_event_processed", table_name="domain_event")
    op.drop_table("domain_event")

    op.drop_index("ix_audit_log_doctor_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_doctor_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_lesion_doctor_created_at", table_name="lesion")
    op.drop_index("ix_lesion_patient_id", table_name="lesion")
    op.drop_index("ix_lesion_doctor_id", table_name="lesion")
    op.drop_table("lesion")

    op.drop_index("ix_image_doctor_created_at", table_name="image")
    op.drop_index("ix_image_consultation_id", table_name="image")
    op.drop_index("ix_image_patient_id", table_name="image")
    op.drop_index("ix_image_doctor_id", table_name="image")
    op.drop_table("image")

    op.drop_index("ix_consultation_doctor_created_at", table_name="consultation")
    op.drop_index("ix_consultation_patient_id", table_name="consultation")
    op.drop_index("ix_consultation_doctor_id", table_name="consultation")
    op.drop_table("consultation")

    op.drop_index("ix_patient_doctor_created_at", table_name="patient")
    op.drop_index("ix_patient_doctor_id", table_name="patient")
    op.drop_table("patient")

    op.drop_table("medication")
    op.drop_table("disease")

    op.drop_index("ix_doctor_email", table_name="doctor")
    op.drop_table("doctor")

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.infrastructure.security.field_encryption import EncryptedJSON, EncryptedString


class Doctor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "doctor"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )


class Patient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "patient"

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    medical_history: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    notes: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)


class Consultation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consultation"

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scheduled_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    notes: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    chief_complaint: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    physical_exam: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    conduct: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)


class PatientContinuousMedication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "patient_continuous_medication"
    __table_args__ = (
        Index("ix_pcm_doctor_patient", "doctor_id", "patient_id"),
        Index("ix_pcm_doctor_patient_status", "doctor_id", "patient_id", "status"),
    )

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    dosage: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    notes: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="active")


class PatientMedicalHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "patient_medical_history"
    __table_args__ = (
        Index("ix_pmh_doctor_patient", "doctor_id", "patient_id"),
        Index("ix_pmh_doctor_patient_consultation", "doctor_id", "patient_id", "consultation_id"),
    )

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    body: Mapped[str] = mapped_column(EncryptedString, nullable=False)


class Exam(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exam"
    __table_args__ = (
        Index("ix_exam_doctor_patient", "doctor_id", "patient_id"),
        Index("ix_exam_doctor_patient_date", "doctor_id", "patient_id", "exam_date"),
    )

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    type: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="requested")
    result_notes: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)


class Procedure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "procedure"
    __table_args__ = (
        Index("ix_procedure_doctor_patient", "doctor_id", "patient_id"),
        Index("ix_procedure_doctor_patient_date", "doctor_id", "patient_id", "procedure_date"),
    )

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    procedure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    description: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    notes: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)


class DoctorTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "doctor_template"
    __table_args__ = (Index("ix_doctor_template_doctor_type", "doctor_id", "type"),)

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    body: Mapped[str] = mapped_column(EncryptedString, nullable=False)


class TextDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "text_document"
    __table_args__ = (Index("ix_text_document_doctor_patient", "doctor_id", "patient_id"),)

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    template_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor_template.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    body: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, server_default="1")


class Disease(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "disease"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cid10: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Medication(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "medication"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    active_principle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    form: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Image(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "image"

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    body_region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    coord_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    coord_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    upload_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pending")
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Lesion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lesion"

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    coord_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    coord_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Evolution(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evolution"

    doctor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("doctor.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    consultation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consultation.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    origin_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        server_onupdate=text("now()"),
        nullable=False,
    )


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_log"

    doctor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(EncryptedJSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DomainEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "domain_event"

    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

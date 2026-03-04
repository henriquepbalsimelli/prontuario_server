from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.infrastructure.security.field_encryption import EncryptedJSON, EncryptedString


class Doctor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "doctor"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


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
    chief_complaint: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    physical_exam: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    conduct: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)


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

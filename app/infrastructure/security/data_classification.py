from enum import StrEnum


class DataSensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    HIGHLY_SENSITIVE = "highly_sensitive"


FIELD_SENSITIVITY: dict[str, DataSensitivity] = {
    "doctor.id": DataSensitivity.INTERNAL,
    "doctor.name": DataSensitivity.SENSITIVE,
    "doctor.email": DataSensitivity.SENSITIVE,
    "doctor.password_hash": DataSensitivity.HIGHLY_SENSITIVE,
    "doctor.preferences": DataSensitivity.INTERNAL,
    "doctor.created_at": DataSensitivity.INTERNAL,
    "patient.id": DataSensitivity.INTERNAL,
    "patient.doctor_id": DataSensitivity.INTERNAL,
    "patient.name": DataSensitivity.SENSITIVE,
    "patient.birth_date": DataSensitivity.SENSITIVE,
    "patient.gender": DataSensitivity.SENSITIVE,
    "patient.phone": DataSensitivity.SENSITIVE,
    "patient.notes": DataSensitivity.HIGHLY_SENSITIVE,
    "patient.created_at": DataSensitivity.INTERNAL,
    "consultation.id": DataSensitivity.INTERNAL,
    "consultation.doctor_id": DataSensitivity.INTERNAL,
    "consultation.patient_id": DataSensitivity.INTERNAL,
    "consultation.consultation_date": DataSensitivity.SENSITIVE,
    "consultation.chief_complaint": DataSensitivity.HIGHLY_SENSITIVE,
    "consultation.physical_exam": DataSensitivity.HIGHLY_SENSITIVE,
    "consultation.conduct": DataSensitivity.HIGHLY_SENSITIVE,
    "consultation.created_at": DataSensitivity.INTERNAL,
    "disease.id": DataSensitivity.INTERNAL,
    "disease.name": DataSensitivity.PUBLIC,
    "disease.cid10": DataSensitivity.PUBLIC,
    "disease.description": DataSensitivity.PUBLIC,
    "medication.id": DataSensitivity.INTERNAL,
    "medication.name": DataSensitivity.PUBLIC,
    "medication.active_principle": DataSensitivity.PUBLIC,
    "medication.form": DataSensitivity.PUBLIC,
    "medication.notes": DataSensitivity.INTERNAL,
    "image.id": DataSensitivity.INTERNAL,
    "image.doctor_id": DataSensitivity.INTERNAL,
    "image.patient_id": DataSensitivity.INTERNAL,
    "image.consultation_id": DataSensitivity.INTERNAL,
    "image.s3_key": DataSensitivity.HIGHLY_SENSITIVE,
    "image.type": DataSensitivity.SENSITIVE,
    "image.body_region": DataSensitivity.SENSITIVE,
    "image.coord_x": DataSensitivity.SENSITIVE,
    "image.coord_y": DataSensitivity.SENSITIVE,
    "image.created_at": DataSensitivity.INTERNAL,
    "lesion.id": DataSensitivity.INTERNAL,
    "lesion.doctor_id": DataSensitivity.INTERNAL,
    "lesion.patient_id": DataSensitivity.INTERNAL,
    "lesion.label": DataSensitivity.SENSITIVE,
    "lesion.body_region": DataSensitivity.SENSITIVE,
    "lesion.coord_x": DataSensitivity.SENSITIVE,
    "lesion.coord_y": DataSensitivity.SENSITIVE,
    "lesion.status": DataSensitivity.SENSITIVE,
    "lesion.notes": DataSensitivity.HIGHLY_SENSITIVE,
    "lesion.created_at": DataSensitivity.INTERNAL,
    "audit_log.id": DataSensitivity.INTERNAL,
    "audit_log.doctor_id": DataSensitivity.INTERNAL,
    "audit_log.entity_type": DataSensitivity.INTERNAL,
    "audit_log.entity_id": DataSensitivity.INTERNAL,
    "audit_log.action": DataSensitivity.INTERNAL,
    "audit_log.before_state": DataSensitivity.HIGHLY_SENSITIVE,
    "audit_log.after_state": DataSensitivity.HIGHLY_SENSITIVE,
    "audit_log.ip_address": DataSensitivity.SENSITIVE,
    "audit_log.user_agent": DataSensitivity.SENSITIVE,
    "audit_log.created_at": DataSensitivity.INTERNAL,
    "domain_event.id": DataSensitivity.INTERNAL,
    "domain_event.event_type": DataSensitivity.INTERNAL,
    "domain_event.entity_id": DataSensitivity.INTERNAL,
    "domain_event.payload": DataSensitivity.SENSITIVE,
    "domain_event.created_at": DataSensitivity.INTERNAL,
    "domain_event.processed": DataSensitivity.INTERNAL,
}


def get_field_sensitivity(field_path: str) -> DataSensitivity:
    return FIELD_SENSITIVITY.get(field_path, DataSensitivity.INTERNAL)


def is_sensitive(field_path: str) -> bool:
    level = get_field_sensitivity(field_path)
    return level in {DataSensitivity.SENSITIVE, DataSensitivity.HIGHLY_SENSITIVE}


def is_highly_sensitive(field_path: str) -> bool:
    return get_field_sensitivity(field_path) == DataSensitivity.HIGHLY_SENSITIVE

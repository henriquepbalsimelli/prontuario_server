from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.infrastructure.security.data_classification import DataSensitivity, FIELD_SENSITIVITY

MASK_VALUE = "***REDACTED***"

_ALWAYS_MASK_KEYS = {
    "authorization",
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "secret",
    "api_key",
}

_SENSITIVITY_ORDER = {
    DataSensitivity.PUBLIC: 0,
    DataSensitivity.INTERNAL: 1,
    DataSensitivity.SENSITIVE: 2,
    DataSensitivity.HIGHLY_SENSITIVE: 3,
}

_FIELD_LEVEL_BY_NAME: dict[str, DataSensitivity] = {}
for field_path, sensitivity in FIELD_SENSITIVITY.items():
    _, _, field_name = field_path.partition(".")
    current = _FIELD_LEVEL_BY_NAME.get(field_name)
    if current is None or _SENSITIVITY_ORDER[sensitivity] > _SENSITIVITY_ORDER[current]:
        _FIELD_LEVEL_BY_NAME[field_name] = sensitivity


def _resolve_sensitivity(field_name: str) -> DataSensitivity:
    normalized = field_name.strip().lower()
    if normalized in _ALWAYS_MASK_KEYS:
        return DataSensitivity.HIGHLY_SENSITIVE
    return _FIELD_LEVEL_BY_NAME.get(normalized, DataSensitivity.INTERNAL)


def _mask_scalar(value: Any) -> Any:
    if value is None:
        return None
    return MASK_VALUE


def mask_payload(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        masked: dict[str, Any] = {}
        for key, value in payload.items():
            key_str = str(key)
            sensitivity = _resolve_sensitivity(key_str)
            if sensitivity in {DataSensitivity.SENSITIVE, DataSensitivity.HIGHLY_SENSITIVE}:
                masked[key_str] = _mask_scalar(value)
            else:
                masked[key_str] = mask_payload(value)
        return masked

    if isinstance(payload, list):
        return [mask_payload(item) for item in payload]

    if isinstance(payload, tuple):
        return tuple(mask_payload(item) for item in payload)

    return payload


def mask_event_dict(event_dict: dict[str, Any]) -> dict[str, Any]:
    allowed_plain_fields = {"event", "level", "logger", "timestamp"}
    masked: dict[str, Any] = {}
    for key, value in event_dict.items():
        if key in allowed_plain_fields:
            masked[key] = value
            continue

        sensitivity = _resolve_sensitivity(key)
        if sensitivity in {DataSensitivity.SENSITIVE, DataSensitivity.HIGHLY_SENSITIVE}:
            masked[key] = _mask_scalar(value)
            continue

        masked[key] = mask_payload(value)

    return masked

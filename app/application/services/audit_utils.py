from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


def _serialize_value(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if is_dataclass(value):
        return {k: _serialize_value(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    return value


def to_audit_dict(value):
    if value is None:
        return None
    return _serialize_value(value)

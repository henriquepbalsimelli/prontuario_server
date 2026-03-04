from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.infrastructure.settings import get_settings


@lru_cache
def _get_fernets_by_version() -> dict[str, Fernet]:
    settings = get_settings()
    if not settings.encryption_keys:
        raise ValueError("At least one encryption key is required")

    return {
        version: Fernet(key.encode("utf-8"))
        for version, key in settings.encryption_keys.items()
    }


def _get_active_key_version() -> str:
    return get_settings().encryption_active_key_version


def _parse_versioned_ciphertext(value: str) -> tuple[str | None, str]:
    if ":" not in value:
        return None, value
    version, ciphertext = value.split(":", 1)
    if version and ciphertext:
        return version, ciphertext
    return None, value


def encrypt_text(value: str) -> str:
    active_version = _get_active_key_version()
    fernet = _get_fernets_by_version().get(active_version)
    if fernet is None:
        raise ValueError("Active encryption key version is not configured")

    token = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{active_version}:{token}"


def decrypt_text(value: str) -> str:
    fernets = _get_fernets_by_version()
    version, ciphertext = _parse_versioned_ciphertext(value)

    if version is not None and version in fernets:
        try:
            raw = fernets[version].decrypt(ciphertext.encode("utf-8"))
            return raw.decode("utf-8")
        except InvalidToken:
            pass

    for fernet in fernets.values():
        try:
            raw = fernet.decrypt(value.encode("utf-8"))
            return raw.decode("utf-8")
        except InvalidToken:
            continue

    for fernet in fernets.values():
        try:
            raw = fernet.decrypt(ciphertext.encode("utf-8"))
            return raw.decode("utf-8")
        except InvalidToken:
            continue

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    return json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))


class EncryptedString(TypeDecorator[str]):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return encrypt_text(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None:
            return None
        return decrypt_text(value)


class EncryptedJSON(TypeDecorator[dict[str, Any]]):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: dict[str, Any] | None, dialect) -> str | None:
        if value is None:
            return None
        payload = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        return encrypt_text(payload)

    def process_result_value(self, value: str | None, dialect) -> dict[str, Any] | None:
        if value is None:
            return None

        decrypted = decrypt_text(value)
        try:
            parsed = json.loads(decrypted)
        except json.JSONDecodeError:
            return {"_legacy_plaintext": decrypted}

        if isinstance(parsed, dict):
            return parsed
        return {"_value": parsed}

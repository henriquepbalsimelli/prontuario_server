from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path


class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str | None:
        raise NotImplementedError


class EnvSecretProvider(SecretProvider):
    def get_secret(self, key: str) -> str | None:
        return os.getenv(key)


class FileSecretProvider(SecretProvider):
    def __init__(self, path: str) -> None:
        file_path = Path(path)
        if not file_path.exists():
            raise ValueError(f"Secrets file not found: {path}")

        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            raise ValueError("Secrets file must contain a JSON object")

        self._payload = {str(k): str(v) for k, v in payload.items() if v is not None}

    def get_secret(self, key: str) -> str | None:
        return self._payload.get(key)


class AWSSecretsManagerProvider(SecretProvider):
    def __init__(self, region: str, secret_id: str) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError(
                "boto3 is required to use SECRET_PROVIDER=aws_secrets_manager"
            ) from exc

        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_id)
        secret_string = response.get("SecretString")
        if not secret_string:
            raise ValueError("AWS secret does not contain SecretString")

        payload = json.loads(secret_string)
        if not isinstance(payload, dict):
            raise ValueError("AWS secret payload must be a JSON object")

        self._payload = {str(k): str(v) for k, v in payload.items() if v is not None}

    def get_secret(self, key: str) -> str | None:
        return self._payload.get(key)

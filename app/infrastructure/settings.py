from functools import lru_cache
import json

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infrastructure.secrets import (
    AWSSecretsManagerProvider,
    EnvSecretProvider,
    FileSecretProvider,
    SecretProvider,
)


MANAGED_SECRET_FIELD_TO_KEY = {
    "database_url": "DATABASE_URL",
    "redis_url": "REDIS_URL",
    "jwt_secret_key": "JWT_SECRET_KEY",
    "encryption_key": "ENCRYPTION_KEY",
    "encryption_keys_json": "ENCRYPTION_KEYS_JSON",
    "encryption_active_key_version": "ENCRYPTION_ACTIVE_KEY_VERSION",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "Prontuario API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = ""
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    gzip_enabled: bool = True
    gzip_minimum_size: int = 1000
    log_level: str = "INFO"
    log_json: bool = False
    log_request_bodies: bool = True
    enforce_https: bool = False
    hsts_enabled: bool = False
    hsts_max_age_seconds: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    default_page_size: int = 20
    max_page_size: int = 100

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/prontuario",
        validation_alias="DATABASE_URL",
    )
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    s3_bucket_name: str = "prontuario-dev"
    s3_region: str = "us-east-1"
    max_upload_size_mb: int = 20
    s3_presigned_expires_seconds: int = 900

    jwt_secret_key: str = Field(
        default="replace-this-with-a-strong-random-secret-32-bytes-min",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_exp_minutes: int = Field(
        default=60,
        validation_alias="JWT_ACCESS_TOKEN_EXP_MINUTES",
    )
    encryption_key: str = Field(
        default="MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=",
        validation_alias="ENCRYPTION_KEY",
    )
    encryption_keys_json: str = Field(default="", validation_alias="ENCRYPTION_KEYS_JSON")
    encryption_active_key_version: str = Field(
        default="v1",
        validation_alias="ENCRYPTION_ACTIVE_KEY_VERSION",
    )
    secret_provider: str = Field(default="env", validation_alias="SECRET_PROVIDER")
    secret_file_path: str = Field(default=".secrets.json", validation_alias="SECRET_FILE_PATH")
    aws_secrets_region: str = Field(default="us-east-1", validation_alias="AWS_SECRETS_REGION")
    aws_secrets_id: str = Field(default="", validation_alias="AWS_SECRETS_ID")
    require_managed_secrets_in_deploy: bool = Field(
        default=True,
        validation_alias="REQUIRE_MANAGED_SECRETS_IN_DEPLOY",
    )
    require_encryption_key_in_deploy: bool = Field(
        default=True,
        validation_alias="REQUIRE_ENCRYPTION_KEY_IN_DEPLOY",
    )

    @property
    def hsts_value(self) -> str:
        value = f"max-age={self.hsts_max_age_seconds}"
        if self.hsts_include_subdomains:
            value += "; includeSubDomains"
        if self.hsts_preload:
            value += "; preload"
        return value

    @property
    def encryption_keys(self) -> dict[str, str]:
        keys: dict[str, str] = {}
        if self.encryption_keys_json.strip():
            parsed = json.loads(self.encryption_keys_json)
            if not isinstance(parsed, dict):
                raise ValueError("ENCRYPTION_KEYS_JSON must be a JSON object")
            keys.update({str(version): str(key) for version, key in parsed.items() if key})

        # Backward compatibility with single-key setup.
        if self.encryption_key:
            keys.setdefault(self.encryption_active_key_version, self.encryption_key)

        return keys


def _build_secret_provider(settings: Settings) -> SecretProvider:
    provider_name = settings.secret_provider.strip().lower()

    if provider_name == "env":
        return EnvSecretProvider()
    if provider_name == "file":
        return FileSecretProvider(path=settings.secret_file_path)
    if provider_name == "aws_secrets_manager":
        if not settings.aws_secrets_id:
            raise ValueError("AWS_SECRETS_ID is required for SECRET_PROVIDER=aws_secrets_manager")
        return AWSSecretsManagerProvider(
            region=settings.aws_secrets_region,
            secret_id=settings.aws_secrets_id,
        )

    raise ValueError(f"Unsupported secret provider: {settings.secret_provider}")


def _apply_managed_secrets(settings: Settings) -> Settings:
    provider = _build_secret_provider(settings=settings)
    updates: dict[str, str] = {}

    for field_name, secret_key in MANAGED_SECRET_FIELD_TO_KEY.items():
        value = provider.get_secret(secret_key)
        if value:
            updates[field_name] = value

    if updates:
        return settings.model_copy(update=updates)

    return settings


def _validate_deploy_secret_policy(settings: Settings) -> None:
    if settings.jwt_algorithm.upper() == "HS256" and len(settings.jwt_secret_key.encode("utf-8")) < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 bytes for HS256")
    if settings.jwt_access_token_exp_minutes <= 0:
        raise ValueError("JWT_ACCESS_TOKEN_EXP_MINUTES must be greater than zero")

    is_deploy_env = settings.environment.lower() in {"staging", "production"}
    using_env_provider = settings.secret_provider.strip().lower() == "env"
    if is_deploy_env and settings.require_managed_secrets_in_deploy and using_env_provider:
        raise ValueError(
            "In staging/production you must configure SECRET_PROVIDER as "
            "'file' or 'aws_secrets_manager'."
        )
    if is_deploy_env and settings.require_encryption_key_in_deploy and not settings.encryption_keys:
        raise ValueError("ENCRYPTION_KEY/ENCRYPTION_KEYS_JSON must be configured in staging/production")
    if settings.encryption_active_key_version not in settings.encryption_keys:
        raise ValueError("ENCRYPTION_ACTIVE_KEY_VERSION must exist in encryption key set")


@lru_cache
def get_settings() -> Settings:
    base_settings = Settings()
    settings = _apply_managed_secrets(settings=base_settings)
    _validate_deploy_secret_policy(settings=settings)
    return settings

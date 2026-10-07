from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    app_name: str = "Zhenhang ERP API"
    app_env: Literal["local", "dev", "staging", "prod"] = "local"
    environment: Literal["development", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    # Round 226: these two were plain `int`s while every other policy number in this file carried a bound — including
    # `realtime_ticket_expire_seconds` three lines below. **So an operator could set the access-token lifetime to ten
    # years or to zero and nothing would fail either way**, even though this is the number that decides how long a stolen
    # token works, and `le=1440` is the point past which re-login stops being a revocation path.
    access_token_expire_minutes: int = Field(default=60, ge=1, le=1440)
    # A refresh token is a session. **Past a year it is not a session, it is a credential**, so it is bounded there.
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 7, ge=1, le=525600)
    # Realtime transports carry this credential in a URL, so it stays short-lived.
    realtime_ticket_expire_seconds: int = Field(default=300, ge=30, le=3600)

    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://erp:erp@127.0.0.1:5432/erp_db",
    )

    # 127.0.0.1 rather than localhost: on Windows the name resolves to both 127.0.0.1 and ::1, and
    # redis-py and minio-py each spend ~21 s across the two families before connecting. Measured:
    # localhost took 21.07 s and 127.0.0.1 0.00 s. The deployment supplies a service name instead.
    redis_url: RedisDsn = Field(default="redis://127.0.0.1:6379/0")
    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket: str = "erp-files"

    cors_origins: list[str] = Field(default_factory=list)

    default_tenant_code: str = "default"

    realtime_hot_retention_days: int = Field(default=7, ge=1, le=90)
    realtime_replay_retention_days: int = Field(default=3, ge=1, le=30)
    realtime_archive_retention_days: int = Field(default=90, ge=7, le=365)
    realtime_retention_batch_size: int = Field(default=2000, ge=100, le=20000)
    # Round 204: the upload path read the whole body into memory with no limit. This is the bound, and it is enforced by
    # counting bytes as they arrive rather than by trusting `Content-Length`, which a client can omit or misstate.
    max_upload_bytes: int = Field(default=25 * 1024 * 1024, ge=1024)

    maintenance_interval_seconds: int = Field(default=300, ge=60, le=86400)

    metrics_api_key: str | None = None

    company_name: str = Field(default="振航智能制造", max_length=120)
    company_export_footer: str = Field(
        default="本报价单由振航 ERP 工业报价模块生成，具有版本追溯能力。",
        max_length=500,
    )

    mes_enabled: bool = Field(default=True)
    mes_signal_stale_seconds: int = Field(default=120, ge=30, le=3600)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if not v.strip():
                return []
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def reject_shipped_credentials_in_production(self) -> "Settings":
        """Refuse to run production on a credential that shipped in this repository.

        Development keeps the compose defaults so a local stack starts out of the box. In
        production a container that boots with ``minioadmin`` is far more likely to be an
        oversight than a decision, so it becomes a startup error instead of a silent weakness.
        """
        if self.environment != "production":
            return self
        problems: list[str] = []
        if "minioadmin" in {self.minio_access_key, self.minio_secret_key}:
            problems.append("MINIO_ACCESS_KEY / MINIO_SECRET_KEY still use the shipped default")
        if self.secret_key.strip().lower() in {"change-me", "changeme", "secret", "dev", "test"}:
            problems.append("SECRET_KEY is a well-known placeholder value")
        if problems:
            raise ValueError("production configuration refused: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

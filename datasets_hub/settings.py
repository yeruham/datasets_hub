from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class HubSettings(BaseSettings):
    """Central configuration for datasets_hub (loaded from env / .env)."""

    model_config = SettingsConfigDict(
        env_prefix="DATASETS_HUB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- lakeFS connection ---
    lakefs_host: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("lakefs_host", "DATASETS_HUB_LAKEFS_HOST", "LAKEFS_HOST"),
    )
    lakefs_username: str = Field(
        default="",
        validation_alias=AliasChoices(
            "lakefs_username", "DATASETS_HUB_LAKEFS_USERNAME", "LAKEFS_USERNAME"
        ),
    )
    lakefs_password: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices(
            "lakefs_password", "DATASETS_HUB_LAKEFS_PASSWORD", "LAKEFS_PASSWORD"
        ),
    )
    lakefs_access_token: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "lakefs_access_token", "DATASETS_HUB_LAKEFS_ACCESS_TOKEN", "LAKEFS_ACCESS_TOKEN"
        ),
    )
    lakefs_storage_namespace: str = Field(
        default="",
        validation_alias=AliasChoices(
            "lakefs_storage_namespace",
            "DATASETS_HUB_LAKEFS_STORAGE_NAMESPACE",
            "LAKEFS_STORAGE_NAMESPACE",
        ),
    )

    # --- Validation integration ---
    validation_enabled: bool = Field(
        default=True,
        description="Attach validation profile metadata on every commit",
    )
    validation_required: bool = Field(
        default=True,
        description="Fail commit if lakefs_validation.json is missing",
    )
    validation_profile_filename: str = Field(
        default="lakefs_validation.json",
        description="Validation profile file searched from cwd upward",
    )
    validation_metadata_key: str = Field(
        default="profile",
        description="Commit metadata key consumed by the validation service",
    )
    validation_service_url: str | None = Field(
        default=None,
        description="Base URL of validation service, e.g. http://localhost:8080",
    )
    validation_registry_api_key: SecretStr | None = Field(
        default=None,
        description="X-Registry-Api-Key sent when registering profiles",
    )
    validation_sync_on_commit: bool = Field(
        default=True,
        description="POST profile to validation service registry before commit",
    )
    validation_repo_object_path: str = Field(
        default=".lakefs/validation.json",
        description="Path in the lakeFS repo where the profile JSON is stored",
    )
    validation_auto_scaffold: bool = Field(
        default=True,
        description="Create lakefs_validation.json automatically when missing",
    )
    validation_schema_url: str | None = Field(
        default=None,
        description=(
            "HTTPS URL for editor JSON Schema (.vscode/settings.json). "
            "If unset, uses ./.lakefs/lakefs_validation.schema.json in the project."
        ),
    )
    validation_ide_setup: bool = Field(
        default=True,
        description="Wire lakefs_validation.json to JSON Schema via .vscode/settings.json",
    )

    def search_roots(self) -> list[Path]:
        return [Path.cwd()]


@lru_cache
def get_hub_settings() -> HubSettings:
    return HubSettings()

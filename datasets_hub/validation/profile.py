from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from datasets_hub.settings import HubSettings, get_hub_settings
from datasets_hub.validation.ide import ensure_ide_support
from datasets_hub.validation.schema import remove_schema_from_profile_file, strip_documentation_keys
from datasets_hub.validation.scaffold import scaffold_validation_profile

logger = logging.getLogger(__name__)


class ValidationProfileError(FileNotFoundError):
    pass


class ValidationProfile(BaseModel):
    """User-defined validation rules (same schema as validation_service registry)."""

    profile_id: str
    validation_policy: str = "strict"
    sampling_ratio: float = Field(default=0.05, ge=0.0, le=1.0)
    steps: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _strip_documentation_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return strip_documentation_keys(data)
        return data

    @classmethod
    def from_path(cls, path: Path) -> "ValidationProfile":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)

    def to_registry_payload(self) -> dict[str, Any]:
        """JSON-safe dict for the validation service (no IDE-only fields)."""
        return self.model_dump(mode="json")


def resolve_profile_path(
    path: Path | None = None,
    start_dir: Path | None = None,
    settings: HubSettings | None = None,
) -> Path | None:
    if path is not None:
        return path if path.is_file() else None
    return find_validation_profile(start_dir=start_dir, settings=settings)


def find_validation_profile(
    start_dir: Path | None = None,
    settings: HubSettings | None = None,
) -> Path | None:
    settings = settings or get_hub_settings()
    filename = settings.validation_profile_filename
    current = (start_dir or Path.cwd()).resolve()

    for _ in range(6):
        candidate = current / filename
        if candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def load_validation_profile(
    path: Path | None = None,
    settings: HubSettings | None = None,
    *,
    auto_scaffold: bool | None = None,
    scaffold_dir: Path | None = None,
) -> ValidationProfile:
    """
    Load the validation profile, optionally creating a default file first.

    When ``auto_scaffold`` is enabled (default from settings) and the file is
    missing, a rules-only template is written to the project root.
    """
    settings = settings or get_hub_settings()
    should_scaffold = (
        auto_scaffold if auto_scaffold is not None else settings.validation_auto_scaffold
    )

    resolved = resolve_profile_path(path, settings=settings)
    if resolved is None and should_scaffold:
        target = scaffold_dir or Path.cwd()
        resolved = scaffold_validation_profile(target, settings=settings)
        logger.warning(
            "Created default %s — review validation steps before pushing to protected branches.",
            resolved.name,
        )
    elif resolved is None:
        raise ValidationProfileError(
            f"Validation profile not found. Create '{settings.validation_profile_filename}' "
            "in your project root, or enable auto-scaffold "
            "(DATASETS_HUB_VALIDATION_AUTO_SCAFFOLD=true)."
        )
    else:
        if remove_schema_from_profile_file(resolved):
            logger.debug("Removed legacy $schema from %s", resolved)

    ensure_ide_support(resolved.parent, settings)
    return ValidationProfile.from_path(resolved)


def init_validation_profile(
    target_dir: Path | None = None,
    *,
    profile_id: str | None = None,
    overwrite: bool = False,
    settings: HubSettings | None = None,
) -> Path:
    """Explicit API to scaffold ``lakefs_validation.json`` (also used by auto-scaffold)."""
    return scaffold_validation_profile(
        target_dir,
        settings=settings,
        profile_id=profile_id,
        overwrite=overwrite,
    )

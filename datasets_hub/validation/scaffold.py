from __future__ import annotations

import json
import logging
from pathlib import Path

from datasets_hub.settings import HubSettings, get_hub_settings
from datasets_hub.validation.ide import ensure_ide_support
from datasets_hub.validation.schema import remove_schema_from_profile_file, suggest_profile_id

logger = logging.getLogger(__name__)


def build_default_profile_document(
    profile_id: str | None = None,
    *,
    settings: HubSettings | None = None,
    target_dir: Path | None = None,
) -> dict:
    """Return the default validation profile (rules only — no ``$schema``)."""
    profile_id = profile_id or suggest_profile_id(target_dir)

    return {
        "_comment": "lakeFS validation rules. Fields starting with '_' are ignored by the engine.",
        "profile_id": profile_id,
        "validation_policy": "strict",
        "sampling_ratio": 0.05,
        "steps": [
            {
                "_comment": "Phase 1: required files must exist in every commit",
                "type": "file_structure",
                "params": {
                    "required_files": [
                        "train.parquet",
                        "metadata.json",
                    ],
                },
            },
            {
                "_comment": "Phase 2 (optional): adjust column types for your dataset",
                "type": "schema",
                "params": {
                    "file": "train.parquet",
                    "columns": {
                        "text": "string",
                        "label": "int",
                    },
                    "strict": True,
                },
            },
        ],
    }


def scaffold_validation_profile(
    target_dir: Path | None = None,
    *,
    settings: HubSettings | None = None,
    profile_id: str | None = None,
    overwrite: bool = False,
) -> Path:
    """
    Create ``lakefs_validation.json`` (rules only) and wire IDE validation via ``.vscode/settings.json``.
    """
    settings = settings or get_hub_settings()
    directory = (target_dir or Path.cwd()).resolve()
    path = directory / settings.validation_profile_filename

    if path.is_file() and not overwrite:
        remove_schema_from_profile_file(path)
        ensure_ide_support(directory, settings)
        logger.info("Validation profile already exists: %s", path)
        return path

    document = build_default_profile_document(profile_id, settings=settings, target_dir=directory)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    ensure_ide_support(directory, settings)
    logger.info(
        "Created validation profile %s (profile_id=%s). Edit steps, then push_to_hub().",
        path,
        document["profile_id"],
    )
    return path

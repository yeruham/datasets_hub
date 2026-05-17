from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from datasets_hub.settings import HubSettings, get_hub_settings
from datasets_hub.validation.schema import schema_file_path

logger = logging.getLogger(__name__)

# Tooling directory (like .vite/) — schema lives here, not in the user's config file.
LAKEFS_TOOLING_DIR = ".lakefs"
TOOLING_SCHEMA_NAME = "lakefs_validation.schema.json"
VSCODE_DIR = ".vscode"
VSCODE_SETTINGS = "settings.json"


def _tooling_schema_path(project_dir: Path) -> Path:
    return project_dir.resolve() / LAKEFS_TOOLING_DIR / TOOLING_SCHEMA_NAME


def _sync_tooling_schema(project_dir: Path) -> Path:
    """Copy bundled schema into ``.lakefs/`` for stable relative IDE resolution."""
    destination = _tooling_schema_path(project_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = schema_file_path()
    if not destination.exists() or destination.read_bytes() != source.read_bytes():
        shutil.copy2(source, destination)
    return destination


def resolve_ide_schema_url(project_dir: Path, settings: HubSettings | None = None) -> str:
    """
    Schema URL referenced only from editor settings (never written into lakefs_validation.json).

    - Org HTTPS URL when ``DATASETS_HUB_VALIDATION_SCHEMA_URL`` is set
    - Otherwise a relative path to ``.lakefs/lakefs_validation.schema.json``
    """
    settings = settings or get_hub_settings()
    if settings.validation_schema_url:
        return settings.validation_schema_url.rstrip("/")
    _sync_tooling_schema(project_dir)
    return f"./{LAKEFS_TOOLING_DIR}/{TOOLING_SCHEMA_NAME}"


def _file_match_patterns(filename: str) -> list[str]:
    return [filename, f"**/{filename}"]


def _merge_json_schemas(
    existing: list[dict],
    *,
    file_match: list[str],
    url: str,
) -> list[dict]:
    filtered = [
        entry
        for entry in existing
        if entry.get("url") != url
        and not (set(entry.get("fileMatch", [])) & set(file_match))
    ]
    filtered.append({"fileMatch": file_match, "url": url})
    return filtered


def ensure_vscode_schema_mapping(
    project_dir: Path | None = None,
    settings: HubSettings | None = None,
) -> bool:
    """
    Register JSON Schema for ``lakefs_validation.json`` via ``.vscode/settings.json``.

    Same idea as Vite: validation rules live in the config file; editor wiring is separate.
    Returns True if settings were created or updated.
    """
    settings = settings or get_hub_settings()
    if not settings.validation_ide_setup:
        return False

    project_dir = (project_dir or Path.cwd()).resolve()
    filename = settings.validation_profile_filename
    schema_url = resolve_ide_schema_url(project_dir, settings)

    vscode_dir = project_dir / VSCODE_DIR
    settings_path = vscode_dir / VSCODE_SETTINGS
    vscode_dir.mkdir(parents=True, exist_ok=True)

    if settings_path.is_file():
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        data = {}

    file_match = _file_match_patterns(filename)
    schemas: list[dict] = list(data.get("json.schemas", []))
    merged = _merge_json_schemas(schemas, file_match=file_match, url=schema_url)

    if data.get("json.schemas") == merged:
        return False

    data["json.schemas"] = merged
    settings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.debug("Updated %s for %s IDE validation", settings_path, filename)
    return True


def ensure_ide_support(
    project_dir: Path | None = None,
    settings: HubSettings | None = None,
) -> None:
    """Configure editor JSON Schema mapping (VS Code / Cursor)."""
    ensure_vscode_schema_mapping(project_dir, settings)

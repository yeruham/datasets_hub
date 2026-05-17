from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path
from typing import Any

from datasets_hub.settings import HubSettings, get_hub_settings

SCHEMA_RESOURCE = "lakefs_validation.schema.json"


def schema_file_path() -> Path:
    """Absolute path to the bundled JSON Schema (shipped inside datasets_hub)."""
    try:
        ref = resources.files("datasets_hub").joinpath("schemas", SCHEMA_RESOURCE)
        with resources.as_file(ref) as path:
            return Path(path)
    except (TypeError, FileNotFoundError, ModuleNotFoundError):
        return Path(__file__).resolve().parent.parent / "schemas" / SCHEMA_RESOURCE


def get_schema_uri(settings: HubSettings | None = None) -> str:
    """Deprecated alias — use ``validation.ide.resolve_ide_schema_url`` for editor wiring."""
    settings = settings or get_hub_settings()
    if settings.validation_schema_url:
        return settings.validation_schema_url.rstrip("/")
    return schema_file_path().resolve().as_uri()


def load_schema_document() -> dict[str, Any]:
    return json.loads(schema_file_path().read_text(encoding="utf-8"))


def strip_documentation_keys(value: Any) -> Any:
    """Remove keys ignored by the validation engine ($schema, _comment, ...)."""
    if isinstance(value, dict):
        return {
            key: strip_documentation_keys(item)
            for key, item in value.items()
            if not key.startswith("_") and key != "$schema"
        }
    if isinstance(value, list):
        return [strip_documentation_keys(item) for item in value]
    return value


def remove_schema_from_profile_file(path: Path) -> bool:
    """Strip legacy ``$schema`` from user config (rules-only file). Returns True if modified."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if "$schema" not in data:
        return False
    del data["$schema"]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def suggest_profile_id(directory: Path | None = None) -> str:
    directory = (directory or Path.cwd()).resolve()
    slug = re.sub(r"[^a-z0-9]+", "_", directory.name.lower()).strip("_")
    if not slug or not slug[0].isalpha():
        slug = "project"
    return f"{slug}_v1"

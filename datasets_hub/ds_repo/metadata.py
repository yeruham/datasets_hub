from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from datasets_hub.models import MetadataInput

DATASET_METADATA_PATH = "_datasets_hub/metadata.json"


def metadata_to_dict(metadata: MetadataInput) -> dict[str, Any]:
    if metadata is None:
        raise ValueError("metadata is required")
    if isinstance(metadata, BaseModel):
        return metadata.model_dump()
    if isinstance(metadata, dict):
        return metadata
    raise TypeError(f"Unsupported metadata type: {type(metadata)}")


def metadata_to_lakefs(metadata: MetadataInput) -> dict[str, str]:
    return {key: _stringify(value) for key, value in metadata_to_dict(metadata).items()}


def metadata_to_json(metadata: MetadataInput) -> str:
    return json.dumps(metadata_to_dict(metadata), ensure_ascii=False, sort_keys=True)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)

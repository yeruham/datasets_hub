from __future__ import annotations

from typing import TYPE_CHECKING

from datasets_hub.validation.profile import (
    ValidationProfile,
    ValidationProfileError,
    find_validation_profile,
    init_validation_profile,
    load_validation_profile,
)
from datasets_hub.validation.ide import ensure_ide_support
from datasets_hub.validation.schema import get_schema_uri, schema_file_path
from datasets_hub.validation.scaffold import build_default_profile_document, scaffold_validation_profile

if TYPE_CHECKING:
    from datasets_hub.validation.commit import prepare_commit_metadata

__all__ = [
    "ValidationProfile",
    "ValidationProfileError",
    "find_validation_profile",
    "init_validation_profile",
    "load_validation_profile",
    "prepare_commit_metadata",
    "ensure_ide_support",
    "get_schema_uri",
    "schema_file_path",
    "build_default_profile_document",
    "scaffold_validation_profile",
]


def __getattr__(name: str):
    if name == "prepare_commit_metadata":
        from datasets_hub.validation.commit import prepare_commit_metadata

        return prepare_commit_metadata
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

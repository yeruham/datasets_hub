from __future__ import annotations

import json
from pathlib import Path

import pytest

from datasets_hub.settings import HubSettings
from datasets_hub.validation.commit import prepare_commit_metadata
from datasets_hub.validation.profile import ValidationProfile


def test_prepare_commit_metadata_injects_profile(tmp_path):
    profile_file = tmp_path / "lakefs_validation.json"
    profile_file.write_text(
        json.dumps(
            {
                "profile_id": "demo_v1",
                "steps": [{"type": "file_structure", "params": {"required_files": ["x.parquet"]}}],
            }
        ),
        encoding="utf-8",
    )

    settings = HubSettings(
        validation_enabled=True,
        validation_required=True,
        validation_sync_on_commit=False,
        validation_service_url=None,
    )
    metadata, profile = prepare_commit_metadata(
        {},
        profile_path=profile_file,
        settings=settings,
        sync_registry=False,
    )
    assert metadata["profile"] == "demo_v1"
    assert profile is not None
    assert profile.profile_id == "demo_v1"


def test_prepare_commit_metadata_required_missing(tmp_path):
    settings = HubSettings(
        validation_enabled=True,
        validation_required=True,
        validation_auto_scaffold=False,
    )
    with pytest.raises(FileNotFoundError):
        prepare_commit_metadata({}, profile_path=tmp_path / "missing.json", settings=settings)

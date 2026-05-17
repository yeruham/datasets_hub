from __future__ import annotations

import json

from datasets_hub.settings import HubSettings
from datasets_hub.validation.ide import LAKEFS_TOOLING_DIR, ensure_vscode_schema_mapping
from datasets_hub.validation.profile import ValidationProfile, load_validation_profile
from datasets_hub.validation.scaffold import scaffold_validation_profile
from datasets_hub.validation.schema import strip_documentation_keys


def test_scaffold_creates_rules_only_template(tmp_path):
    settings = HubSettings(
        validation_profile_filename="lakefs_validation.json",
        validation_ide_setup=True,
    )
    path = scaffold_validation_profile(tmp_path, settings=settings, profile_id="demo_v1")

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["profile_id"] == "demo_v1"
    assert "$schema" not in raw
    assert raw["steps"][0]["type"] == "file_structure"

    vscode_settings = tmp_path / ".vscode" / "settings.json"
    assert vscode_settings.is_file()
    vscode = json.loads(vscode_settings.read_text(encoding="utf-8"))
    assert any(
        "lakefs_validation.json" in entry.get("fileMatch", [])
        for entry in vscode["json.schemas"]
    )

    tooling_schema = tmp_path / LAKEFS_TOOLING_DIR / "lakefs_validation.schema.json"
    assert tooling_schema.is_file()

    profile = ValidationProfile.from_path(path)
    assert profile.profile_id == "demo_v1"
    assert "_comment" not in profile.steps[0]


def test_load_validation_profile_auto_scaffolds(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = HubSettings(
        validation_auto_scaffold=True,
        validation_sync_on_commit=False,
        validation_ide_setup=True,
    )
    profile = load_validation_profile(settings=settings)
    assert profile.profile_id.endswith("_v1")
    assert (tmp_path / "lakefs_validation.json").is_file()
    assert (tmp_path / ".vscode" / "settings.json").is_file()


def test_strip_legacy_schema_from_profile(tmp_path):
    path = tmp_path / "lakefs_validation.json"
    path.write_text(
        json.dumps({"$schema": "file:///x", "profile_id": "demo_v1", "steps": []}),
        encoding="utf-8",
    )
    settings = HubSettings(validation_ide_setup=True)
    ensure_vscode_schema_mapping(tmp_path, settings)
    profile = load_validation_profile(path, settings=settings, auto_scaffold=False)
    assert profile.profile_id == "demo_v1"
    assert "$schema" not in json.loads(path.read_text(encoding="utf-8"))


def test_strip_documentation_keys():
    payload = {
        "$schema": "file:///x",
        "_comment": "note",
        "profile_id": "x_v1",
        "steps": [{"_comment": "s", "type": "schema", "params": {}}],
    }
    clean = strip_documentation_keys(payload)
    assert "$schema" not in clean
    assert "_comment" not in clean
    assert clean["steps"][0] == {"type": "schema", "params": {}}

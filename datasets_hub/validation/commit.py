from __future__ import annotations

import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Any

from lakefs import Client

from datasets_hub.settings import HubSettings, get_hub_settings
from datasets_hub.validation.profile import ValidationProfile, ValidationProfileError, load_validation_profile
from datasets_hub.validation.registry_client import ValidationRegistryClient

logger = logging.getLogger(__name__)


def prepare_commit_metadata(
    commit_metadata: dict[str, Any] | None = None,
    *,
    profile_path: Path | None = None,
    settings: HubSettings | None = None,
    sync_registry: bool | None = None,
) -> tuple[dict[str, Any], ValidationProfile | None]:
    """
    Merge validation profile id into commit metadata and optionally sync to registry.

    Returns (metadata, profile).
    """
    settings = settings or get_hub_settings()
    metadata = dict(commit_metadata or {})

    if not settings.validation_enabled:
        return metadata, None

    try:
        profile = load_validation_profile(profile_path, settings=settings)
    except ValidationProfileError:
        if settings.validation_required:
            raise
        logger.warning(
            "Validation enabled but %s not found; commit proceeds without profile",
            settings.validation_profile_filename,
        )
        return metadata, None

    metadata[settings.validation_metadata_key] = profile.profile_id

    should_sync = (
        sync_registry if sync_registry is not None else settings.validation_sync_on_commit
    )
    if should_sync:
        ValidationRegistryClient(settings).register_profile(profile)

    return metadata, profile


def upload_profile_to_branch(
    client: Client,
    repo_name: str,
    branch: str,
    profile: ValidationProfile,
    settings: HubSettings | None = None,
) -> None:
    """Store the validation JSON in the repo for audit/versioning."""
    settings = settings or get_hub_settings()
    path = settings.validation_repo_object_path
    payload = profile.model_dump_json(indent=2).encode("utf-8")
    buffer = BytesIO(payload)

    staging = client.sdk_client.staging_api.get_physical_address(
        repository=repo_name,
        branch=branch,
        path=path,
        presign=True,
    )
    import requests

    response = requests.put(
        staging.presigned_url,
        data=buffer.getvalue(),
        headers={"Content-Type": "application/json"},
        timeout=120,
    )
    response.raise_for_status()

    from lakefs_sdk import StagingMetadata

    staging_metadata = StagingMetadata(
        staging=staging,
        size_bytes=len(payload),
        checksum=response.headers.get("ETag", "").strip('"'),
        content_type="application/json",
    )
    client.sdk_client.staging_api.link_physical_address(
        repository=repo_name,
        branch=branch,
        path=path,
        staging_metadata=staging_metadata,
    )
    logger.info("Uploaded validation profile to %s@%s:%s", repo_name, branch, path)

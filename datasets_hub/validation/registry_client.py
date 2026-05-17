from __future__ import annotations

import logging

import httpx

from datasets_hub.settings import HubSettings, get_hub_settings
from datasets_hub.validation.profile import ValidationProfile

logger = logging.getLogger(__name__)


class ValidationRegistryClient:
    """Registers user profiles with the validation service before commits."""

    def __init__(self, settings: HubSettings | None = None) -> None:
        self._settings = settings or get_hub_settings()

    @property
    def base_url(self) -> str | None:
        return self._settings.validation_service_url

    def register_profile(self, profile: ValidationProfile) -> None:
        if not self.base_url:
            logger.debug("validation_service_url not set; skipping registry sync")
            return

        url = f"{self.base_url.rstrip('/')}/registry/profiles"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        api_key = self._settings.validation_registry_api_key
        if api_key is not None:
            headers["X-Registry-Api-Key"] = api_key.get_secret_value()

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=profile.to_registry_payload(), headers=headers)
            if response.status_code == 201:
                logger.info("Registered validation profile '%s'", profile.profile_id)
                return
            if response.status_code == 409:
                return
            response.raise_for_status()

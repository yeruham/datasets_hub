from __future__ import annotations

from lakefs import Client

from datasets_hub.settings import HubSettings, get_hub_settings

_client: Client | None = None


def get_lakefs_client(
    host: str | None = None,
    username: str | None = None,
    password: str | None = None,
    access_token: str | None = None,
    settings: HubSettings | None = None,
) -> Client:
    cfg = settings or get_hub_settings()
    _host = host or cfg.lakefs_host
    _username = username or cfg.lakefs_username
    _password = password or cfg.lakefs_password.get_secret_value()
    _access_token = access_token or (
        cfg.lakefs_access_token.get_secret_value() if cfg.lakefs_access_token else None
    )

    global _client
    if (
        not _client
        or _client.config.host != _host
        or _client.config.username != _username
        or _client.config.password != _password
        or _client.config.access_token != _access_token
    ):
        _client = Client(
            host=_host,
            username=_username,
            password=_password,
            access_token=_access_token,
        )
    return _client


# Backward-compatible module-level constants
_settings = get_hub_settings()
LAKEFS_HOST = _settings.lakefs_host
LAKEFS_USERNAME = _settings.lakefs_username
LAKEFS_PASSWORD = _settings.lakefs_password.get_secret_value()
STORAGE_NAMESPACE = _settings.lakefs_storage_namespace
STORAGE_OPTIONS = {
    "username": LAKEFS_USERNAME,
    "password": LAKEFS_PASSWORD,
    "host": LAKEFS_HOST,
}

import os
from lakefs import Client

# Credentials should be set via environment variables:
# LAKEFS_HOST, LAKEFS_USERNAME, LAKEFS_PASSWORD, LAKEFS_ACCESS_TOKEN, LAKEFS_STORAGE_NAMESPACE
LAKEFS_HOST = os.environ.get("LAKEFS_HOST", "http://localhost:8005")
LAKEFS_USERNAME = os.environ.get("LAKEFS_USERNAME", "")
LAKEFS_PASSWORD = os.environ.get("LAKEFS_PASSWORD", "")
BASE_STORAGE_NAMESPACE = os.environ.get("LAKEFS_STORAGE_NAMESPACE", "s3://datasets-hub")

STORAGE_OPTIONS = {
    "username": LAKEFS_USERNAME,
    "password": LAKEFS_PASSWORD,
    "host": LAKEFS_HOST,
}

_client: Client | None = None


def get_lakefs_client(
    host: str | None = None,
    username: str | None = None,
    password: str | None = None,
    access_token: str | None = None,
) -> Client:
    _host = host or LAKEFS_HOST
    _username = username or LAKEFS_USERNAME
    _password = password or LAKEFS_PASSWORD
    _access_token = access_token

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

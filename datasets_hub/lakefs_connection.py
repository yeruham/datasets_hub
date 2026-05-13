LAKEFS_HOST = "http://localhost:8007"
LAKEFS_USERNAME = "yeruham"
LAKEFS_PASSWORD = "xxx"
STORAGE_NAMESPACE = ""

STORAGE_OPTIONS = {
         "username": LAKEFS_USERNAME,
         "password": LAKEFS_PASSWORD,
         "host": LAKEFS_HOST
}

from lakefs import Client

_client: Client | None = None


def get_lakefs_client(host: str | None = None,
                      username: str | None = None,
                      password: str | None = None,
                      access_token: str | None = None) -> Client:

    _host = LAKEFS_HOST if host is None else host
    _username = LAKEFS_USERNAME if username is None else username
    _password = LAKEFS_PASSWORD if password is None else password
    _access_token = access_token

    global _client
    if (not _client
        or _client.config.host != _host
        or _client.config.username != username
        or _client.config.password != password
        or _client.config.access_token != access_token):

        _client = Client(
            host=_host,
            username=_username,
            password=_password,
            access_token=_access_token
        )
    return _client

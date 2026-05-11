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


def get_lakefs_client() -> Client:
    global _client
    if isinstance(_client, Client):
        return _client
    else:
        _client = Client(
            host=LAKEFS_HOST,
            username=LAKEFS_USERNAME,
            password=LAKEFS_PASSWORD,
        )
        return _client

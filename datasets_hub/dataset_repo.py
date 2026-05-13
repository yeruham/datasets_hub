from __future__ import annotations

from lakefs import Repository, Client, Reference
from typing import Optional

from lakefs_connection import get_lakefs_client


class DatasetRepo(Repository):

    def __init__(self, repository_id: str, client: Optional[Client] = None):
        if not isinstance(client, Client):
            client = get_lakefs_client()
        super().__init__(repository_id, client)

    @classmethod
    def from_repo(cls, repo: Repository) -> DatasetRepo:
        repo.__class__ = cls
        return repo

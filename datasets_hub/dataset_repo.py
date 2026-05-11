from __future__ import annotations
from lakefs_sdk import client
from lakefs import Repository, Client
from datasets import Dataset, load_dataset
from typing import Optional, Union
from pydantic import BaseModel

from lakefs_connection import get_lakefs_client
from lfs_datasets import LFSDataset, LFSDatasetDict, IterableDatasetDict, LFSIterableDatasetDict

class PresignedUrl(BaseModel):
    physical_address: str
    physical_address_expiry: int



class DatasetRepo(Repository):

    def __init__(self, repository_id: str, client: Optional[Client] = None):
        if not isinstance(client, Client):
            client = get_lakefs_client()
        super().__init__(repository_id, client)

    @classmethod
    def from_repo(cls, repo: Repository) -> DatasetRepo:
        repo.__class__ = cls
        return repo

    def get_presigned_url(self, ref: str, path: str) -> PresignedUrl:
        state_objects = self._client.sdk_client.objects_api.stat_object(repository=self.id, ref=ref, path=path, presign=True)
        physical_address = state_objects.physical_address
        physical_address_expiry = state_objects.physical_address_expiry
        return PresignedUrl(physical_address=physical_address, physical_address_expiry=physical_address_expiry)






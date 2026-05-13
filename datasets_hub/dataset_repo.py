from __future__ import annotations

from io import BytesIO

from lakefs_sdk import client
from lakefs import Repository, Client, Reference
from lakefs_sdk import StagingMetadata, ObjectStats
from datasets import Dataset, load_dataset
from typing import Optional, Union
from pydantic import BaseModel
from pathlib import Path
import io
import requests
import base64
import binascii
import mimetypes

from lakefs_connection import get_lakefs_client
from lfs_datasets import LFSDataset, LFSDatasetDict, IterableDatasetDict, LFSIterableDatasetDict

class PresignedUrl(BaseModel):
    name: str
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

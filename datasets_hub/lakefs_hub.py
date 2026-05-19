from __future__ import annotations

from typing import Optional, Union, cast, Literal

from lakefs import repositories
from lakefs.client import _BaseLakeFSObject
from datasets import Split, Features
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict

from datasets_hub.upload.lfs_upload import LFSUpload
from datasets_hub.ds_repo import DatasetRepo
from datasets_hub.lakefs_connection import get_lakefs_client, STORAGE_NAMESPACE
from datasets_hub.settings import get_hub_settings
from datasets_hub.validation.commit import prepare_commit_metadata, upload_profile_to_branch
from datasets_hub.models import PresignedUrl
from datasets_hub.ds_repo import DatasetReference, DatasetRepo
from datasets_hub.lakefs_connection import get_lakefs_client, BASE_STORAGE_NAMESPACE
from datasets_hub.models import CommitMetadata, DatasetMetadata, MetadataInput, PresignedUrl


class LakefsHub(_BaseLakeFSObject):

    def __init__(
            self,
            host: str | None = None,
            username: str | None = None,
            password: str | None = None,
            access_token: str | None = None,
    ):
        self._settings = get_hub_settings()
        self._storage_namespace = STORAGE_NAMESPACE or self._settings.lakefs_storage_namespace
        client = get_lakefs_client(
            host=host,
            username=username,
            password=password,
            access_token=access_token,
            settings=self._settings,
        )
        self.lfs_upload = LFSUpload(client)
        super().__init__(client)


    def list_ds_repos(self, prefix: str | None = None, after: str | None = None, **kwargs) -> list[str]:
        return [repo.id for repo in repositories(client=self._client, prefix=prefix, after=after, **kwargs)]


    def create_ds_repo(self, name: str, metadata: DatasetMetadata | MetadataInput) -> DatasetRepo:
        return DatasetRepo(
            repository_id=name,
            client=self._client,
            storage_namespace=self._storage_namespace,
        ).create(metadata)


    def get_ds_repo(self, name: str) -> DatasetRepo:
        return DatasetRepo(
            repository_id=name,
            client=self._client,
            storage_namespace=self._storage_namespace,
        )


    def load_dataset(
            self,
            path: str,
            name: str,
            revision: str,
            data_dir: Optional[str] = None,
            split: Optional[Union[str, Split, list[str], list[Split]]] = None,
            features: Optional[Features] = None,
            keep_in_memory: Optional[bool] = None,
            token: Optional[Union[bool, str]] = None,
            streaming: bool = False,
            num_proc: Optional[int] = None,
            auth_splits: bool = True,
            **kwargs,
    ) -> Union["LFSDataset", "LFSDatasetDict", "LFSIterableDataset", "LFSIterableDatasetDict"]:
        ds_repo = self.get_ds_repo(name)
        return ds_repo.get_dataset(
            file_type=path,
            ref=revision,
            data_dir=data_dir,
            split=split,
            features=features,
            keep_in_memory=keep_in_memory,
            streaming=streaming,
            num_proc=num_proc,
            auth_splits=auth_splits,
            **kwargs,
        )


    def push_and_commit_dataset(
            self,
            dataset: Dataset | DatasetDict | IterableDataset | IterableDatasetDict,
            ds_name: str,
            commit_message: str,
            commit_metadata: CommitMetadata | MetadataInput,
            file_type: str = "csv",
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            branch: Optional[str] = None,
            presign: bool = True,
            multipart: bool = False,
            batch_size: Optional[int] = None,
            validation_profile_path: Optional[str] = None,
            skip_validation: bool = False,
            **kwargs,
    ) -> DatasetReference:
        """
        Push any dataset type to lakeFS and commit.

        Validation (when enabled via env):
            Place ``lakefs_validation.json`` in your project root.
            The library injects ``profile=<profile_id>`` into commit metadata and
            registers the profile with the validation service before commit.

        Args:
            multipart: Use experimental multipart upload API. Keeps memory bounded to batch_size.
            batch_size: Part size in bytes. Required when multipart=True. Must be >= 5MB.
            presign: Use presigned URL for single-shot upload. Ignored when multipart=True.
            validation_profile_path: Override path to validation JSON (default: auto-discover).
            skip_validation: If True, do not attach validation metadata for this commit.
        """
        ds_repo = self.get_ds_repo(ds_name)
        ds_repo.upload_dataset(
            dataset=dataset,
            file_type=file_type,
            split=split,
            data_dir=data_dir,
            branch=branch,
            presign=presign,
            multipart=multipart,
            batch_size=batch_size
        )
        return ds_repo.commit(branch=branch, message=commit_message, metadata=commit_metadata, validation_profile_path=validation_profile_path, skip_validation=skip_validation)

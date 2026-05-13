from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, cast, Literal
from collections.abc import Mapping, Sequence

from lakefs import repository, repositories, Client, Reference
from lakefs.client import _BaseLakeFSObject
from datasets import load_dataset as hf_load_dataset, Split, Features
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict

from lakefs_upload import LakefsUpload
from dataset_repo import DatasetRepo
from lakefs_connection import get_lakefs_client, STORAGE_NAMESPACE
from models import PresignedUrl


class LakefsHub(_BaseLakeFSObject):

    def __init__(
            self,
            host: str | None = None,
            username: str | None = None,
            password: str | None = None,
            access_token: str | None = None,
    ):
        self._storage_namespace = STORAGE_NAMESPACE
        client = get_lakefs_client(host=host, username=username, password=password, access_token=access_token)
        self.lakefs_upload = LakefsUpload(client)
        super().__init__(client)


    def list_ds_repos(self, prefix: str | None = None, after: str | None = None, **kwargs) -> list[str]:
        return [repo.id for repo in repositories(client=self._client, prefix=prefix, after=after, **kwargs)]

    def create_ds_repo(self, name: str) -> DatasetRepo:
        repo = DatasetRepo(repository_id=name, client=self._client).create(
            storage_namespace=self._storage_namespace
        )
        return DatasetRepo.from_repo(repo)

    def get_ds_repo(self, name: str) -> DatasetRepo:
        repo = repository(repository_id=name, client=self._client)
        return DatasetRepo.from_repo(repo)


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
    ):
        from lfs_datasets import LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict, _convert_ds_to_lfs

        presign_urls: list[PresignedUrl] = self.lakefs_upload.get_presigned_urls(
            repo_name=name, ref=revision, prefix=data_dir
        )

        if auth_splits:
            data_files = {obj.name: obj.physical_address for obj in presign_urls}
        else:
            data_files = [obj.physical_address for obj in presign_urls]

        ds = hf_load_dataset(
            path=path,
            data_files=data_files,
            split=split,
            streaming=cast(Literal[False], streaming),
            features=features,
            keep_in_memory=keep_in_memory,
            num_proc=num_proc,
        )

        return _convert_ds_to_lfs(ds)


    def push_and_commit_dataset(
            self,
            dataset: Dataset | DatasetDict,
            file_type: str,
            ds_name: str,
            commit_message: str,
            commit_metadata: Optional[dict] = None,
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            branch: Optional[str] = None,
            presign: bool = True,
            **kwargs,
    ) -> Reference | None:
        from lfs_datasets import LFSDataset, LFSDatasetDict

        uploaded_and_linked = False

        if isinstance(dataset, (Dataset, LFSDataset)):
            path_parts = [data_dir, split or str(dataset.split), file_type]
            full_path = Path(*(p for p in path_parts if p))
            uploaded_and_linked = self.lakefs_upload.upload_dataset(
                dataset=dataset,
                repo_name=ds_name,
                branch=branch,
                path=str(full_path),
                presign=presign,
            )

        elif isinstance(dataset, (DatasetDict, LFSDatasetDict)):
            splits = list(dataset.keys())
            num_uploaded = 0
            for ds_split in splits:
                ds = dataset[ds_split]
                path_parts = [data_dir, ds_split, file_type]
                full_path = Path(*(p for p in path_parts if p))
                success = self.lakefs_upload.upload_dataset(
                    dataset=ds,
                    repo_name=ds_name,
                    branch=branch,
                    path=str(full_path),
                    presign=presign,
                )
                if success:
                    num_uploaded += 1
            uploaded_and_linked = num_uploaded == len(splits)

        if not uploaded_and_linked:
            raise RuntimeError(f"Upload failed for dataset '{ds_name}' on branch '{branch}'.")

        ds_repo = self.get_ds_repo(ds_name)
        return ds_repo.branch(branch).commit(commit_message, commit_metadata)

    def push_and_commit_iterable_dataset(
            self,
            dataset: IterableDataset | IterableDatasetDict,
            file_type: str,
            repo_id: str,
            commit_message: str,
            commit_metadata: Optional[dict] = None,
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            branch: Optional[str] = None,
            presign: bool = True,
            batch_size: Optional[int] = None,
            **kwargs,
    ) -> Reference:
        """
        Push an IterableDataset or IterableDatasetDict to lakeFS.

        Args:
            batch_size: If None, collects all rows into memory before uploading.
                        If set, writes in batches (only supported for CSV).
        """
        from lfs_datasets import LFSIterableDataset, LFSIterableDatasetDict

        uploaded_and_linked = False

        if isinstance(dataset, (IterableDataset, LFSIterableDataset)):
            path_parts = [data_dir, split, file_type]
            full_path = Path(*(p for p in path_parts if p))
            uploaded_and_linked = self.lakefs_upload.upload_iterable_dataset(
                dataset=dataset,
                repo_name=repo_id,
                branch=branch,
                path=str(full_path),
                file_type=file_type,
                presign=presign,
                batch_size=batch_size,
            )

        elif isinstance(dataset, (IterableDatasetDict, LFSIterableDatasetDict)):
            splits = list(dataset.keys())
            num_uploaded = 0
            for ds_split in splits:
                ds = dataset[ds_split]
                path_parts = [data_dir, ds_split, file_type]
                full_path = Path(*(p for p in path_parts if p))
                success = self.lakefs_upload.upload_iterable_dataset(
                    dataset=ds,
                    repo_name=repo_id,
                    branch=branch,
                    path=str(full_path),
                    file_type=file_type,
                    presign=presign,
                    batch_size=batch_size,
                )
                if success:
                    num_uploaded += 1
            uploaded_and_linked = num_uploaded == len(splits)

        if not uploaded_and_linked:
            raise RuntimeError(f"Upload failed for iterable dataset '{repo_id}' on branch '{branch}'.")

        ds_repo = self.get_ds_repo(repo_id)
        return ds_repo.branch(branch).commit(commit_message, commit_metadata)

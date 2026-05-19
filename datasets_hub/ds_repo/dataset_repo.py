from __future__ import annotations

import json
from typing import Any, Literal, Optional, cast, Union

from datasets import Dataset, DatasetDict, Features, IterableDataset, IterableDatasetDict, Split
from datasets import load_dataset as hf_load_dataset
from lakefs import Client, Repository, repository, Tag
from lakefs.exceptions import ConflictException

from datasets_hub.lakefs_connection import BASE_STORAGE_NAMESPACE, get_lakefs_client
from datasets_hub.models import CommitMetadata, DatasetMetadata, PresignedUrl
from datasets_hub.upload.lfs_upload import LFSUpload
from datasets_hub.ds_repo.dataset_branch import DatasetBranch
from datasets_hub.ds_repo.dataset_reference import DatasetReference
from datasets_hub.ds_repo.metadata import (
    DATASET_METADATA_PATH,
    metadata_to_json,
    metadata_to_lakefs,
)
from datasets_hub.ds_repo import utils as _


class DatasetRepo:
    """Dataset repository domain object backed by a lakeFS Repository."""

    def __init__(
        self,
        repository_id: str,
        client: Optional[Client] = None,
        lakefs_repo: Optional[Repository] = None,
        storage_namespace: Optional[str] = None,
    ):
        self._client = client if isinstance(client, Client) else get_lakefs_client()
        self._repo = lakefs_repo or repository(repository_id=repository_id, client=self._client)
        self._storage_namespace = f"{storage_namespace or BASE_STORAGE_NAMESPACE}/{repository_id}"
        self._lfs_upload = LFSUpload(self._client)
        self._default_branch = "main"

    @classmethod
    def from_repo(cls, repo: Repository, storage_namespace: Optional[str] = None) -> DatasetRepo:
        return cls(
            repository_id=repo.id,
            client=repo._client,
            lakefs_repo=repo,
            storage_namespace=storage_namespace,
        )

    @property
    def id(self) -> str:
        return self._repo.id

    @property
    def _lakefs_repo(self) -> Repository:
        return self._repo

    @property
    def metadata(self) -> dict[str, str]:
        with self._repo.branch(self._default_branch).object(DATASET_METADATA_PATH).reader() as f:
            repo_metadata = f.read()
        return json.loads(repo_metadata)

    @property
    def properties(self) -> Any:
        return self._repo.properties

    def create(
        self,
        metadata: DatasetMetadata,
        include_samples: bool = False,
        exist_ok: bool = False,
        **kwargs: Any,
    ) -> DatasetRepo:
        _.create_ds_confirm(metadata)
        try:
            self._repo.create(
                storage_namespace=self._storage_namespace,
                default_branch=self._default_branch,
                include_samples=include_samples,
                exist_ok=False,
                **kwargs,
            )
        except Exception as e:
            if isinstance(e, ConflictException) and exist_ok:
                return self
            raise e
        branch = self._repo.branch(self._default_branch)
        branch.object(DATASET_METADATA_PATH).upload(
            metadata_to_json(metadata),
            content_type="application/json",
        )
        branch.commit(
            message="Create dataset metadata",
            metadata=metadata_to_lakefs(metadata),
            allow_empty=exist_ok,
        )
        return self

    def delete(self) -> None:
        self._repo.delete()

    def commit(
        self,
        branch: str,
        message: str,
        metadata: CommitMetadata,
        **kwargs: Any,
    ) -> DatasetReference:
        _.commit_confirm(message, metadata)
        return self.branch(branch).commit(message=message, metadata=metadata, **kwargs)

    def create_branch(
        self,
        name: str,
        source_ref: Any,
        exist_ok: bool = False,
        **kwargs: Any,
    ) -> DatasetBranch:
        return DatasetBranch(self._repo.branch(name).create(source_ref, exist_ok=exist_ok, **kwargs))

    def branch(self, name: str = "main") -> DatasetBranch:
        return DatasetBranch(self._repo.branch(name))

    def branches(
        self,
        max_amount: Optional[int] = None,
        after: Optional[str] = None,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        for branch in self._repo.branches(
            max_amount=max_amount,
            after=after,
            prefix=prefix,
            **kwargs,
        ):
            yield DatasetBranch(branch)

    def get_commit(self, commit_id: str) -> DatasetReference:
        return DatasetReference(self._repo.commit(commit_id))

    def ref(self, ref_id: str) -> DatasetReference:
        return DatasetReference(self._repo.ref(ref_id))

    def tag(self, tag_id: str) -> Tag:
        return self._repo.tag(tag_id)

    def tags(
        self,
        max_amount: Optional[int] = None,
        after: Optional[str] = None,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        for tag in self._repo.tags(
            max_amount=max_amount,
            after=after,
            prefix=prefix,
            **kwargs,
        ):
            yield tag

    def diff(self, left_ref: str, right_ref: str, *args: Any, **kwargs: Any) -> Any:
        return self.ref(left_ref).diff(right_ref, *args, **kwargs)

    def objects(self, ref: str, *args: Any, **kwargs: Any) -> Any:
        return self.ref(ref).objects(*args, **kwargs)

    def commits(self, ref: str, *args: Any, **kwargs: Any) -> Any:
        return self.ref(ref).log(*args, **kwargs)

    def get_dataset(
        self,
        file_type: str = "csv",
        ref: str = "main",
        data_dir: Optional[str] = None,
        split: Optional[str | Split | list[str] | list[Split]] = None,
        features: Optional[Features] = None,
        keep_in_memory: Optional[bool] = None,
        streaming: bool = False,
        num_proc: Optional[int] = None,
        auth_splits: bool = True,
        **kwargs: Any,
    ) -> Union["LFSDataset", "LFSDatasetDict", "LFSIterableDataset", "LFSIterableDatasetDict"]:
        from datasets_hub.lfs_datasets import _convert_ds_to_lfs  # local import to avoid circular dependency

        presign_urls: list[PresignedUrl] = self._lfs_upload.presign.get_presigned_urls(
            repo_name=self.id,
            ref=ref,
            prefix=data_dir,
        )

        metadata_filename = _.get_metadata_file_name()
        presign_urls = [obj for obj in presign_urls if obj.name != metadata_filename]

        if auth_splits:
            data_files = {obj.name: obj.physical_address for obj in presign_urls}
        else:
            data_files = [obj.physical_address for obj in presign_urls]

        ds = hf_load_dataset(
            path=file_type,
            data_files=data_files,
            split=split,
            streaming=cast(Literal[False], streaming),
            features=features,
            keep_in_memory=keep_in_memory,
            num_proc=num_proc,
        )
        return _convert_ds_to_lfs(ds)


    def upload_dataset(
        self,
        dataset: Dataset | DatasetDict | IterableDataset | IterableDatasetDict,
        branch: str = "main",
        file_type: str = "csv",
        split: Optional[str] = None,
        data_dir: Optional[str] = None,
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None
        ):
        pairs = _.dataset_pairs(dataset=dataset, split=split)

        num_uploaded = 0
        for ds_split, ds in pairs:
            full_path = _.dataset_object_path(data_dir, ds_split, file_type)
            success = self._lfs_upload.upload_dataset(
                dataset=ds,
                repo_name=self.id,
                branch=branch,
                path=full_path,
                file_type=file_type,
                presign=presign,
                multipart=multipart,
                batch_size=batch_size,
            )
            if success:
                num_uploaded += 1

        if num_uploaded != len(pairs):
            raise RuntimeError(f"Upload failed for dataset '{self.id}' on branch '{branch}'.")


    def __repr__(self) -> str:
        return f'DatasetRepo(id="{self.id}")'

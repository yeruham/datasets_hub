from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, cast, Literal

from lakefs import repository, repositories, Reference
from lakefs.client import _BaseLakeFSObject
from datasets import load_dataset as hf_load_dataset, Split, Features
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict

from datasets_hub.upload.lfs_upload import LFSUpload
from datasets_hub.dataset_repo import DatasetRepo
from datasets_hub.lakefs_connection import get_lakefs_client, STORAGE_NAMESPACE
from datasets_hub.settings import get_hub_settings
from datasets_hub.validation.commit import prepare_commit_metadata, upload_profile_to_branch
from datasets_hub.models import PresignedUrl


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
    ) -> Union["LFSDataset", "LFSDatasetDict", "LFSIterableDataset", "LFSIterableDatasetDict"]:
        from datasets_hub.lfs_datasets import _convert_ds_to_lfs  # local import to avoid circular dependency

        presign_urls: list[PresignedUrl] = self.lfs_upload.presign.get_presigned_urls(
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
            dataset: Dataset | DatasetDict | IterableDataset | IterableDatasetDict,
            ds_name: str,
            commit_message: str,
            file_type: str = "csv",
            commit_metadata: Optional[dict] = None,
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            branch: Optional[str] = None,
            presign: bool = True,
            multipart: bool = False,
            batch_size: Optional[int] = None,
            validation_profile_path: Optional[str] = None,
            skip_validation: bool = False,
            **kwargs,
    ) -> Reference:
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

        # Normalize to iterable of (split_name, ds) pairs
        if isinstance(dataset, (DatasetDict, IterableDatasetDict)):
            pairs = [(ds_split, dataset[ds_split]) for ds_split in dataset.keys()]
        elif isinstance(dataset, (Dataset, IterableDataset)):
            split_name = split or (str(dataset.split) if hasattr(dataset, "split") else None)
            pairs = [(split_name, dataset)]
        else:
            raise TypeError(f"Unsupported dataset type: {type(dataset)}")

        num_uploaded = 0
        for ds_split, ds in pairs:
            path_parts = [data_dir, ds_split]
            full_path = "/".join(p.strip("/") for p in path_parts if p)
            ext = file_type if file_type.startswith('.') else f".{file_type}"
            full_path += ext
            success = self.lfs_upload.upload_dataset(
                dataset=ds,
                repo_name=ds_name,
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
            raise RuntimeError(f"Upload failed for dataset '{ds_name}' on branch '{branch}'.")

        from pathlib import Path

        final_metadata = dict(commit_metadata or {})
        profile = None
        if not skip_validation and self._settings.validation_enabled:
            profile_path = Path(validation_profile_path) if validation_profile_path else None
            final_metadata, profile = prepare_commit_metadata(
                final_metadata,
                profile_path=profile_path,
                settings=self._settings,
            )
            if profile is not None and branch:
                upload_profile_to_branch(self._client, ds_name, branch, profile, self._settings)

        ds_repo = self.get_ds_repo(ds_name)
        return ds_repo.branch(branch).commit(commit_message, final_metadata)

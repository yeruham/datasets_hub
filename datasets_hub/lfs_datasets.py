from __future__ import annotations

from typing import Optional
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from datasets_hub.lakefs_hub import LakefsHub
from datasets_hub.ds_repo import DatasetReference
from datasets_hub.models import CommitMetadata

_PUSH_DOCSTRING = """
Push dataset to lakeFS.
Note: returns lakeFS Reference, not HuggingFace CommitInfo.
`token` is accepted for API compatibility but is not used.

Args:
    repo_id: lakeFS repository name.
    metadata: Required metadata for the saved dataset version.
    revision: branch name.
    file_type: 'csv' or 'parquet'.
    multipart: Use experimental multipart upload API.
               Keeps memory bounded to batch_size bytes at a time.
    batch_size: Part size in bytes. Required when multipart=True. Must be >= 5MB.
    presign: Use presigned URL for single-shot upload. Ignored when multipart=True.
"""


class LFSDataset(Dataset):

    @classmethod
    def from_dataset(cls, ds: Dataset) -> LFSDataset:
        ds.__class__ = cls
        return ds

    def push_to_hub(
        self,
        repo_id: str,
        commit_metadata: CommitMetadata,
        commit_message: str,
        split: Optional[str] = None,
        data_dir: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        file_type: str = "csv",
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> DatasetReference:
        return LakefsHub().push_and_commit_dataset(
            dataset=self,
            ds_name=repo_id,
            data_dir=data_dir,
            split=split,
            commit_message=commit_message,
            commit_metadata=commit_metadata,
            branch=revision,
            file_type=file_type,
            presign=presign,
            multipart=multipart,
            batch_size=batch_size,
        )

    push_to_hub.__doc__ = _PUSH_DOCSTRING


class LFSDatasetDict(DatasetDict):

    @classmethod
    def from_dataset_dict(cls, ds: DatasetDict) -> LFSDatasetDict:
        ds.__class__ = cls
        return ds

    def push_to_hub(
        self,
        repo_id: str,
        commit_metadata: CommitMetadata,
        commit_message: str,
        data_dir: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        file_type: str = "csv",
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> DatasetReference:
        return LakefsHub().push_and_commit_dataset(
            dataset=self,
            ds_name=repo_id,
            data_dir=data_dir,
            commit_message=commit_message,
            commit_metadata=commit_metadata,
            branch=revision,
            file_type=file_type,
            presign=presign,
            multipart=multipart,
            batch_size=batch_size,
        )

    push_to_hub.__doc__ = _PUSH_DOCSTRING


class LFSIterableDataset(IterableDataset):

    @classmethod
    def from_iterable_dataset(cls, ds: IterableDataset) -> LFSIterableDataset:
        ds.__class__ = cls
        return ds

    def push_to_hub(
        self,
        repo_id: str,
        commit_metadata: CommitMetadata,
        commit_message: str,
        split: Optional[str] = None,
        data_dir: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        file_type: str = "csv",
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> DatasetReference:
        return LakefsHub().push_and_commit_dataset(
            dataset=self,
            ds_name=repo_id,
            data_dir=data_dir,
            split=split,
            commit_message=commit_message,
            commit_metadata=commit_metadata,
            branch=revision,
            file_type=file_type,
            presign=presign,
            multipart=multipart,
            batch_size=batch_size,
        )

    push_to_hub.__doc__ = _PUSH_DOCSTRING


class LFSIterableDatasetDict(IterableDatasetDict):

    @classmethod
    def from_iterable_dataset_dict(cls, ds: IterableDatasetDict) -> LFSIterableDatasetDict:
        ds.__class__ = cls
        return ds

    def push_to_hub(
        self,
        repo_id: str,
        commit_metadata: CommitMetadata,
        commit_message: str,
        data_dir: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        file_type: str = "csv",
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> DatasetReference:
        return LakefsHub().push_and_commit_dataset(
            dataset=self,
            ds_name=repo_id,
            data_dir=data_dir,
            commit_message=commit_message,
            commit_metadata=commit_metadata,
            branch=revision,
            file_type=file_type,
            presign=presign,
            multipart=multipart,
            batch_size=batch_size,
        )

    push_to_hub.__doc__ = _PUSH_DOCSTRING


def _convert_ds_to_lfs(
    ds: Dataset | DatasetDict | IterableDataset | IterableDatasetDict,
) -> LFSDataset | LFSDatasetDict | LFSIterableDataset | LFSIterableDatasetDict:
    _converters = {
        Dataset: LFSDataset.from_dataset,
        DatasetDict: LFSDatasetDict.from_dataset_dict,
        IterableDataset: LFSIterableDataset.from_iterable_dataset,
        IterableDatasetDict: LFSIterableDatasetDict.from_iterable_dataset_dict,
    }
    converter = _converters.get(type(ds))
    if converter is None:
        raise TypeError(f"Unsupported dataset type: {type(ds)}")
    return converter(ds)

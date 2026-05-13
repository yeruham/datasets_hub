from __future__ import annotations
from typing import Optional, Union
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from lakefs import Commit, Reference

from datasets_hub.datasets_hub import LakefsHub


class LFSDataset(Dataset):

    @classmethod
    def from_dataset(cls, ds: Dataset) -> LFSDataset:
        ds.__class__ = cls
        return ds


    def push_to_hub(
        self,
        repo_id: str,
        split: Optional[str] = None,
        data_dir: Optional[str] = None,
        commit_message: Optional[str] = "",
        token: Optional[str] = None,
        revision: Optional[str] = None,
        file_type: Optional[str] = ".csv",
        **kwargs
    ) -> Reference:
        """
        Push dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """

        hub = LakefsHub()
        ref = hub.push_and_commit_dataset(
                        dataset=self,
                        ds_name=repo_id,
                        data_dir=data_dir,
                        split=split,
                        commit_message=commit_message,
                        branch=revision,
                        file_type=file_type
                        )
        return ref

class LFSDatasetDict(DatasetDict):

    @classmethod
    def from_dataset_dict(cls, ds: DatasetDict) -> LFSDatasetDict:
        ds.__class__ = cls
        return ds


    def push_to_hub(
            self,
            repo_id: str,
            data_dir: Optional[str] = None,
            commit_message: Optional[str] = "",
            token: Optional[str] = None,
            revision: Optional[str] = None,
            file_type: Optional[str] = ".csv",
            **kwargs
    ) -> Reference:
        """
        Push dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """

        hub = LakefsHub()
        ref = hub.push_and_commit_dataset(
                        dataset=self,
                        ds_name=repo_id,
                        data_dir=data_dir,
                        commit_message=commit_message,
                        branch=revision,
                        file_type=file_type
                        )
        return ref


class LFSIterableDataset(IterableDataset):

    @classmethod
    def from_iterable_dataset(cls, ds: IterableDataset) -> LFSIterableDataset:
        ds.__class__ = cls
        return ds


    def push_to_hub(
            self,
            repo_id: str,
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            commit_message: Optional[str] = "",
            token: Optional[str] = None,
            revision: Optional[str] = None,
            file_type: Optional[str] = ".csv",
            **kwargs
    ) -> Reference:
        """
        Push dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """
        hub = LakefsHub()
        ref = hub.push_iterable_dataset(dataset=self,
                        repo_id=repo_id,
                        data_dir=data_dir,
                        split=split,
                        commit_message=commit_message,
                        branch=revision,
                        file_type=file_type
                        )
        return ref

class LFSIterableDatasetDict(IterableDatasetDict):

    @classmethod
    def from_iterable_dataset_dict(cls, ds: IterableDatasetDict) -> LFSIterableDatasetDict:
        ds.__class__ = cls
        return ds


    def push_to_hub(
            self,
            repo_id: str,
            data_dir: Optional[str] = None,
            commit_message: Optional[str] = "",
            token: Optional[str] = None,
            revision: Optional[str] = None,
            file_type: Optional[str] = ".csv",
            **kwargs
    ) -> Reference:
        """
        Push dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """
        hub = LakefsHub()
        ref = hub.push_iterable_dataset(dataset=self,
                        repo_id=repo_id,
                        data_dir=data_dir,
                        commit_message=commit_message,
                        branch=revision,
                        file_type=file_type
                        )
        return ref
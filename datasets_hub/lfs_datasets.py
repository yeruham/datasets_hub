from __future__ import annotations
from typing import Optional, Union
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from lakefs import Commit

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
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        **kwargs
    ) -> Commit:
        pass

class LFSDatasetDict(DatasetDict):

    @classmethod
    def from_dataset_dict(cls, ds: DatasetDict) -> LFSDatasetDict:
        ds.__class__ = cls
        return ds


    def push_to_hub(
        self,
        repo_id: str,
        split: Optional[str] = None,
        data_dir: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        **kwargs
    ) -> Commit:
        pass

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
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        **kwargs
    ) -> Commit:
        pass

class LFSIterableDatasetDict(IterableDatasetDict):

    @classmethod
    def from_iterable_dataset_dict(cls, ds: IterableDatasetDict) -> LFSIterableDatasetDict:
        ds.__class__ = cls
        return ds


    def push_to_hub(
        self,
        repo_id: str,
        split: Optional[str] = None,
        data_dir: Optional[str] = None,
        commit_message: Optional[str] = None,
        commit_description: Optional[str] = None,
        token: Optional[str] = None,
        revision: Optional[str] = None,
        **kwargs
    ) -> Commit:
        pass
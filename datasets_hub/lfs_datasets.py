from __future__ import annotations
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict

class LFSDataset(Dataset):

    @classmethod
    def from_dataset(cls, ds: Dataset) -> LFSDataset:
        ds.__class__ = cls
        return ds

class LFSDatasetDict(DatasetDict):

    @classmethod
    def from_dataset_dict(cls, ds: DatasetDict) -> LFSDatasetDict:
        ds.__class__ = cls
        return ds

class LFSIterableDataset(IterableDataset):

    @classmethod
    def from_iterable_dataset(cls, ds: IterableDataset) -> LFSIterableDataset:
        ds.__class__ = cls
        return ds

class LFSIterableDatasetDict(IterableDatasetDict):

    @classmethod
    def from_iterable_dataset_dict(cls, ds: IterableDatasetDict) -> LFSIterableDatasetDict:
        ds.__class__ = cls
        return ds
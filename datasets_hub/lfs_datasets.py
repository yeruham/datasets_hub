from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from lakefs import Reference

if TYPE_CHECKING:
    from lakefs_hub import LakefsHub


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
        **kwargs,
    ) -> Reference:
        """
        Push dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """
        from lakefs_hub import LakefsHub  # local import to avoid circular dependency
        hub = LakefsHub()
        return hub.push_and_commit_dataset(
            dataset=self,
            ds_name=repo_id,
            data_dir=data_dir,
            split=split,
            commit_message=commit_message,
            branch=revision,
            file_type=file_type,
        )


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
        **kwargs,
    ) -> Reference:
        """
        Push dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """
        from lakefs_hub import LakefsHub  # local import to avoid circular dependency
        hub = LakefsHub()
        return hub.push_and_commit_dataset(
            dataset=self,
            ds_name=repo_id,
            data_dir=data_dir,
            commit_message=commit_message,
            branch=revision,
            file_type=file_type,
        )


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
        **kwargs,
    ) -> Reference:
        """
        Push iterable dataset to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """
        from lakefs_hub import LakefsHub  # local import to avoid circular dependency
        hub = LakefsHub()
        return hub.push_iterable_dataset(
            dataset=self,
            repo_id=repo_id,
            data_dir=data_dir,
            split=split,
            commit_message=commit_message,
            branch=revision,
            file_type=file_type,
        )


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
        **kwargs,
    ) -> Reference:
        """
        Push iterable dataset dict to lakeFS.
        Note: returns lakeFS Reference, not HuggingFace CommitInfo.
        """
        from lakefs_hub import LakefsHub  # local import to avoid circular dependency
        hub = LakefsHub()
        return hub.push_iterable_dataset(
            dataset=self,
            repo_id=repo_id,
            data_dir=data_dir,
            commit_message=commit_message,
            branch=revision,
            file_type=file_type,
        )


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

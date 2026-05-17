from __future__ import annotations

from typing import Optional

from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from datasets_hub.models import CommitMetadata, DatasetMetadata

def create_ds_confirm(metadata: DatasetMetadata):
    if not isinstance(metadata, DatasetMetadata):
        raise ValueError("metadata is required when creating dataset")

def commit_confirm(message: str, metadata: CommitMetadata):
    if message is None:
        raise ValueError("message is required when committing dataset changes")
    if not isinstance(metadata, CommitMetadata):
        raise ValueError("metadata is required when committing dataset changes")


def dataset_pairs(
        dataset: Dataset | DatasetDict | IterableDataset | IterableDatasetDict,
        split: Optional[str],
) -> list[tuple[Optional[str], Dataset | IterableDataset]]:
    if isinstance(dataset, (DatasetDict, IterableDatasetDict)):
        return [(ds_split, dataset[ds_split]) for ds_split in dataset.keys()]
    if isinstance(dataset, (Dataset, IterableDataset)):
        split_name = split or (str(dataset.split) if hasattr(dataset, "split") else None)
        return [(split_name, dataset)]
    raise TypeError(f"Unsupported dataset type: {type(dataset)}")


def dataset_object_path(
        data_dir: Optional[str],
        split: Optional[str],
        file_type: str,
) -> str:
    path_parts = [data_dir, split]
    full_path = "/".join(p.strip("/") for p in path_parts if p)
    ext = file_type if file_type.startswith(".") else f".{file_type}"
    return f"{full_path}{ext}"
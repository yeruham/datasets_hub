from __future__ import annotations

from datasets import Dataset, DatasetDict, IterableDataset, IterableDatasetDict, NamedSplit

from datasets_hub import (
    CommitMetadata,
    DatasetMetadata,
    DatasetReference,
    LFSDataset,
    LFSDatasetDict,
    LFSIterableDataset,
    LFSIterableDatasetDict,
    LakefsHub,
)
from examples.utils import assert_type, ensure_repo, REPO_NAME, DATA_DIR, FILE_TYPE, REVISION


def main() -> None:
    ensure_repo(repo_name=REPO_NAME, example_md="dataset_wrappers")

    lfs_split_name = NamedSplit(name="LFSDataset")
    base_dataset = Dataset.from_dict(
        {
            "id": [10, 11, 12],
            "value": ["red", "green", "blue"],
        },
        split=lfs_split_name
    )
    lfs_dataset = LFSDataset.from_dataset(base_dataset)
    assert_type("lfs_dataset", lfs_dataset, LFSDataset)

    metadata = CommitMetadata.model_validate({"example": "dataset_wrappers", "object": "LFSDataset"})
    reference = lfs_dataset.push_to_hub(
        repo_id=REPO_NAME,
        revision=REVISION,
        commit_metadata=metadata,
        data_dir=DATA_DIR,
        commit_message="examples: push LFSDataset",
        file_type=FILE_TYPE,
        presign=True,
    )
    assert_type("LFSDataset push reference", reference, DatasetReference)
    print(reference)

    dataset_dict = DatasetDict(
        {
            "LFSDatasetDictTrain": Dataset.from_dict({"id": [1, 2], "value": ["train-a", "train-b"]}),
            "LFSDatasetDictValidation": Dataset.from_dict({"id": [3], "value": ["validation-a"]}),
        }
    )
    lfs_dataset_dict = LFSDatasetDict.from_dataset_dict(dataset_dict)
    assert_type("lfs_dataset_dict", lfs_dataset_dict, LFSDatasetDict)

    metadata = CommitMetadata.model_validate({"example": "dataset_wrappers", "object": "LFSDatasetDict"})
    reference = lfs_dataset_dict.push_to_hub(
        repo_id=REPO_NAME,
        revision=REVISION,
        commit_metadata=metadata,
        data_dir=DATA_DIR,
        commit_message="examples: push LFSDatasetDict",
        file_type=FILE_TYPE,
    )
    assert_type("LFSDatasetDict push reference", reference, DatasetReference)
    print(reference)

    ilfs_split_name = NamedSplit(name="ILFSDataset")
    iterable = IterableDataset.from_generator(
        lambda: ({"id": i, "value": f"iterable-{i}"} for i in range(1000000)),
        split=ilfs_split_name
    )
    lfs_iterable = LFSIterableDataset.from_iterable_dataset(iterable)
    assert_type("ilfs_iterable", lfs_iterable, LFSIterableDataset)
    reference = lfs_iterable.push_to_hub(
        repo_id=REPO_NAME,
        revision=REVISION,
        commit_metadata=metadata,
        data_dir=DATA_DIR,
        commit_message="examples: push ILFSDataset",
        file_type=FILE_TYPE,
        multipart=True,
        batch_size=5
    )
    assert_type("ILFSDataset push reference", reference, DatasetReference)
    print(reference)

    iterable_dict = IterableDatasetDict({"ILFSDatasetDict": lfs_iterable})
    lfs_iterable_dict = LFSIterableDatasetDict.from_iterable_dataset_dict(iterable_dict)
    assert_type("lfs_iterable_dict", lfs_iterable_dict, LFSIterableDatasetDict)
    reference = lfs_iterable_dict.push_to_hub(
        repo_id=REPO_NAME,
        revision=REVISION,
        commit_metadata=metadata,
        data_dir=DATA_DIR,
        commit_message="examples: push ILFSDatasetDict",
        file_type=FILE_TYPE,
        multipart=True,
        batch_size=5
    )
    assert_type("ILFSDatasetDict push reference", reference, DatasetReference)
    print(reference)


if __name__ == "__main__":
    main()

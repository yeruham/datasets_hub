from __future__ import annotations

import os
from datetime import datetime, timezone

from datasets import Dataset

from datasets_hub import (
    CommitMetadata,
    DatasetBranch,
    DatasetMetadata,
    DatasetReference,
    DatasetRepo,
    LakefsHub,
)
from examples.utils import assert_type, ensure_repo, DATA_DIR, REPO_NAME

def main() -> None:
    repo = ensure_repo(repo_name=REPO_NAME, example_md="repo lifecycle")

    branch = repo.branch("main")
    assert_type("branch", branch, DatasetBranch)
    print(f"branch head: {branch.head}")
    assert_type("branch.head", branch.head, DatasetReference)

    branches = list(repo.branches())
    print(f"branches: {branches}")

    dataset = Dataset.from_dict(
        {
            "id": [1, 2, 3, 4],
            "text": ["alpha", "beta", "gamma", "delta"],
            "label": [0, 1, 1, 0],
        }
    )
    print(dataset)

    repo.upload_dataset(dataset=dataset, branch="main", file_type="csv", split="train", data_dir=DATA_DIR)
    print("uploaded Dataset to lakeFS")

    uncommitted = list(branch.uncommitted())
    print(f"uncommitted changes: {uncommitted}")

    commit_metadata = CommitMetadata.model_validate(
        {
            "example": "repo_lifecycle",
            "dataset_rows": dataset.num_rows,
        }
    )
    assert_type("commit_metadata", commit_metadata, CommitMetadata)

    reference = branch.commit(
        message="examples: upload dataset from 01_repo_lifecycle",
        metadata=commit_metadata,
    )
    assert_type("commit reference", reference, DatasetReference)
    print(reference)

    loaded = repo.get_dataset(file_type="csv", ref="main", data_dir=DATA_DIR)
    print(f"loaded dataset type: {type(loaded).__name__}")
    print(loaded)

    commit = reference.get_commit()
    print(f"resolved lakeFS commit: {commit}")


if __name__ == "__main__":
    main()

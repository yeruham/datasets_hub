from __future__ import annotations

import os

from datasets_hub import (
    CommitMetadata,
    DatasetMetadata,
    DatasetRepo,
    LFSDataset,
    LFSDatasetDict,
    LFSIterableDataset,
    LFSIterableDatasetDict,
    LakefsHub,
)
from examples.utils import assert_type, REPO_NAME, REVISION, FILE_TYPE, DATA_DIR


def main() -> None:
    hub = LakefsHub()
    assert_type("hub", hub, LakefsHub)

    repo_metadata = DatasetMetadata.model_validate(
        {
            "created_by": "datasets-hub-example",
            "example": "hub",
        }
    )
    assert_type("repo_metadata", repo_metadata, DatasetMetadata)

    repo = hub.create_ds_repo(name=REPO_NAME, metadata=repo_metadata)
    assert_type("repo", repo, DatasetRepo)
    print(f"create repo id: {repo.id}")
    print(f"repo metadata: {repo.metadata}")

    repos = hub.list_ds_repos()
    print(f"repositories before example run: {repos}")

    repo = hub.get_ds_repo(name=REPO_NAME)
    assert_type("repo", repo, DatasetRepo)
    print(f"get repo id: {repo.id}")
    print(f"repo metadata: {repo.metadata}")

if __name__ == "__main__":
    main()

from __future__ import annotations

from datasets_hub import (
    DatasetMetadata,
    LakefsHub, DatasetRepo,
)

REPO_NAME =  "datasets-hub-example-1"
DATA_DIR = "examples/dataset"
FILE_TYPE = "csv"
REVISION = "main"

def assert_type(name: str, value: object, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"{name} expected {expected_type.__name__}, got {type(value).__name__}")
    print(f"{name}: {type(value).__name__}")


def ensure_repo(repo_name: str, example_md: str = "ensure_repo") -> DatasetRepo:
    metadata = DatasetMetadata.model_validate(
        {
            "created_by": "datasets-hub-example",
            "example": example_md,
        }
    )
    return LakefsHub().get_ds_repo(repo_name).create(metadata=metadata, exist_ok=True)
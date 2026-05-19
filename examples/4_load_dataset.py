from __future__ import annotations

from datasets_hub import (
    LFSDataset,
    LFSDatasetDict,
    LFSIterableDataset,
    LFSIterableDatasetDict,
    LakefsHub,
)
from examples.utils import REPO_NAME, DATA_DIR, FILE_TYPE, REVISION


def main() -> None:
    hub = LakefsHub()

    loaded = hub.load_dataset(
        path=FILE_TYPE,
        name=REPO_NAME,
        revision=REVISION,
        data_dir=DATA_DIR,
    )
    if not isinstance(loaded, (LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict)):
        raise TypeError(f"unexpected loaded dataset type: {type(loaded).__name__}")

    print(f"loaded from {REPO_NAME}@{REVISION}: {type(loaded).__name__}")
    print(loaded)


if __name__ == "__main__":
    main()
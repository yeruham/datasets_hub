from __future__ import annotations

from typing import TYPE_CHECKING

from datasets_hub.settings import HubSettings, get_hub_settings

if TYPE_CHECKING:
    from datasets_hub.dataset_repo import DatasetRepo
    from datasets_hub.lakefs_hub import LakefsHub
    from datasets_hub.lfs_datasets import (
        LFSDataset,
        LFSDatasetDict,
        LFSIterableDataset,
        LFSIterableDatasetDict,
    )
    from datasets_hub.validation.profile import ValidationProfile

__all__ = [
    "LakefsHub",
    "LFSDataset",
    "LFSDatasetDict",
    "LFSIterableDataset",
    "LFSIterableDatasetDict",
    "DatasetRepo",
    "HubSettings",
    "get_hub_settings",
    "ValidationProfile",
    "init_validation_profile",
    "load_validation_profile",
]

_LAZY_EXPORTS = {
    "LakefsHub": ("datasets_hub.lakefs_hub", "LakefsHub"),
    "LFSDataset": ("datasets_hub.lfs_datasets", "LFSDataset"),
    "LFSDatasetDict": ("datasets_hub.lfs_datasets", "LFSDatasetDict"),
    "LFSIterableDataset": ("datasets_hub.lfs_datasets", "LFSIterableDataset"),
    "LFSIterableDatasetDict": ("datasets_hub.lfs_datasets", "LFSIterableDatasetDict"),
    "DatasetRepo": ("datasets_hub.dataset_repo", "DatasetRepo"),
    "ValidationProfile": ("datasets_hub.validation.profile", "ValidationProfile"),
    "init_validation_profile": ("datasets_hub.validation.profile", "init_validation_profile"),
    "load_validation_profile": ("datasets_hub.validation.profile", "load_validation_profile"),
}


def __getattr__(name: str):
    if name in _LAZY_EXPORTS:
        module_path, attr = _LAZY_EXPORTS[name]
        import importlib

        module = importlib.import_module(module_path)
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

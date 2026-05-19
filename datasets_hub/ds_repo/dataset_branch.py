from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Optional, Literal

import lakefs_sdk
from lakefs import Branch

from datasets_hub.models import CommitMetadata
from datasets_hub.ds_repo.dataset_reference import DatasetReference
from datasets_hub.ds_repo.metadata import metadata_to_lakefs
from datasets_hub.ds_repo import utils as _


class DatasetBranch(DatasetReference):
    """Domain wrapper around a lakeFS Branch."""

    def __init__(self, branch: Branch):
        super().__init__(branch)
        self._branch = branch

    @property
    def head(self) -> DatasetReference:
        return DatasetReference(self._branch.head)

    @property
    def lakefs_branch(self) -> Branch:
        return self._branch

    def cherry_pick(
        self,
        reference: Any,
        metadata: CommitMetadata,
        parent_number: Optional[int] = None,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        _.commit_confirm(message, metadata)
        kwargs.setdefault(
            "commit_overrides",
            lakefs_sdk.CommitOverrides(message=message, metadata=metadata_to_lakefs(metadata)),
        )
        return self._branch.cherry_pick(reference, parent_number=parent_number, **kwargs)

    def commit(
        self,
        message: str,
        metadata: CommitMetadata,
        **kwargs: Any,
    ) -> DatasetReference:
        _.commit_confirm(message, metadata)
        return DatasetReference(
            self._branch.commit(message=message, metadata=metadata_to_lakefs(metadata), **kwargs)
        )

    def create(self, source_reference: Any, exist_ok: bool = False, **kwargs: Any) -> DatasetBranch:
        return DatasetBranch(self._branch.create(source_reference, exist_ok=exist_ok, **kwargs))

    def delete(self, **kwargs: Any) -> None:
        self._branch.delete(**kwargs)

    def delete_objects(self, object_paths: Any) -> None:
        self._branch.delete_objects(object_paths)

    def reset_changes(
        self,
        path_type: Literal["common_prefix", "object", "reset"] = "reset",
        path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self._branch.reset_changes(path_type=path_type, path=path, **kwargs)

    def revert(
        self,
        reference: Any,
        metadata: CommitMetadata,
        parent_number: int = 0,
        message: Optional[str] = "",
        **kwargs: Any,
    ) -> Any:
        _.commit_confirm(message, metadata)
        kwargs.setdefault(
            "commit_overrides",
            lakefs_sdk.CommitOverrides(message=message, metadata=metadata_to_lakefs(metadata)),
        )
        return self._branch.revert(reference, parent_number=parent_number, **kwargs)

    def uncommitted(
        self,
        max_amount: Optional[int] = None,
        after: Optional[str] = None,
        prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        return self._branch.uncommitted(
            max_amount=max_amount,
            after=after,
            prefix=prefix,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f'DatasetBranch(repository="{self.repo_id}", id="{self.id}")'

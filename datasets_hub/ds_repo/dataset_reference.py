from __future__ import annotations

from typing import Any, Optional

from lakefs import Reference

from datasets_hub.models import CommitMetadata
from datasets_hub.ds_repo.metadata import metadata_to_lakefs


class DatasetReference:
    """Domain wrapper around a lakeFS Reference."""

    def __init__(self, reference: Reference):
        self._reference = reference

    @property
    def id(self) -> str:
        return self._reference.id

    @property
    def repo_id(self) -> str:
        return self._reference.repo_id

    @property
    def lakefs_reference(self) -> Reference:
        return self._reference

    def diff(
        self,
        other_ref: Any,
        max_amount: Optional[int] = None,
        after: Optional[str] = None,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        return self._reference.diff(
            other_ref,
            max_amount=max_amount,
            after=after,
            prefix=prefix,
            delimiter=delimiter,
            **kwargs,
        )

    def get_commit(self) -> Any:
        return self._reference.get_commit()

    def log(self, max_amount: Optional[int] = None, **kwargs: Any) -> Any:
        return self._reference.log(max_amount=max_amount, **kwargs)

    def merge_into(
        self,
        destination_branch: Any,
        metadata: CommitMetadata | MetadataInput,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        return self._reference.merge_into(
            destination_branch,
            message=message,
            metadata=metadata_to_lakefs(metadata),
            **kwargs,
        )

    def object(self, path: str) -> Any:
        return self._reference.object(path)

    def objects(
        self,
        max_amount: Optional[int] = None,
        after: Optional[str] = None,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        return self._reference.objects(
            max_amount=max_amount,
            after=after,
            prefix=prefix,
            delimiter=delimiter,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f'DatasetReference(repository="{self.repo_id}", id="{self.id}")'

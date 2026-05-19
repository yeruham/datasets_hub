from typing import Any

from pydantic import BaseModel, ConfigDict


class PresignedUrl(BaseModel):
    name: str
    physical_address: str
    physical_address_expiry: int


class DatasetMetadata(BaseModel):
    """Metadata required when creating a dataset repository."""

    model_config = ConfigDict(extra="allow")


class CommitMetadata(BaseModel):
    """Metadata required when saving a dataset version."""

    model_config = ConfigDict(extra="allow")


MetadataInput = BaseModel | dict[str, Any]
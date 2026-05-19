from __future__ import annotations

from io import BytesIO
from typing import Optional, Union
from lakefs import Client
from datasets import Dataset, IterableDataset
import io

from datasets_hub.upload.presign import LFSPresign
from datasets_hub.upload.multipart_upload import MultipartUpload
from datasets_hub.upload.utils import extract_etag_from_response, content_type_for_file_type

SUPPORTED_FILE_TYPES = {"csv", "parquet"}

# S3 minimum part size is 5MB (except for the last part)
MIN_PART_SIZE_MEGABYTES = 5


class LFSUpload:

    def __init__(self, client: Client):
        self._client = client
        self.multipart_upload = MultipartUpload(client)
        self.presign = LFSPresign(client)

    def _obj_upload(self, repo_name: str, branch: str, path: str, buffer: BytesIO) -> bool:
        state = self._client.sdk_client.objects_api.upload_object(
            repository=repo_name, branch=branch, path=path, content=buffer.getvalue()
        )
        return state is not None


    def upload_dataset(
        self,
        repo_name: str,
        dataset: Union[Dataset, IterableDataset],
        branch: str,
        path: str,
        file_type: str,
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None,
    ) -> bool:
        """
        Upload a Dataset or IterableDataset to lakeFS.

        Args:
            file_type: 'csv' or 'parquet'
            presign: Use presigned URL for single-shot upload (staging_api).
                     Ignored when multipart=True.
            multipart: Use multipart upload (experimental_api).
                       Keeps memory bounded to batch_size bytes at a time.
            batch_size: Part size in bytes. Required when multipart=True.
                        Must be >= 5MB (MIN_PART_SIZE_MEGABYTES) except for the last part.
        """
        if file_type not in SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file_type '{file_type}'. Supported: {SUPPORTED_FILE_TYPES}")

        if multipart and batch_size is None:
            raise ValueError("batch_size is required when multipart=True.")

        if not multipart and batch_size is not None:
            print("batch_size has no effect when multipart=False.")

        if multipart and batch_size < MIN_PART_SIZE_MEGABYTES:
            raise ValueError(
                f"batch_size must be >= {MIN_PART_SIZE_MEGABYTES} MB. Got {batch_size}."
            )

        if multipart:
            batch_size = batch_size * 1024 * 1024
            return self.multipart_upload.upload(
                repo_name=repo_name,
                branch=branch,
                path=path,
                dataset=dataset,
                file_type=file_type,
                part_size=batch_size,
            )
        else:
            return self._single_shot_upload(
                repo_name=repo_name,
                branch=branch,
                path=path,
                dataset=dataset,
                file_type=file_type,
                presign=presign,
            )


    def _single_shot_upload(
        self,
        repo_name: str,
        branch: str,
        path: str,
        dataset: Union[Dataset, IterableDataset],
        file_type: str,
        presign: bool,
    ) -> bool:
        buffer = io.BytesIO()
        if file_type == "csv":
            dataset.to_csv(buffer)
        elif file_type == "parquet":
            dataset.to_parquet(buffer)

        size_bytes = buffer.getbuffer().nbytes
        buffer.seek(0)
        content_type = content_type_for_file_type(file_type)

        if presign:
            return self.presign.presign_obj_upload(repo_name, branch, path, buffer, content_type, size_bytes)
        else:
            return self._obj_upload(repo_name, branch, path, buffer)
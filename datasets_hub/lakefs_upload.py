from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from lakefs import Client
from lakefs_sdk import StagingMetadata, CompletePresignMultipartUpload, UploadPartFrom
from datasets import Dataset, IterableDataset
import io
import requests
import pyarrow as pa
import pyarrow.parquet as pq

from models import PresignedUrl

SUPPORTED_FILE_TYPES = {".csv", ".parquet"}

# S3 minimum part size is 5MB (except for the last part)
MIN_PART_SIZE_BYTES = 5 * 1024 * 1024


class LakefsUpload:

    def __init__(self, client: Client):
        self._client = client


    def get_presigned_urls(self, repo_name: str, ref: str, prefix: str) -> list[PresignedUrl]:
        state_objects = self._client.sdk_client.objects_api.list_objects(
            repository=repo_name, ref=ref, prefix=prefix, presign=True
        )
        return [
            PresignedUrl(
                name=self._get_object_name(state.path),
                physical_address=state.physical_address,
                physical_address_expiry=state.physical_address_expiry,
            )
            for state in state_objects.results
        ]

    def _get_object_name(self, path: str) -> str:
        return Path(path).stem


    def upload_dataset(
        self,
        repo_name: str,
        dataset: Union[Dataset, IterableDataset],
        branch: str,
        path: str,
        file_type: str = ".csv",
        presign: bool = True,
        multipart: bool = False,
        batch_size: Optional[int] = None,
    ) -> bool:
        """
        Upload a Dataset or IterableDataset to lakeFS.

        Args:
            file_type: '.csv' or '.parquet'
            presign: Use presigned URL for single-shot upload (staging_api).
                     Ignored when multipart=True.
            multipart: Use multipart upload (experimental_api).
                       Keeps memory bounded to batch_size bytes at a time.
            batch_size: Part size in bytes. Required when multipart=True.
                        Must be >= 5MB (MIN_PART_SIZE_BYTES) except for the last part.
        """
        if file_type not in SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file_type '{file_type}'. Supported: {SUPPORTED_FILE_TYPES}")

        if multipart and batch_size is None:
            raise ValueError("batch_size is required when multipart=True.")

        if not multipart and batch_size is not None:
            raise ValueError("batch_size has no effect when multipart=False.")

        if multipart and batch_size < MIN_PART_SIZE_BYTES:
            raise ValueError(
                f"batch_size must be >= {MIN_PART_SIZE_BYTES} bytes (5MB). Got {batch_size}."
            )

        if multipart:
            return self._multipart_upload(
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
        if file_type == ".csv":
            dataset.to_csv(buffer)
        elif file_type == ".parquet":
            dataset.to_parquet(buffer)

        size_bytes = buffer.getbuffer().nbytes
        buffer.seek(0)
        content_type = self._content_type_for_file_type(file_type)

        if presign:
            return self._presign_obj_upload(repo_name, branch, path, buffer, content_type, size_bytes)
        else:
            return self._obj_upload(repo_name, branch, path, buffer)


    def _multipart_upload(
        self,
        repo_name: str,
        branch: str,
        path: str,
        dataset: Union[Dataset, IterableDataset],
        file_type: str,
        part_size: int,
    ) -> bool:
        """
        Upload using lakeFS experimental multipart API.
        Memory usage is bounded to ~part_size bytes at a time.
        Automatically aborts on failure.
        """
        multipart = self._client.sdk_client.experimental_api.create_presign_multipart_upload(
            repository=repo_name,
            branch=branch,
            path=path,
        )
        upload_id = multipart.upload_id
        etags: list[str] = []

        try:
            if file_type == ".csv":
                etags = self._multipart_csv(repo_name, branch, path, upload_id, dataset, part_size)
            elif file_type == ".parquet":
                etags = self._multipart_parquet(repo_name, branch, path, upload_id, dataset, part_size)

            self._client.sdk_client.experimental_api.complete_presign_multipart_upload(
                repository=repo_name,
                branch=branch,
                upload_id=upload_id,
                path=path,
                body=CompletePresignMultipartUpload(
                    physical_address=multipart.physical_address,
                    etags=etags,
                ),
            )
            return True

        except Exception as e:
            self._client.sdk_client.experimental_api.abort_presign_multipart_upload(
                repository=repo_name,
                branch=branch,
                upload_id=upload_id,
                path=path,
            )
            raise RuntimeError(f"Multipart upload failed and was aborted: {e}") from e

    def _multipart_csv(
        self,
        repo_name: str,
        branch: str,
        path: str,
        upload_id: str,
        dataset: Union[Dataset, IterableDataset],
        part_size: int,
    ) -> list[str]:
        """Stream CSV rows into parts. Header is written once at the start of the first part."""
        etags: list[str] = []
        part_number = 1
        part_buffer = io.BytesIO()
        header_written = False

        for row in dataset:
            if not header_written:
                header_line = ",".join(str(k) for k in row.keys()) + "\n"
                part_buffer.write(header_line.encode())
                header_written = True

            line = ",".join(str(v) for v in row.values()) + "\n"
            part_buffer.write(line.encode())

            if part_buffer.tell() >= part_size:
                etag = self._upload_part(repo_name, branch, path, upload_id, part_number, part_buffer)
                etags.append(etag)
                part_number += 1
                part_buffer = io.BytesIO()

        if part_buffer.tell() > 0:
            etag = self._upload_part(repo_name, branch, path, upload_id, part_number, part_buffer)
            etags.append(etag)

        return etags

    def _multipart_parquet(
        self,
        repo_name: str,
        branch: str,
        path: str,
        upload_id: str,
        dataset: Union[Dataset, IterableDataset],
        part_size: int,
    ) -> list[str]:
        """
        Stream parquet parts using PyArrow.
        Rows are accumulated; once serialized size >= part_size the part is uploaded.
        Schema is inferred from the first batch and kept consistent across all parts.
        """
        etags: list[str] = []
        part_number = 1
        batch_rows: list[dict] = []
        schema: pa.Schema | None = None

        for row in dataset:
            batch_rows.append(row)

            # Probe size every 1000 rows to avoid serializing on every row
            if len(batch_rows) % 1000 == 0:
                table = pa.Table.from_pylist(batch_rows)
                if schema is None:
                    schema = table.schema
                else:
                    table = table.cast(schema)

                probe = io.BytesIO()
                pq.write_table(table, probe)

                if probe.tell() >= part_size:
                    etag = self._upload_part(repo_name, branch, path, upload_id, part_number, probe)
                    etags.append(etag)
                    part_number += 1
                    batch_rows = []

        # Flush remaining rows as the final part
        if batch_rows:
            table = pa.Table.from_pylist(batch_rows)
            if schema is not None:
                table = table.cast(schema)
            buf = io.BytesIO()
            pq.write_table(table, buf)
            etag = self._upload_part(repo_name, branch, path, upload_id, part_number, buf)
            etags.append(etag)

        return etags

    def _upload_part(
        self,
        repo_name: str,
        branch: str,
        path: str,
        upload_id: str,
        part_number: int,
        part_buffer: io.BytesIO,
    ) -> str:
        """Request a presigned URL for the part, upload it, and return its ETag."""
        part_buffer.seek(0)

        upload_to = self._client.sdk_client.experimental_api.upload_part(
            repository=repo_name,
            branch=branch,
            upload_id=upload_id,
            path=path,
            part_number=part_number,
            body=UploadPartFrom(),
        )

        response = requests.put(upload_to.presigned_url, data=part_buffer)
        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"Failed to upload part {part_number}. "
                f"Status: {response.status_code}. Response: {response.text}"
            )

        return self._extract_etag_from_response(response.headers)


    def _presign_obj_upload(
        self,
        repo_name: str,
        branch: str,
        path: str,
        buffer: BytesIO,
        content_type: str,
        size_bytes: int,
    ) -> bool:
        staging_location = self._client.sdk_client.staging_api.get_physical_address(
            repository=repo_name, branch=branch, path=path, presign=True
        )
        physical_address = staging_location.physical_address

        response = requests.put(physical_address, data=buffer)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to upload to presigned URL: {physical_address}. "
                f"Status: {response.status_code}. Response: {response.text}"
            )

        etag = self._extract_etag_from_response(response.headers)
        staging_metadata = StagingMetadata(
            staging=staging_location,
            size_bytes=size_bytes,
            checksum=etag,
            content_type=content_type,
            mtime=None,
        )
        state = self._client.sdk_client.staging_api.link_physical_address(
            repository=repo_name,
            branch=branch,
            path=path,
            staging_metadata=staging_metadata,
        )
        return state is not None

    def _obj_upload(self, repo_name: str, branch: str, path: str, buffer: BytesIO) -> bool:
        state = self._client.sdk_client.objects_api.upload_object(
            repository=repo_name, branch=branch, path=path, content=buffer
        )
        return state is not None
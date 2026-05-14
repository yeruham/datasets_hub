from __future__ import annotations

from csv import DictWriter
from typing import Optional, Union
import csv

from lakefs import Client
from lakefs_sdk import CompletePresignMultipartUpload, UploadPartFrom, UploadPart
from datasets import Dataset, IterableDataset
import io
import requests
import pyarrow as pa
import pyarrow.parquet as pq

from datasets_hub.upload.utils import extract_etag_from_response, content_type_for_file_type


class MultipartUpload:

    def __init__(self, client: Client):
        self._client = client


    def upload(
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
        physical_address = multipart.physical_address
        upload_parts: list[UploadPart] = []

        try:
            if file_type == "csv":
                upload_parts = self.multipart_csv(repo_name, branch, path, upload_id, physical_address, dataset, part_size)
            elif file_type == "parquet":
                upload_parts = self.multipart_parquet(repo_name, branch, path, upload_id, physical_address, dataset, part_size)

            self._client.sdk_client.experimental_api.complete_presign_multipart_upload(
                repository=repo_name,
                branch=branch,
                upload_id=upload_id,
                path=path,
                complete_presign_multipart_upload=CompletePresignMultipartUpload(
                    physical_address=physical_address,
                    parts=upload_parts,
                    content_type=file_type,
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

    def multipart_csv(
        self,
        repo_name: str,
        branch: str,
        path: str,
        upload_id: str,
        physical_address: str,
        dataset: Union[Dataset, IterableDataset],
        part_size: int,
    ) -> list[UploadPart]:
        """Stream CSV rows into parts. Header is written once at the start of the first part."""
        upload_parts = []
        part_number = 1
        fieldnames = None
        text_buf = io.StringIO()
        writer = None

        for row in dataset:
            if fieldnames is None:
                fieldnames = list(row.keys())
                writer = csv.DictWriter(text_buf, fieldnames=fieldnames)
                writer.writeheader()

            writer.writerow(row)

            if text_buf.tell() >= part_size:
                binary_buf = io.BytesIO(text_buf.getvalue().encode("utf-8"))
                etag = self.upload_part(repo_name, branch, path, upload_id, physical_address, part_number, binary_buf)
                upload_parts.append(UploadPart(etag=etag, part_number=part_number))
                part_number += 1
                text_buf = io.StringIO()
                writer = csv.DictWriter(text_buf, fieldnames=fieldnames)

        if text_buf.tell() > 0:
            binary_buf = io.BytesIO(text_buf.getvalue().encode("utf-8"))
            etag = self.upload_part(repo_name, branch, path, upload_id, physical_address, part_number, binary_buf)
            upload_parts.append(UploadPart(etag=etag, part_number=part_number))

        return upload_parts

    def multipart_parquet(
        self,
        repo_name: str,
        branch: str,
        path: str,
        upload_id: str,
        physical_address: str,
        dataset: Union[Dataset, IterableDataset],
        part_size: int,
    ) -> list[UploadPart]:
        """
        Stream parquet parts using PyArrow.
        Rows are accumulated; once serialized size >= part_size the part is uploaded.
        Schema is inferred from the first batch and kept consistent across all parts.
        """
        # upload_parts: list[UploadPart] = []
        # part_number = 1
        # batch_rows: list[dict] = []
        # schema: pa.Schema | None = None
        #
        # for row in dataset:
        #     batch_rows.append(row)
        #
        #     # Probe size every 1000 rows to avoid serializing on every row
        #     if len(batch_rows) % 1000 == 0:
        #         table = pa.Table.from_pylist(batch_rows)
        #         if schema is None:
        #             schema = table.schema
        #         else:
        #             table = table.cast(schema)
        #
        #         probe = io.BytesIO()
        #         pq.write_table(table, probe)
        #
        #         if probe.tell() >= part_size:
        #             etag = self.upload_part(repo_name, branch, path, upload_id, physical_address, part_number, probe)
        #             upload_part = UploadPart(etag=etag, part_number=part_number)
        #             upload_parts.append(upload_part)
        #             part_number += 1
        #             batch_rows = []
        #
        # # Flush remaining rows as the final part
        # if batch_rows:
        #     table = pa.Table.from_pylist(batch_rows)
        #     if schema is not None:
        #         table = table.cast(schema)
        #     buf = io.BytesIO()
        #     pq.write_table(table, buf)
        #     etag = self.upload_part(repo_name, branch, path, upload_id, physical_address, part_number, buf)
        #     upload_part = UploadPart(etag=etag, part_number=part_number)
        #     upload_parts.append(upload_part)
        #
        # return upload_parts
        raise NotImplemented

    def upload_part(
        self,
        repo_name: str,
        branch: str,
        path: str,
        upload_id: str,
        physical_address: str,
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
            upload_part_from=UploadPartFrom(physical_address=physical_address),
        )

        response = requests.put(upload_to.presigned_url, data=part_buffer)
        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"Failed to upload part {part_number}. "
                f"Status: {response.status_code}. Response: {response.text}"
            )

        return extract_etag_from_response(response.headers)
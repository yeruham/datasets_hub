from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional

from lakefs import Client
from lakefs_sdk import StagingMetadata
from datasets import Dataset
import io
import requests
import base64
import binascii
import mimetypes

from models import PresignedUrl


class LakefsUpload:

    def __init__(self, client: Client):
        self._client = client

    def get_presigned_urls(self, repo_name: str, ref: str, prefix: str) -> list[PresignedUrl]:
        state_objects = self._client.sdk_client.objects_api.list_objects(
            repository=repo_name, ref=ref, prefix=prefix, presign=True
        )
        presign_urls = [
            PresignedUrl(
                name=self._get_object_name(state.path),
                physical_address=state.physical_address,
                physical_address_expiry=state.physical_address_expiry,
            )
            for state in state_objects.results
        ]
        return presign_urls

    def _get_object_name(self, path: str) -> str:
        return Path(path).stem

    def upload_dataset(
        self,
        repo_name: str,
        dataset: Dataset,
        branch: str,
        path: str,
        presign: bool = True,
    ) -> bool:
        buffer = io.BytesIO()
        dataset.to_csv(buffer)
        size_bytes = buffer.getbuffer().nbytes
        buffer.seek(0)
        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"

        if presign:
            return self._presign_obj_upload(repo_name, branch, path, buffer, content_type, size_bytes)
        else:
            return self._obj_upload(repo_name, branch, path, buffer)

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
                f"Status: {response.status_code}. Response: {response.json()}"
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

    @staticmethod
    def _extract_etag_from_response(headers) -> str:
        # prefer Content-MD5 if exists
        content_md5 = headers.get("Content-MD5")
        if content_md5 is not None and len(content_md5) > 0:
            try:  # decode base64, return as hex
                decode_md5 = base64.b64decode(content_md5)
                return binascii.hexlify(decode_md5).decode("utf-8")
            except binascii.Error:
                pass

        # fallback to ETag
        etag = headers.get("ETag", "").strip(' "')
        return etag
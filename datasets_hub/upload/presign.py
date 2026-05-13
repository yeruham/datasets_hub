from __future__ import annotations

from io import BytesIO
from pathlib import Path

from lakefs import Client
from lakefs_sdk import StagingMetadata
import requests

from datasets_hub.models import PresignedUrl
from datasets_hub.upload.utils import extract_etag_from_response, content_type_for_file_type


class LFSPresign:

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


    def presign_obj_upload(
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
        presign_url = staging_location.presigned_url

        response = requests.put(presign_url, data=buffer)
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to upload to presigned URL: {presign_url}. "
                f"Status: {response.status_code}. Response: {response.text}"
            )

        etag = extract_etag_from_response(response.headers)
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
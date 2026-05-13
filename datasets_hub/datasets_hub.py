from lakefs import repository, repositories, Client, Commit, Reference
from lakefs.client import _BaseLakeFSObject
from datasets import load_dataset as hf_load_dataset, Split, NamedSplit, Features
from datasets import  Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from typing import Optional, Union, cast, Literal
from collections.abc import Mapping, Sequence
from pathlib import Path
import io
import mimetypes

from dataset_repo import PresignedUrl
from lfs_datasets import LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict
from dataset_repo import DatasetRepo
from lakefs_connection import get_lakefs_client, STORAGE_OPTIONS, STORAGE_NAMESPACE

class LakefsHub(_BaseLakeFSObject):

    def __init__(self, host: str | None = None,
                      username: str | None = None,
                      password: str | None = None,
                      access_token: str | None = None):
        self._storage_namespace = STORAGE_NAMESPACE
        client = get_lakefs_client(host=host, username=username, password=password, access_token=access_token)
        super().__init__(client)

    def list_ds_repos(self, prefix:  str | None = None, after: str | None = None, **kwargs) -> list[str]:
        yield_list_repos = repositories(client=self._client, prefix=prefix, after=after, **kwargs)
        list_repos = [repo.id for repo in yield_list_repos]
        return list_repos

    def create_ds_repo(self, name: str) -> DatasetRepo:
        repo = DatasetRepo(repository_id=name, client=self._client).create(storage_namespace=self._storage_namespace)
        ds_repo = DatasetRepo.from_repo(repo)
        return ds_repo


    def get_ds_repo(self, name: str) -> DatasetRepo:
        repo = repository(repository_id=name, client=self._client)
        ds_repo = DatasetRepo.from_repo(repo)
        return ds_repo


    def load_dataset(
                    self,
                    path: str,
                    name: str,
                    revision: str,
                    data_dir: Optional[str] = None,
                    split: Optional[Union[str, Split, list[str], list[Split]]] = None,
                    features: Optional[Features] = None,
                    keep_in_memory: Optional[bool] = None,
                    token: Optional[Union[bool, str]] = None,
                    streaming: bool = False,
                    num_proc: Optional[int] = None,
                    auth_splits: bool = True,
                    **kwargs
                    ) -> Union[LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict]:

        ds_repo = self.get_ds_repo(name)
        presign_urls: list[PresignedUrl] = ds_repo.get_presigned_urls(ref=revision, prefix=data_dir)

        data_files: str | Sequence[str] | Mapping[str, str | Sequence[str]] | None = None
        if auth_splits:
            data_files = {
                obj.name: obj.physical_address
                for obj in presign_urls
            }
        else:
            data_files = [obj.physical_address for obj in presign_urls]

        ds = hf_load_dataset(path=path,
                             data_files=data_files,
                             split=split,
                             streaming=cast(Literal[False], streaming),
                             features=features,
                             keep_in_memory=keep_in_memory,
                             num_proc=num_proc,
        )

        lfs_ds = _convert_ds_to_lfs(ds)
        return lfs_ds


    def push_dataset(self,
                       ds_name: str,
                       dataset: Dataset,
                       branch: str,
                       path: str,
                       presign: bool=True
                       ) -> bool:

        buffer = io.BytesIO()
        dataset.to_csv(buffer)
        size_bytes = buffer.getbuffer().nbytes
        buffer.seek(0)
        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"

        ds_repo = self.get_ds_repo(ds_name)

        uploaded = False
        linked = False
        if presign:
             uploaded = ds_repo.presign_obj_upload(branch, path, buffer, content_type, size_bytes)
        else:
            linked = ds_repo.obj_upload(branch, path, buffer, content_type, size_bytes)

        return uploaded and linked


    def push_and_commit_dataset(
            self,
            dataset: Dataset | DatasetDict | LFSDataset | LFSDatasetDict,
            file_type: str,
            ds_name: str,
            commit_message: str,
            commit_metadata: Optional[str] = None,
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            token: Optional[str] = None,
            branch: Optional[str] = None,
            presign: Optional[bool] = True,
            **kwargs
    ) -> Reference | None:

        uploaded_and_linked = False

        if isinstance(dataset, Dataset) or isinstance(dataset, LFSDataset):
            path_parts = [data_dir, split or str(dataset.split), file_type]
            full_path = Path(*(p for p in path_parts if p))
            uploaded_and_linked = self.push_dataset(dataset=dataset,
                                                    ds_name=ds_name,
                                                    branch=branch,
                                                    path=str(full_path),
                                                    presign=presign
                                                    )

        elif isinstance(dataset, DatasetDict) or isinstance(dataset, LFSDatasetDict):
            splits = dataset.keys()
            for split in splits:
                dataset = dataset[split]
                path_parts = [data_dir, split or str(dataset.split), file_type]
                full_path = Path(*(p for p in path_parts if p))
                uploaded_and_linked = uploaded_and_linked and self.push_dataset(dataset=dataset,
                                                        ds_name=ds_name,
                                                        branch=branch,
                                                        path=str(full_path),
                                                        presign=presign
                                                        )

        if uploaded_and_linked:
            ds_repo = self.get_ds_repo(ds_name)
            ref = ds_repo.branch(branch).commit(commit_message, commit_metadata)
            return ref


    def push_iterable_dataset(
            self,
            dataset: IterableDataset | IterableDatasetDict | LFSIterableDataset | LFSIterableDatasetDict,
            file_type: str,
            repo_id: str,
            commit_message: str,
            commit_metadata: Optional[str] = None,
            split: Optional[str] = None,
            data_dir: Optional[str] = None,
            token: Optional[str] = None,
            branch: Optional[str] = None,
            presign: Optional[bool] = True,
            ** kwargs

    ) -> Reference:
        pass



def _convert_ds_to_lfs(ds: Dataset | DatasetDict | IterableDataset | IterableDatasetDict) -> Union[LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict]:
    _converters = {
        Dataset: LFSDataset.from_dataset,
        DatasetDict: LFSDatasetDict.from_dataset_dict,
        IterableDataset: LFSIterableDataset.from_iterable_dataset,
        IterableDatasetDict: LFSIterableDatasetDict.from_iterable_dataset_dict,
    }

    converter = _converters.get(type(ds))
    if converter is None:
        raise TypeError(f"Unsupported dataset type: {type(ds)}")

    return converter(ds)
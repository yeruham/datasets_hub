from lakefs import repository, repositories, Client
from lakefs.client import _BaseLakeFSObject
from datasets import load_dataset as hf_load_dataset, Split
from datasets import  Dataset, DatasetDict, IterableDataset, IterableDatasetDict
from typing import Optional, Union

from .lfs_datasets import LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict
from .dataset_repo import DatasetRepo
from .lakefs_connection import get_lakefs_client, STORAGE_OPTIONS, STORAGE_NAMESPACE

class DatasetsHub(_BaseLakeFSObject):

    def __init__(self, client: Optional[Client] = None):
        self._storage_namespace = STORAGE_NAMESPACE
        if not isinstance(client, Client):
            client = get_lakefs_client()
        super().__init__(client)

    def list_ds_repos(self, prefix:  str | None = None, after: str | None = None, **kwargs) -> list[str]:
        yield_list_repos = repositories(client=self._client, prefix=prefix, after=after, **kwargs)
        list_repos = [repo.id for repo in yield_list_repos]
        return list_repos

    def create_ds_repo(self, name: str) -> DatasetRepo:
        repo = DatasetRepo(repository_id=name, client=self._client).create(storage_namespace=self._storage_namespace)
        return repo


    def get_ds_repo(self, name: str) -> DatasetRepo:
        repo = repository(repository_id=name, client=self._client)
        ds_repo = DatasetRepo.from_repo(repo)
        return ds_repo


    def load_dataset(
                    self,
                    ds_type: str,
                    name: str,
                    ref: str,
                        # path: str,
                        # name: Optional[str] = None,
                        # data_dir: Optional[str] = None,
                        # data_files: Optional[Union[str, Sequence[str], Mapping[str, Union[str, Sequence[str]]]]] = None,
                        split: Optional[Union[str, Split, list[str], list[Split]]] = None,
                        # cache_dir: Optional[str] = None,
                        # features: Optional[Features] = None,
                        # download_config: Optional[DownloadConfig] = None,
                        # download_mode: Optional[Union[DownloadMode, str]] = None,
                        # verification_mode: Optional[Union[VerificationMode, str]] = None,
                        # keep_in_memory: Optional[bool] = None,
                        # save_infos: bool = False,
                        # revision: Optional[Union[str, Version]] = None,
                        # token: Optional[Union[bool, str]] = None,
                        streaming: bool = False,
                        # num_proc: Optional[int] = None,
                        # storage_options: Optional[dict] = None,
                        # **config_kwargs,
                         ) -> Union[LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict]:

        ds_repo = self.get_ds_repo(name)
        objects = ds_repo.branch(branch_id=ref).objects()
        print(objects)
        presign_urls = []
        for obj in objects:
            presign_url = ds_repo.get_presigned_url(ref=ref, path=obj.path).physical_address
            presign_urls.append(presign_url)
        print(presign_urls)
        ds = hf_load_dataset(
                             path=ds_type,
                             data_files=presign_urls,
                             split=split,
                             streaming=streaming,
                             # storage_options=STORAGE_OPTIONS
                             )
        lfs_ds = self._convert_ds_to_lfs(ds)
        return lfs_ds


    def _convert_ds_to_lfs(self, ds: Dataset | DatasetDict | IterableDataset | IterableDatasetDict) -> Union[LFSDataset, LFSDatasetDict, LFSIterableDataset, LFSIterableDatasetDict]:
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
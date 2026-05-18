from datasets import Dataset
from datasets_hub import LakefsHub, DatasetRepo, DatasetMetadata, CommitMetadata

hub = LakefsHub()
ds_repos = hub.list_ds_repos()
print(ds_repos)

ds_metadata = DatasetMetadata.model_validate({"by": "yeruham"}) # TODO: add metadata
ds_repo = hub.get_ds_repo(name="repo-3").create(metadata=ds_metadata)
print(ds_repo)
print(ds_repo.metadata)

branches = ds_repo.branches()
for branch in branches:
    print(branch)

data_dict = {
    "id": [1, 2, 3, 4],
    "text":  ["dog", "lion", "cat", "tiger"],
    "label": [0, 1, 1, 0]
}
ds = Dataset.from_dict(mapping=data_dict)
print(ds)

uploaded = ds_repo.upload_dataset(dataset=ds)
load_ds = ds_repo.get_dataset()
print(f"load _ds type: {type(load_ds)}")
print(load_ds)

branch = ds_repo.branch()
uncommitted = branch.uncommitted()
for uncommit in uncommitted:
    print(uncommit)

commit_metadata = CommitMetadata() # TODO: add metadata
commit_message = "commit after dataset uploaded"
commit = branch.commit(message=commit_message, metadata=commit_metadata)
print(commit)
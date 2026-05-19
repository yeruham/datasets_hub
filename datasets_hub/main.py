from datasets import Dataset
from datasets_hub import LakefsHub, DatasetRepo, DatasetMetadata, CommitMetadata

# init lakefs hub connection
hub = LakefsHub()
# get list of all datasets-repos from the hub
ds_repos = hub.list_ds_repos()
print("get list of all datasets-repos from the hub")
print(ds_repos)

# create new dataset-repo + metadata through the LakefsHub
ds_metadata = DatasetMetadata.model_validate({"created_by": "some user"}) # TODO: add metadata schema
ds_repo = hub.get_ds_repo(name="my-repo").create(metadata=ds_metadata)
print(f"create new DatasetRepo: {ds_repo.id}")
print(ds_repo)
print(ds_repo.metadata)

# get the branches of the DatasetRepo
branches = ds_repo.branches()
for branch in branches:
    print(branch)

# create Dataset example for upload
data_dict = {
    "id": [1, 2, 3, 4],
    "text":  ["dog", "lion", "cat", "tiger"],
    "label": [0, 1, 1, 0]
}
ds = Dataset.from_dict(mapping=data_dict)
print("create Dataset example for upload: ")
print(ds)

# upload the Dataset to the DatasetRepo
uploaded = ds_repo.upload_dataset(dataset=ds)
print("upload the Dataset to the DatasetRepo success")

# after the upload - get the current DatasetBranch from DatasetRepo and print the uncommitted changes
branch = ds_repo.branch()
uncommitted = branch.uncommitted()
for uncommit in uncommitted:
    print(uncommit)

# load the Dataset back from the DatasetRepo
load_ds = ds_repo.get_dataset()
print(f"load _ds type: {type(load_ds)}")
print(load_ds)

# commit the changes + metadata by DatasetBranch
commit_metadata = CommitMetadata() # TODO: add metadata schema
commit_message = "commit after dataset uploaded"
commit = branch.commit(message=commit_message, metadata=commit_metadata)
print(commit)
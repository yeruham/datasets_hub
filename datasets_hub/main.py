from datasets_hub.lakefs_hub import LakefsHub


hub = LakefsHub()
ds_names = hub.list_ds_repos()
print(ds_names)
ds = hub.load_dataset("csv", "test", "c7a38422a406b46804557471edd4477cc37843d8e6d09ae4f1aafa030ae947b3")
print(type(ds))
print(ds)
# train = ds["train"]
for r in ds:
    print(r)

commit = ds.push_to_hub(repo_id="test", data_dir="data", revision="dev-branch", commit_message=" sdk commit!!!",  file_type="parquet")
print(commit)
from datasets import load_dataset
# ds = load_dataset('nyu-mll/glue', 'sst2', streaming=True)
# print(type(ds))
# print(ds)
# train = ds["train"]
# num = 0
# for i in train:
#     num += 1
#     print(i)
#     if num > 10:
#         break
#
# from datasets import load_dataset
# ds = load_dataset('cornell-movie-review-data/rotten_tomatoes', split='train', streaming=True)
# print(type(ds))
# print(ds)
# # train = ds["train"]
# num = 0
# for i in ds:
#     num += 1
#     print(i)
#     if num > 10:
#         break
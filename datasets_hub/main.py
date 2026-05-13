from datasets_hub import DatasetsHub
from lakefs_hub import get_lakefs_client

get_lakefs_client().sdk_client.experimental_api.create_presign_multipart_upload()


hub = DatasetsHub()
ds_names = hub.list_ds_repos()
print(ds_names)
ds = hub.load_dataset("csv", "test", "c7a38422a406b46804557471edd4477cc37843d8e6d09ae4f1aafa030ae947b3", auth_splits=False)
print(type(ds))
print(ds)
# train = ds["train"]
for r in ds:
    print(r)

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
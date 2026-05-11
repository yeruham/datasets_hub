from .datasets_hub import DatasetsHub


hub = DatasetsHub()
ds_names = hub.list_ds_repos()
print(ds_names)
ds = hub.load_dataset("csv", "test", "70bcd0b031e642ccb4170cc92b0768e4fb6245fb7b8ebc7c21fff7fd1a5b41a2", streaming=True, split="train")
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
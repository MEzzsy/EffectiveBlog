import os

char_sum = 0
blog_dir = "/Users/mezzsy/Projects/EffectiveBlog"
ignore_file = blog_dir + "/ignoredFile"


def traverse_folder(dir_path):
    global char_sum
    for file in os.listdir(dir_path):
        item_path = os.path.join(dir_path, file)
        if os.path.isdir(item_path):
            traverse_folder(item_path)
        elif os.path.isfile(item_path):
            if item_path.rfind(".md") == -1:
                continue
            with open(item_path) as file_object:
                lines = file_object.readlines()
                for line in lines:
                    char_sum = char_sum + len(line)


ignore_set = set()
with open(ignore_file) as file_object:
    lines = file_object.readlines()
    for line in lines:
        if len(line) > 0:
            ignore_set.add(line)

for file in os.listdir(blog_dir):
    item_path = os.path.join(blog_dir, file)
    if file in ignore_set:
        continue
    if os.path.isdir(item_path):
        traverse_folder(item_path)

print(f"总字数：{char_sum}")

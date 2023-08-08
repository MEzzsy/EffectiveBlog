import os
import re

char_sum = 0
code_sum = 0
blog_dir = "/Users/mezzsy/Projects/EffectiveBlog"
ignore_file = blog_dir + "/ignoredFile"


def traverse_folder(dir_path):
    global char_sum
    global code_sum
    for file in os.listdir(dir_path):
        item_path = os.path.join(dir_path, file)
        if os.path.isdir(item_path):
            traverse_folder(item_path)
        elif os.path.isfile(item_path):
            if item_path.rfind(".md") == -1:
                continue
            with open(item_path) as file_object:
                lines = file_object.readlines()
                find_code = False
                for line in lines:
                    if line.startswith("```"):
                        find_code = not find_code

                    if find_code:
                        code_sum = code_sum + 1
                    else:
                        char_sum = char_sum + get_char_count(line)


def get_char_count(line):
    # 统计汉字数量
    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', line))

    # 统计单词数量
    word_list = re.findall(r'\b\w+\b', line)
    word_count = len(word_list)
    return chinese_count + word_count


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
print(f"代码总行数：{code_sum}")

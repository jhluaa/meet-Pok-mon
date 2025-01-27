import json
from collections import defaultdict

def get_dict_hash(data):
    """ 通过json序列化并计算字典的哈希值 """
    return hash(json.dumps(data, sort_keys=True))

def remove_duplicates(input_file, output_file):
    # 读取输入的JSON文件
    with open(input_file, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    seen_hashes = set()  # 存储已处理的字典哈希值
    unique_data = []  # 存储去重后的数据
    duplicate_counts = defaultdict(int)  # 用于存储重复项及其出现的次数

    # 处理数据
    for item in entities:
        item_hash = get_dict_hash(item)  # 获取字典的哈希值
        if item_hash not in seen_hashes:
            unique_data.append(item)
            seen_hashes.add(item_hash)
        else:
            duplicate_counts[json.dumps(item, ensure_ascii=False)] += 1  # 记录重复项

    # 将去重后的结果写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, indent=2, ensure_ascii=False)

    # 打印重复项的统计信息
    if duplicate_counts:
        print("重复项统计：")
        for item, count in duplicate_counts.items():
            print(f"重复项: {item} 重复次数: {count + 1}")  # 包括第一次出现的计数
    else:
        print("没有重复项")

# 调用函数处理数据
input_file = 'entities1.json'
output_file = 'entities1.json'
remove_duplicates(input_file, output_file)

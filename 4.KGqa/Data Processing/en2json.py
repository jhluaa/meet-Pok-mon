import json
import os

# 提取實體
def process_entity_file(input_file, output_file):
    entities = []

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 去除每行的前后空格，并过滤空行
    lines = [line.strip() for line in lines if line.strip()]

    for line in lines:
        # 根据你的要求格式化实体数据
        entity = {
            "label": "Affair",
            "name": line
        }
        entities.append(entity)

    # 将结果输出到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=4)

# txt
def update_entities_from_txt(existing_file, txt_file, output_file, label):
    # 读取已有的 JSON 文件
    with open(existing_file, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)

    # 读取新的 txt 文件并处理
    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 去除每行的前后空格，并过滤空行
    lines = [line.strip() for line in lines if line.strip()]

    # 遍历新实体，添加到现有数据中
    for line in lines:
        new_entity = {
            "label": label,  # 设置新的 label
            "name": line
        }
        existing_data.append(new_entity)

    # 将更新后的数据保存到新的 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    print(f"实体已成功添加并保存到 {output_file}")



# json
def update_entities_from_json_file(existing_file, input_json_file, output_file, label):
    # 检查原始 JSON 文件是否存在
    if not os.path.exists(existing_file):
        print(f"错误：文件 {existing_file} 不存在。")
        return

    # 读取已有的 JSON 文件
    with open(existing_file, 'r', encoding='utf-8') as f:
        try:
            existing_data = json.load(f)
        except json.JSONDecodeError:
            print(f"错误：文件 {existing_file} 格式不正确，无法解析。")
            return

    # 检查输入的 JSON 文件是否存在
    if not os.path.exists(input_json_file):
        print(f"错误：输入文件 {input_json_file} 不存在。")
        return

    # 读取输入的 JSON 文件
    with open(input_json_file, 'r', encoding='utf-8') as f:
        try:
            input_data = json.load(f)
        except json.JSONDecodeError:
            print(f"错误：文件 {input_json_file} 格式不正确，无法解析。")
            return

    # 遍历输入的 JSON 数据并添加到现有数据中
    for entity in input_data:
        new_entity = {
            "label": label,  # 设置新的 label
            "name": entity
        }
        existing_data.append(new_entity)

    # 如果 output_file 是原始文件，则避免覆盖，提示用户
    if existing_file == output_file:
        print("警告：你正在覆盖原始文件。")

    # 将更新后的数据保存到新的 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

    print(f"实体已成功添加并保存到 {output_file}")

#
# 输入数据文件路径
existing_file = "entities.json"  # 原始的 JSON 文件路径
input_json_file = "a.json"  # 新的实体 JSON 文件路径（例如：Area.json）
output_file = "entities.json"  # 输出的 JSON 文件路径（可以修改为新的文件名）
label = "Affair"
#
# # 调用函数处理更新
# update_entities_from_json_file(existing_file, input_json_file, output_file, label)
#
# #
# # 调用函数处理文件
# input_file = "Affair.txt"  # 输入的txt文件路径
# output_file = "entities.json"  # 输出的json文件路径
# process_entity_file(input_file, output_file)

# # 输入数据文件路径
# existing_file = "entities.json"  # 原始的 JSON 文件路径
# txt_file = "ban_zhuti.txt"  # 新的实体 txt 文件路径
# output_file = "entities.json"  # 输出的 JSON 文件路径
# label = "Affair"  # 新实体的 label（根据实际需要修改）
#
# # 调用函数处理更新
# update_entities_from_txt(existing_file, txt_file, output_file, label)


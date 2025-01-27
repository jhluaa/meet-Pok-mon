import json
import re

def remove_invalid_characters(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    # 删除所有的控制字符（除了换行符、回车符、制表符之外的字符）
    cleaned_content = re.sub(r'[\x00-\x1F\x7F]', '', content)
    return cleaned_content

def extract_entities_and_relationships_from_file(input_file):
    # 使用 utf-8-sig 编码以处理 BOM 问题
    cleaned_data = remove_invalid_characters(input_file)
    json_data = json.loads(cleaned_data)

    output_data = []

    # 遍历每个元素
    for item in json_data:
        start_labels = item['p']['start']['labels']
        end_labels = item['p']['end']['labels']

        # 提取 start 和 end 的类型
        start_entity_type = start_labels[0] if start_labels else "Unknown"
        end_entity_type = end_labels[0] if end_labels else "Unknown"

        # 提取 relationship 中的 type
        rel_type = item['p']['segments'][0]['relationship']['type'] if item['p']['segments'] else "Unknown"

        # 根据 start_entity_type 和 end_entity_type 确定 rel_name
        if start_entity_type == "Business" and end_entity_type == "File":
            rel_name = "业务的支撑依据是"
        else:
            if start_entity_type == "Policy"and end_entity_type == "Business":
                rel_name = "具体实施的表现在"
            else:
                rel_name = rel_type

        # 提取实体的名称
        start_entity_name = item['p']['start']['properties']['name']
        end_entity_name = item['p']['end']['properties']['name']

        # 将该条关系存储到 output_data 中
        output_data.append({
            "start_entity_type": start_entity_type,
            "end_entity_type": end_entity_type,
            "rel_type": rel_type,
            "rel_name": rel_name,
            "rels": [
                {
                    "start_entity_name": start_entity_name,
                    "end_entity_name": end_entity_name
                }
            ]
        })

    return output_data

def save_to_json(output_data, output_file):
    # 检查文件是否存在，如果存在，读取已有数据
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        # 如果文件不存在，初始化一个空列表
        existing_data = []

    # 将新的数据追加到现有数据中
    existing_data.extend(output_data)

    # 将更新后的数据保存回文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    print(f"数据已成功追加到 {output_file}")

# 输入 JSON 数据文件路径
input_file = '../datasets_/HAS_FILE.json'
output_file = 'relations.json'

# 调用函数处理
output_json_data = extract_entities_and_relationships_from_file(input_file)

# 保存结果到 relations.json
save_to_json(output_json_data, output_file)

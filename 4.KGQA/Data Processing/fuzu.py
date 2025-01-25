import json
import re


def remove_invalid_characters(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    # 删除所有的控制字符（除了换行符、回车符、制表符之外的字符）
    cleaned_content = re.sub(r'[\x00-\x1F\x7F]', '', content)
    return cleaned_content


def extract_entity_relationships(input_file):
    # 使用 utf-8-sig 编码处理 BOM 问题，并清除无效字符
    cleaned_data = remove_invalid_characters(input_file)

    # 尝试加载 cleaned_data 为 JSON
    json_data = json.loads(cleaned_data)

    # 用于存储所有的关系对
    relationships = []

    # 遍历每个元素，提取 start 和 end 的 labels 类型及其关系
    for item in json_data:
        start_labels = item['p']['start']['labels']
        end_labels = item['p']['end']['labels']

        # 提取 start 和 end 的类型（假设只有一个 label）
        start_entity_type = start_labels[0] if start_labels else "Unknown"
        end_entity_type = end_labels[0] if end_labels else "Unknown"

        # 提取 relationship 中的 type
        rel_type = item['p']['segments'][0]['relationship']['type'] if item['p']['segments'] else "Unknown"

        # 创建关系对并添加到列表中
        relationships.append({
            "start_entity_type": start_entity_type,
            "end_entity_type": end_entity_type,
            "rel_type": rel_type
        })

    return relationships


def save_relationships_to_file(relationships, output_file):
    # 将关系对存储到指定的 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(relationships, f, ensure_ascii=False, indent=4)
    print(f"提取的关系对已保存到 {output_file}")


# 输入 JSON 数据文件路径
input_file = '../datasets_/HAS_DEPT.json'  # 输入的 JSON 文件路径
output_file = ('relationships.json')  # 输出文件路径

# 提取关系对
relationships = extract_entity_relationships(input_file)

# 保存关系对到文件
save_relationships_to_file(relationships, output_file)

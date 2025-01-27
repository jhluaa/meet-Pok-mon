import json

def remove_duplicates(input_file, output_file):
    # 读取输入的JSON文件
    with open(input_file, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    # 创建一个数组来存储最终去重后的数据
    result = []

    # 用集合来记录已经出现的 label 和 name 的组合
    seen = set()

    for item in entities:
        # 只处理 label 为 "Affair" 的条目
        if item.get('label') == "Affair":
            name = item.get('name')
            # 处理有 properties 的数据
            if isinstance(name, dict) and 'name' in name:
                name_value = name['name']
                # 判断 name 和 properties 是否重复
                if (item['label'], name_value) not in seen:
                    seen.add((item['label'], name_value))
                    result.append(item)
            elif isinstance(name, str):
                name_value = name
                # 判断 name 和 properties 是否重复
                if (item['label'], name_value) not in seen:
                    seen.add((item['label'], name_value))
                    result.append(item)

    # 将去重后的结果写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("去重后的数据已经保存到:", output_file)

# 调用函数处理数据
input_file = 'entities.json'
output_file = 'entities1.json'
remove_duplicates(input_file, output_file)

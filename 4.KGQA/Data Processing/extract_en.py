import json

# 处理单个文件的转换逻辑
def process_json(data):
    if isinstance(data, list):
        # 假设数据是一个列表，处理每个列表元素
        results = []
        for item in data:
            results.append(process_json(item))  # 递归处理每个元素
        return results

    # 如果数据是字典，进行处理
    result = {
        "label": "Affair",
        "name":data.get("事项名称", ""),
        "properties":{
            "name": data.get("事项名称", ""),
            "type": data.get("事项类型", ""),
            "info": data.get("行政相对人权利和义务", ""),
            "material": data.get("办理材料", []),
            "procedure": data.get("办理流程", []),
            "legal_limit": data.get("法定办结时限", ""),
            "service_object": data.get("承诺办结时限", ""),
            "is_free": data.get("收费情况", ""),
            "level": data.get("行使层级", ""),
            "code": data.get("业务办理项编码", "")
        }
    }
    return result

# 处理单个 JSON 文件
def process_single_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            processed_data = process_json(data)
            # 将处理后的数据写入输出文件
            with open(output_file, "w", encoding="utf-8") as out_file:
                json.dump(processed_data, out_file, ensure_ascii=False, indent=4)
            print(f"Processing complete. Output saved to {output_file}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {input_file}")

# 调用处理函数
if __name__ == "__main__":
    # 设置输入文件路径和输出文件路径
    input_file = "data.json"  # 原始 JSON 文件
    output_file = "a.json"  # 输出的处理后 JSON 文件

    # 执行处理
    process_single_file(input_file, output_file)

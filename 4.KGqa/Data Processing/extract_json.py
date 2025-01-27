import json

def append_to_json(input_file, output_file):
    # 读取 entities.json 文件
    try:
        with open(output_file, "r", encoding="utf-8") as out_file:
            try:
                entities_data = json.load(out_file)
            except json.JSONDecodeError:
                # 如果文件为空或内容不符合 JSON 格式，则初始化为空列表
                entities_data = []
    except FileNotFoundError:
        # 如果 entities.json 文件不存在，初始化为空列表
        entities_data = []

    # 读取 a.json 文件
    try:
        with open(input_file, "r", encoding="utf-8") as in_file:
            a_data = json.load(in_file)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {input_file}")
        return

    # 将 a.json 的内容追加到 entities_data 中
    entities_data.extend(a_data)

    # 将合并后的数据写回 entities.json
    with open(output_file, "w", encoding="utf-8") as out_file:
        json.dump(entities_data, out_file, ensure_ascii=False, indent=4)

    print(f"Data from {input_file} successfully appended to {output_file}.")

# 调用函数，设置输入和输出文件路径
if __name__ == "__main__":
    input_file = "a.json"  # 需要追加的数据
    output_file = "entities.json"  # 目标文件

    # 执行追加操作
    append_to_json(input_file, output_file)

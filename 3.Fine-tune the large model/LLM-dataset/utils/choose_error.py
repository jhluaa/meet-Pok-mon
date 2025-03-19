import json

# 输入和输出文件
input_file = "../error_log.json"
output_file = "../filtered_logs.json"

# 存储提取的数据
extracted_data = []

try:
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())  # 解析每行 JSON
                if "original_data" in entry:
                    extracted_data.append(entry["original_data"])
            except json.JSONDecodeError:
                print(f"跳过无法解析的行: {line.strip()}")

    # 将提取的数据写入新的 JSON 文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)

    print(f"提取完成！已保存到 {output_file}")

except Exception as e:
    print(f"发生错误: {e}")

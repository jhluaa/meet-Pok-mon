import json

input_file = "pokemon_data_10.json"
output_file = "pokemon_data_10_fixed.json"

json_list = []

try:
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().strip()

        # 检查是否是 NDJSON 格式（每行一个 `{}`）
        if content.startswith("{"):
            content = "[" + content.replace("}\n{", "},\n{") + "]"

        # 去掉尾部逗号
        content = content.rstrip(",")

        # 解析 JSON
        json_list = json.loads(content)

    # 重新写入标准 JSON 格式
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_list, f, ensure_ascii=False, indent=4)

    print(f"✅ 修复完成，JSON 数据已保存到 {output_file}")

except json.JSONDecodeError as e:
    print(f"❌ JSON 解析失败: {e}")

import json

# 读取 JSON 文件
with open("final_merged_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 处理数据，去除 comment 字段中的 \n
for item in data:
    if "comment" in item and isinstance(item["output"], str):
        item["comment"] = item["output"].replace("\n", " ")  # 替换换行符为空格

# 写回 JSON 文件
with open("final_merged_data_cleaned.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)  # 保持格式化输出

print("处理完成，已去除换行符并保存到 final_merged_data_cleaned.json")

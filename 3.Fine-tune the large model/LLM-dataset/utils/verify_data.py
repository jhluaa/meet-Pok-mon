import json

# 读取 JSON 数据
with open("pokemon_data_10_fixed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 遍历数据，检查格式
for i, entry in enumerate(data):
    if not isinstance(entry, dict):
        print(f"⚠️ 第 {i+1} 条数据格式错误：不是字典类型")
    if "instruction" not in entry or not isinstance(entry["instruction"], str):
        print(f"⚠️ 第 {i+1} 条数据缺少 'instruction' 或格式错误")
        entry["instruction"] = ""  # 填充默认值
    if "input" not in entry or not isinstance(entry["input"], str):
        print(f"⚠️ 第 {i+1} 条数据缺少 'input' 或格式错误")
        entry["input"] = ""  # 填充默认值
    if "output" not in entry or not isinstance(entry["output"], str):
        print(f"⚠️ 第 {i+1} 条数据缺少 'output' 或格式错误")
        entry["output"] = ""  # 填充
          # 默认值
    if "history" not in entry or not isinstance(entry["history"], list):
        print(f"⚠️ 第 {i+1} 条数据缺少 'history' 或格式错误")
        entry["history"] = []  # 填充默认值

#  将修正后的数据写回文件
with open("../clean_dataset/pokemon_data_10.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("✅ JSON 数据检查并填充缺失项完成")

import os
import json

# 当前目录路径
folder_path = "./entity_data"

# 收集所有实体
entity_set = set()
for filename in os.listdir(folder_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                entity = line.strip()
                if entity:
                    entity_set.add(entity)

# 生成实体到ID的映射
entity_list = sorted(entity_set)
entity2id = {entity: idx for idx, entity in enumerate(entity_list)}

# 保存为 JSON 文件
with open("entity2id1.json", "w", encoding="utf-8") as f:
    json.dump(entity2id, f, ensure_ascii=False, indent=2)

print(f"共提取实体 {len(entity2id)} 个，已保存为 entity2id.json")

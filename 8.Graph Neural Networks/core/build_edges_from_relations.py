import json
from collections import defaultdict

# 加载 entity2id.json
with open("entity2id.json", "r", encoding="utf-8") as f:
    entity2id = json.load(f)

# 加载 relations.json
with open("relations.json", "r", encoding="utf-8") as f:
    relations_data = json.load(f)

# 初始化输出结构
edge_list = []  # [(head_id, tail_id)]
edge_types = []  # [rel_type string]
entity_type_map = {}  # {entity_name: type}
edge_dict = defaultdict(lambda: ([], []))  # for hetero graph

for block in relations_data:
    src_type = block["start_entity_type"]
    dst_type = block["end_entity_type"]
    rel_type = block["rel_type"]
    for rel in block["rels"]:
        h_name = rel["start_entity_name"]
        t_name = rel["end_entity_name"]

        if h_name not in entity2id or t_name not in entity2id:
            continue

        h_id = entity2id[h_name]
        t_id = entity2id[t_name]

        # 保存类型
        entity_type_map[h_name] = src_type
        entity_type_map[t_name] = dst_type

        # 边
        edge_list.append([h_id, t_id])
        edge_types.append(rel_type)

        # 异构图专用结构
        edge_dict[(src_type, rel_type, dst_type)][0].append(h_id)
        edge_dict[(src_type, rel_type, dst_type)][1].append(t_id)

# 保存边文件为 edge_list.json
with open("edge_list.json", "w", encoding="utf-8") as f:
    json.dump(edge_list, f, indent=2, ensure_ascii=False)

# 保存类型映射
with open("entity_type_map.json", "w", encoding="utf-8") as f:
    json.dump(entity_type_map, f, indent=2, ensure_ascii=False)

# 保存异构图边结构
edge_dict_serializable = {
    f"{k[0]}__{k[1]}__{k[2]}": {"src": v[0], "dst": v[1]}
    for k, v in edge_dict.items()
}
with open("edge_dict.json", "w", encoding="utf-8") as f:
    json.dump(edge_dict_serializable, f, indent=2, ensure_ascii=False)

print(f"✅ 共抽取 {len(edge_list)} 条边，已保存 edge_list.json / entity_type_map.json / edge_dict.json")

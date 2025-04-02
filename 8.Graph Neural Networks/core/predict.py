# predict.py
import json
import torch
from torch_geometric.data import Data
from models import GCN
from get_data import load_data
from util import device


def predict_entity(entity_name, model, data, entity2id, id2type):
    model.eval()
    if entity_name not in entity2id:
        print(f"[❌] 实体 '{entity_name}' 不存在！")
        return

    idx = entity2id[entity_name]
    out = model(data)
    prob = torch.softmax(out[idx], dim=0)
    pred_class = torch.argmax(prob).item()
    pred_type = id2type[pred_class]
    confidence = prob[pred_class].item()

    print(f"[✅] 实体：{entity_name}")
    print(f"→ 预测类型：{pred_type}")
    print(f"→ 置信度：{confidence:.4f}")
    return pred_type, confidence


def main():
    # === 加载数据 ===
    path = "./"  # 根路径
    data, in_feats, num_classes = load_data(path, name='pokemon_homogeneous')

    # === 加载实体映射 ===
    with open("pokemon/homogeneous/entity2id.json", "r", encoding="utf-8") as f:
        entity2id = json.load(f)
    with open("pokemon/homogeneous/entity_type_map.json", "r", encoding="utf-8") as f:
        entity_type_map = json.load(f)

    type_set = sorted(set(entity_type_map.values()))
    type2id = {t: i for i, t in enumerate(type_set)}
    id2type = {i: t for t, i in type2id.items()}

    # === 初始化并加载模型 ===
    model = GCN(in_feats, 64, num_classes).to(device)
    model.load_state_dict(torch.load("F:/GNN/GNNs-for-Node-Classification/homogeneous/saved_models/gcn_model.pth"))
    model.eval()

    # === 预测实体类型 ===
    while True:
        name = input("\n请输入要预测的实体名称（或输入 'exit' 退出）：")
        if name.lower() == 'exit':
            break
        predict_entity(name, model, data, entity2id, id2type)


if __name__ == "__main__":
    main()

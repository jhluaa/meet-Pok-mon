# 图神经网络图谱构建项目（GNN Knowledge Graph Builder）

![GNN](https://img.shields.io/badge/Graph-Neural%20Network-blue) 
![Pokémon](https://img.shields.io/badge/Dataset-Pokémon-brightgreen) 
![PyG](https://img.shields.io/badge/Framework-PyTorch_Geometric-red)

本项目旨在将宝可梦领域的知识图谱数据（实体、关系）转化为图神经网络（GNN）可用的数据格式，支持：

- ✅ 普通图（用于 GCN、GraphSAGE,GAT 等模型）
- ✅ 异构图（用于 RGCN、HGT 等异构图模型）

---
## 📁 项目结构说明

| 文件/目录名                      | 说明                                    |
|---------------------------------|---------------------------------------|
| `entities.json`                 | 原始实体数据（含属性）                           |
| `relations.json`                | 原始关系数据，结构化关系组 + 实体对                   |
| `entity2id.json`                | 实体名称 → 唯一 ID 的映射表                     |
| `entity_type_map.json`          | 实体名称 → 实体类型（如 Person、Pokémon 等）       |
| `edge_list.json`                | 普通图用的边列表（每条边是两个实体 ID）                 |
| `edge_dict.json`                | 异构图用的边结构（每种关系一组边）                     |
| `entity_data/`                  | 实体文本来源目录（从多个 `.txt` 自动抽取实体）           |
| `gen_entity2id.py`              | 从 `.txt` 抽取实体，生成 `entity2id.json` 的脚本 |
| `build_edges_from_relations.py` | 解析 `relations.json` 构建边数据的脚本          |
| `README.md`                     | 本说明文件                                 |

---

## 🧠 核心数据文件说明

### ✅ `entity2id.json`

将所有实体名转换为整数 ID，用于图神经网络建图：

```json
{
  "小智": 0,
  "皮卡丘": 1,
  "妙蛙种子": 2
}
```

---

### ✅ `edge_list.json`

用于普通图（无向图）的边列表，格式为实体 ID 对：

```json
[
  [0, 1],
  [1, 2]
]
```

示例含义：  
- `[0, 1]` 表示“小智”与“皮卡丘”之间的无向边  
- `[1, 2]` 表示“皮卡丘”与“妙蛙种子”之间的无向边  

可用于 GCN、GraphSAGE 等图神经网络结构。

---

### ✅ `entity_type_map.json`

记录每个实体的类型，用于构造 one-hot 特征或异构图节点类型：

```json
{
  "皮卡丘": "Pokémon",
  "妙蛙种子": "Pokémon",
  "小智": "Person"
}
```

---

### ✅ `edge_dict.json`

构建异构图（Heterogeneous Graph）所需结构，每类边记录其起点和终点 ID：

```json
{
  "Pokémon__evolves_into__Pokémon": {
    "src": [1, 2],
    "dst": [2, 3]
  },
  "Town__has_celebrity__Person": {
    "src": [4],
    "dst": [0]
  }
}
```

- 键名格式为：`源节点类型__关系类型__目标节点类型`
- 由于 JSON 不支持元组结构，因此用字符串拼接代替

---

## 🛠 使用流程

### 1️⃣ 从多个实体 `.txt` 文件中自动生成实体 ID：

```bash
python gen_entity2id.py
```

生成结果：`entity2id.json`

---

### 2️⃣ 解析 `relations.json` 生成边结构和类型映射：

```bash
python build_edges_from_relations.py
```

生成结果：  
- `edge_list.json`：普通图边  
- `edge_dict.json`：异构图边结构  
- `entity_type_map.json`：实体类型映射  

---

## 📊 训练说明

 图神经网络建模：

- 构建普通图（使用 PyG 的 `Data`）→ 训练 GCN、GraphSAGE ,GAT  **使用 GraphSAGE 作为图嵌入的最终结构**
- 构建异构图（使用 PyG 的 `HeteroData`）→ 训练 RGCN、HGT 属性预测


## 🔍 GNN应用

图神经网络生成的实体表示可以用于：

- 多跳问答、知识推理、结构增强  
- 结合大模型（ Qwen）实现语义问答或向量增强  
- 实体推荐、实体分类、关系预测等下游任务

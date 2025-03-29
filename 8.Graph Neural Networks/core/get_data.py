import json
import os
import torch
from torch_geometric.data import Data
from torch_geometric.data import HeteroData
from util import device
import random


def load_data(path, name):
    # 一个包含2708个节点、5429条边的图 Cora
    if name in ['Cora', 'PubMed', 'CiteSeer', 'NELL']:
        # 默认处理内置数据
        from torch_geometric.datasets import NELL, Planetoid
        if name == 'NELL':
            dataset = NELL(root=os.path.join(path, 'NELL'))
        else:
            dataset = Planetoid(root=path, name=name)
        data = dataset[0].to(
            device)  # (2708, 2708) Data(x=[2708, 1433], edge_index=[2, 10556], y=[2708], train_mask=[2708], val_mask=[2708], test_mask=[2708])

        if name == 'NELL':
            data.x = data.x.to_dense()
        return data, dataset.num_node_features, dataset.num_classes


    elif name == 'pokemon_homogeneous':
        base_path = os.path.join(path, 'pokemon', 'homogeneous')
        pt_path = os.path.join(base_path, 'pokemon_data.pt')
        if os.path.exists(pt_path):
            # data = torch.load(pt_path).to(device)
            data = torch.load(pt_path, weights_only=False).to(device)  # torch 2.6
            return data, data.num_node_features, data.y.max().item() + 1
        with open(os.path.join(base_path, 'edge_list.json'), 'r', encoding='utf-8') as f:
            edge_list = json.load(f)
        with open(os.path.join(base_path, 'entity_type_map.json'), 'r', encoding='utf-8') as f:
            entity_type_map = json.load(f)
        with open(os.path.join(base_path, 'entity2id.json'), 'r', encoding='utf-8') as f:
            entity2id = json.load(f)
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()

        type_set = sorted(set(entity_type_map.values()))
        type2id = {t: i for i, t in enumerate(type_set)}
        num_nodes = len(entity2id)
        x = torch.zeros((num_nodes, len(type2id)))
        y = torch.full((num_nodes,), -1, dtype=torch.long)
        for name, idx in entity2id.items():
            if name in entity_type_map:
                t_idx = type2id[entity_type_map[name]]
                x[idx][t_idx] = 1.0
                y[idx] = t_idx

        valid_mask = y >= 0
        valid_indices = torch.nonzero(valid_mask).view(-1).tolist()
        random.shuffle(valid_indices)
        train_split = int(0.6 * len(valid_indices))
        val_split = int(0.2 * len(valid_indices))
        train_idx = valid_indices[:train_split]
        val_idx = valid_indices[train_split:train_split + val_split]
        test_idx = valid_indices[train_split + val_split:]
        train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        test_mask = torch.zeros(num_nodes, dtype=torch.bool)
        train_mask[train_idx] = True
        val_mask[val_idx] = True
        test_mask[test_idx] = True

        data = Data(
            x=x,
            edge_index=edge_index,
            y=y,
            train_mask=train_mask,
            val_mask=val_mask,
            test_mask=test_mask
        )

        torch.save(data, pt_path)
        data = data.to(device)
        return data, x.size(1), len(type2id)
    elif name == 'pokemon_Heterogeneous':
        base_path = os.path.join(path, 'pokemon', 'heterogeneous')
        pt_path = os.path.join(base_path, 'pokemon_hetero_data.pt')
        if os.path.exists(pt_path):
            data = torch.load(pt_path, weights_only=False).to(device)
            return data, -1, -1
        # 加载 JSON 文件
        with open(os.path.join(base_path, 'edge_dict.json'), 'r', encoding='utf-8') as f:
            edge_dict = json.load(f)
        with open(os.path.join(base_path, 'entity_type_map.json'), 'r', encoding='utf-8') as f:
            entity_type_map = json.load(f)
        with open(os.path.join(base_path, 'entity2id.json'), 'r', encoding='utf-8') as f:
            entity2id = json.load(f)

        node_type_set = sorted(set(entity_type_map.values()))
        node_type_to_id = {t: i for i, t in enumerate(node_type_set)}

        hetero_data = HeteroData()

        # 构造节点特征
        x_all = {typ: {} for typ in node_type_set}
        for name, idx in entity2id.items():
            typ = entity_type_map.get(name)
            if typ is None:
                continue
            one_hot = torch.zeros(len(node_type_set))
            one_hot[node_type_to_id[typ]] = 1.0
            x_all[typ][idx] = one_hot

        for typ in node_type_set:
            if len(x_all[typ]) == 0:
                continue
            max_id = max(x_all[typ].keys()) + 1
            x_tensor = torch.zeros((max_id, len(node_type_set)))
            for i, feat in x_all[typ].items():
                x_tensor[i] = feat
            hetero_data[typ].x = x_tensor

        # 添加边 edge_index
        for rel_key, rel_val in edge_dict.items():
            try:
                src_type, rel_type, dst_type = rel_key.split("__")
            except ValueError:
                print(f"跳过无效关系: {rel_key}")
                continue
            src = torch.tensor(rel_val["src"], dtype=torch.long)
            dst = torch.tensor(rel_val["dst"], dtype=torch.long)
            edge_index = torch.stack([src, dst], dim=0)
            hetero_data[(src_type, rel_type, dst_type)].edge_index = edge_index

        # 添加 Pokémon 节点标签和掩码
        if 'Pokémon__has_type__identity' in edge_dict:
            label_src = edge_dict['Pokémon__has_type__identity']['src']
            label_dst = edge_dict['Pokémon__has_type__identity']['dst']

            unique_labels = sorted(list(set(label_dst)))
            label2id = {l: i for i, l in enumerate(unique_labels)}

            num_pokemon = hetero_data['Pokémon'].num_nodes
            y = torch.full((num_pokemon,), -1, dtype=torch.long)

            for src, dst in zip(label_src, label_dst):
                y[src] = label2id[dst]

            valid_idx = (y >= 0).nonzero(as_tuple=False).view(-1)
            perm = torch.randperm(len(valid_idx))
            num_train = int(0.6 * len(valid_idx))
            num_val = int(0.2 * len(valid_idx))

            train_mask = torch.zeros_like(y, dtype=torch.bool)
            val_mask = torch.zeros_like(y, dtype=torch.bool)
            test_mask = torch.zeros_like(y, dtype=torch.bool)

            train_mask[valid_idx[perm[:num_train]]] = True
            val_mask[valid_idx[perm[num_train:num_train + num_val]]] = True
            test_mask[valid_idx[perm[num_train + num_val:]]] = True

            hetero_data['Pokémon'].y = y
            hetero_data['Pokémon'].train_mask = train_mask
            hetero_data['Pokémon'].val_mask = val_mask
            hetero_data['Pokémon'].test_mask = test_mask
            print(f"[✅] Pokémon 标签已添加：共 {len(valid_idx)} 个有监督样本")
        else:
            print("[⚠️] 没有找到 Pokémon__has_type__identity 关系，无法生成标签")

        os.makedirs(os.path.dirname(pt_path), exist_ok=True)
        torch.save(hetero_data, pt_path)
        print(f"[✅] 异构图已保存至: {pt_path}")
        hetero_data = hetero_data.to(device)
        return hetero_data, -1, -1
    else:
        raise ValueError(f"Unknown dataset name: {name}")

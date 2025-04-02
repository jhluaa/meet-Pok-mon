# -*- coding:utf-8 -*-
import copy
import json
import numpy as np
import torch
from tqdm import tqdm
import os

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


@torch.no_grad()
def test(model, data):
    model.eval()
    out = model(data)
    loss_function = torch.nn.CrossEntropyLoss().to(device)
    loss = loss_function(out[data.val_mask], data.y[data.val_mask])
    _, pred = out.max(dim=1)
    correct = int(pred[data.test_mask].eq(data.y[data.test_mask]).sum().item())
    acc = correct / int(data.test_mask.sum())
    model.train()
    return loss.item(), acc


def train(model, data):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    loss_function = torch.nn.CrossEntropyLoss().to(device)
    min_val_loss = np.inf
    best_model = None
    min_epochs = 5
    model.train()
    final_test_acc = 0
    for epoch in tqdm(range(200)):
        out = model(data)
        optimizer.zero_grad()
        loss = loss_function(out[data.train_mask], data.y[data.train_mask])
        loss.backward()
        optimizer.step()

        # validation
        val_loss, test_acc = test(model, data)
        if val_loss < min_val_loss and epoch + 1 > min_epochs:
            min_val_loss = val_loss
            final_test_acc = test_acc
            best_model = copy.deepcopy(model)
        tqdm.write('Epoch {:03d} train_loss {:.4f} val_loss {:.4f} test_acc {:.4f}'
                   .format(epoch, loss.item(), val_loss, test_acc))

    os.makedirs("saved_models", exist_ok=True)
    torch.save(best_model.state_dict(), "saved_models/gcn_model.pth")
    print("[✅] 模型参数已保存到：saved_models/gcn_model.pth")
    return best_model, final_test_acc


def save_entity_embeddings(model, data, entity2id, save_path="embeddings/gnn_embeddings.json"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    model.eval()
    with torch.no_grad():
        hidden_embeddings = model(data, return_hidden=True)

    id2entity = {v: k for k, v in entity2id.items()}
    embedding_dict = {}
    for idx in range(hidden_embeddings.shape[0]):
        name = id2entity.get(idx, f"id_{idx}")
        vec = hidden_embeddings[idx].cpu().tolist()
        embedding_dict[name] = vec

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(embedding_dict, f, ensure_ascii=False, indent=2)

    print(f"[✅] 实体结构嵌入已保存到：{save_path}")


if __name__ == '__main__':
    from models import GCN
    from get_data import load_data

    path = r"F:\GNN\GNNs-for-Node-Classification\data"
    data, in_dim, out_dim = load_data(path, name="pokemon_homogeneous")

    model = GCN(in_dim, 64, out_dim).to(device)
    model.load_state_dict(torch.load("F:/GNN/GNNs-for-Node-Classification/homogeneous/saved_models/gcn_model.pth"))
    model.eval()

    with open(os.path.join(path, "pokemon/homogeneous/entity2id.json"), "r", encoding="utf-8") as f:
        entity2id = json.load(f)

    save_entity_embeddings(model, data, entity2id, save_path="embeddings/gnn_embeddings.json")

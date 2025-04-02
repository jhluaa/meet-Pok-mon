import copy
import os
import os.path as osp
import torch
from torch import nn
from torch_geometric.nn import HANConv
from tqdm import tqdm
from get_data import load_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

path = osp.join('F:/GNN/GNNs-for-Node-Classification/data')
hetero_data, _, _ = load_data(path, name="pokemon_Heterogeneous")

in_feats = 64
for node_type in hetero_data.node_types:
    num_nodes = hetero_data[node_type].num_nodes
    hetero_data[node_type].x = torch.randn((num_nodes, in_feats)).to(device)

if ('Pokémon', 'self_loop', 'Pokémon') not in hetero_data.edge_index_dict:
    num_pokemon = hetero_data['Pokémon'].num_nodes
    self_loop = torch.arange(num_pokemon, dtype=torch.long).unsqueeze(0).repeat(2, 1).to(device)
    hetero_data[('Pokémon', 'self_loop', 'Pokémon')].edge_index = self_loop

num_classes = int(hetero_data['Pokémon'].y.max().item()) + 1

node_types, edge_types = hetero_data.metadata()
train_mask = hetero_data['Pokémon'].train_mask
val_mask = hetero_data['Pokémon'].val_mask
test_mask = hetero_data['Pokémon'].test_mask
y = hetero_data['Pokémon'].y

# 模型参数
hidden_feats = 64
heads = 4


class HAN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(HAN, self).__init__()
        # 第一层：输出特征维度 = hidden_channels * heads
        self.conv1 = HANConv(in_channels, hidden_channels, hetero_data.metadata(), heads=heads)
        # 第二层：输入维度为 hidden_channels * heads
        self.conv2 = HANConv(hidden_channels * heads, out_channels, hetero_data.metadata(), heads=1)
        # fallback 投影：将原始 in_channels 投影到 hidden_channels * heads
        self.fallback_proj = nn.Linear(in_channels, hidden_channels * heads)

    def forward(self, data):
        x_dict, edge_index_dict = data.x_dict, data.edge_index_dict
        # 第一层卷积
        x_dict_updated = self.conv1(x_dict, edge_index_dict)
        # 对于未更新的节点类型（值为 None 或维度未改变），使用 fallback 投影补齐
        for node_type in x_dict:
            if x_dict_updated[node_type] is None:
                x_dict_updated[node_type] = self.fallback_proj(x_dict[node_type])
            elif x_dict_updated[node_type].shape[1] != self.conv2.in_channels:
                x_dict_updated[node_type] = self.fallback_proj(x_dict[node_type])
        # 第二层卷积
        x_dict_final = self.conv2(x_dict_updated, edge_index_dict)
        # 返回目标节点类型 Pokémon的输出
        return x_dict_final['Pokémon']


def train():
    model = HAN(in_feats, hidden_feats, num_classes).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001, weight_decay=1e-4)
    loss_function = torch.nn.CrossEntropyLoss().to(device)
    min_epochs = 5
    best_val_acc = 0
    final_best_acc = 0
    model.train()
    for epoch in tqdm(range(5000)):
        out = model(hetero_data)
        loss = loss_function(out[train_mask], y[train_mask])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        val_acc, _ = test(model, val_mask)
        test_acc, _ = test(model, test_mask)
        if epoch + 1 > min_epochs and val_acc > best_val_acc:
            best_val_acc = val_acc
            final_best_acc = test_acc
        tqdm.write('Epoch{:3d} train_loss {:.5f} val_acc {:.3f} test_acc {:.3f}'.format(
            epoch, loss.item(), val_acc, test_acc))
    os.makedirs("saved_models", exist_ok=True)
    torch.save(model.state_dict(), "saved_models/han_model.pth")
    print("[✅] 模型保存至 saved_models/han_model.pth")
    return final_best_acc


@torch.no_grad()
def test(model, mask):
    model.eval()
    out = model(hetero_data)
    loss_function = torch.nn.CrossEntropyLoss().to(device)
    loss = loss_function(out[mask], y[mask])
    _, pred = out.max(dim=1)
    correct = int(pred[mask].eq(y[mask]).sum().item())
    acc = correct / int(mask.sum())
    return acc, loss.item()


def main():
    final_best_acc = train()
    print('HAN Accuracy:', final_best_acc)


if __name__ == '__main__':
    main()

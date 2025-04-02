import copy
import os.path as osp
import torch
import os
from torch import nn
from torch_geometric.nn import RGCNConv
from tqdm import tqdm
from get_data import load_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

path = osp.join('F:/GNN/GNNs-for-Node-Classification/data')
hetero_data, _, _ = load_data(path, name="pokemon_Heterogeneous")
in_feats = hetero_data['Pokémon'].x.size(1)  # 输入维度
num_classes = int(hetero_data['Pokémon'].y.max().item()) + 1  # 类别数
node_types, edge_types = hetero_data.metadata()
num_nodes = hetero_data['Pokémon'].num_nodes
train_mask, val_mask, test_mask = hetero_data['Pokémon'].train_mask, hetero_data['Pokémon'].val_mask, hetero_data[
    'Pokémon'].test_mask
y = hetero_data['Pokémon'].y  # 属性

init_sizes = [hetero_data[x].x.shape[1] for x in node_types]

hidden_feats = 64


class RGCN(nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(RGCN, self).__init__()
        self.conv1 = RGCNConv(in_channels, hidden_channels,
                              num_relations=len(edge_types), num_bases=30)
        self.conv2 = RGCNConv(hidden_channels, out_channels,
                              num_relations=len(edge_types), num_bases=30)
        self.lins = torch.nn.ModuleList()
        for i in range(len(node_types)):
            lin = nn.Linear(init_sizes[i], in_channels)
            self.lins.append(lin)

    def trans_dimensions(self, g):
        data = copy.deepcopy(g)
        for node_type, lin in zip(node_types, self.lins):
            data[node_type].x = lin(data[node_type].x)
        return data

    def forward(self, data):
        data = self.trans_dimensions(data)
        homogeneous_data = data.to_homogeneous()
        edge_index, edge_type = homogeneous_data.edge_index, homogeneous_data.edge_type
        x = self.conv1(homogeneous_data.x, edge_index, edge_type)
        x = self.conv2(x, edge_index, edge_type)
        return x[:num_nodes]


def train():
    model = RGCN(in_feats, hidden_feats, num_classes).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=1e-4)
    loss_function = torch.nn.CrossEntropyLoss().to(device)
    min_epochs = 5
    best_val_acc = 0
    final_best_acc = 0
    model.train()
    for epoch in tqdm(range(1000)):
        f = model(hetero_data)
        loss = loss_function(f[train_mask], y[train_mask])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        val_acc, val_loss = test(model, val_mask)
        test_acc, test_loss = test(model, test_mask)
        if epoch + 1 > min_epochs and val_acc > best_val_acc:
            best_val_acc = val_acc
            final_best_acc = test_acc
        tqdm.write('Epoch{:3d} train_loss {:.5f} val_acc {:.3f} test_acc {:.3f}'.
                   format(epoch, loss.item(), val_acc, test_acc))

    os.makedirs("saved_models", exist_ok=True)
    torch.save(model.state_dict(), "saved_models/rgcn_model.pth")
    print("[✅] 模型保存至 saved_models/rgcn_model.pth")
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
    print('RGCN Accuracy:', final_best_acc)


if __name__ == '__main__':
    main()

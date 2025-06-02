import torch
import pandas as pd
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
import torch.nn.functional as F
from sklearn.preprocessing import LabelEncoder

# Завантаження даних
inter_df = pd.read_csv("interact.csv")
user_feat_df = pd.read_csv("user_feat.csv")
item_feat_df = pd.read_csv("item_feat.csv")

user_feat_df.rename(columns={"UserID": "userId"}, inplace=True)
item_feat_df.rename(columns={"MovieID": "movieId"}, inplace=True)

# Кодування
user_encoder = LabelEncoder()
item_encoder = LabelEncoder()

inter_df["user"] = user_encoder.fit_transform(inter_df["userId"])
inter_df["item"] = item_encoder.fit_transform(inter_df["movieId"])

valid_user_ids = set(inter_df["userId"])
valid_movie_ids = set(inter_df["movieId"])
user_feat_df = user_feat_df[user_feat_df["userId"].isin(valid_user_ids)].copy()
item_feat_df = item_feat_df[item_feat_df["movieId"].isin(valid_movie_ids)].copy()

user_feat_df["user"] = user_encoder.transform(user_feat_df["userId"])
item_feat_df["item"] = item_encoder.transform(item_feat_df["movieId"])

num_users = inter_df["user"].nunique()
user_feat_df = user_feat_df.sort_values("user")
item_feat_df = item_feat_df.sort_values("item")

user_features = torch.tensor(user_feat_df[["F", "M"]].values, dtype=torch.float)
item_features = torch.tensor(item_feat_df.drop(columns=["movieId", "item"]).values, dtype=torch.float)

# Вирівнювання розмірностей
user_dim = user_features.shape[1]
item_dim = item_features.shape[1]
if user_dim < item_dim:
    user_features = torch.cat([user_features, torch.zeros((user_features.shape[0], item_dim - user_dim))], dim=1)
elif item_dim < user_dim:
    item_features = torch.cat([item_features, torch.zeros((item_features.shape[0], user_dim - item_dim))], dim=1)

x = torch.cat([user_features, item_features], dim=0)
user_indices = torch.tensor(inter_df["user"].values, dtype=torch.long)
item_indices = torch.tensor(inter_df["item"].values + num_users, dtype=torch.long)
edge_index = torch.stack([user_indices, item_indices], dim=0)
edge_attr = torch.tensor(inter_df["rating"].values, dtype=torch.float)
data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

# Модель
class GAT(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GAT, self).__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads=2, concat=True)
        self.conv2 = GATConv(hidden_channels * 2, out_channels, heads=1, concat=False)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return x

device = torch.device("cpu")
model = GAT(in_channels=x.shape[1], hidden_channels=64, out_channels=32).to(device)
data = data.to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
model.train()

for epoch in range(50):
    optimizer.zero_grad()
    out = model(data.x, data.edge_index)
    user_emb = out[user_indices]
    item_emb = out[item_indices]
    preds = (user_emb * item_emb).sum(dim=1)
    loss = F.mse_loss(preds, edge_attr)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch + 1}/50, Loss: {loss.item():.4f}")

# Зберегти модель
torch.save(model.state_dict(), "gnn_model.pth")

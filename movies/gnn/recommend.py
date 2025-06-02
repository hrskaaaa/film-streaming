import os
import torch
import pandas as pd
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
import torch.nn.functional as F
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_model_and_data():
    inter_df = pd.read_csv(os.path.join(BASE_DIR, "interact.csv"))
    user_feat_df = pd.read_csv(os.path.join(BASE_DIR, "user_feat.csv"))
    item_feat_df = pd.read_csv(os.path.join(BASE_DIR, "item_feat.csv"))

    # Якщо потрібно: перейменовуємо колонки для узгодження
    # user_feat_df.rename(columns={"UserID": "userId"}, inplace=True)
    # item_feat_df.rename(columns={"MovieID": "movieId"}, inplace=True)

    # Отримуємо тільки користувачів/фільми, які є в interaction
    valid_users = inter_df["userId"].unique()
    valid_items = inter_df["movieId"].unique()
    user_feat_df = user_feat_df[user_feat_df["userId"].isin(valid_users)].copy()
    item_feat_df = item_feat_df[item_feat_df["movieId"].isin(valid_items)].copy()

    user_encoder = LabelEncoder()
    item_encoder = LabelEncoder()

    inter_df["user"] = user_encoder.fit_transform(inter_df["userId"])
    inter_df["item"] = item_encoder.fit_transform(inter_df["movieId"])
    user_feat_df["user"] = user_encoder.transform(user_feat_df["userId"])
    item_feat_df["item"] = item_encoder.transform(item_feat_df["movieId"])

    num_users = inter_df["user"].nunique()
    user_feat_df = user_feat_df.sort_values("user")
    item_feat_df = item_feat_df.sort_values("item")

    user_features = torch.tensor(user_feat_df[["F", "M"]].values, dtype=torch.float)
    item_features = torch.tensor(item_feat_df.drop(columns=["movieId", "item"]).values, dtype=torch.float)

    # Padding до однакових розмірів
    if user_features.shape[1] < item_features.shape[1]:
        user_features = torch.cat([user_features, torch.zeros((user_features.shape[0], item_features.shape[1] - user_features.shape[1]))], dim=1)
    elif item_features.shape[1] < user_features.shape[1]:
        item_features = torch.cat([item_features, torch.zeros((item_features.shape[0], user_features.shape[1] - item_features.shape[1]))], dim=1)

    x = torch.cat([user_features, item_features], dim=0)
    edge_index = torch.stack([
        torch.tensor(inter_df["user"].values, dtype=torch.long),
        torch.tensor(inter_df["item"].values + num_users, dtype=torch.long)
    ])
    edge_attr = torch.tensor(inter_df["rating"].values, dtype=torch.float)
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

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

    model = GAT(in_channels=x.shape[1], hidden_channels=64, out_channels=32)
    model.load_state_dict(torch.load(os.path.join(BASE_DIR, "gnn_model.pth"), map_location=torch.device("cpu")))
    model.eval()

    return model, data, user_encoder, item_encoder, num_users


# Інтерфейс виклику для Django 
model, data, user_encoder, item_encoder, num_users = load_model_and_data()

def get_recommendations(user_id_raw, top_k=5):
    try:
        user_id = user_encoder.transform([user_id_raw])[0]
    except Exception:
        return []

    with torch.no_grad():
        embeddings = model(data.x, data.edge_index)
        user_emb = embeddings[user_id]
        item_embs = embeddings[num_users:]
        scores = torch.matmul(item_embs, user_emb)
        top_scores, top_indices = torch.topk(scores, top_k)
        recommended_movie_ids = item_encoder.inverse_transform(top_indices.numpy())
        return recommended_movie_ids.tolist()

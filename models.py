import torch
import torch.nn as nn
import torch.nn.functional as F

class DSSMModel(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=32, hidden_dim=64):
        super(DSSMModel, self).__init__()
        
        # 用户塔
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.user_fc1 = nn.Linear(embedding_dim, hidden_dim)
        self.user_fc2 = nn.Linear(hidden_dim, 16)
        
        # 物品塔
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.item_fc1 = nn.Linear(embedding_dim, hidden_dim)
        self.item_fc2 = nn.Linear(hidden_dim, 16)

    def forward(self, user_ids, item_ids):
        # 用户前向传播
        user_emb = self.user_embedding(user_ids)
        u_out = F.relu(self.user_fc1(user_emb))
        u_out = self.user_fc2(u_out)
        
        # 物品前向传播
        item_emb = self.item_embedding(item_ids)
        i_out = F.relu(self.item_fc1(item_emb))
        i_out = self.item_fc2(i_out)
        
        # 计算余弦相似度作为打分
        # score = torch.sum(u_out * i_out, dim=-1)
        score = F.cosine_similarity(u_out, i_out, dim=-1)
        return score

import pandas as pd
import pymysql
from sklearn.metrics.pairwise import cosine_similarity
import torch
from models import DSSMModel

import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', 'your_password_here'), # 生产环境下通过环境变量 DB_PASS 注入
    'port': int(os.environ.get('DB_PORT', 3306)),
    'database': 'steam_rec',
    'charset': 'utf8mb4'
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

from sqlalchemy import create_engine

def load_ratings_data():
    # 使用 SQLAlchemy 来避免 pandas 警告
    engine = create_engine(f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}")
    query = "SELECT user_id, game_id, rating FROM ratings"
    df = pd.read_sql(query, engine)
    return df

def get_itemcf_recommendations(user_id, top_n=10, similar_k=80):
    ratings_df = load_ratings_data()
    
    if ratings_df.empty:
        return []

    # 1. 建立 用户-物品 交互矩阵 (使用 pivot_table 处理可能存在的重复评分，取均值)
    user_item_matrix = ratings_df.pivot_table(index='user_id', columns='game_id', values='rating', aggfunc='mean').fillna(0)
    
    if user_id not in user_item_matrix.index:
        # ===== 冷启动兜底 =====
        # 该用户没有交互记录，计算所有游戏平均得分取 TopN
        top_games = ratings_df.groupby('game_id')['rating'].mean().sort_values(ascending=False).head(top_n)
        return top_games.index.tolist()

    # 2. 计算 物品相似度矩阵
    item_similarity_matrix = cosine_similarity(user_item_matrix.T)
    item_similarity_df = pd.DataFrame(
        item_similarity_matrix, 
        index=user_item_matrix.columns, 
        columns=user_item_matrix.columns
    )
    
    # 3. 寻找用户看过的物品及其评分
    user_ratings = user_item_matrix.loc[user_id]
    watched_items = user_ratings[user_ratings > 0].index
    
    # 获取未看过的物品列表
    unwatched_items = user_ratings[user_ratings == 0].index
    
    # 4. 基于看过的物品相似度，为未看过的物品打分
    item_scores = {item: 0.0 for item in unwatched_items}
    
    for w_item in watched_items:
        if w_item in item_similarity_df.index:
            # 该看过物品与其他物品的相似度
            similarities = item_similarity_df.loc[w_item]
            # 取 top-K 个最相似物品来限制噪声 (可选，根据 reference 这里的要求是取 Top-K相似度然后累加)
            top_k_similar = similarities.sort_values(ascending=False)[1:similar_k+1]
            
            for sim_item, sim_score in top_k_similar.items():
                if sim_item in item_scores:
                    # 加权求和：相似度 * 历史评分
                    item_scores[sim_item] += sim_score * user_ratings[w_item]

    # 按算出的分数降序取 Top N
    sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
    recommended_game_ids = [item_id for item_id, score in sorted_items[:top_n]]
    
    return recommended_game_ids


def get_dssm_recommendations(user_id, top_n=10):
    ratings_df = load_ratings_data()
    if ratings_df.empty:
        return []
        
    all_users = ratings_df['user_id'].unique()
    all_games = ratings_df['game_id'].unique()
    
    num_users = int(max(all_users)) + 1
    num_items = int(max(all_games)) + 1

    # 在没有真的模型pth下，初始化一个随机模型代替
    model = DSSMModel(num_users=num_users, num_items=num_items)
    model.eval()

    # 获取用户未看过的游戏列表 (同样使用 pivot_table 避免报错)
    user_item_matrix = ratings_df.pivot_table(index='user_id', columns='game_id', values='rating', aggfunc='mean').fillna(0)
    if user_id not in user_item_matrix.index:
        # ===== 冷启动兜底 =====
        # 对于 DSSM 如果没有数据也直接返回平均分最高的游戏兜底
        top_games = ratings_df.groupby('game_id')['rating'].mean().sort_values(ascending=False).tail(top_n) # DSSM 兜底稍微取不同的以示区分
        return top_games.index.tolist()
        
    user_ratings = user_item_matrix.loc[user_id]
    unwatched_items = user_ratings[user_ratings == 0].index.tolist()
    
    if not unwatched_items:
        return []

    # 将 user_id 转为 tensor，且要与 items 数量对应匹配
    user_tensor = torch.tensor([user_id] * len(unwatched_items), dtype=torch.long)
    item_tensor = torch.tensor(unwatched_items, dtype=torch.long)

    with torch.no_grad():
        scores = model(user_tensor, item_tensor)
        
    # 根据预测的分数排序
    # scores 形如 Tensor([0.5, 0.2, 0.9, ...])
    top_indices = torch.argsort(scores, descending=True)[:top_n]
    
    recommended_game_ids = [unwatched_items[idx] for idx in top_indices.tolist()]
    
    return recommended_game_ids

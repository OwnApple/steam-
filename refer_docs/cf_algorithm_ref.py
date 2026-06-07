"""
【Agent阅读提示】
这是导师提供的协同过滤（ItemCF & UserCF）算法核心逻辑参考。
请重点参考以下使用 pandas.pivot 构建共现矩阵，以及使用 sklearn 计算余弦相似度（cosine_similarity）的数学逻辑。
**行动要求**：请提取此数学逻辑，将其优雅地封装进我们的 `utils.py` 中，并使其能够接收从 MySQL 读取的二维数据，而不是直接读取 csv。
"""
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def reference_item_cf_logic(ratings_df, target_user_id, top_n=10, similar_k=80):
    # 1. 建立 用户-物品 交互矩阵 (行：user_id，列：movie/game_id，值：ratings)
    user_item_matrix = ratings_df.pivot(index='user_id', columns='movie_id', values='ratings').fillna(0)
    
    # 2. 计算 物品相似度矩阵 (转置后计算 cosine_similarity)
    item_similarity_matrix = cosine_similarity(user_item_matrix.T)
    item_similarity_df = pd.DataFrame(
        item_similarity_matrix, 
        index=user_item_matrix.columns, 
        columns=user_item_matrix.columns
    )
    
    # 3. 寻找用户看过的物品
    watched_items = user_item_matrix.loc[target_user_id][user_item_matrix.loc[target_user_id] > 0].index
    
    # 4. 根据导师逻辑：遍历看过的物品，寻找 Top-K 相似物品
    top_k_similar_items_dict = {}
    for item in watched_items:
        if item in item_similarity_df.index:
            # 排序并获取前K个相似物品 (排除自身)
            similar_items = item_similarity_df.loc[item].sort_values(ascending=False)[1:similar_k+1]
            top_k_similar_items_dict[item] = similar_items
            
    # （Agent注意：后续需要根据相似度与历史评分的乘积，对未看过的物品进行加权求和并输出 Top-N 推荐列表）
    return list(top_k_similar_items_dict.keys())[:top_n] # 仅作演示
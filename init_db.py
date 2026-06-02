import pandas as pd
import pymysql
from werkzeug.security import generate_password_hash

# ================= 配置数据库连接 =================
# 课件标准配置：请替换成你真实的 MySQL 密码
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '123456', # 填入你的数据库密码
    'port': 3306,
    'database': 'steam_rec',           # 提前在 MySQL 里 CREATE DATABASE steam_rec;
    'charset': 'utf8mb4'
}

def init_database_and_import_data():
    print("🚀 开始连接数据库并构建表结构...")
    
    # 读取第一步清洗好的三个表
    try:
        users_df = pd.read_csv('./data/users_cleaned.csv')
        games_df = pd.read_csv('./data/games_cleaned.csv')
        ratings_df = pd.read_csv('./data/ratings_cleaned.csv')
    except FileNotFoundError:
        print("错误：找不到 CSV 文件，请确保上一步的数据清洗已经成功执行并导出。")
        return

    # 建立数据库连接
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # ================= 1. 创建数据表 =================
        # 创建 Users 表，并按要求加入默认密码字段用于登录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY,
                username VARCHAR(128),
                password VARCHAR(256)
            )
        ''')

        # 创建 Games 表 (对标电影推荐里的 movies 表)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                game_id INT PRIMARY KEY,
                game_name VARCHAR(128)
            )
        ''')

        # 创建 Ratings 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                user_id INT,
                game_id INT,
                rating FLOAT,
                playtime FLOAT
            )
        ''')
        
        print("✅ 数据表创建完成，开始导入数据...")

        # ================= 2. 导入数据并生成哈希密码 =================
        # 导入 Users：用 generate_password_hash 将 user_id 设为初始密码
        for _, row in users_df.iterrows():
            hashed_pwd = generate_password_hash(str(row['user_id']))
            cursor.execute(
                "INSERT IGNORE INTO users (user_id, username, password) VALUES (%s, %s, %s)",
                (row['user_id'], row['用户名'], hashed_pwd)
            )
        
        # 导入 Games
        for _, row in games_df.iterrows():
            cursor.execute(
                "INSERT IGNORE INTO games (game_id, game_name) VALUES (%s, %s)",
                (row['game_id'], row['游戏名称'])
            )
            
        # 导入 Ratings
        for _, row in ratings_df.iterrows():
            # 游玩时长可能存在空值，需转换为浮点数处理
            playtime = float(row['游玩时长']) if pd.notna(row['游玩时长']) else 0.0
            cursor.execute(
                "INSERT INTO ratings (user_id, game_id, rating, playtime) VALUES (%s, %s, %s, %s)",
                (row['user_id'], row['game_id'], row['rating'], playtime)
            )
            
        conn.commit()
        print("✅ 数据及加密密码导入完毕！")

        # ================= 3. 核心大招：创建索引 =================
        print("🚀 开始为数据库创建索引 (这步是防止后期查表卡死的关键)...")
        # 为 user_id 和 game_id 建立索引，显著优化带 WHERE 的 SELECT 查询
        cursor.execute("CREATE INDEX idx_user_id ON ratings(user_id)")
        cursor.execute("CREATE INDEX idx_game_id ON ratings(game_id)")
        cursor.execute("CREATE INDEX idx_user_game ON ratings(user_id, game_id)")
        
        conn.commit()
        print("✅ 索引创建成功，数据库性能拉满！")

    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("🔒 数据库连接已安全关闭。")

if __name__ == "__main__":
    init_database_and_import_data()
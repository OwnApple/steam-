from flask import Flask, render_template, request, session, redirect, url_for, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import os

from utils import get_itemcf_recommendations, get_dssm_recommendations

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 设置 session secret_key

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '123456', # 测试环境密码
    'port': 3306,
    'database': 'steam_rec',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

@app.before_request
def load_logged_in_user():
    """每次请求前检查 session 中的登录状态并赋给 g.user"""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                g.user = cursor.fetchone()
        finally:
            conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return "Username and password are required.", 400
            
        hashed_password = generate_password_hash(password)
        
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # 检查用户名是否已存在
                cursor.execute('SELECT user_id FROM users WHERE username = %s', (username,))
                if cursor.fetchone():
                    return "Username already exists.", 400
                
                # 获取最大的 user_id 并 +1
                cursor.execute('SELECT MAX(user_id) as max_id FROM users')
                max_id_row = cursor.fetchone()
                new_user_id = (max_id_row['max_id'] or 0) + 1

                # 插入新用户
                cursor.execute('INSERT INTO users (user_id, username, password) VALUES (%s, %s, %s)', (new_user_id, username, hashed_password))
            conn.commit()
            return redirect(url_for('login'))
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return "Username and password are required.", 400
            
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password'], password):
                    session.clear()
                    session['user_id'] = user['user_id']
                    return redirect(url_for('index'))
                else:
                    return "Invalid username or password.", 401
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if g.user is None:
        return redirect(url_for('login'))
        
    user_id = g.user['user_id']
    
    # 调用推荐算法并查出游戏名
    itemcf_recs_info = []
    dssm_recs_info = []
    try:
        itemcf_ids = get_itemcf_recommendations(user_id, top_n=10)
        dssm_ids = get_dssm_recommendations(user_id, top_n=10)
        
        conn = get_db()
        with conn.cursor() as cursor:
            # 批量查询 itemcf 信息
            if itemcf_ids:
                format_strings = ','.join(['%s'] * len(itemcf_ids))
                cursor.execute(f"SELECT game_id, game_name FROM games WHERE game_id IN ({format_strings})", tuple(itemcf_ids))
                games_dict = {str(row['game_id']): row['game_name'] for row in cursor.fetchall()}
                itemcf_recs_info = [{'game_id': str(gid), 'game_name': games_dict.get(str(gid), f"Game {gid}")} for gid in itemcf_ids]

            # 批量查询 dssm 信息
            if dssm_ids:
                format_strings = ','.join(['%s'] * len(dssm_ids))
                cursor.execute(f"SELECT game_id, game_name FROM games WHERE game_id IN ({format_strings})", tuple(dssm_ids))
                games_dict = {str(row['game_id']): row['game_name'] for row in cursor.fetchall()}
                dssm_recs_info = [{'game_id': str(gid), 'game_name': games_dict.get(str(gid), f"Game {gid}")} for gid in dssm_ids]
                
    except Exception as e:
        print(f"Recommend Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    return render_template('index.html', user=g.user, itemcf_recs=itemcf_recs_info, dssm_recs=dssm_recs_info)

@app.route('/rate', methods=['POST'])
def rate():
    if g.user is None:
        return jsonify({"error": "Unauthorized"}), 401
        
    game_id = request.form.get('game_id')
    rating = request.form.get('rating')
    
    if not game_id or not rating:
        return jsonify({"error": "game_id and rating are required"}), 400
        
    try:
        rating = float(rating)
    except ValueError:
        return jsonify({"error": "Invalid rating format"}), 400

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 记录评分闭环
            cursor.execute('''
                INSERT INTO ratings (user_id, game_id, rating) 
                VALUES (%s, %s, %s)
            ''', (g.user['user_id'], game_id, rating))
        conn.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

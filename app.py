from flask import Flask, render_template, request, redirect, url_for, g
import utils
import models

app = Flask(__name__)
# 此处配置 secret_key 用于 session 保护，实际应用中建议使用更安全的方式存储
app.secret_key = 'your_super_secret_key_here'

@app.before_request
def check_user_session():
    """
    每次请求前检查用户是否登录，
    如果已登录则将用户信息保存至全局变量 g.user，否则置为空。
    """
    g.user = None
    # TODO: 后续在这里编写获取 session 的逻辑，例如：
    # if 'user_id' in session:
    #     g.user = models.User.find_by_id(session['user_id'])
    pass

@app.route('/')
def index():
    """
    网站首页路由。
    """
    return "Hello, Steam Recommendation System!"

if __name__ == '__main__':
    # 根据部署环境需求开启 host='0.0.0.0' 以供外部访问
    app.run(host='0.0.0.0', port=5000, debug=True)
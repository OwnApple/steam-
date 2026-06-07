import requests

BASE_URL = 'http://127.0.0.1:5000'

def test_api():
    session = requests.Session()

    print("1. 测试注册 /register")
    res_reg = session.post(f"{BASE_URL}/register", data={"username": "testuser_routing", "password": "password123"})
    print(f"Register Status Code: {res_reg.status_code}")
    # 注册成功会发生重定向到 login 页面，通常 status_code 是 200 (因为 requests 自动跟从重定向)
    
    print("\n2. 测试登录 /login")
    res_login = session.post(f"{BASE_URL}/login", data={"username": "testuser_routing", "password": "password123"})
    print(f"Login Status Code: {res_login.status_code}")
    
    print("\n3. 测试获取主页内容 (验证登录态和算法调用) /")
    res_index = session.get(f"{BASE_URL}/")
    print(f"Index Status Code: {res_index.status_code}")

    print("\n4. 测试评分闭环 /rate")
    res_rate = session.post(f"{BASE_URL}/rate", data={"game_id": 12345, "rating": 4.5})
    print(f"Rate Status Code: {res_rate.status_code}")
    print(f"Rate Response: {res_rate.text}")

    print("\n5. 测试退出登录 /logout")
    res_logout = session.get(f"{BASE_URL}/logout")
    print(f"Logout Status Code: {res_logout.status_code}")

if __name__ == "__main__":
    test_api()
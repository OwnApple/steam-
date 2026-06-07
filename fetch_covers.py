import pandas as pd
import requests
import json
import os
import re
import time
from PIL import Image

# 解决本地证书问题如果需要的话
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_PATH = 'data/games_cleaned.csv'
COVERS_DIR = 'static/covers/'
DEFAULT_COVER_PATH = os.path.join(COVERS_DIR, 'default_cover.jpg')

# 确保目录存在
os.makedirs(COVERS_DIR, exist_ok=True)

# 生成一个默认的 fallback 封面
def generate_default_cover():
    if not os.path.exists(DEFAULT_COVER_PATH):
        # 创建一张 600x900 的暗色背景渐变或者纯色图
        img = Image.new('RGB', (600, 900), color=(42, 71, 94))  # Steam 风格背景色
        img.save(DEFAULT_COVER_PATH)

def clean_game_name(name):
    """清洗游戏名，去掉斜杠后面的中文或者括号及其内容，保留纯英文主标题"""
    if pd.isna(name):
        return ""
    # 1. 按照斜杠切割，取第一部分并去空白
    clean_name = str(name).split('/')[0].strip()
    
    # 2. 去掉可能存在的任何中文等非ASCII支付（如果是纯英文游戏）或者用正则处理
    # 简单处理：去掉中文字符（有些游戏本身只有中文名，这种没法直接用 steam 英文搜索）
    clean_name = re.sub(r'[\u4e00-\u9fa5]+', '', clean_name)
    
    # 3. 如果去掉中文后为空，返回原名尝试一下
    clean_name = clean_name.strip()
    return clean_name if clean_name else str(name).strip()

def fetch_steam_id(game_name):
    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(game_name)}&l=english&cc=US"
        resp = requests.get(url, timeout=5, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            if 'items' in data and len(data['items']) > 0:
                first_item = data['items'][0]
                return str(first_item.get('id'))
    except Exception as e:
        print(f"Error fetching id for {game_name}: {e}")
    return None

def download_cover(app_id, game_id):
    """尝试下载 600x900 的竖图，如果失败退回到普通图"""
    urls = [
        f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/library_600x900_2x.jpg",
        f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"
    ]
    
    save_path = os.path.join(COVERS_DIR, f"{game_id}.jpg")
    if os.path.exists(save_path):
        return True # 已经下载过

    for url in urls:
        try:
            resp = requests.get(url, timeout=5, verify=False)
            if resp.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
                return True
        except Exception as e:
            pass
            
    return False

def use_fallback_cover(game_id):
    import shutil
    save_path = os.path.join(COVERS_DIR, f"{game_id}.jpg")
    shutil.copy(DEFAULT_COVER_PATH, save_path)


def main():
    print("开始初始化兜底图片...")
    generate_default_cover()
    
    print("加载游戏数据...")
    df = pd.read_csv(DATA_PATH, encoding='utf-8')
    
    total = len(df)
    success_count = 0
    fallback_count = 0
    
    print(f"共需处理 {total} 款游戏。")
    
    for index, row in df.iterrows():
        game_id = row['game_id']
        raw_name = row['游戏名称']
        
        # 如果已经存在该文件，跳过
        if os.path.exists(os.path.join(COVERS_DIR, f"{game_id}.jpg")):
            success_count += 1
            if index % 10 == 0:
                print(f"进度: {index+1}/{total} - {raw_name} 封面已存在，跳过。")
            continue
            
        clean_name = clean_game_name(raw_name)
        
        print(f"[{index+1}/{total}] 搜索: {clean_name} (原名: {raw_name})")
        app_id = fetch_steam_id(clean_name)
        
        if app_id:
            if download_cover(app_id, game_id):
                print(f"  -> 成功下载封面! SteamAppID: {app_id}")
                success_count += 1
            else:
                print(f"  -> 下载封面失败，使用兜底。SteamAppID: {app_id}")
                use_fallback_cover(game_id)
                fallback_count += 1
        else:
            print(f"  -> 未找到相关游戏，使用兜底。")
            use_fallback_cover(game_id)
            fallback_count += 1
            
        time.sleep(0.1) # 频率限制，避免被封
        
    print(f"\n处理完成! 成功: {success_count}, 兜底: {fallback_count}")

if __name__ == '__main__':
    main()

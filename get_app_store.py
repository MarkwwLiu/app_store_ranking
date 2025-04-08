"""
App Store 應用程式資訊爬蟲

這個腳本用於從 App Store 抓取特定應用程式的資訊，包括：
- 應用程式名稱
- 應用程式排名
- 其他相關資訊

使用方法：
    python get_app_store.py

依賴套件：
    - requests
    - beautifulsoup4
    - logging
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
from datetime import datetime, timedelta
import time
import json
import os

# 定義目錄常量
LOG_DIR = "log"
DATA_DIR = "app_store_ranking"

# 確保目錄存在
for directory in [LOG_DIR, DATA_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"創建目錄: {directory}")

# 設置日誌記錄
log_file = os.path.join(LOG_DIR, f'app_store_crawler_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def get_taiwan_time() -> str:
    """
    獲取台灣時間 (UTC+8)

    Returns:
        台灣時間的 ISO 格式字符串
    """
    # 獲取當前 UTC 時間
    utc_now = datetime.utcnow()
    # 加上 8 小時得到台灣時間
    taiwan_time = utc_now + timedelta(hours=8)
    return taiwan_time.isoformat()

class AppStoreCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_app_info(self, urls: List[str]) -> List[Dict]:
        """
        從 App Store 抓取應用程式資訊

        Args:
            urls: App Store 應用程式網址列表

        Returns:
            包含應用程式資訊的字典列表
        """
        app_infos = []

        for url in urls:
            try:
                logging.info(f"開始抓取: {url}")

                # 添加延遲以避免過度請求
                time.sleep(2)

                response = self.session.get(url)
                response.raise_for_status()
                response.encoding = 'utf-8'

                soup = BeautifulSoup(response.text, 'html.parser')

                # 抓取應用程式資訊
                app_info = {
                    'name': self._get_app_name(soup),
                    'ranking': self._get_app_ranking(soup),
                    'url': url,
                    'timestamp': get_taiwan_time()
                }

                app_infos.append(app_info)
                logging.info(f"成功抓取應用程式資訊: {app_info['name']}")

            except requests.RequestException as e:
                logging.error(f"網路請求錯誤: {url} - {str(e)}")
                app_infos.append({
                    'name': '未知',
                    'ranking': '999999',  # 設置一個很大的數字，確保錯誤的排在最後
                    'url': url,
                    'error': str(e),
                    'timestamp': get_taiwan_time()
                })
            except Exception as e:
                logging.error(f"處理錯誤: {url} - {str(e)}")
                app_infos.append({
                    'name': '未知',
                    'ranking': '999999',  # 設置一個很大的數字，確保錯誤的排在最後
                    'url': url,
                    'error': str(e),
                    'timestamp': get_taiwan_time()
                })

        return app_infos

    def _get_app_name(self, soup: BeautifulSoup) -> str:
        """獲取應用程式名稱"""
        try:
            return soup.find('h1', class_='product-header__title').get_text(strip=True)
        except AttributeError:
            return "未知"

    def _get_app_ranking(self, soup: BeautifulSoup) -> str:
        """獲取應用程式排名"""
        try:
            ranking_text = soup.find('a', class_='inline-list__item')
            if ranking_text:
                return "".join(filter(str.isdigit, ranking_text.get_text()))
            return "999999"  # 如果找不到排名，返回一個很大的數字
        except AttributeError:
            return "999999"

def sort_apps_by_ranking(app_infos: List[Dict]) -> List[Dict]:
    """
    根據排名對應用程式進行排序

    Args:
        app_infos: 應用程式資訊列表

    Returns:
        排序後的應用程式資訊列表
    """
    return sorted(app_infos, key=lambda x: int(x['ranking']))

def print_app_ranking(app_infos: List[Dict]):
    """
    格式化輸出應用程式排名資訊

    Args:
        app_infos: 應用程式資訊列表
    """
    print("\n=== App Store 應用程式排名 ===")
    print(f"抓取時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    print(f"{'排名':<6} {'應用程式名稱':<40} {'網址'}")
    print("-" * 50)

    for app in app_infos:
        if 'error' in app:
            print(f"{'錯誤':<6} {app['name']:<40} {app['url']}")
            print(f"錯誤信息: {app['error']}")
        else:
            print(f"{app['ranking']:<6} {app['name']:<40} {app['url']}")
    print("-" * 50)

def save_to_json(app_infos: List[Dict], folder_name: str = DATA_DIR):
    """
    將應用程式資訊保存到 JSON 文件

    Args:
        app_infos: 應用程式資訊列表
        folder_name: 保存數據的文件夾名稱
    """
    # 生成文件名（使用當前日期和時間）
    file_name = f"app_store_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = os.path.join(folder_name, file_name)

    # 準備要保存的數據
    data = {
        "timestamp": get_taiwan_time(),
        "apps": app_infos
    }

    # 保存到 JSON 文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    logging.info(f"數據已保存到: {file_path}")
    print(f"\n數據已保存到: {file_path}")

def get_app_urls() -> List[str]:
    """
    獲取要爬取的 App Store 應用程式網址列表

    Returns:
        App Store 應用程式網址列表
    """
    return [
        "https://apps.apple.com/tw/app/max-%E8%99%9B%E6%93%AC%E8%B2%A8%E5%B9%A3%E4%BA%A4%E6%98%93%E6%89%80/id1370837255",
        "https://apps.apple.com/tw/app/bitopro-%E5%B9%A3%E8%A8%97%E4%BA%A4%E6%98%93%E6%89%80-%E6%AF%94%E7%89%B9%E5%B9%A3%E8%B2%B7%E8%B3%A3%E9%A6%96%E9%81%B8/id6468561188",
        "https://apps.apple.com/tw/app/%E5%B9%A3%E5%AE%89-%E8%B2%B7%E6%AF%94%E7%89%B9%E5%B9%A3-%E5%B0%B1%E7%94%A8%E5%85%A8%E7%90%83%E7%AC%AC%E4%B8%80%E6%8A%95%E8%B3%87%E7%90%86%E8%B2%A1%E9%A6%96%E9%81%B8%E5%8A%A0%E5%AF%86%E8%B2%A8%E5%B9%A3%E4%BA%A4%E6%98%93%E6%89%80/id1436799971",
        "https://apps.apple.com/tw/app/okx-%E6%AF%94%E7%89%B9%E5%B9%A3%E6%8A%95%E8%B3%87-%E4%BD%BF%E7%94%A8%E5%85%A8%E7%90%83%E5%89%8D%E4%BA%8C%E5%8A%A0%E5%AF%86%E8%B2%A8%E5%B9%A3%E4%BA%A4%E6%98%93%E6%89%80-web3%E9%8C%A2%E5%8C%85/id1327268470"
    ]

def main():
    # 獲取要爬取的網址
    urls = get_app_urls()

    # 創建爬蟲實例並抓取應用程式資訊
    crawler = AppStoreCrawler()
    app_info_list = crawler.fetch_app_info(urls)

    # 根據排名排序
    sorted_apps = sort_apps_by_ranking(app_info_list)

    # 輸出排序後的結果
    print_app_ranking(sorted_apps)

    # 保存到 JSON 文件
    save_to_json(sorted_apps)

if __name__ == "__main__":
    main()

"""
JSON 數據轉換為 SQLite 資料庫

這個腳本用於將 App Store 爬蟲生成的 JSON 數據轉換為 SQLite 資料庫格式。
SQLite 是一個輕量級的資料庫，不需要安裝額外的資料庫服務器，也不需要輸入帳號密碼。

使用方法：
    python json_to_db.py [json_file_path]

參數：
    json_file_path: JSON 文件的路徑，如果未提供，則使用最新的 JSON 文件
"""

import os
import json
import sqlite3
import glob
from datetime import datetime
import logging
from typing import List, Dict, Optional

# 設置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'json_to_db_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# 定義目錄常量
DATA_DIR = "app_store_ranking"
DB_DIR = "database"

# 確保資料庫目錄存在
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
    logging.info(f"創建目錄: {DB_DIR}")

def get_latest_json_file() -> Optional[str]:
    """
    獲取最新的 JSON 文件路徑

    Returns:
        最新的 JSON 文件路徑，如果沒有找到則返回 None
    """
    json_files = glob.glob(os.path.join(DATA_DIR, "app_store_ranking_*.json"))
    if not json_files:
        return None

    # 按文件修改時間排序，返回最新的文件
    return max(json_files, key=os.path.getmtime)

def create_database(db_path: str) -> None:
    """
    創建 SQLite 資料庫和表

    Args:
        db_path: 資料庫文件路徑
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 創建應用程式表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS apps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        version TEXT,
        ranking INTEGER,
        url TEXT NOT NULL,
        date TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    # 創建錯誤記錄表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        error_message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    logging.info(f"資料庫已創建: {db_path}")

def import_json_to_db(json_file_path: str, db_path: str) -> None:
    """
    將 JSON 數據導入到 SQLite 資料庫

    Args:
        json_file_path: JSON 文件路徑
        db_path: 資料庫文件路徑
    """
    # 讀取 JSON 文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 連接資料庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 獲取當前時間
    current_time = datetime.now().isoformat()

    # 從時間戳中提取日期部分
    date = data.get('timestamp', '').split('T')[0]

    # 檢查是否已經存在相同日期的數據
    cursor.execute('''
    SELECT COUNT(*) FROM apps WHERE date = ?
    ''', (date,))

    if cursor.fetchone()[0] > 0:
        logging.info(f"已存在 {date} 的數據，將覆蓋原有數據")
        # 刪除相同日期的數據
        cursor.execute('''
        DELETE FROM apps WHERE date = ?
        ''', (date,))
        # 刪除相同日期的錯誤記錄
        cursor.execute('''
        DELETE FROM errors WHERE date(timestamp) = ?
        ''', (date,))

    # 導入應用程式數據
    for app in data.get('apps', []):
        if 'error' in app:
            # 導入錯誤記錄
            cursor.execute('''
            INSERT INTO errors (name, url, error_message, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                app['name'],
                app['url'],
                app['error'],
                app['timestamp'],
                current_time
            ))
        else:
            # 導入應用程式數據
            cursor.execute('''
            INSERT INTO apps (name, version, ranking, url, date, timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                app['name'],
                app['version'],
                int(app['ranking']),
                app['url'],
                date,
                app['timestamp'],
                current_time
            ))

    # 提交事務並關閉連接
    conn.commit()
    conn.close()

    logging.info(f"已將 {json_file_path} 導入到 {db_path}")

def query_apps(db_path: str, limit: int = 10) -> List[Dict]:
    """
    查詢應用程式數據

    Args:
        db_path: 資料庫文件路徑
        limit: 返回的記錄數量限制

    Returns:
        應用程式數據列表
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 設置行工廠，使結果可以通過列名訪問
    cursor = conn.cursor()

    cursor.execute('''
    SELECT name, version, ranking, url, date, timestamp
    FROM apps
    ORDER BY ranking ASC
    LIMIT ?
    ''', (limit,))

    results = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return results

def query_errors(db_path: str, limit: int = 10) -> List[Dict]:
    """
    查詢錯誤記錄

    Args:
        db_path: 資料庫文件路徑
        limit: 返回的記錄數量限制

    Returns:
        錯誤記錄列表
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 設置行工廠，使結果可以通過列名訪問
    cursor = conn.cursor()

    cursor.execute('''
    SELECT name, url, error_message, timestamp
    FROM errors
    ORDER BY timestamp DESC
    LIMIT ?
    ''', (limit,))

    results = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return results

def print_query_results(apps: List[Dict], errors: List[Dict]) -> None:
    """
    打印查詢結果

    Args:
        apps: 應用程式數據列表
        errors: 錯誤記錄列表
    """
    print("\n=== App Store 應用程式排名 (資料庫查詢結果) ===")
    print(f"查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    print(f"{'排名':<6} {'應用程式名稱':<25} {'版本':<8} {'日期':<10} {'網址'}")
    print("-" * 80)

    for app in apps:
        print(f"{app['ranking']:<6} {app['name']:<25} {app['version']:<8} {app['date']:<10} {app['url']}")

    if errors:
        print("\n=== 錯誤記錄 ===")
        print("-" * 50)
        print(f"{'應用程式名稱':<40} {'網址'}")
        print("-" * 50)

        for error in errors:
            print(f"{error['name']:<40} {error['url']}")
            print(f"錯誤信息: {error['error_message']}")

    print("-" * 80)

def main():
    import sys

    # 獲取 JSON 文件路徑
    json_file_path = None
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
    else:
        json_file_path = get_latest_json_file()

    if not json_file_path:
        logging.error("未找到 JSON 文件")
        print("錯誤: 未找到 JSON 文件")
        return

    # 設置資料庫文件路徑
    db_path = os.path.join(DB_DIR, "app_store.db")

    # 創建資料庫
    create_database(db_path)

    # 導入 JSON 數據
    import_json_to_db(json_file_path, db_path)

    # 查詢並顯示結果
    apps = query_apps(db_path)
    errors = query_errors(db_path)
    print_query_results(apps, errors)

    print(f"\n數據已成功導入到資料庫: {db_path}")

if __name__ == "__main__":
    main()

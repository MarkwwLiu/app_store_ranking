# App Store 應用程式排名爬蟲

這是一個用於抓取 App Store 應用程式排名資訊的爬蟲工具。該工具可以抓取特定應用程式的名稱、排名等資訊，並將結果保存為 JSON 格式，同時也支持將數據導入到 SQLite 資料庫中。

## 功能特點

- 抓取 App Store 應用程式的名稱、排名和版本號
- 自動處理網路錯誤和解析錯誤
- 將結果按排名排序
- 將數據保存為 JSON 格式
- 支持將 JSON 數據導入到 SQLite 資料庫
- 使用台灣時間 (UTC+8) 記錄時間戳
- 自動創建日誌文件記錄運行情況
- 根據日期判斷，相同日期的數據會覆蓋原有數據

## 安裝方法

1. 克隆或下載此專案到本地
2. 安裝所需套件：

```bash
pip install -r requirements.txt
```

## 使用方法

### 抓取 App Store 數據

直接運行主程式：

```bash
python get_app_store.py
```

### 將 JSON 數據導入到 SQLite 資料庫

運行 JSON 轉資料庫工具：

```bash
python json_to_db.py [json_file_path]
```

參數說明：
- `json_file_path`：JSON 文件的路徑，如果未提供，則使用最新的 JSON 文件

## 輸出結果

程式會輸出以下內容：

1. 控制台顯示應用程式排名資訊
2. JSON 文件保存在 `app_store_ranking` 目錄中
3. 日誌文件保存在 `log` 目錄中
4. SQLite 資料庫文件保存在 `database` 目錄中

## 目錄結構

```
app_store_ranking/
├── README.md                 # 說明文件
├── requirements.txt          # 依賴套件列表
├── get_app_store.py          # 主程式
├── json_to_db.py             # JSON 轉資料庫工具
├── log/                      # 日誌文件目錄
│   └── app_store_crawler_YYYYMMDD.log
├── app_store_ranking/        # 數據文件目錄
│   └── app_store_ranking_YYYYMMDD_HHMMSS.json
└── database/                 # 資料庫目錄
    └── app_store.db          # SQLite 資料庫文件
```

## 資料庫結構

SQLite 資料庫包含兩個表：

1. `apps` 表：存儲應用程式資訊
   - `id`：主鍵
   - `name`：應用程式名稱
   - `version`：應用程式版本號
   - `ranking`：應用程式排名
   - `url`：應用程式網址
   - `date`：抓取日期 (YYYY-MM-DD)
   - `timestamp`：抓取時間戳
   - `created_at`：數據導入時間

2. `errors` 表：存儲錯誤記錄
   - `id`：主鍵
   - `name`：應用程式名稱
   - `url`：應用程式網址
   - `error_message`：錯誤信息
   - `timestamp`：抓取時間戳
   - `created_at`：數據導入時間

## 自定義配置

如需修改要爬取的應用程式，請編輯 `get_app_store.py` 文件中的 `get_app_urls()` 函數。

## 注意事項

- 請合理設置爬取頻率，避免對 App Store 伺服器造成過大負擔
- 爬取的數據僅供參考，實際排名可能與 App Store 官方顯示有所差異
- 建議定期檢查程式是否正常運行，確保數據的連續性
- SQLite 資料庫是輕量級的，適合小型應用，如果需要處理大量數據，建議使用 MySQL 或 PostgreSQL 等資料庫
- 程式會自動檢查日期，如果同一天已有數據，則會覆蓋原有數據
- 版本號信息可以幫助追蹤應用程式的更新情況

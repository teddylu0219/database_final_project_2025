## 環境需求
- Ubuntu 22.04+、Python 3.10+、PostgreSQL 12+
- 套件：`sudo apt-get install python3-venv python3-pip libpq-dev postgresql postgresql-contrib`

## 安裝與啟動（Ubuntu）
在專案根目錄執行：
```bash
sudo service postgresql start
sudo -u postgres createuser -s "$USER" || true   # 已存在可忽略
createdb nycu_food
cp .env.example .env   # 依需求修改 DB_USER/DB_PASSWORD
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash load_all.sh       # 重建 schema 並匯入 data/ 下 8 個 CSV
python3 app.py
```
開啟瀏覽器 http://localhost:5000

### 連線/權限常見問題
- `password authentication failed for user "xxx"`：確認 DB 有該角色並設密碼，再把 `.env` 對應：
  ```bash
  sudo -u postgres psql -c "ALTER USER <user> WITH PASSWORD 'your_pwd';"
  createdb -U <user> -W nycu_food
  psql -U <user> -W -d nycu_food -f schema.sql
  ```
- `Peer authentication failed for user "postgres"`：本機 postgres 使用 peer。改用系統 postgres 身份（免密）：`sudo -u postgres psql -d nycu_food -f schema.sql` 或 `sudo -u postgres createdb nycu_food`。若要改成密碼登入需調整 pg_hba.conf 為 md5 並重啟（不建議為作業修改）。
- `schema.sql: Permission denied`（用 `sudo -u postgres ... -f schema.sql`）：postgres 無權讀你的路徑。用重導向：`sudo -u postgres psql -d nycu_food < schema.sql`，或將檔案放到可讀位置並用絕對路徑。

## 匯入與重置資料
- 一鍵重建+匯入資料：`bash load_all.sh`（讀 `.env` 設定 DB 連線，重跑 schema 並匯入 `data/` 下 8 個 CSV）。
- 重置資料：`psql -U <user> -W -d nycu_food -f schema.sql` 後再跑 `load_all.sh`。
- 建議的編輯/匯入順序（避免 FK 失敗）：`locations -> categories -> stores -> business_hours -> store_categories -> foods -> users -> reviews`。改完 CSV 後執行 `bash load_all.sh` 重灌並載入。
- 若在前端新增/刪除資料，CSV 不會自動更新；要把當前 DB 狀態回寫到 `data/`，請執行 `bash export_all.sh`。

## 專案結構
- `app.py`：Flask 路由與頁面
- `db.py`：PostgreSQL 連線與 helper
- `schema.sql`：建表腳本（`load_all.sh` 會執行）
- `templates/`：頁面模板
- `data/`：示範 CSV（8 張表）
- `load_all.sh`：重建 schema 並匯入 `data/` 的一鍵腳本
- `export_all.sh`：將目前 DB 資料匯出到 `data/`

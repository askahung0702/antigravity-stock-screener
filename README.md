# Taiwan Stock Analysis Web App

## 啟動方式 (How to run)

本專案分為前端 (Next.js) 與後端 (FastAPI)。請開兩個終端機 (Terminal) 分別啟動。

### 1. 啟動後端 FastAPI
在終端機 1 執行：
```bash
cd backend

# 啟動虛擬環境 (Windows)
# 如果您使用 PowerShell 遇到「無法載入檔案...因為這個系統上已停用指令碼執行」的紅字錯誤，請先執行以下指令一次：
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\activate

# 啟動 FastAPI 伺服器
uvicorn main:app --reload --port 8000
```
後端 API 測試網址：http://localhost:8000/api/health
自動生成的文件 (Swagger UI)：http://localhost:8000/docs
資料管線狀態：http://localhost:8000/api/system/pipeline-status

### 2. 啟動前端 Next.js
在終端機 2 執行：
```bash
cd frontend
npm run dev
```
前端網址：http://localhost:3000

## 資料更新

每日收盤後執行股價、三大法人與新聞增量更新：

```powershell
.\run_stock_analysis.bat
```

每週或需要更新觀察池與 TTM 財務快照時：

```powershell
.\run_stock_analysis.bat --include-prescreen
```

更新流程採 upsert，不會先刪除既有資料。每項工作都會寫入
`pipeline_run`，抓取失敗時保留最後一次有效資料。舊版隨機產生的法人資料
會被標記為 `is_estimated=1`，新版法人資料僅使用 TWSE T86 正式來源。

目前預篩選仍是 32 檔大型優質股觀察池，不代表完整上市櫃市場；前端已依此
調整名稱。評分改採品質、成長、相對估值、價格動能與風險流動性的多因子模型。

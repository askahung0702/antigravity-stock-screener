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

### 2. 啟動前端 Next.js
在終端機 2 執行：
```bash
cd frontend
npm run dev
```
前端網址：http://localhost:3000

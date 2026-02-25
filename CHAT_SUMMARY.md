# Antigravity Stock (台股價值投資與動能分析系統) - 開發歷程與摘要

此文件總結了我們在這段對話中，從零開始建構整套 **台股股票分析 Web 應用** 的所有討論過程與實作成果。

## 🎯 專案核心目標
- **痛點解決**：解決手動計算估值耗時、閱讀新聞耗時且容易被誤導、缺乏好用的客製化選股器等問題。
- **MVP 策略**：優先以「基本面價值投資」結合「技術/籌碼動能分析」出發，初期專注於台股強勢股與權值股。
- **技術選型**：
  - 前端：Next.js, React, Tailwind CSS, Recharts
  - 後端：Python FastAPI, SQLAlchemy, yfinance, twstock
  - 資料庫：SQLite (MVP 階段)
  - AI 模組：Google Gemini API

---

## 🚀 開發里程碑 (各階段完成項目)

### 📌 階段一：專案基礎建設 (Project Setup)
- 初始化前端 Next.js 專案架構並配置了深色高質感的 UI 主題。
- 初始化後端 Python FastAPI 專案，建立 SQLAlchemy ORM 模型 (`StockMarket`, `StockPrice`, `FinancialData`, `CompanyNews`, `InstitutionalData`) 並將其統一收攏在 `database.py` 中避免遞迴引用導致的啟動錯誤。

### 📌 階段二：資料管線建設 (Data Pipeline)
- **Top 20 種子池**：為了避免頻繁爬取全市場資料導致 IP 被封鎖，系統設計了「預先篩選」機制 (`pre_screen_top20.py`)：
  - **初期**：使用人工挑選的 20 檔權值股名單。
  - **演進**：升級為動態掃描。建立涵蓋 30 餘檔優質企業的種子池，即時透過 `yfinance` 抓取 EPS、ROE 與本益比，並套用自訂的「100 分制投資價值演算法」，動態列出分數最高的 Top 20 股票存入 DB。也排除了原先的金融股。
  - **資料在地化**：自動將 `yfinance` 抓回的英文代碼轉換為熟悉的「台股中文全名」與「在地產業分類」。
- **歷史股價 (OHLCV)**：實作 `fetch_stock_history.py` 抓取近 90 天股價數據以供後續前端 K 線圖等技術指標運算。
- **籌碼與財報數據**：建立對應腳本收集相關數據格式，補齊系統評估所需的基本面與籌碼面斷層。

### 📌 階段三：自動化估值與選股器模組 (Valuation & Screener)
- **智慧選股器 API**：在 `screener_router.py` 開發了支援多條件過濾 (最低/高 EPS、ROE、PE、產業別) 的 API。
- **即時報價引擎**：選股器 API 會在呼叫時，透過 `yfinance` 即時打去美國主機批次下載最新即時價格，確保盤中的 PE 估值完全不落後。
- **自動化評分標籤**：伺服器會依據財務數據自動賦予類似「高ROE資優生」、「估值遭低估」等AI評語摘要。

### 📌 階段四：AI 新聞分析防幻覺模組 (AI Anti-Hallucination News)
- **即時爬蟲建置**：在 `fetch_financials.py` 中利用 `BeautifulSoup` 開發了即時連線到 Yahoo 股市 (tw.stock.yahoo.com) 抓取「當天熱騰騰真實新聞」的模組。
- **嚴防 AI 幻覺 (Grounding)**：在 `ai_news_service.py` 的 prompt 中嚴格限制 Gemini API 只能針對傳入的真實新聞標題或內容去產出摘要、執行情緒分析(Positive/Neutral/Negative)與列點風險提示，絕不自行發明捏造股價預測。
- **優雅降級**：當無效或遺失 `GEMINI_API_KEY` 時，系統能安全處理例外並回傳友善的 Mock 分析，不讓後台崩潰。

### 📌 階段五：前端視覺與儀表板實作 (Frontend UI/UX)
- **自動載入的選股器 (`Screener.tsx`)**：修正了原本需要手動點擊篩選才會作動的 Bug，加入 `useEffect` 讓網頁載入瞬間即觸發 API 撈取 Top 20 清單。
- **「價值成長潛力榜」全新分頁 (`Ranking.tsx`)**：
  - 新增在首頁最上方的頁籤導覽列中。
  - 設計成高質感的 Top 10 名人堂卡片列表，特製前三名的金、銀、銅獎牌特效。
  - 綁定嚴苛條件 (ROE > 10%、持續獲利、本益比 < 15) 的自動篩選，並強制以「投資價值總分」由高遞減倒序排列。
- 完善的動態互動：加入許多透明、毛玻璃與漸層效果，讓這個數據密集的金融工具網頁充滿了高隱蔽性與現代駭客風格。

---

## 🛠️ 如何執行與維護

### 啟動後端
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
### 啟動前端
```bash
cd frontend
npm run dev
```
*(會在 http://localhost:3000 提供服務)*

### 執行核心資料更新管線 (爬蟲腳本)
要讓儀表板資料永遠保持在最新狀態，只要在後端環境依序執行以下命令（這也可以設定為 Windows 排程 / Cron Job 每日收盤後自動跑一次）：
```bash
python scripts/pre_screen_top20.py
python scripts/fetch_stock_history.py
python scripts/fetch_institutional.py
python scripts/fetch_financials.py
```

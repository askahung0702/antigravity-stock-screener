# 角色設定：全端金融系統工程師與資料科學家
你現在是一位資深的全端工程師，同時具備豐富的量化金融與 AI 應用開發經驗。我們現在要打造一套「台股價值投資與動能分析 Web 系統」。

# 專案核心目標 (MVP 優先針對台股，且聚焦 Top 20 潛力股)
1. **漏斗式預先篩選 (Top 20 Screener)**：系統啟動或每日更新數據時，**第一步必須先實作一支預篩選腳本**。它要能從公開資訊中 (如 Goodinfo, 證交所 或 twstockAPI)，透過基本面條件 (例如 ROE > 15%, EPS 成長, 本益比 < 20) 直接過濾出「20 檔最值得投資的潛力股」作為系統的心臟名單。
2. **深度數據管線**：後續的「OHLCV 歷史股價」、「三大法人籌碼」、「財經新聞爬蟲」，**全部都只針對這 20 檔股票**進行深度抓取，避免浪費系統資源。
3. **防幻覺 (Anti-Hallucination) AI 新聞分析**：將爬取到的「真實新聞文本」送入 LLM (如 Gemini/OpenAI API)，指示 AI 單純作為「客觀分析師」總結並判斷情緒，絕不憑空幻想預測。
4. **全端 Web 儀表板**：提供直覺的 UI (Screener + 估值河流圖 + AI 報告)。

# 技術堆疊建議
- **前端**：Next.js (React) + Tailwind CSS + Recharts。要現代感、深色模式。
- **後端**：Python FastAPI。實作 RESTful API、背景爬蟲 (`requests`, `beautifulsoup4`, `twstock` 等)、技術指標 (`pandas-ta`)。
- **資料庫**：SQLite，儲存這 20 檔的深度資料。

# 首要任務 (Phase 1 & Phase 2 啟動指令)
請依照以下步驟直接開始實作，並幫我建立好檔案結構：
1. 建立前端 Next.js 專案 (`frontend`) 與 Tailwind 基礎設定。
2. 建立後端 Python FastAPI 專案 (`backend`) 與 `requirements.txt`。
3. **[關鍵] 撰寫第一支爬蟲腳本**：建立 `backend/scripts/pre_screen_top20.py`，實作邏輯來抓取並篩選出 20 檔符合「價值投資」條件的台股，並存入 SQLite 資料庫中 (作為 `StockMarket` 表格的種子資料)。
4. 完成後，請簡短告訴我如何同時將這兩端 (前端與 FastAPI) 跑起來測試。

我已經準備好了，請直接開始建立目錄與撰寫第一步的這支預篩選程式碼！

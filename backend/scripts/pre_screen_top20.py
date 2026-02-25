import sys
import os
import yfinance as yf
from sqlalchemy.orm import Session
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, StockMarket, FinancialData, engine, Base

# 我們將提供一個涵蓋了台灣主要權值股與熱門科技/傳產股的「種子池」(約 60 檔)。
# 腳本將會即時透過 yfinance 抓取這些公司的真實財報數據 (EPS, ROE, PE)，
# 並套用我們的「投資價值評分演算法」，最後只選出「分數最高的前 20 名」寫入資料庫！
# 建立帶有中文名稱與產業分類的種子池
POOL_STOCKS = {
    "2330": {"name": "台積電", "industry": "半導體業"}, "2454": {"name": "聯發科", "industry": "半導體業"},
    "2308": {"name": "台達電", "industry": "電子零組件業"}, "2317": {"name": "鴻海", "industry": "其他電子業"},
    "2382": {"name": "廣達", "industry": "電腦及週邊設備業"}, "3231": {"name": "緯創", "industry": "電腦及週邊設備業"},
    "3017": {"name": "奇鋐", "industry": "電腦及週邊設備業"}, "2345": {"name": "智邦", "industry": "通信網路業"},
    "2603": {"name": "長榮", "industry": "航運業"}, "2412": {"name": "中華電", "industry": "通信網路業"},
    "3045": {"name": "台灣大", "industry": "通信網路業"}, "3711": {"name": "日月光投控", "industry": "半導體業"},
    "2395": {"name": "研華", "industry": "電腦及週邊設備業"}, "1216": {"name": "統一", "industry": "食品工業"},
    "5871": {"name": "中租-KY", "industry": "其他業"}, "2379": {"name": "瑞昱", "industry": "半導體業"},
    "2303": {"name": "聯電", "industry": "半導體業"}, "6669": {"name": "緯穎", "industry": "電腦及週邊設備業"},
    "3034": {"name": "聯詠", "industry": "半導體業"}, "6415": {"name": "矽力*-KY", "industry": "半導體業"},
    "3035": {"name": "智原", "industry": "半導體業"}, "4966": {"name": "譜瑞-KY", "industry": "半導體業"},
    "3661": {"name": "世芯-KY", "industry": "半導體業"}, "2357": {"name": "華碩", "industry": "電腦及週邊設備業"},
    "3037": {"name": "欣興", "industry": "電子零組件業"}, "2353": {"name": "宏碁", "industry": "電腦及週邊設備業"},
    "2609": {"name": "陽明", "industry": "航運業"}, "2615": {"name": "萬海", "industry": "航運業"},
    "1101": {"name": "台泥", "industry": "水泥工業"}, "2002": {"name": "中鋼", "industry": "鋼鐵工業"},
    "2912": {"name": "統一超", "industry": "貿易百貨業"}, "4904": {"name": "遠傳", "industry": "通信網路業"}
}

def calculate_score(roe, eps, pe):
    score = 50
    if roe >= 15: score += 20
    elif roe >= 10: score += 10
    
    if eps >= 8: score += 15
    elif eps > 0: score += 5
    
    if 0 < pe < 15: score += 20
    elif 15 <= pe <= 25: score += 5
    elif pe > 25: score -= 10
    return min(100, max(0, score))

def setup_top_20_pool():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    print("Clearing old data to prepare for the NEW Dynamic Top 20...")
    db.query(StockMarket).delete()
    db.query(FinancialData).delete()
    
    print(f"Fetching real financial data (EPS, ROE, PE) for {len(POOL_STOCKS)} candidate stocks from yfinance...")
    scored_stocks = []
    
    for symbol in POOL_STOCKS:
        yf_symbol = f"{symbol}.TW"
        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            # yfinance mapping
            eps = info.get("trailingEps") or info.get("forwardEps") or 0
            pe = info.get("trailingPE") or info.get("forwardPE") or 0
            roe = (info.get("returnOnEquity") or 0) * 100 # yfinance returns ROE as decimal
            
            # 使用我們定義的中文名稱與分類
            name = POOL_STOCKS[symbol]["name"]
            industry = POOL_STOCKS[symbol]["industry"]
            
            if eps > 0 and pe > 0:
                score = calculate_score(roe, eps, pe)
                scored_stocks.append({
                    "symbol": symbol,
                    "name": name,
                    "industry": industry,
                    "eps": round(eps, 2),
                    "roe": round(roe, 2),
                    "pe": round(pe, 2),
                    "score": score
                })
                print(f"Scored {symbol} ({name}): Score={score}, EPS={eps}, ROE={roe}%, PE={pe}")
                
        except Exception as e:
            print(f"Could not fetch data for {symbol}: {e}")
            
    # Sort by score descending and take Top 20
    scored_stocks.sort(key=lambda x: x["score"], reverse=True)
    top_20 = scored_stocks[:20]
    
    print("\n=== THE TOP 20 HIGHEST SCORING STOCKS ===")
    for rank, s in enumerate(top_20, 1):
        print(f"#{rank} {s['symbol']} {s['name']} | Score: {s['score']} (PE: {s['pe']})")
        
        # Insert into StockMarket
        stock = StockMarket(
            symbol=s['symbol'],
            name=s['name'],
            market_type="上市",
            industry=s["industry"]
        )
        db.add(stock)
        
        # Insert Real Financial Data
        fin = FinancialData(
            symbol=s['symbol'],
            year=date.today().year,
            quarter=1,
            eps=s['eps'],
            roe=s['roe'],
            bvps=0, # Optional for MVP
            revenue=0
        )
        db.add(fin)
    
    db.commit()
    print("Successfully dynamically screened and saved Top 20 stocks to database.")
    db.close()

if __name__ == "__main__":
    setup_top_20_pool()

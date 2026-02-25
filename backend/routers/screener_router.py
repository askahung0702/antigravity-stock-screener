from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
import yfinance as yf
import pandas as pd
from database import SessionLocal, StockMarket, FinancialData, StockPrice

router = APIRouter(
    prefix="/api/screener",
    tags=["screener"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def screen_stocks(
    db: Session = Depends(get_db),
    min_eps: Optional[float] = Query(None, description="Minimum EPS"),
    min_roe: Optional[float] = Query(None, description="Minimum ROE (%)"),
    max_pe: Optional[float] = Query(None, description="Maximum P/E Ratio"),
    market_type: Optional[str] = Query(None, description="上市 or 上櫃"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    limit: int = Query(50, description="Max results")
):
    # Base query joining StockMarket and FinancialData
    query = db.query(StockMarket, FinancialData).join(
        FinancialData, StockMarket.symbol == FinancialData.symbol
    )
    
    # Apply filters dynamically
    if market_type:
        query = query.filter(StockMarket.market_type == market_type)
    if industry:
        query = query.filter(StockMarket.industry == industry)
    if min_eps is not None:
        query = query.filter(FinancialData.eps >= min_eps)
    if min_roe is not None:
        query = query.filter(FinancialData.roe >= min_roe)
        
    print(f"Executing screener query with params: EPS>={min_eps}, ROE>={min_roe}, PE<={max_pe}, Industry={industry}")    
        
    # We order by EPS descending as a default sorting strategy
    results = query.order_by(desc(FinancialData.eps)).limit(limit).all()
    print(f"Found {len(results)} base records matching DB filters.")
    
    # Build list of symbols for real-time yf batch download
    yf_symbols = []
    symbol_map = {}
    for stock, fin in results:
        yf_symbol = f"{stock.symbol}.TW" if stock.market_type == '上市' else f"{stock.symbol}.TWO"
        yf_symbols.append(yf_symbol)
        symbol_map[stock.symbol] = yf_symbol

    # Fetch real-time prices
    live_prices = {}
    if yf_symbols:
        try:
            print(f"Fetching live prices via yfinance for {len(yf_symbols)} stocks...")
            yf_data = yf.download(yf_symbols, period="1d", progress=False, threads=True)
            if not yf_data.empty and 'Close' in yf_data:
                close_data = yf_data['Close']
                if len(yf_symbols) == 1:
                    live_prices[yf_symbols[0]] = float(close_data.iloc[-1]) if not pd.isna(close_data.iloc[-1]) else 0
                else:
                    for s in yf_symbols:
                        if s in close_data and not pd.isna(close_data[s].iloc[-1]):
                            live_prices[s] = float(close_data[s].iloc[-1])
        except Exception as e:
            print(f"Failed to fetch real-time prices: {e}")
            
    output = []
    for stock, fin in results:
        yf_s = symbol_map[stock.symbol]
        price_val = live_prices.get(yf_s, 0)
        
        # Fallback to daily close in DB if live fails
        if price_val == 0:
            latest_price = db.query(StockPrice).filter(StockPrice.symbol == stock.symbol).order_by(desc(StockPrice.date)).first()
            price_val = latest_price.close if latest_price else 0
            
        pe_val = price_val / fin.eps if (fin.eps and fin.eps > 0 and price_val > 0) else 0
        
        # Apply strict API driven PE filter if requested
        if max_pe is not None and (pe_val == 0 or pe_val > max_pe):
            continue
            
        # Calculate Worthiness Rating (0-100) and Reason
        score = 50
        reasons = []
        if fin.roe >= 15:
            score += 20
            reasons.append("高ROE資優生")
        elif fin.roe >= 10:
            score += 10
            reasons.append("ROE穩定")
            
        if fin.eps >= 8:
            score += 15
            reasons.append("高獲利能力")
        elif fin.eps > 0:
            score += 5
            
        if 0 < pe_val < 15:
            score += 20
            reasons.append("估值遭低估")
        elif 15 <= pe_val <= 25:
            score += 5
            reasons.append("估值合理")
        elif pe_val > 25:
            score -= 10
            reasons.append("估值偏高需留意")
            
        rating_explanation = "、".join(reasons) + "的標的" if reasons else "一般表現"
            
        output.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "industry": stock.industry,
            "market": stock.market_type,
            "price": round(price_val, 2),
            "eps": fin.eps,
            "roe": fin.roe,
            "pe": round(pe_val, 2) if pe_val > 0 else "-",
            "score": min(100, score),
            "rating_explanation": rating_explanation
        })
        
        # ... other logic
    # Sort output dynamically by our newly calculated Investment Worthiness Score
    output.sort(key=lambda x: x["score"], reverse=True)
        
    print(f"Returning {len(output)} stocks after dynamic calculations.")
    return {"count": len(output), "results": output}

@router.get("/templates/{template_name}")
def screener_templates(template_name: str, db: Session = Depends(get_db)):
    if template_name == "high_roe_undervalued":
        # e.g., ROE > 15%, PE < 15
        return screen_stocks(db=db, min_roe=15.0, max_pe=15.0, limit=20)
    elif template_name == "turnaround":
        # e.g. EPS > 0 to simplify
        return screen_stocks(db=db, min_eps=0.5, max_pe=20.0, limit=20)
    return {"error": "Template not found"}

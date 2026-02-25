from sqlalchemy.orm import Session
from database import StockPrice, FinancialData
from sqlalchemy import desc
from typing import Dict, Any

def calculate_valuation(db: Session, symbol: str) -> Dict[str, Any]:
    # 1. Fetch latest financial data (mocked as 2025 Q3)
    fin_data = db.query(FinancialData).filter(FinancialData.symbol == symbol).order_by(desc(FinancialData.year), desc(FinancialData.quarter)).first()
    
    if not fin_data:
        return {"error": "Financial data not found for valuation"}

    # 2. Fetch latest stock prices (e.g., last 60 days to calculate PE/PB bands)
    prices = db.query(StockPrice).filter(StockPrice.symbol == symbol).order_by(desc(StockPrice.date)).limit(60).all()
    
    if not prices:
        return {"error": "Price data not found for valuation"}

    # Sort prices ascending for rendering charts
    prices.reverse()

    latest_price = prices[-1].close

    # Graham Number = sqrt(22.5 * EPS * BVPS)
    # Usually uses trailing 12 months EPS, we use our mocked EPS for demonstration
    eps = fin_data.eps
    bvps = fin_data.bvps
    
    graham_number = 0
    if eps > 0 and bvps > 0:
        graham_number = (22.5 * eps * bvps) ** 0.5
    
    # Calculate historical PE and PB for the river chart
    # A real PE river uses rolling EPS, here we use fixed recent EPS for the mocked 60 days band
    pe_river_data = []
    
    # Define arbitrary PE bands for visualization (e.g. 10x, 15x, 20x, 25x, 30x)
    pe_bands = [10, 15, 20, 25, 30]
    pb_bands = [1.0, 1.5, 2.0, 2.5, 3.0]

    for p in prices:
        current_pe = p.close / eps if eps > 0 else 0
        current_pb = p.close / bvps if bvps > 0 else 0
        
        day_data = {
            "date": p.date.strftime("%Y-%m-%d"),
            "price": p.close,
            "pe": current_pe,
            "pb": current_pb
        }
        
        # Add bands based on fixed EPS/BVPS
        for band in pe_bands:
            day_data[f"pe_band_{band}"] = eps * band
            
        for band in pb_bands:
            day_data[f"pb_band_{band}"] = bvps * band
            
        pe_river_data.append(day_data)

    current_pe = latest_price / eps if eps > 0 else 0
    
    # Valuation Status
    status = "合理 (Fair)"
    if current_pe > 0:
        if current_pe < 12:
            status = "低估 (Undervalued)"
        elif current_pe > 20:
            status = "高估 (Overvalued)"

    return {
        "symbol": symbol,
        "latest_price": latest_price,
        "eps": eps,
        "bvps": bvps,
        "graham_number": round(graham_number, 2),
        "current_pe": round(current_pe, 2),
        "valuation_status": status,
        "river_data": pe_river_data
    }

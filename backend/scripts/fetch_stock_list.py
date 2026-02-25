import sys
import os
import twstock
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import the database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, StockMarket, engine, Base

def fetch_and_store_stock_list():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    print("Fetching stock list using twstock...")
    codes = twstock.codes
    
    count = 0
    for code, info in codes.items():
        # Only care about normal stocks (上市/上櫃), we exclude warrants etc if possible.
        # twstock type provides "股票", "ETF" etc.
        if info.type == "股票" or info.type == "ETF":
            # Check if exists
            existing = db.query(StockMarket).filter(StockMarket.symbol == code).first()
            if not existing:
                stock = StockMarket(
                    symbol=code,
                    name=info.name,
                    market_type=info.market, # e.g. 上市, 上櫃
                    industry=info.group # e.g. 半導體業
                )
                db.add(stock)
                count += 1
                
    db.commit()
    print(f"Successfully added {count} new stocks to the database.")
    db.close()

if __name__ == "__main__":
    fetch_and_store_stock_list()

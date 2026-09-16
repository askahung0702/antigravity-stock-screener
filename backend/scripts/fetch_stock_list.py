import sys
import os
import twstock
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import the database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, StockMarket, utc_now
from services.pipeline_service import track_pipeline

def fetch_and_store_stock_list():
    with track_pipeline("fetch_stock_list") as stats:
        db: Session = SessionLocal()
        try:
            print("Fetching common-stock universe using twstock...")
            codes = twstock.codes
            stats.records_read = len(codes)
            count = 0
            for code, info in codes.items():
                # ETFs and other products are deliberately excluded from stock factors.
                if info.type != "股票":
                    continue
                stock = (
                    db.query(StockMarket)
                    .filter(StockMarket.symbol == code)
                    .first()
                )
                if stock is None:
                    stock = StockMarket(symbol=code, is_active=False)
                    db.add(stock)
                stock.name = info.name
                stock.market_type = info.market
                stock.industry = info.group
                stock.source = "twstock"
                stock.updated_at = utc_now()
                count += 1
            db.commit()
            stats.records_written = count
            print(f"Upserted {count} common-stock universe records.")
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

if __name__ == "__main__":
    fetch_and_store_stock_list()

import sys
import os
import requests
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time
from sqlalchemy import Column, Integer, String, Float, Date, Boolean

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, StockMarket, InstitutionalData, engine, Base

def fetch_institutional_data():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    # We will simulate fetching TWSE institutional data (三大法人買賣超), 
    # because actual TWSE scraping requires specialized logic to bypass blockers and parsing raw CSVs/JSONs.
    # In a full production app, we would use an API like FinMind or Fugle.
    # For this MVP phase build script, we create the schema and mock the entry to demonstrate the data structure.

    date_to_fetch = datetime.now().date() - timedelta(days=1)
    if date_to_fetch.weekday() > 4: # If weekend, use Friday
        date_to_fetch = date_to_fetch - timedelta(days=date_to_fetch.weekday() - 4)

    print(f"Simulating fetching institutional data for date: {date_to_fetch}")
    
    stocks = db.query(StockMarket).all()
    count = 0
    for stock in stocks:
        existing = db.query(InstitutionalData).filter(
            InstitutionalData.symbol == stock.symbol,
            InstitutionalData.date == date_to_fetch
        ).first()
        
        if not existing:
            # Fake data for demonstration purposes. In reality, requires `requests.get('https://www.twse.com.tw/fund/T86...')`
            import random
            data = InstitutionalData(
                symbol=stock.symbol,
                date=date_to_fetch,
                foreign_buy_sell=random.randint(-1000, 1000),
                investment_trust_buy_sell=random.randint(-500, 500),
                dealer_buy_sell=random.randint(-200, 200)
            )
            db.add(data)
            count += 1
            
    db.commit()
    print(f"Successfully added institutional data for {count} stocks.")
    db.close()

if __name__ == "__main__":
    fetch_institutional_data()

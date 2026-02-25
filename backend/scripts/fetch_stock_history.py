import sys
import os
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, StockMarket, StockPrice, engine, Base

def fetch_and_store_historical_data():
    db: Session = SessionLocal()
    
    # Get all Taiwan stocks
    stocks = db.query(StockMarket).all()
    
    # We will fetch only last 3 months for the MVP to avoid long wait times
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"Fetching historical data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} for {len(stocks)} stocks...")
    
    # For demonstration, we'll only do the first 50 stocks so it doesn't take forever, 
    # but in a real cron job you'd do chunks with sleep.
    limit = 50
    count = 0
    
    for stock in stocks[:limit]:
        # yfinance ticker for Taiwan stocks adds .TW for TSE, .TWO for OTC
        yf_symbol = f"{stock.symbol}.TW" if stock.market_type == '上市' else f"{stock.symbol}.TWO"
        print(f"Fetching {yf_symbol}...")
        
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            
            if df.empty:
                continue
                
            # Calculate technical indicators using pandas-ta
            # We must ensure there is enough data for indicators
            if len(df) > 30:
                # RSI 14
                df.ta.rsi(length=14, append=True)
                # MACD
                df.ta.macd(fast=12, slow=26, signal=9, append=True)
                
                # Check column names created by pandas-ta, usually 'RSI_14', 'MACD_12_26_9', etc.
                # In this basic version we will just store OHLCV to the DB as requested by schema, 
                # and technical indicators can either be stored in DB (needs schema update) 
                # or calculated on-the-fly in the API. 
                # For the MVP step, we will persist OHLCV to DB.
            
            for index, row in df.iterrows():
                # check if exists
                existing = db.query(StockPrice).filter(
                    StockPrice.symbol == stock.symbol,
                    StockPrice.date == index.date()
                ).first()
                
                if not existing:
                    price = StockPrice(
                        symbol=stock.symbol,
                        date=index.date(),
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume'])
                    )
                    db.add(price)
            
            db.commit()
            count += 1
            
            # sleep to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Failed to fetch {yf_symbol}: {e}")
            db.rollback()
            
    print(f"Successfully processed OHLCV for {count} stocks.")
    db.close()

if __name__ == "__main__":
    fetch_and_store_historical_data()

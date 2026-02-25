import sys
import os
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, Text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import SessionLocal, StockMarket, FinancialData, CompanyNews, engine, Base

def fetch_financial_and_news_data():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    print("Fetching REAL company news from Yahoo Finance Taiwan for screened Top 20 stocks...")
    
    stocks = db.query(StockMarket).all()
    count_news = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for stock in stocks:
        news_existing = db.query(CompanyNews).filter(
            CompanyNews.symbol == stock.symbol
        ).count()

        if news_existing < 3: # Let's fetch at least 3 news per stock
            try:
                # Scrape Yahoo Finance TW News
                # Yahoo Finance TW usually uses `.TW` or `.TWO` suffix, or just plain ID depending on the route.
                yf_symbol = f"{stock.symbol}.TW" if stock.market_type == '上市' else f"{stock.symbol}.TWO"
                url = f"https://tw.stock.yahoo.com/quote/{yf_symbol}/news"
                print(f"Scraping news for {stock.symbol} {stock.name}...")
                
                # Retry logic for timeout
                for retry in range(3):
                    try:
                        response = requests.get(url, headers=headers, timeout=15)
                        break
                    except requests.Timeout:
                        if retry == 2: raise
                        print("Timeout, retrying...")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Yahoo TW news links generally are inside 'a' tags with href containing 'news/'
                    # We will find the main news stream items
                    news_items = soup.find_all('a', href=True)
                    
                    fetched_for_stock = 0
                    for item in news_items:
                        href = item['href']
                        if 'news/' in href and item.text.strip() and len(item.text.strip()) > 10:
                            title = item.text.strip()
                            article_url = href if href.startswith('http') else f"https://tw.stock.yahoo.com{href}"
                            
                            # Avoid duplicates
                            existing_link = db.query(CompanyNews).filter(CompanyNews.url == article_url).first()
                            
                            if not existing_link:
                                # For MVP, we use the title as the content as well to save scraping the full article body,
                                # since Yahoo often puts sufficient summary in the title for AI to gauge sentiment.
                                news = CompanyNews(
                                    symbol=stock.symbol,
                                    publish_date=date.today(),
                                    title=title,
                                    content=f"{title} (連結: {article_url})",
                                    url=article_url,
                                    sentiment="Pending AI Analysis"
                                )
                                db.add(news)
                                count_news += 1
                                fetched_for_stock += 1
                                
                            if fetched_for_stock >= 5: # Get top 5 news
                                break
                                
            except Exception as e:
                print(f"Failed to fetch news for {stock.symbol}: {e}")
            
    db.commit()
    print(f"Added {count_news} REAL news articles for {len(stocks)} stocks.")
    db.close()

if __name__ == "__main__":
    fetch_financial_and_news_data()

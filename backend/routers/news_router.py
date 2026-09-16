from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from database import SessionLocal, CompanyNews, StockMarket
from services.ai_news_service import analyze_news

router = APIRouter(
    prefix="/api/news",
    tags=["news"]
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{symbol}")
def get_stock_news(symbol: str, db: Session = Depends(get_db)):
    raw_news_records = (
        db.query(CompanyNews)
        .filter(CompanyNews.symbol == symbol)
        .order_by(desc(CompanyNews.published_at), desc(CompanyNews.publish_date))
        .limit(25)
        .all()
    )
    news_records = []
    seen_urls = set()
    for record in raw_news_records:
        dedupe_key = record.url or f"legacy:{record.id}"
        if dedupe_key in seen_urls:
            continue
        seen_urls.add(dedupe_key)
        news_records.append(record)
        if len(news_records) >= 5:
            break
    
    if not news_records:
        return {"symbol": symbol, "news": []}
    
    stock = db.query(StockMarket).filter(StockMarket.symbol == symbol).first()
    stock_name = stock.name if stock else symbol
    results = []
    for news in news_records:
        if news.sentiment == "Pending AI Analysis" or not news.ai_summary:
            ai_result = analyze_news(news.content, stock_name)
            news.sentiment = ai_result.get("sentiment", "Neutral")
            summaries = ai_result.get("summary", [])
            news.ai_summary = json.dumps(summaries, ensure_ascii=False)
            db.commit()
        else:
            try:
                summaries = json.loads(news.ai_summary)
            except (TypeError, json.JSONDecodeError):
                summaries = [news.ai_summary] if news.ai_summary else []

        results.append({
            "id": news.id,
            "date": news.publish_date.strftime("%Y-%m-%d") if news.publish_date else None,
            "published_at": news.published_at.isoformat() if news.published_at else None,
            "title": news.title,
            "url": news.url,
            "source": news.source,
            "original_content": news.content,
            "ai_sentiment": news.sentiment,
            "ai_summary": summaries,
        })
            
    return {"symbol": symbol, "news": results}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import SessionLocal, CompanyNews
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
    # Fetch latest news from database (we mocked 1 entry per stock earlier)
    news_records = db.query(CompanyNews).filter(CompanyNews.symbol == symbol).order_by(desc(CompanyNews.publish_date)).limit(5).all()
    
    if not news_records:
        return {"symbol": symbol, "news": []}
    
    results = []
    for news in news_records:
        # Check if sentiment is pending
        if news.sentiment == "Pending AI Analysis":
            # Call AI
            ai_result = analyze_news(news.content, symbol)
            
            # Update DB with AI findings
            news.sentiment = ai_result.get("sentiment", "Neutral")
            # We can override the content or keep it. Let's append the summary to a new field if we had one, 
            # or just return it in the API response. We'll store the AI summary dynamically in the response.
            db.commit()
            
            results.append({
                "id": news.id,
                "date": news.publish_date.strftime("%Y-%m-%d"),
                "title": news.title,
                "original_content": news.content,
                "ai_sentiment": news.sentiment,
                "ai_summary": ai_result.get("summary", [])
            })
        else:
            # Already analyzed (or has static sentiment)
            results.append({
                "id": news.id,
                "date": news.publish_date.strftime("%Y-%m-%d"),
                "title": news.title,
                "original_content": news.content,
                "ai_sentiment": news.sentiment,
                "ai_summary": ["(由先前分析保留)"]
            })
            
    return {"symbol": symbol, "news": results}

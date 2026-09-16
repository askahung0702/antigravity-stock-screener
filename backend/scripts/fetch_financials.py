import json
import os
import sys
from datetime import date, datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3.util.retry import Retry

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import CompanyNews, SessionLocal, StockMarket, utc_now
from services.pipeline_service import track_pipeline


BASE_URL = "https://tw.stock.yahoo.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124 Safari/537.36"
    )
}


def _session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(HEADERS)
    return session


def _parse_datetime(value):
    if not value:
        return None
    normalized = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _json_ld_values(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _json_ld_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _json_ld_values(child)


def _article_details(session, url, fallback_title):
    response = session.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("meta", property="og:title")
    title = title_tag.get("content", "").strip() if title_tag else fallback_title
    description_tag = soup.find("meta", property="og:description") or soup.find(
        "meta", attrs={"name": "description"}
    )
    description = (
        description_tag.get("content", "").strip() if description_tag else ""
    )

    published_at = None
    published_tag = soup.find("meta", property="article:published_time")
    if published_tag:
        published_at = _parse_datetime(published_tag.get("content"))
    if published_at is None:
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag:
            published_at = _parse_datetime(time_tag.get("datetime"))

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(script.string or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        for item in _json_ld_values(payload):
            if not published_at:
                published_at = _parse_datetime(item.get("datePublished"))
            if not description:
                description = str(item.get("description") or "").strip()

    article = soup.find("article")
    paragraphs = article.find_all("p") if article else []
    body = "\n".join(
        paragraph.get_text(" ", strip=True)
        for paragraph in paragraphs
        if paragraph.get_text(" ", strip=True)
    )
    content = body[:12000] or description[:4000] or title
    return title or fallback_title, content, published_at


def _news_links(session, stock):
    suffix = ".TW" if stock.market_type == "上市" else ".TWO"
    response = session.get(
        f"{BASE_URL}/quote/{stock.symbol}{suffix}/news",
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    seen = set()
    for item in soup.find_all("a", href=True):
        href = item["href"]
        title = item.get_text(" ", strip=True)
        if "/news/" not in href or len(title) <= 10:
            continue
        url = urljoin(BASE_URL, href).split("?")[0]
        if url in seen:
            continue
        seen.add(url)
        links.append((url, title))
        if len(links) >= 5:
            break
    return links


def fetch_financial_and_news_data():
    with track_pipeline("fetch_company_news") as stats:
        db: Session = SessionLocal()
        session = _session()
        article_cache = {}
        try:
            stocks = (
                db.query(StockMarket)
                .filter(StockMarket.is_active.is_(True))
                .order_by(StockMarket.symbol)
                .all()
            )
            stats.records_read = len(stocks)
            if not stocks:
                raise RuntimeError("No active stocks are available for news ingestion")

            successful_stocks = 0
            for stock in stocks:
                try:
                    links = _news_links(session, stock)
                    for url, fallback_title in links:
                        details = article_cache.get(url)
                        if details is None:
                            details = _article_details(session, url, fallback_title)
                            article_cache[url] = details
                        title, content, published_at = details

                        record = (
                            db.query(CompanyNews)
                            .filter(
                                CompanyNews.symbol == stock.symbol,
                                CompanyNews.url == url,
                            )
                            .first()
                        )
                        if record is None:
                            record = CompanyNews(symbol=stock.symbol, url=url)
                            db.add(record)
                        record.title = title
                        record.content = content
                        record.published_at = published_at
                        record.publish_date = (
                            published_at.date() if published_at else date.today()
                        )
                        record.source = "Yahoo Taiwan"
                        record.fetched_at = utc_now()
                        if not record.sentiment:
                            record.sentiment = "Pending AI Analysis"
                        stats.records_written += 1

                    db.commit()
                    successful_stocks += 1
                    print(f"{stock.symbol}: upserted {len(links)} news records")
                except Exception as exc:
                    db.rollback()
                    print(f"Failed to fetch news for {stock.symbol}: {exc}")

            if successful_stocks == 0:
                raise RuntimeError("News ingestion failed for every active stock")
        finally:
            session.close()
            db.close()


if __name__ == "__main__":
    fetch_financial_and_news_data()

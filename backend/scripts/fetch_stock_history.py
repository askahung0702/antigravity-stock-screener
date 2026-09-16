import os
import sys
import time
from datetime import date, datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import desc
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, StockMarket, StockPrice, utc_now
from services.pipeline_service import track_pipeline


INITIAL_LOOKBACK_DAYS = 400
REVISION_LOOKBACK_DAYS = 7


def _fetch_history(stock: StockMarket, start_date: date, end_date: date):
    suffix = ".TW" if stock.market_type == "上市" else ".TWO"
    ticker = yf.Ticker(f"{stock.symbol}{suffix}")
    return ticker.history(
        start=start_date.isoformat(),
        end=end_date.isoformat(),
        auto_adjust=False,
        actions=False,
    )


def _upsert_prices(db: Session, stock: StockMarket, frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0

    dates = [index.date() for index in frame.index]
    existing = {
        row.date: row
        for row in db.query(StockPrice)
        .filter(
            StockPrice.symbol == stock.symbol,
            StockPrice.date.in_(dates),
        )
        .all()
    }

    written = 0
    for index, row in frame.iterrows():
        trade_date = index.date()
        price = existing.get(trade_date)
        if price is None:
            price = StockPrice(symbol=stock.symbol, date=trade_date)
            db.add(price)

        price.open = float(row["Open"])
        price.high = float(row["High"])
        price.low = float(row["Low"])
        price.close = float(row["Close"])
        adjusted = row.get("Adj Close")
        price.adj_close = (
            float(adjusted) if adjusted is not None and not pd.isna(adjusted) else price.close
        )
        price.volume = int(row["Volume"])
        price.source = "yfinance"
        price.fetched_at = utc_now()
        written += 1
    return written


def fetch_and_store_historical_data():
    with track_pipeline("fetch_stock_history") as stats:
        db: Session = SessionLocal()
        try:
            stocks = (
                db.query(StockMarket)
                .filter(StockMarket.is_active.is_(True))
                .order_by(StockMarket.symbol)
                .all()
            )
            stats.records_read = len(stocks)
            if not stocks:
                raise RuntimeError("No active stocks are available for price ingestion")

            processed = 0
            failed = []
            end_date = datetime.now().date() + timedelta(days=1)

            for stock in stocks:
                latest_date = (
                    db.query(StockPrice.date)
                    .filter(StockPrice.symbol == stock.symbol)
                    .order_by(desc(StockPrice.date))
                    .limit(1)
                    .scalar()
                )
                start_date = (
                    latest_date - timedelta(days=REVISION_LOOKBACK_DAYS)
                    if latest_date
                    else datetime.now().date() - timedelta(days=INITIAL_LOOKBACK_DAYS)
                )

                try:
                    frame = _fetch_history(stock, start_date, end_date)
                    written = _upsert_prices(db, stock, frame)
                    db.commit()
                    stats.records_written += written
                    processed += 1
                    print(
                        f"{stock.symbol}: upserted {written} rows "
                        f"from {start_date} to {end_date - timedelta(days=1)}"
                    )
                    time.sleep(0.5)
                except Exception as exc:
                    db.rollback()
                    failed.append(stock.symbol)
                    print(f"Failed to fetch {stock.symbol}: {exc}")

            if processed == 0:
                raise RuntimeError("Price ingestion failed for every active stock")
            if failed:
                print(f"Warning: {len(failed)} symbols failed: {', '.join(failed)}")
        finally:
            db.close()


if __name__ == "__main__":
    fetch_and_store_historical_data()

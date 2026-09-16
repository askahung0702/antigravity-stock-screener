import os
import sys
import time
from datetime import date

import yfinance as yf
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import FinancialData, SessionLocal, StockMarket, utc_now
from services.pipeline_service import parse_number, track_pipeline
from services.scoring_service import score_universe


# This remains a curated MVP universe. The UI now describes it as a watchlist,
# not as a complete Taiwan market scan.
POOL_STOCKS = {
    "2330": {"name": "台積電", "industry": "半導體業"},
    "2454": {"name": "聯發科", "industry": "半導體業"},
    "2308": {"name": "台達電", "industry": "電子零組件業"},
    "2317": {"name": "鴻海", "industry": "其他電子業"},
    "2382": {"name": "廣達", "industry": "電腦及週邊設備業"},
    "3231": {"name": "緯創", "industry": "電腦及週邊設備業"},
    "3017": {"name": "奇鋐", "industry": "電腦及週邊設備業"},
    "2345": {"name": "智邦", "industry": "通信網路業"},
    "2603": {"name": "長榮", "industry": "航運業"},
    "2412": {"name": "中華電", "industry": "通信網路業"},
    "3045": {"name": "台灣大", "industry": "通信網路業"},
    "3711": {"name": "日月光投控", "industry": "半導體業"},
    "2395": {"name": "研華", "industry": "電腦及週邊設備業"},
    "1216": {"name": "統一", "industry": "食品工業"},
    "5871": {"name": "中租-KY", "industry": "其他業"},
    "2379": {"name": "瑞昱", "industry": "半導體業"},
    "2303": {"name": "聯電", "industry": "半導體業"},
    "6669": {"name": "緯穎", "industry": "電腦及週邊設備業"},
    "3034": {"name": "聯詠", "industry": "半導體業"},
    "6415": {"name": "矽力*-KY", "industry": "半導體業"},
    "3035": {"name": "智原", "industry": "半導體業"},
    "4966": {"name": "譜瑞-KY", "industry": "半導體業"},
    "3661": {"name": "世芯-KY", "industry": "半導體業"},
    "2357": {"name": "華碩", "industry": "電腦及週邊設備業"},
    "3037": {"name": "欣興", "industry": "電子零組件業"},
    "2353": {"name": "宏碁", "industry": "電腦及週邊設備業"},
    "2609": {"name": "陽明", "industry": "航運業"},
    "2615": {"name": "萬海", "industry": "航運業"},
    "1101": {"name": "台泥", "industry": "水泥工業"},
    "2002": {"name": "中鋼", "industry": "鋼鐵工業"},
    "2912": {"name": "統一超", "industry": "貿易百貨業"},
    "4904": {"name": "遠傳", "industry": "通信網路業"},
}


def _as_percent(value):
    parsed = parse_number(value)
    return parsed * 100 if parsed is not None else None


def _fetch_info(symbol: str, attempts: int = 3):
    last_error = None
    for attempt in range(attempts):
        try:
            return yf.Ticker(f"{symbol}.TW").info
        except Exception as exc:  # yfinance raises several transport exceptions
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"yfinance failed for {symbol}: {last_error}")


def _collect_candidates():
    candidates = []
    for symbol, metadata in POOL_STOCKS.items():
        try:
            info = _fetch_info(symbol)
            eps = parse_number(info.get("trailingEps"))
            pe = parse_number(info.get("trailingPE"))

            # Do not silently mix trailing and forward values in the same field.
            if eps is None or eps <= 0 or pe is None or pe <= 0:
                print(f"Skipping {symbol}: positive trailing EPS/PE unavailable")
                continue

            candidate = {
                "symbol": symbol,
                "name": metadata["name"],
                "industry": metadata["industry"],
                "market": "上市",
                "eps": eps,
                "roe": _as_percent(info.get("returnOnEquity")),
                "bvps": parse_number(info.get("bookValue")),
                "revenue": parse_number(info.get("totalRevenue")),
                "revenue_growth": _as_percent(info.get("revenueGrowth")),
                "earnings_growth": _as_percent(info.get("earningsGrowth")),
                "debt_to_equity": parse_number(info.get("debtToEquity")),
                "free_cashflow": parse_number(info.get("freeCashflow")),
                "pe": pe,
                "pb": parse_number(info.get("priceToBook")),
                "momentum_60d": None,
                "volatility_60d": None,
                "liquidity_20d": None,
            }
            candidates.append(candidate)
            print(f"Fetched {symbol} {metadata['name']}: EPS={eps}, PE={pe}")
        except Exception as exc:
            print(f"Could not fetch {symbol}: {exc}")
    return candidates


def _save_snapshot(db: Session, candidates, top_symbols, snapshot_date: date):
    existing_stocks = {
        stock.symbol: stock for stock in db.query(StockMarket).all()
    }
    for stock in existing_stocks.values():
        stock.is_active = stock.symbol in top_symbols
        stock.updated_at = utc_now()

    for candidate in candidates:
        symbol = candidate["symbol"]
        stock = existing_stocks.get(symbol)
        if stock is None:
            stock = StockMarket(symbol=symbol)
            db.add(stock)
        stock.name = candidate["name"]
        stock.market_type = candidate["market"]
        stock.industry = candidate["industry"]
        stock.is_active = symbol in top_symbols
        stock.source = "curated_pool+yfinance"
        stock.updated_at = utc_now()

        financial = (
            db.query(FinancialData)
            .filter(
                FinancialData.symbol == symbol,
                FinancialData.as_of_date == snapshot_date,
                FinancialData.period_type == "TTM",
            )
            .first()
        )
        if financial is None:
            financial = FinancialData(
                symbol=symbol,
                as_of_date=snapshot_date,
                period_type="TTM",
            )
            db.add(financial)

        financial.year = snapshot_date.year
        financial.quarter = 0
        financial.eps = candidate["eps"]
        financial.roe = candidate["roe"]
        financial.bvps = candidate["bvps"]
        financial.revenue = candidate["revenue"]
        financial.revenue_growth = candidate["revenue_growth"]
        financial.earnings_growth = candidate["earnings_growth"]
        financial.debt_to_equity = candidate["debt_to_equity"]
        financial.free_cashflow = candidate["free_cashflow"]
        financial.pe_ratio = candidate["pe"]
        financial.price_to_book = candidate["pb"]
        financial.source = "yfinance"
        financial.fetched_at = utc_now()


def setup_top_20_pool():
    with track_pipeline("pre_screen_top20") as stats:
        candidates = _collect_candidates()
        stats.records_read = len(POOL_STOCKS)
        if len(candidates) < 20:
            raise RuntimeError(
                f"Only {len(candidates)} valid candidates were fetched; "
                "the existing active list was left unchanged."
            )

        scored = score_universe(candidates)
        top_20 = scored[:20]
        top_symbols = {item["symbol"] for item in top_20}
        snapshot_date = date.today()

        db = SessionLocal()
        try:
            _save_snapshot(db, scored, top_symbols, snapshot_date)
            db.commit()
            stats.records_written = len(scored)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        print("\n=== TOP 20 MULTI-FACTOR WATCHLIST ===")
        for rank, item in enumerate(top_20, 1):
            print(
                f"#{rank} {item['symbol']} {item['name']} | "
                f"Score={item['score']} | completeness={item['data_completeness']}"
            )
        print("Saved a versioned TTM snapshot without deleting historical data.")


if __name__ == "__main__":
    setup_top_20_pool()

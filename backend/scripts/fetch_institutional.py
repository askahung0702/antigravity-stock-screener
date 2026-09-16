import argparse
import os
import sys
from datetime import date, datetime, timedelta

import requests
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import InstitutionalData, SessionLocal, StockMarket, utc_now
from services.pipeline_service import parse_number, track_pipeline


TWSE_T86_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"
HEADERS = {"User-Agent": "AntigravityStock/1.0 data-research@example.invalid"}


def _field_index(fields, candidates):
    for index, field in enumerate(fields):
        normalized = field.replace(" ", "").replace("\u3000", "")
        if any(candidate in normalized for candidate in candidates):
            return index
    raise ValueError(f"Required TWSE field not found: {candidates}")


def _parse_twse_payload(payload, target_date: date):
    if payload.get("stat") != "OK" or not payload.get("data"):
        return None

    fields = payload["fields"]
    symbol_index = _field_index(fields, ["證券代號"])
    foreign_index = _field_index(
        fields,
        ["外陸資買賣超股數", "外資及陸資買賣超股數"],
    )
    trust_index = _field_index(fields, ["投信買賣超股數"])
    dealer_index = _field_index(fields, ["自營商買賣超股數"])

    rows = {}
    for row in payload["data"]:
        symbol = str(row[symbol_index]).strip()
        rows[symbol] = {
            "foreign_buy_sell": int(parse_number(row[foreign_index], 0)),
            "investment_trust_buy_sell": int(parse_number(row[trust_index], 0)),
            "dealer_buy_sell": int(parse_number(row[dealer_index], 0)),
        }

    response_date = payload.get("date") or target_date.strftime("%Y%m%d")
    return datetime.strptime(response_date, "%Y%m%d").date(), rows


def _fetch_twse(target_date: date):
    response = requests.get(
        TWSE_T86_URL,
        params={
            "date": target_date.strftime("%Y%m%d"),
            "selectType": "ALLBUT0999",
            "response": "json",
        },
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    return _parse_twse_payload(response.json(), target_date)


def _find_latest_available(requested_date=None, max_lookback_days=10):
    start_date = requested_date or (datetime.now().date() - timedelta(days=1))
    last_error = None
    for days_back in range(max_lookback_days + 1):
        target_date = start_date - timedelta(days=days_back)
        try:
            result = _fetch_twse(target_date)
            if result:
                return result
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
    raise RuntimeError(
        f"No TWSE institutional data found within {max_lookback_days} days: {last_error}"
    )


def fetch_institutional_data(requested_date=None):
    with track_pipeline("fetch_institutional") as stats:
        trade_date, market_rows = _find_latest_available(requested_date)
        stats.records_read = len(market_rows)

        db: Session = SessionLocal()
        try:
            stocks = (
                db.query(StockMarket)
                .filter(StockMarket.is_active.is_(True))
                .all()
            )
            written = 0
            skipped_otc = []
            for stock in stocks:
                if stock.market_type != "上市":
                    skipped_otc.append(stock.symbol)
                    continue
                values = market_rows.get(stock.symbol)
                if values is None:
                    continue

                record = (
                    db.query(InstitutionalData)
                    .filter(
                        InstitutionalData.symbol == stock.symbol,
                        InstitutionalData.date == trade_date,
                    )
                    .first()
                )
                if record is None:
                    record = InstitutionalData(
                        symbol=stock.symbol,
                        date=trade_date,
                    )
                    db.add(record)

                record.foreign_buy_sell = values["foreign_buy_sell"]
                record.investment_trust_buy_sell = values[
                    "investment_trust_buy_sell"
                ]
                record.dealer_buy_sell = values["dealer_buy_sell"]
                record.source = "TWSE_T86"
                record.is_estimated = False
                record.fetched_at = utc_now()
                written += 1

            if written == 0:
                raise RuntimeError(
                    f"TWSE returned data for {trade_date}, but none matched active stocks"
                )
            db.commit()
            stats.records_written = written
            print(f"Upserted {written} official TWSE rows for {trade_date}")
            if skipped_otc:
                print(
                    "Warning: TPEx ingestion is not implemented yet; skipped "
                    + ", ".join(skipped_otc)
                )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        help="Requested trade date in YYYY-MM-DD format; defaults to latest available.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    parsed_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else None
    fetch_institutional_data(parsed_date)

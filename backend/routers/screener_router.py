from math import sqrt
from statistics import mean, pstdev
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import FinancialData, SessionLocal, StockMarket, StockPrice
from services.scoring_service import score_universe


router = APIRouter(prefix="/api/screener", tags=["screener"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _latest_financial(db: Session, symbol: str):
    return (
        db.query(FinancialData)
        .filter(FinancialData.symbol == symbol)
        .order_by(
            desc(FinancialData.as_of_date),
            desc(FinancialData.year),
            desc(FinancialData.quarter),
            desc(FinancialData.id),
        )
        .first()
    )


def _market_metrics(db: Session, symbol: str):
    prices = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol)
        .order_by(desc(StockPrice.date))
        .limit(260)
        .all()
    )
    prices.reverse()
    if not prices:
        return {
            "price": None,
            "price_date": None,
            "momentum_60d": None,
            "volatility_60d": None,
            "liquidity_20d": None,
        }

    closes = [
        row.adj_close if row.adj_close and row.adj_close > 0 else row.close
        for row in prices
    ]
    latest_price = prices[-1].close
    momentum_60d = None
    if len(closes) >= 61 and closes[-61] > 0:
        momentum_60d = (closes[-1] / closes[-61] - 1) * 100

    returns = []
    for previous, current in zip(closes[-61:-1], closes[-60:]):
        if previous and previous > 0:
            returns.append(current / previous - 1)
    volatility_60d = (
        pstdev(returns) * sqrt(252) * 100 if len(returns) >= 20 else None
    )

    recent = prices[-20:]
    liquidity_20d = (
        mean((row.close or 0) * (row.volume or 0) for row in recent)
        if recent
        else None
    )
    return {
        "price": latest_price,
        "price_date": prices[-1].date,
        "momentum_60d": momentum_60d,
        "volatility_60d": volatility_60d,
        "liquidity_20d": liquidity_20d,
    }


def _build_universe(db: Session):
    stocks = (
        db.query(StockMarket)
        .filter(StockMarket.is_active.is_(True))
        .order_by(StockMarket.symbol)
        .all()
    )
    records = []
    for stock in stocks:
        financial = _latest_financial(db, stock.symbol)
        if financial is None:
            continue
        market = _market_metrics(db, stock.symbol)
        price = market["price"]
        eps = financial.eps
        bvps = financial.bvps
        pe = price / eps if price and eps and eps > 0 else financial.pe_ratio
        pb = (
            price / bvps
            if price and bvps and bvps > 0
            else financial.price_to_book
        )

        records.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "industry": stock.industry,
            "market": stock.market_type,
            "price": price,
            "price_date": market["price_date"],
            "eps": eps,
            "roe": financial.roe,
            "bvps": bvps,
            "revenue_growth": financial.revenue_growth,
            "earnings_growth": financial.earnings_growth,
            "debt_to_equity": financial.debt_to_equity,
            "pe": pe,
            "pb": pb,
            "momentum_60d": market["momentum_60d"],
            "volatility_60d": market["volatility_60d"],
            "liquidity_20d": market["liquidity_20d"],
            "financial_as_of": financial.as_of_date,
            "financial_period_type": financial.period_type,
            "financial_source": financial.source,
        })
    return score_universe(records)


@router.get("/")
def screen_stocks(
    db: Session = Depends(get_db),
    min_eps: Optional[float] = Query(None, description="Minimum TTM EPS"),
    min_roe: Optional[float] = Query(None, description="Minimum ROE (%)"),
    max_pe: Optional[float] = Query(None, description="Maximum trailing P/E ratio"),
    market_type: Optional[str] = Query(None, description="上市 or 上櫃"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
):
    # Score the full active universe first. Filters and limit are applied afterwards,
    # so eligible lower-EPS stocks are no longer accidentally discarded.
    universe = _build_universe(db)
    filtered = []
    for record in universe:
        if market_type and record["market"] != market_type:
            continue
        if industry and record["industry"] != industry:
            continue
        if min_eps is not None and (
            record["eps"] is None or record["eps"] < min_eps
        ):
            continue
        if min_roe is not None and (
            record["roe"] is None or record["roe"] < min_roe
        ):
            continue
        if max_pe is not None and (
            record["pe"] is None or record["pe"] <= 0 or record["pe"] > max_pe
        ):
            continue
        filtered.append(record)

    output = []
    for record in filtered[:limit]:
        output.append({
            **record,
            "price": round(record["price"], 2) if record["price"] else None,
            "pe": round(record["pe"], 2) if record["pe"] else None,
            "pb": round(record["pb"], 2) if record["pb"] else None,
            "roe": round(record["roe"], 2) if record["roe"] is not None else None,
            "momentum_60d": (
                round(record["momentum_60d"], 2)
                if record["momentum_60d"] is not None
                else None
            ),
            "volatility_60d": (
                round(record["volatility_60d"], 2)
                if record["volatility_60d"] is not None
                else None
            ),
            "price_date": (
                record["price_date"].isoformat() if record["price_date"] else None
            ),
            "financial_as_of": (
                record["financial_as_of"].isoformat()
                if record["financial_as_of"]
                else None
            ),
        })

    return {
        "count": len(output),
        "universe_count": len(universe),
        "scoring_method": "sector-aware multi-factor v1",
        "results": output,
    }


@router.get("/templates/{template_name}")
def screener_templates(template_name: str, db: Session = Depends(get_db)):
    if template_name == "high_roe_undervalued":
        return screen_stocks(
            db=db,
            min_eps=None,
            min_roe=15.0,
            max_pe=15.0,
            market_type=None,
            industry=None,
            limit=20,
        )
    if template_name == "turnaround":
        return screen_stocks(
            db=db,
            min_eps=0.01,
            min_roe=None,
            max_pe=20.0,
            market_type=None,
            industry=None,
            limit=20,
        )
    return {"error": "Template not found"}

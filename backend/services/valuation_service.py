from bisect import bisect_right
from typing import Any, Dict, List

from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import FinancialData, StockPrice


def _percentile(values: List[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def calculate_valuation(db: Session, symbol: str) -> Dict[str, Any]:
    financials = (
        db.query(FinancialData)
        .filter(FinancialData.symbol == symbol)
        .order_by(
            FinancialData.as_of_date,
            FinancialData.year,
            FinancialData.quarter,
        )
        .all()
    )
    if not financials:
        return {"error": "Financial data not found for valuation"}

    prices = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol)
        .order_by(desc(StockPrice.date))
        .limit(1260)
        .all()
    )
    if not prices:
        return {"error": "Price data not found for valuation"}
    prices.reverse()

    latest_financial = financials[-1]
    latest_price = prices[-1].close
    eps = latest_financial.eps
    bvps = latest_financial.bvps
    current_pe = latest_price / eps if eps and eps > 0 else None
    current_pb = latest_price / bvps if bvps and bvps > 0 else None
    graham_number = (
        (22.5 * eps * bvps) ** 0.5
        if eps and eps > 0 and bvps and bvps > 0
        else None
    )

    dated_financials = [
        item
        for item in financials
        if item.as_of_date is not None and item.eps is not None and item.eps > 0
    ]
    warnings = []
    if len(prices) < 756:
        warnings.append("歷史價格少於三年，估值分位的代表性不足")
    if not dated_financials:
        warnings.append("缺少具公布日期的歷史財報，河流圖暫以最新 TTM EPS 估算")
    if not bvps or bvps <= 0:
        warnings.append("缺少有效 BVPS，PB 與葛拉漢數字無法計算")

    financial_dates = [item.as_of_date for item in dated_financials]
    river_rows = []
    historical_pe_values = []
    for price in prices:
        financial = latest_financial
        if dated_financials:
            index = bisect_right(financial_dates, price.date) - 1
            if index < 0:
                continue
            financial = dated_financials[index]
        row_eps = financial.eps
        row_bvps = financial.bvps
        row_pe = price.close / row_eps if row_eps and row_eps > 0 else None
        row_pb = price.close / row_bvps if row_bvps and row_bvps > 0 else None
        if row_pe and 0 < row_pe < 200:
            historical_pe_values.append(row_pe)
        river_rows.append({
            "date": price.date.strftime("%Y-%m-%d"),
            "price": price.close,
            "pe": row_pe,
            "pb": row_pb,
            "eps_used": row_eps,
        })

    pe_bands = []
    if len(historical_pe_values) >= 60:
        for label, percentile in (
            ("P10", 0.10),
            ("P25", 0.25),
            ("P50", 0.50),
            ("P75", 0.75),
            ("P90", 0.90),
        ):
            multiple = _percentile(historical_pe_values, percentile)
            key = f"pe_band_{label.lower()}"
            pe_bands.append({
                "key": key,
                "label": f"{label} ({multiple:.1f}x)",
                "multiple": round(multiple, 2),
            })
            for row in river_rows:
                row[key] = row["eps_used"] * multiple if row["eps_used"] else None
    else:
        warnings.append("有效歷史 PE 少於 60 筆，暫不產生估值河流區間")

    valuation_status = "資料不足 (Insufficient history)"
    pe_percentile = None
    if current_pe and len(historical_pe_values) >= 60:
        below = sum(value <= current_pe for value in historical_pe_values)
        pe_percentile = below / len(historical_pe_values) * 100
        if pe_percentile <= 25:
            valuation_status = "相對偏低 (Below historical range)"
        elif pe_percentile >= 75:
            valuation_status = "相對偏高 (Above historical range)"
        else:
            valuation_status = "歷史中位區間 (Historical mid-range)"

    return {
        "symbol": symbol,
        "latest_price": latest_price,
        "price_date": prices[-1].date.isoformat(),
        "financial_as_of": (
            latest_financial.as_of_date.isoformat()
            if latest_financial.as_of_date
            else None
        ),
        "financial_period_type": latest_financial.period_type,
        "eps": eps,
        "bvps": bvps,
        "graham_number": round(graham_number, 2) if graham_number else None,
        "current_pe": round(current_pe, 2) if current_pe else None,
        "current_pb": round(current_pb, 2) if current_pb else None,
        "pe_percentile": round(pe_percentile, 1) if pe_percentile is not None else None,
        "valuation_status": valuation_status,
        "pe_bands": pe_bands,
        "river_data": river_rows,
        "data_quality_warnings": warnings,
    }

from collections import defaultdict
from statistics import mean
from typing import Any, Dict, Iterable, List


FACTOR_WEIGHTS = {
    "quality": 0.25,
    "growth": 0.25,
    "valuation": 0.20,
    "momentum": 0.20,
    "risk_liquidity": 0.10,
}

METRIC_DIRECTIONS = {
    "roe": True,
    "debt_to_equity": False,
    "revenue_growth": True,
    "earnings_growth": True,
    "pe": False,
    "pb": False,
    "momentum_60d": True,
    "volatility_60d": False,
    "liquidity_20d": True,
}

FACTOR_METRICS = {
    "quality": ("roe", "debt_to_equity"),
    "growth": ("revenue_growth", "earnings_growth"),
    "valuation": ("pe", "pb"),
    "momentum": ("momentum_60d",),
    "risk_liquidity": ("volatility_60d", "liquidity_20d"),
}

FACTOR_LABELS = {
    "quality": "品質",
    "growth": "成長",
    "valuation": "相對估值",
    "momentum": "價格動能",
    "risk_liquidity": "風險與流動性",
}


def _valid_metric(metric: str, value: Any) -> bool:
    if value is None:
        return False
    if metric in {"pe", "pb", "liquidity_20d"} and value <= 0:
        return False
    if metric in {"debt_to_equity", "volatility_60d"} and value < 0:
        return False
    return True


def _percentile_map(
    records: Iterable[Dict[str, Any]], metric: str, higher_is_better: bool
) -> Dict[str, float]:
    values = [
        (record["symbol"], float(record[metric]))
        for record in records
        if _valid_metric(metric, record.get(metric))
    ]
    if not values:
        return {}
    if len(values) == 1:
        return {values[0][0]: 50.0}

    sorted_values = sorted(values, key=lambda item: item[1])
    positions: Dict[float, List[int]] = defaultdict(list)
    for position, (_, value) in enumerate(sorted_values):
        positions[value].append(position)

    result = {}
    denominator = len(values) - 1
    for symbol, value in values:
        average_position = mean(positions[value])
        percentile = average_position / denominator * 100
        result[symbol] = percentile if higher_is_better else 100 - percentile
    return result


def _metric_scores(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    scores: Dict[str, Dict[str, float]] = {
        record["symbol"]: {} for record in records
    }
    industries: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        industries[record.get("industry") or "未分類"].append(record)

    for metric, higher_is_better in METRIC_DIRECTIONS.items():
        global_scores = _percentile_map(records, metric, higher_is_better)
        for symbol, score in global_scores.items():
            scores[symbol][metric] = score

        # Use sector-relative ranks only when the peer group is large enough.
        for group in industries.values():
            if len(group) < 4:
                continue
            sector_scores = _percentile_map(group, metric, higher_is_better)
            for symbol, score in sector_scores.items():
                scores[symbol][metric] = score
    return scores


def score_universe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return explainable, sector-aware multi-factor scores for a stock universe."""
    if not records:
        return []

    metric_scores = _metric_scores(records)
    scored_records = []
    total_metric_count = len(METRIC_DIRECTIONS)

    for source_record in records:
        record = dict(source_record)
        symbol = record["symbol"]
        factor_scores = {}
        available_metric_count = 0

        for factor, metrics in FACTOR_METRICS.items():
            available_scores = []
            for metric in metrics:
                if _valid_metric(metric, record.get(metric)):
                    available_metric_count += 1
                    if metric in metric_scores[symbol]:
                        available_scores.append(metric_scores[symbol][metric])
            factor_scores[factor] = (
                round(mean(available_scores), 2) if available_scores else 50.0
            )

        total_score = sum(
            factor_scores[factor] * weight
            for factor, weight in FACTOR_WEIGHTS.items()
        )
        completeness = available_metric_count / total_metric_count
        strongest = sorted(
            factor_scores.items(), key=lambda item: item[1], reverse=True
        )[:2]
        reasons = [
            f"{FACTOR_LABELS[factor]}較強"
            for factor, value in strongest
            if value >= 60
        ]
        if completeness < 0.6:
            reasons.append("資料完整度偏低")
        if not reasons:
            reasons.append("綜合表現中性")

        record["score"] = round(total_score, 1)
        record["factor_scores"] = factor_scores
        record["data_completeness"] = round(completeness, 2)
        record["rating_explanation"] = "、".join(reasons)
        scored_records.append(record)

    return sorted(scored_records, key=lambda item: item["score"], reverse=True)

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from routers.screener_router import screen_stocks


def record(symbol, score, pe):
    return {
        "symbol": symbol,
        "name": symbol,
        "industry": "測試",
        "market": "上市",
        "price": 100.0,
        "price_date": date(2026, 9, 15),
        "eps": 5.0,
        "roe": 15.0,
        "bvps": 20.0,
        "pe": pe,
        "pb": 2.0,
        "momentum_60d": 5.0,
        "volatility_60d": 20.0,
        "score": score,
        "factor_scores": {},
        "data_completeness": 1.0,
        "rating_explanation": "測試",
        "financial_as_of": date(2026, 6, 30),
        "financial_period_type": "TTM",
        "financial_source": "test",
    }


class ScreenerRouterTests(unittest.TestCase):
    @patch(
        "routers.screener_router._build_universe",
        return_value=[record("HIGH_SCORE_EXPENSIVE", 90, 30), record("ELIGIBLE", 80, 10)],
    )
    def test_filter_is_applied_before_limit(self, _mock_universe):
        result = screen_stocks(
            db=object(),
            min_eps=None,
            min_roe=None,
            max_pe=15,
            market_type=None,
            industry=None,
            limit=1,
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["symbol"], "ELIGIBLE")


if __name__ == "__main__":
    unittest.main()

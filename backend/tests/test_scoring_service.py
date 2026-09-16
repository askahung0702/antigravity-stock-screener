import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from services.scoring_service import score_universe


class ScoringServiceTests(unittest.TestCase):
    def _record(self, symbol, **overrides):
        record = {
            "symbol": symbol,
            "industry": "測試產業",
            "eps": 1,
            "roe": 10,
            "debt_to_equity": 50,
            "revenue_growth": 10,
            "earnings_growth": 10,
            "pe": 15,
            "pb": 2,
            "momentum_60d": 5,
            "volatility_60d": 20,
            "liquidity_20d": 1_000_000,
        }
        record.update(overrides)
        return record

    def test_absolute_eps_does_not_distort_cross_company_score(self):
        records = [
            self._record("A", eps=1),
            self._record("B", eps=100),
        ]
        result = {item["symbol"]: item for item in score_universe(records)}
        self.assertEqual(result["A"]["score"], result["B"]["score"])

    def test_dominant_factor_profile_ranks_first(self):
        strong = self._record(
            "STRONG",
            roe=30,
            debt_to_equity=10,
            revenue_growth=40,
            earnings_growth=50,
            pe=10,
            pb=1,
            momentum_60d=25,
            volatility_60d=10,
            liquidity_20d=10_000_000,
        )
        weak = self._record(
            "WEAK",
            roe=2,
            debt_to_equity=200,
            revenue_growth=-20,
            earnings_growth=-30,
            pe=40,
            pb=8,
            momentum_60d=-25,
            volatility_60d=60,
            liquidity_20d=100_000,
        )
        result = score_universe([weak, strong])
        self.assertEqual(result[0]["symbol"], "STRONG")
        self.assertGreater(result[0]["score"], result[1]["score"])

    def test_missing_metrics_lower_confidence_not_crash_score(self):
        result = score_universe([
            self._record(
                "MISSING",
                revenue_growth=None,
                earnings_growth=None,
                debt_to_equity=None,
                pb=None,
            )
        ])[0]
        self.assertLess(result["data_completeness"], 1)
        self.assertIsInstance(result["score"], float)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from datetime import date
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = BACKEND_DIR / "scripts"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from fetch_institutional import _parse_twse_payload


class InstitutionalParserTests(unittest.TestCase):
    def test_parses_official_t86_columns_by_name(self):
        payload = {
            "stat": "OK",
            "date": "20260915",
            "fields": [
                "證券代號",
                "外陸資買賣超股數(不含外資自營商)",
                "投信買賣超股數",
                "自營商買賣超股數",
            ],
            "data": [["2330", "1,200", "-300", "50"]],
        }
        trade_date, rows = _parse_twse_payload(payload, date(2026, 9, 15))
        self.assertEqual(trade_date, date(2026, 9, 15))
        self.assertEqual(rows["2330"]["foreign_buy_sell"], 1200)
        self.assertEqual(rows["2330"]["investment_trust_buy_sell"], -300)
        self.assertEqual(rows["2330"]["dealer_buy_sell"], 50)


if __name__ == "__main__":
    unittest.main()

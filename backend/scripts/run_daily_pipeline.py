import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from fetch_financials import fetch_financial_and_news_data
from fetch_institutional import fetch_institutional_data
from fetch_stock_history import fetch_and_store_historical_data
from pre_screen_top20 import setup_top_20_pool


def run_daily_pipeline(include_prescreen=False, skip_news=False):
    jobs = []
    if include_prescreen:
        jobs.append(("pre_screen_top20", setup_top_20_pool))
    jobs.extend([
        ("fetch_stock_history", fetch_and_store_historical_data),
        ("fetch_institutional", fetch_institutional_data),
    ])
    if not skip_news:
        jobs.append(("fetch_company_news", fetch_financial_and_news_data))

    failures = []
    for job_name, job in jobs:
        print(f"\n=== Running {job_name} ===")
        try:
            job()
        except Exception as exc:
            failures.append((job_name, str(exc)))
            print(f"FAILED {job_name}: {exc}")

    if failures:
        print("\nDaily pipeline completed with failures:")
        for job_name, error in failures:
            print(f"- {job_name}: {error}")
        return 1

    print("\nDaily pipeline completed successfully.")
    return 0


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-prescreen",
        action="store_true",
        help="Refresh the curated universe and TTM fundamentals (recommended weekly).",
    )
    parser.add_argument(
        "--skip-news",
        action="store_true",
        help="Skip Yahoo Taiwan news ingestion.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(
        run_daily_pipeline(
            include_prescreen=args.include_prescreen,
            skip_news=args.skip_news,
        )
    )

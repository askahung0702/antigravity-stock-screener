from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from database import PipelineRun, SessionLocal, utc_now


@dataclass
class PipelineStats:
    records_read: int = 0
    records_written: int = 0


@contextmanager
def track_pipeline(job_name: str) -> Iterator[PipelineStats]:
    """Persist a durable success/failure record for one ingestion job."""
    tracking_db = SessionLocal()
    run = PipelineRun(job_name=job_name, status="running")
    tracking_db.add(run)
    tracking_db.commit()
    tracking_db.refresh(run)
    stats = PipelineStats()

    try:
        yield stats
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)[:4000]
        raise
    else:
        run.status = "success"
    finally:
        run.records_read = stats.records_read
        run.records_written = stats.records_written
        run.finished_at = utc_now()
        tracking_db.commit()
        tracking_db.close()


def parse_number(value, default=None):
    """Parse API values that may contain commas, percent signs, or blanks."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value

    normalized = str(value).replace(",", "").replace("%", "").strip()
    if not normalized or normalized in {"-", "--", "N/A", "nan", "None"}:
        return default
    try:
        return float(normalized)
    except (TypeError, ValueError):
        return default

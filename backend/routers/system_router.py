from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from database import (
    CompanyNews,
    FinancialData,
    InstitutionalData,
    PipelineRun,
    SessionLocal,
    StockMarket,
    StockPrice,
)


router = APIRouter(prefix="/api/system", tags=["system"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/pipeline-status")
def pipeline_status(db: Session = Depends(get_db)):
    job_names = [
        row[0]
        for row in db.query(PipelineRun.job_name).distinct().order_by(PipelineRun.job_name)
    ]
    latest_runs = []
    for job_name in job_names:
        run = (
            db.query(PipelineRun)
            .filter(PipelineRun.job_name == job_name)
            .order_by(desc(PipelineRun.started_at))
            .first()
        )
        latest_runs.append({
            "job_name": run.job_name,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "records_read": run.records_read,
            "records_written": run.records_written,
            "error_message": run.error_message,
        })

    return {
        "active_stock_count": db.query(StockMarket)
        .filter(StockMarket.is_active.is_(True))
        .count(),
        "latest_price_date": db.query(func.max(StockPrice.date)).scalar(),
        "latest_financial_as_of": db.query(func.max(FinancialData.as_of_date)).scalar(),
        "latest_institutional_date": db.query(func.max(InstitutionalData.date))
        .filter(InstitutionalData.is_estimated.is_(False))
        .scalar(),
        "latest_news_date": db.query(func.max(CompanyNews.publish_date)).scalar(),
        "latest_runs": latest_runs,
    }

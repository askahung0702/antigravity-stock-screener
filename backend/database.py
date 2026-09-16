import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BACKEND_DIR / "stock_analysis.db"
SQLALCHEMY_DATABASE_URL = os.getenv(
    "STOCK_DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH.as_posix()}",
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class StockMarket(Base):
    __tablename__ = "stock_market"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, unique=True, nullable=False)
    name = Column(String)
    market_type = Column(String)  # 上市 / 上櫃
    industry = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    source = Column(String, default="unknown")
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class StockPrice(Base):
    __tablename__ = "stock_price"
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_stock_price_symbol_date"),)

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(Integer)
    source = Column(String, default="unknown")
    fetched_at = Column(DateTime, default=utc_now)


class InstitutionalData(Base):
    __tablename__ = "institutional_data"
    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_institutional_symbol_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    foreign_buy_sell = Column(Integer)
    investment_trust_buy_sell = Column(Integer)
    dealer_buy_sell = Column(Integer)
    source = Column(String, default="unknown")
    is_estimated = Column(Boolean, default=False, nullable=False)
    fetched_at = Column(DateTime, default=utc_now)


class FinancialData(Base):
    __tablename__ = "financial_data"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "as_of_date",
            "period_type",
            name="uq_financial_symbol_asof_period",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    year = Column(Integer)
    quarter = Column(Integer)
    period_type = Column(String, default="reported")  # reported / TTM / forward
    as_of_date = Column(Date, index=True)
    eps = Column(Float)
    roe = Column(Float)
    bvps = Column(Float)
    revenue = Column(Float)
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    debt_to_equity = Column(Float)
    free_cashflow = Column(Float)
    pe_ratio = Column(Float)
    price_to_book = Column(Float)
    source = Column(String, default="unknown")
    fetched_at = Column(DateTime, default=utc_now)


class CompanyNews(Base):
    __tablename__ = "company_news"
    __table_args__ = (UniqueConstraint("symbol", "url", name="uq_news_symbol_url"),)

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    publish_date = Column(Date, index=True)
    published_at = Column(DateTime, index=True)
    title = Column(String)
    content = Column(Text)
    url = Column(String)
    sentiment = Column(String)
    ai_summary = Column(Text)
    source = Column(String, default="unknown")
    fetched_at = Column(DateTime, default=utc_now)


class PipelineRun(Base):
    __tablename__ = "pipeline_run"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, index=True, nullable=False)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime)
    status = Column(String, index=True, default="running", nullable=False)
    records_read = Column(Integer, default=0)
    records_written = Column(Integer, default=0)
    error_message = Column(Text)


LEGACY_COLUMNS = {
    "stock_market": {
        "is_active": "BOOLEAN DEFAULT 1",
        "source": "VARCHAR DEFAULT 'legacy'",
        "updated_at": "DATETIME",
    },
    "stock_price": {
        "adj_close": "FLOAT",
        "source": "VARCHAR DEFAULT 'legacy'",
        "fetched_at": "DATETIME",
    },
    "institutional_data": {
        "source": "VARCHAR DEFAULT 'legacy'",
        "is_estimated": "BOOLEAN DEFAULT 1",
        "fetched_at": "DATETIME",
    },
    "financial_data": {
        "period_type": "VARCHAR DEFAULT 'legacy'",
        "as_of_date": "DATE",
        "revenue_growth": "FLOAT",
        "earnings_growth": "FLOAT",
        "debt_to_equity": "FLOAT",
        "free_cashflow": "FLOAT",
        "pe_ratio": "FLOAT",
        "price_to_book": "FLOAT",
        "source": "VARCHAR DEFAULT 'legacy'",
        "fetched_at": "DATETIME",
    },
    "company_news": {
        "published_at": "DATETIME",
        "ai_summary": "TEXT",
        "source": "VARCHAR DEFAULT 'legacy'",
        "fetched_at": "DATETIME",
    },
}


LEGACY_UNIQUE_INDEXES = {
    "uq_stock_price_symbol_date": ("stock_price", "symbol, date"),
    "uq_institutional_symbol_date": ("institutional_data", "symbol, date"),
    "uq_financial_symbol_asof_period": (
        "financial_data",
        "symbol, as_of_date, period_type",
    ),
}


def _ensure_legacy_schema() -> None:
    """Add nullable metadata columns without deleting or rewriting legacy rows."""
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        for table_name, columns in LEGACY_COLUMNS.items():
            existing = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
            }
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )

        connection.execute(
            text("UPDATE stock_market SET is_active = 1 WHERE is_active IS NULL")
        )
        connection.execute(
            text(
                "UPDATE institutional_data "
                "SET is_estimated = 1 WHERE is_estimated IS NULL"
            )
        )

        for index_name, (table_name, column_list) in LEGACY_UNIQUE_INDEXES.items():
            try:
                connection.execute(
                    text(
                        f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} "
                        f"ON {table_name} ({column_list})"
                    )
                )
            except SQLAlchemyError as exc:
                print(f"Warning: could not create {index_name}: {exc}")


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_legacy_schema()


initialize_database()

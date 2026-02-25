from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./stock_analysis.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 股票清單
class StockMarket(Base):
    __tablename__ = "stock_market"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, unique=True)
    name = Column(String)
    market_type = Column(String) # TSE (上市) / OTC (上櫃)
    industry = Column(String)

# 歷史股價
class StockPrice(Base):
    __tablename__ = "stock_price"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)

class InstitutionalData(Base):
    __tablename__ = "institutional_data"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(Date, index=True)
    foreign_buy_sell = Column(Integer)
    investment_trust_buy_sell = Column(Integer)
    dealer_buy_sell = Column(Integer)

from sqlalchemy import Text

class FinancialData(Base):
    __tablename__ = "financial_data"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    year = Column(Integer)
    quarter = Column(Integer)
    eps = Column(Float)
    roe = Column(Float)
    bvps = Column(Float)
    revenue = Column(Float)

class CompanyNews(Base):
    __tablename__ = "company_news"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    publish_date = Column(Date, index=True)
    title = Column(String)
    content = Column(Text)
    url = Column(String)
    sentiment = Column(String)

Base.metadata.create_all(bind=engine)

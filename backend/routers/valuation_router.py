from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from services.valuation_service import calculate_valuation

router = APIRouter(
    prefix="/api/valuation",
    tags=["valuation"]
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{symbol}")
def get_valuation(symbol: str, db: Session = Depends(get_db)):
    result = calculate_valuation(db, symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

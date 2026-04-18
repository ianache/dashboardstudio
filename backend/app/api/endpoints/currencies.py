from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/currencies", tags=["currencies"])

DEFAULT_CURRENCIES = [
    {"id": "cur-usd",     "code": "USD", "symbol": "US$", "name": "United States Dollar"},
    {"id": "cur-pen-sol", "code": "PEN", "symbol": "S/",  "name": "Sol Peruano"},
]


@router.get("/", response_model=List[schemas.CurrencyResponse])
async def list_currencies(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """List all active currencies. Seeds defaults if table is empty."""
    currencies = db.query(models.Currency).filter(models.Currency.is_active == True).all()

    if not currencies:
        for c in DEFAULT_CURRENCIES:
            db.add(models.Currency(**c))
        db.commit()
        currencies = db.query(models.Currency).filter(models.Currency.is_active == True).all()

    return currencies

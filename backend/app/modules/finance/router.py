from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finance import FinanceTransaction, TransactionType
from app.modules.finance.schemas import FinanceSummaryOut, TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(db: Session = Depends(get_db)):
    return db.query(FinanceTransaction).all()


@router.post("/transactions", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    tx = FinanceTransaction(**payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/summary", response_model=FinanceSummaryOut)
def get_summary(db: Session = Depends(get_db)):
    income = (
        db.query(func.coalesce(func.sum(FinanceTransaction.amount), 0))
        .filter(FinanceTransaction.type == TransactionType.INCOME)
        .scalar()
    )
    expense = (
        db.query(func.coalesce(func.sum(FinanceTransaction.amount), 0))
        .filter(FinanceTransaction.type == TransactionType.EXPENSE)
        .scalar()
    )
    income = Decimal(income)
    expense = Decimal(expense)
    return FinanceSummaryOut(total_income=income, total_expense=expense, net_profit=income - expense)

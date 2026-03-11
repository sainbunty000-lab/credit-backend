from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import date

from services.banking_service import analyze_banking


# ======================================================
# TRANSACTION SCHEMA
# ======================================================

class Transaction(BaseModel):

    date: str = Field(..., description="Transaction date (dd/mm/yy)")
    description: str = Field(..., description="Transaction narration")

    credit: float = Field(
        default=0,
        ge=0,
        description="Credit amount"
    )

    debit: float = Field(
        default=0,
        ge=0,
        description="Debit amount"
    )

    balance: float = Field(
        default=0,
        description="Account balance after transaction"
    )


# ======================================================
# REQUEST BODY
# ======================================================

class BankingInput(BaseModel):

    transactions: List[Transaction]


# ======================================================
# ROUTER
# ======================================================

bank_router = APIRouter(
    prefix="/banking",
    tags=["Bank Statement Analysis"]
)


# ======================================================
# FULL BANKING ANALYSIS
# ======================================================

@bank_router.post("/full-analysis")

def banking_full_analysis(data: BankingInput):

    try:

        transactions = [txn.dict() for txn in data.transactions]

        result = analyze_banking(transactions)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Banking analysis error: {str(e)}"
        )

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List

from services.banking_service import analyze_banking
from services.banking_parser import parse_banking_file


# ======================================================
# TRANSACTION SCHEMA
# ======================================================

class Transaction(BaseModel):

    date: str = Field(..., description="Transaction date")

    description: str = Field(
        default="",
        description="Transaction narration"
    )

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
        description="Account balance"
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
# MANUAL JSON ANALYSIS
# ======================================================

@bank_router.post("/manual-analysis")

async def banking_manual_analysis(data: BankingInput):

    try:

        transactions = [txn.dict() for txn in data.transactions]

        result = analyze_banking(transactions)

        return {
            "status": "success",
            "source": "manual_input",
            "transactions_analyzed": len(transactions),
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Banking analysis error: {str(e)}"
        )


# ======================================================
# FILE UPLOAD ANALYSIS (PDF BANK STATEMENT)
# ======================================================

@bank_router.post("/upload-statement")

async def banking_file_analysis(file: UploadFile = File(...)):

    try:

        file_bytes = await file.read()

        transactions = parse_banking_file(file_bytes)

        if not transactions:

            raise HTTPException(
                status_code=400,
                detail="No transactions detected in file"
            )

        result = analyze_banking(transactions)

        return {
            "status": "success",
            "source": "file_upload",
            "file_name": file.filename,
            "transactions_extracted": len(transactions),
            "data": result
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Bank statement processing error: {str(e)}"
        )


# ======================================================
# HEALTH CHECK
# ======================================================

@bank_router.get("/health")

def banking_health():

    return {
        "service": "banking_analysis",
        "status": "running"
    }

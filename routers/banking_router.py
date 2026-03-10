from fastapi import APIRouter
from services.banking_service import analyze_banking

bank_router = APIRouter()

@bank_router.post("/full-analysis")
def banking_full_analysis(data: dict):

    transactions = data.get("transactions", [])

    result = analyze_banking(transactions)

    return result

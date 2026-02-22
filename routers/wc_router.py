from fastapi import APIRouter
from services.wc_service import (
    calculate_working_capital_detailed,
    calculate_agri_eligibility
)

router = APIRouter(prefix="/wc", tags=["Working Capital"])

@router.post("/detailed")
def wc_detailed(data: dict):
    return calculate_working_capital_detailed(data)

@router.post("/agri")
def agri_calculation(data: dict):
    return calculate_agri_eligibility(data)

from fastapi import APIRouter
from services.wc_service import calculate_working_capital

router = APIRouter()

@router.post("/wc/calculate")
def wc_calculation(data: dict):
    return calculate_working_capital(data)

from fastapi import APIRouter
from services.agriculture_service import calculate_agriculture

router = APIRouter(prefix="/agriculture", tags=["Agriculture"])

@router.post("/calculate")
def agri_calculate(data: dict):
    return calculate_agriculture(data)

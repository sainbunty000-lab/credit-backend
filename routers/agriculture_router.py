from fastapi import APIRouter
from services.agriculture_service import calculate_agri_logic

agri_router = APIRouter()

@agri_router.post("/calculate")
def agriculture_calculate(data: dict):

    result = calculate_agri_logic(
        data["documented_income"],
        data["tax"],
        data["undocumented_income_monthly"],
        data["emi_monthly"]
    )

    return result

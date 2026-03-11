from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agriculture_service import calculate_agri_logic


# ======================================================
# REQUEST SCHEMA
# ======================================================

class AgricultureInput(BaseModel):

    documented_income: float = Field(
        default=0,
        ge=0,
        description="Annual documented income"
    )

    tax: float = Field(
        default=0,
        ge=0,
        description="Annual tax paid"
    )

    undocumented_income_monthly: float = Field(
        default=0,
        ge=0,
        description="Monthly undocumented income"
    )

    emi_monthly: float = Field(
        default=0,
        ge=0,
        description="Existing monthly EMI"
    )


# ======================================================
# ROUTER
# ======================================================

agri_router = APIRouter(
    prefix="/agriculture",
    tags=["Agriculture Loan Analysis"]
)


# ======================================================
# CALCULATE ELIGIBILITY
# ======================================================

@agri_router.post("/calculate")

def agriculture_calculate(data: AgricultureInput):

    try:

        result = calculate_agri_logic(

            data.documented_income,

            data.tax,

            data.undocumented_income_monthly,

            data.emi_monthly

        )

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Calculation error: {str(e)}"
        )

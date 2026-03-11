from pydantic import BaseModel, Field
from typing import Optional, Dict


# ======================================================
# CREATE CAM REPORT
# ======================================================

class CAMCreate(BaseModel):

    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Customer full name"
    )

    wc_data: Optional[Dict] = Field(
        default_factory=dict,
        description="Working Capital analysis output"
    )

    agri_data: Optional[Dict] = Field(
        default_factory=dict,
        description="Agriculture eligibility analysis"
    )

    banking_data: Optional[Dict] = Field(
        default_factory=dict,
        description="Bank statement analysis"
    )

    loan_amount: Optional[int] = Field(
        default=0,
        ge=0,
        description="Requested loan amount"
    )

    analyst_name: Optional[str] = Field(
        default="System",
        max_length=100,
        description="Credit analyst name"
    )

    class Config:
        schema_extra = {
            "example": {
                "customer_name": "Rahul Sharma",
                "loan_amount": 2500000,
                "analyst_name": "Credit Team"
            }
        }


# ======================================================
# UPDATE CAM REPORT
# ======================================================

class CAMUpdate(BaseModel):

    wc_data: Optional[Dict] = Field(
        default=None,
        description="Updated WC analysis"
    )

    agri_data: Optional[Dict] = Field(
        default=None,
        description="Updated agriculture analysis"
    )

    banking_data: Optional[Dict] = Field(
        default=None,
        description="Updated banking analysis"
    )

    loan_amount: Optional[int] = Field(
        default=None,
        ge=0,
        description="Updated loan request"
    )

    credit_grade: Optional[str] = Field(
        default=None,
        max_length=5,
        description="Credit risk grade"
    )

    remarks: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Credit analyst remarks"
    )

    status: Optional[str] = Field(
        default=None,
        description="CAM status (Draft / Under Review / Approved / Rejected)"
    )


# ======================================================
# FINAL SUBMISSION
# ======================================================

class CAMSubmit(BaseModel):

    credit_grade: str = Field(
        ...,
        max_length=5,
        description="Final credit grade"
    )

    remarks: Optional[str] = Field(
        default="",
        max_length=1000,
        description="Final decision remarks"
    )

    approved_limit: Optional[int] = Field(
        default=None,
        ge=0,
        description="Approved loan limit"
    )

    decision: Optional[str] = Field(
        default="Approved",
        description="Final decision (Approved / Rejected / Refer)"
    )

    class Config:
        schema_extra = {
            "example": {
                "credit_grade": "A",
                "remarks": "Financials strong. Limit approved.",
                "approved_limit": 2000000,
                "decision": "Approved"
            }
        }

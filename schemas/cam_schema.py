from pydantic import BaseModel
from typing import Optional, Dict


class CAMCreate(BaseModel):

    customer_name: str
    wc_data: Optional[Dict] = {}
    agri_data: Optional[Dict] = {}
    banking_data: Optional[Dict] = {}

    loan_amount: Optional[int] = 0
    analyst_name: Optional[str] = "System"


class CAMUpdate(BaseModel):

    wc_data: Optional[Dict] = None
    agri_data: Optional[Dict] = None
    banking_data: Optional[Dict] = None

    loan_amount: Optional[int] = None
    credit_grade: Optional[str] = None
    remarks: Optional[str] = None


class CAMSubmit(BaseModel):

    credit_grade: str
    remarks: Optional[str] = ""

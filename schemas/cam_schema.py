from pydantic import BaseModel
from typing import Optional, Dict


class CAMCreate(BaseModel):
    customer_name: str
    wc_data: Optional[Dict] = {}
    agri_data: Optional[Dict] = {}
    banking_data: Optional[Dict] = {}


class CAMUpdate(BaseModel):
    wc_data: Optional[Dict] = None
    agri_data: Optional[Dict] = None
    banking_data: Optional[Dict] = None

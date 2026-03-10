from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

# ==========================================
# IMPORT SERVICES
# ==========================================

from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic
from services.agriculture_service import calculate_agri_logic
from services.banking_parser import parse_banking_file


# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(title="Credit Analysis API")


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/")
def root():
    return {"status": "API Running"}


# ==========================================
# WORKING CAPITAL ANALYSIS
# ==========================================

@app.post("/wc-analysis")
async def wc_analysis(file: UploadFile = File(...)) -> Dict[str, Any]:

    file_bytes = await file.read()

    parsed_data = parse_financial_file(file_bytes, file.filename)

    wc_result = calculate_wc_logic(parsed_data)

    return {
        "parser": parsed_data,
        "wc_analysis": wc_result
    }


# ==========================================
# AGRICULTURE ELIGIBILITY
# ==========================================

@app.post("/agriculture-analysis")
async def agriculture_analysis(data: Dict[str, Any]):

    result = calculate_agri_logic(data)

    return result


# ==========================================
# BANK STATEMENT ANALYSIS
# ==========================================

@app.post("/bank-analysis")
async def bank_analysis(file: UploadFile = File(...)):

    file_bytes = await file.read()

    result = parse_banking_file(file_bytes, file.filename)

    return result

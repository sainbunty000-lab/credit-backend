from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic
from services.agriculture_service import calculate_agri_logic
from services.banking_parser import parse_banking_file
from services.banking_service import analyze_banking

# ==========================
# APP INITIALIZATION
# ==========================

app = FastAPI(
    title="WC / Agri Calculator",
    version="2.0.0",
)

# ==========================
# REQUEST MODELS
# ==========================

class BankingAnalyzeRequest(BaseModel):
    transactions: List[Dict[str, Any]]

# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# WORKING CAPITAL UPLOAD
# ==========================

@app.post("/wc/upload-dual")
async def wc_upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):
    try:
        bs_bytes = await balance_sheet.read()
        pl_bytes = await profit_loss.read()

        bs_data = parse_financial_file(bs_bytes, balance_sheet.filename)
        pl_data = parse_financial_file(pl_bytes, profit_loss.filename)

        combined_data = {**bs_data, **pl_data}
        calculations = calculate_wc_logic(combined_data)

        return {
            **combined_data,
            **calculations,
            "success": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==========================
# WORKING CAPITAL MANUAL
# ==========================

@app.post("/wc/manual-calc")
async def wc_manual_calc(data: dict):
    try:
        result = calculate_wc_logic(data)
        return {
            **data,
            **result,
            "success": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ==========================
# AGRICULTURE
# ==========================

@app.post("/agriculture/calculate")
async def agri_calc(data: dict):
    return calculate_agri_logic(
        data.get("documented_income", 0),
        data.get("tax", 0),
        data.get("undocumented_income_monthly", 0),
        data.get("emi_monthly", 0),
        data.get("tenure_years", 5),
        data.get("interest_rate", 12)
    )

# ==========================
# BANKING UPLOAD
# ==========================

@app.post("/banking/upload")
async def banking_upload(file: UploadFile = File(...)):
    file_bytes = await file.read()
    transactions = parse_banking_file(file_bytes, file.filename)
    return {"transactions": transactions}

# ==========================
# BANKING ANALYZE
# ==========================

@app.post("/banking/analyze")
async def banking_analyze(data: dict):
    transactions = data.get("transactions", [])
    return analyze_banking(transactions)

# ==========================
# HEALTH CHECK
# ==========================

@app.get("/")
def health():
    return {"status": "Backend Active"}

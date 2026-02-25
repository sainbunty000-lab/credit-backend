from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic
from services.agriculture_service import calculate_agri_logic
from services.banking_service import analyze_banking
from services.banking_parser import parse_banking_file

app = FastAPI(
    title="WC / Agri Calculator (Dhanush)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

 @app.post("/wc/upload")
async def wc_upload(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()

        # 1️⃣ Parse file
        parsed_data = parse_financial_file(file_bytes, file.filename)

        # 2️⃣ Run WC calculations
        calculations = calculate_wc_logic(parsed_data)

        # 3️⃣ Merge into ONE clean response
        response = {
            **parsed_data,
            **calculations,
            "analysis_type": "working_capital",
            "success": True
        }

        return response

    except Exception as e:
        return {
            "success": False,
            "error": "WC Parsing Failed",
            "message": str(e)
        }
        
@app.post("/wc/calculate")
async def wc_calculate(data: dict):
    try:
        result = calculate_wc_logic(data)

        return {
            **data,
            **result,
            "analysis_type": "manual_working_capital",
            "success": True
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Manual Calculation Failed",
            "message": str(e)
        }

@app.post("/wc/manual-calc")
async def wc_manual_calc(data: dict):
    return calculate_wc_logic(data)
    
@app.post("/agriculture/calculate")
async def agri_calc(data: dict):
    return calculate_agri_logic(
        data.get("documented_income", 0),
        data.get("tax", 0),
        data.get("undocumented_income_monthly", 0),
        data.get("emi_monthly", 0)
    )

@app.post("/banking/upload")
async def banking_upload(file: UploadFile = File(...)):
    try:
        parsed = parse_banking_file(file.file, file.filename)
        return {"transactions": parsed}
    except Exception as e:
        return {
            "error": "Banking file parsing failed",
            "message": str(e)
        }

@app.post("/banking/analyze")
async def banking_analyze(data: dict):
    transactions = data.get("transactions", [])
    months_count = data.get("months_count", 1)

    return analyze_banking(transactions, months_count)

@app.get("/")
def health():
    return {"status": "Railway Backend Active"}

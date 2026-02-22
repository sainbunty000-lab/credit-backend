from fastapi import APIRouter, UploadFile, File
from parsing.financial_parser import extract_financial_values
from services.wc_service import calculate_wc_eligibility

router = APIRouter(prefix="/wc")

@router.post("/parse-and-calculate")
async def process_wc_document(file: UploadFile = File(...)):
    # 1. Mocking OCR engine call (ocr_engine.py)
    # raw_data = ocr_engine.extract_tables(file)
    raw_data = {"Turnover": 1000000, "Current Assets": 400000, "Trade Payables": 150000}

    # 2. Normalize via Dictionary
    standardized = extract_financial_values(raw_data)

    # 3. Calculate using locked formulas
    calculation = calculate_wc_eligibility(
        current_assets=standardized["current_assets"],
        current_liabilities=standardized["current_liabilities"],
        annual_sales=standardized["annual_sales"]
    )

    return {
        "extracted_values": standardized,
        "calculation": calculation
    }

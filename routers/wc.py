from fastapi import APIRouter, UploadFile, File

from parsing.financial_parser import parse_financial_file
from services.accounting_dictionary import extract_financial_values
from services.wc_service import calculate_wc_eligibility

router = APIRouter(prefix="/wc")


@router.post("/upload-dual")
async def process_wc_documents(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    # -----------------------------------------
    # Parse Balance Sheet
    # -----------------------------------------
    bs_values = parse_financial_file(
        balance_sheet.file,
        balance_sheet.filename
    )

    # -----------------------------------------
    # Parse Profit & Loss
    # -----------------------------------------
    pl_values = parse_financial_file(
        profit_loss.file,
        profit_loss.filename
    )

    # -----------------------------------------
    # Merge extracted values
    # -----------------------------------------
    raw_data = {**bs_values, **pl_values}

    # -----------------------------------------
    # Normalize using accounting dictionary
    # -----------------------------------------
    standardized = extract_financial_values(raw_data)

    # -----------------------------------------
    # Calculate WC eligibility
    # -----------------------------------------
    calculation = calculate_wc_eligibility(
        current_assets=standardized.get("current_assets", 0),
        current_liabilities=standardized.get("current_liabilities", 0),
        annual_sales=standardized.get("annual_sales", 0)
    )

    return {
        "success": True,
        "extracted_values": standardized,
        "calculations": calculation
    }

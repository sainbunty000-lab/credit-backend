from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict

from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic


wc_router = APIRouter(
    prefix="/wc",
    tags=["Working Capital Analysis"]
)


# --------------------------------------------------
# FILE TYPE VALIDATION
# --------------------------------------------------

ALLOWED_TYPES = ["pdf", "xlsx", "xls", "csv"]


def validate_file(filename: str):
    ext = filename.split(".")[-1].lower()

    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}"
        )


# --------------------------------------------------
# DUAL FILE UPLOAD (Balance Sheet + P&L)
# --------------------------------------------------

@wc_router.post("/upload-dual")
async def wc_upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    try:

        validate_file(balance_sheet.filename)
        validate_file(profit_loss.filename)

        bs_bytes = await balance_sheet.read()
        pl_bytes = await profit_loss.read()

        # Parse both files
        bs_data = parse_financial_file(bs_bytes, balance_sheet.filename)
        pl_data = parse_financial_file(pl_bytes, profit_loss.filename)

        # Merge inputs
        merged_inputs = {
            **bs_data.get("inputs", {}),
            **pl_data.get("inputs", {})
        }

        merged_calc = {
            **bs_data.get("calculations", {}),
            **pl_data.get("calculations", {})
        }

        merged_data = {
            "inputs": merged_inputs,
            "calculations": merged_calc
        }

        result = calculate_wc_logic(merged_data)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )


# --------------------------------------------------
# SINGLE FILE UPLOAD
# --------------------------------------------------

@wc_router.post("/upload-single")
async def wc_upload_single(file: UploadFile = File(...)):

    try:

        validate_file(file.filename)

        file_bytes = await file.read()

        parsed_data = parse_financial_file(file_bytes, file.filename)

        result = calculate_wc_logic(parsed_data)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )


# --------------------------------------------------
# MANUAL CALCULATION
# --------------------------------------------------

@wc_router.post("/manual-calc")
async def wc_manual_calc(data: Dict):

    try:

        # Convert manual JSON → parser format
        payload = {
            "inputs": data,
            "calculations": {}
        }

        result = calculate_wc_logic(payload)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Calculation error: {str(e)}"
        )

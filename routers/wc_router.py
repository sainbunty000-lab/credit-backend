from fastapi import APIRouter, UploadFile, File
from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic

wc_router = APIRouter()


@wc_router.post("/upload-dual")
async def wc_upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    # ===============================
    # READ FILES
    # ===============================

    bs_bytes = await balance_sheet.read()
    pl_bytes = await profit_loss.read()

    # ===============================
    # PARSE FILES
    # ===============================

    bs_data = parse_financial_file(bs_bytes, balance_sheet.filename)
    pl_data = parse_financial_file(pl_bytes, profit_loss.filename)

    # ===============================
    # MERGE INPUT DATA
    # ===============================

    merged_inputs = {
        **bs_data.get("inputs", {}),
        **pl_data.get("inputs", {})
    }

    merged_data = {
        "inputs": merged_inputs,
        "calculations": {}
    }

    # ===============================
    # RUN WC CALCULATION
    # ===============================

    result = calculate_wc_logic(merged_data)

    return result


@wc_router.post("/manual-calc")
async def wc_manual_calc(data: dict):

    result = calculate_wc_logic(data)

    return result

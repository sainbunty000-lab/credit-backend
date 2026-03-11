from fastapi import APIRouter, UploadFile, File
from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic

wc_router = APIRouter()


@wc_router.post("/upload-dual")
async def wc_upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    bs_bytes = await balance_sheet.read()
    pl_bytes = await profit_loss.read()

    bs_data = parse_financial_file(bs_bytes, balance_sheet.filename)
    pl_data = parse_financial_file(pl_bytes, profit_loss.filename)

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

    return result


@wc_router.post("/manual-calc")
async def wc_manual_calc(data: dict):

    # convert manual JSON → parser structure
    payload = {
        "inputs": data,
        "calculations": {}
    }

    result = calculate_wc_logic(payload)

    return result

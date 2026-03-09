from fastapi import APIRouter, UploadFile, File

from services.parser import parse_financial_file
from services.wc_service import calculate_wc_logic

router = APIRouter(prefix="/wc")


@router.post("/upload-dual")
async def upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    bs_data = parse_financial_file(
        await balance_sheet.read(),
        balance_sheet.filename
    )

    pl_data = parse_financial_file(
        await profit_loss.read(),
        profit_loss.filename
    )

    merged = {**bs_data, **pl_data}

    result = calculate_wc_logic(merged)

    return result

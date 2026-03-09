from fastapi import APIRouter, UploadFile, File
from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic

router = APIRouter(prefix="/wc", tags=["Working Capital"])


@router.post("/upload-dual")
async def upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    try:

        # READ FILES
        bs_bytes = await balance_sheet.read()
        pl_bytes = await profit_loss.read()

        # PARSE FILES
        bs_data = parse_financial_file(bs_bytes, balance_sheet.filename)
        pl_data = parse_financial_file(pl_bytes, profit_loss.filename)

        # MERGE EXTRACTION
        extracted = {}

        if bs_data:
            extracted.update(bs_data)

        if pl_data:
            extracted.update(pl_data)

        # RUN WC ENGINE
        analysis = calculate_wc_logic(extracted)

        return {
            **extracted,
            **analysis,
            "success": True
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

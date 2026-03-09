from fastapi import APIRouter, UploadFile, File
from services.wc_service import calculate_wc_logic
from services.wc_parser import parse_financial_file

router = APIRouter(prefix="/wc", tags=["Working Capital"])


# =====================================================
# WORKING CAPITAL ANALYSIS (DUAL FILE UPLOAD)
# =====================================================

@router.post("/upload-dual")
async def upload_dual_files(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
):

    try:

        # =====================================
        # PARSE BALANCE SHEET
        # =====================================

        bs_data = parse_financial_file(
            await balance_sheet.read(),
            balance_sheet.filename
        )


        # =====================================
        # PARSE PROFIT & LOSS
        # =====================================

        pl_data = parse_financial_file(
            await profit_loss.read(),
            profit_loss.filename
        )


        # =====================================
        # MERGE EXTRACTED DATA
        # =====================================

        extracted = {}

        if bs_data:
            extracted.update(bs_data)

        if pl_data:
            extracted.update(pl_data)


        # =====================================
        # RUN WC ENGINE
        # =====================================

        calculations = calculate_wc_logic(extracted)


        # =====================================
        # FINAL RESPONSE
        # =====================================

        return {
            "extracted_values": extracted,
            "analysis": calculations,
            "success": True
        }


    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

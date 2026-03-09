from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from services.parser import parse_financial_file
from services.wc_service import calculate_wc_logic


router = APIRouter(
    prefix="/wc",
    tags=["Working Capital"]
)


# ==========================================================
# WORKING CAPITAL EXTRACTION + CALCULATION
# ==========================================================

@router.post("/upload-dual")
async def upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...)
) -> Dict[str, Any]:

    try:

        # --------------------------------------------------
        # READ FILES
        # --------------------------------------------------

        bs_bytes = await balance_sheet.read()
        pl_bytes = await profit_loss.read()


        # --------------------------------------------------
        # PARSE FILES (CSV / Excel / PDF / OCR / Image)
        # --------------------------------------------------

        bs_data = parse_financial_file(
            bs_bytes,
            balance_sheet.filename
        )

        pl_data = parse_financial_file(
            pl_bytes,
            profit_loss.filename
        )


        # --------------------------------------------------
        # MERGE FINANCIAL VALUES
        # --------------------------------------------------

        merged: Dict[str, Any] = {}

        if bs_data:
            merged.update(bs_data)

        if pl_data:
            merged.update(pl_data)


        # --------------------------------------------------
        # RUN WORKING CAPITAL MODEL
        # --------------------------------------------------

        result = calculate_wc_logic(merged)


        # --------------------------------------------------
        # FINAL RESPONSE (Frontend Compatible)
        # --------------------------------------------------

        response = {

            "success": True,

            "current_assets": result.get("current_assets", 0),
            "current_liabilities": result.get("current_liabilities", 0),

            "inventory": merged.get("inventory", 0),
            "receivables": merged.get("receivables", 0),

            "nwc": result.get("nwc", 0),
            "current_ratio": result.get("current_ratio", 0),
            "wc_turnover": result.get("wc_turnover", 0),

            "drawing_power": result.get("drawing_power", 0),
            "mpbf_limit": result.get("mpbf_limit", 0),

            "liquidity_score": result.get("liquidity_score", 0),
            "status": result.get("status", "Not Eligible")
        }

        return response


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Working Capital extraction failed: {str(e)}"
        )

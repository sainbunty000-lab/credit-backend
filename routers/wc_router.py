from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Dict

from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic
from services.wc_required_fields import WC_REQUIRED_INPUT_FIELDS
from services.wc_missing import find_missing_fields_present_only


wc_router = APIRouter(
    prefix="/wc",
    tags=["Working Capital Analysis"]
)

# --------------------------------------------------
# FILE TYPE VALIDATION
# --------------------------------------------------

ALLOWED_TYPES = ["pdf", "xlsx", "xls", "csv", "jpg", "jpeg", "png"]


def validate_file(filename: str):
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


# --------------------------------------------------
# DUAL FILE UPLOAD (Balance Sheet + P&L)
# --------------------------------------------------

@wc_router.post("/upload-dual")
async def wc_upload_dual(
    balance_sheet: UploadFile = File(...),
    profit_loss: UploadFile = File(...),
    unit_override: str | None = Form(default=None),
    debug: bool = Form(default=False),
):
    try:
        validate_file(balance_sheet.filename)
        validate_file(profit_loss.filename)

        bs_bytes = await balance_sheet.read()
        pl_bytes = await profit_loss.read()

        # Parse both files
        bs_data = parse_financial_file(bs_bytes, balance_sheet.filename, unit_override=unit_override, debug=debug)
        pl_data = parse_financial_file(pl_bytes, profit_loss.filename, unit_override=unit_override, debug=debug)

        # Merge inputs/calculations
        merged_inputs = {**bs_data.get("inputs", {}), **pl_data.get("inputs", {})}
        merged_calc = {**bs_data.get("calculations", {}), **pl_data.get("calculations", {})}
        merged_data = {"inputs": merged_inputs, "calculations": merged_calc}

        result = calculate_wc_logic(merged_data)

        # Missing keys (0 is allowed)
        missing_fields, present_fields = find_missing_fields_present_only(merged_inputs, WC_REQUIRED_INPUT_FIELDS)

        resp = {
            "status": "success",
            "data": result,
            "missing_fields": missing_fields,
            "missing_fields_count": len(missing_fields),
            "present_fields": present_fields,
            "manual_template": {k: 0 for k in missing_fields},
        }

        if debug:
            resp["debug"] = {
                "balance_sheet": bs_data.get("debug", {}),
                "profit_loss": pl_data.get("debug", {}),
                "merged": {
                    "extracted_keys_count": len(merged_inputs),
                    "extracted_keys": sorted(list(merged_inputs.keys())),
                },
            }

        return resp

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# --------------------------------------------------
# SINGLE FILE UPLOAD
# --------------------------------------------------

@wc_router.post("/upload-single")
async def wc_upload_single(
    file: UploadFile = File(...),
    unit_override: str | None = Form(default=None),
    debug: bool = Form(default=False),
):
    try:
        validate_file(file.filename)

        file_bytes = await file.read()

        parsed_data = parse_financial_file(file_bytes, file.filename, unit_override=unit_override, debug=debug)
        result = calculate_wc_logic(parsed_data)

        inputs = parsed_data.get("inputs", {})
        missing_fields, present_fields = find_missing_fields_present_only(inputs, WC_REQUIRED_INPUT_FIELDS)

        resp = {
            "status": "success",
            "data": result,
            "missing_fields": missing_fields,
            "missing_fields_count": len(missing_fields),
            "present_fields": present_fields,
            "manual_template": {k: 0 for k in missing_fields},
        }

        if debug:
            resp["debug"] = parsed_data.get("debug", {})

        return resp

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# --------------------------------------------------
# MANUAL CALCULATION
# --------------------------------------------------

@wc_router.post("/manual-calc")
async def wc_manual_calc(data: Dict):
    try:
        payload = {"inputs": data, "calculations": {}}
        result = calculate_wc_logic(payload)

        missing_fields, present_fields = find_missing_fields_present_only(data, WC_REQUIRED_INPUT_FIELDS)

        return {
            "status": "success",
            "data": result,
            "missing_fields": missing_fields,
            "missing_fields_count": len(missing_fields),
            "present_fields": present_fields,
            "manual_template": {k: 0 for k in missing_fields},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

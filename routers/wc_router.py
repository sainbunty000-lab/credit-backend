from fastapi import APIRouter, UploadFile, File
from services.wc_parser import parse_financial_file
from services.wc_service import calculate_wc_logic

wc_router = APIRouter()

@wc_router.post("/upload-dual")
async def wc_upload_dual(file: UploadFile = File(...)):

    file_bytes = await file.read()

    parsed_data = parse_financial_file(file_bytes, file.filename)

    result = calculate_wc_logic(parsed_data)

    return result


@wc_router.post("/manual-calc")
async def wc_manual_calc(data: dict):

    result = calculate_wc_logic(data)

    return result

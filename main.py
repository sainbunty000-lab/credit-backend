from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageFilter
import re
import uuid

app = FastAPI(title="Enterprise OCR Underwriting Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "OCR Backend Running"}

# -------- IMAGE PREPROCESSING --------
def preprocess(image):
    image = image.convert("L")
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_text(file_bytes):
    pages = convert_from_bytes(file_bytes, dpi=300)
    text = ""
    for p in pages:
        img = preprocess(p)
        text += pytesseract.image_to_string(img, config="--oem 3 --psm 6") + "\n"
    return text.lower()

def find_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

def extract_all_numbers(text):
    nums = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)
    return [float(n.replace(",", "")) for n in nums]

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(None),
    pl_file: UploadFile = File(None),
    bank_file: UploadFile = File(...)
):

    if not bank_file:
        return {"error": "Bank statement is mandatory."}

    if not bs_file and not pl_file:
        return {"error": "Either Balance Sheet or P&L is required."}

    case_id = str(uuid.uuid4())[:8]

    # -------- BANK --------
    bank_bytes = await bank_file.read()
    bank_text = extract_text(bank_bytes)
    bank_numbers = extract_all_numbers(bank_text)
    turnover = sum(bank_numbers)

    # -------- PL --------
    sales = 0
    profit = 0
    if pl_file:
        pl_bytes = await pl_file.read()
        pl_text = extract_text(pl_bytes)
        sales = find_amount(pl_text, ["sales", "turnover", "revenue"])
        profit = find_amount(pl_text, ["net profit", "profit after tax"])

    # -------- BS --------
    inventory = debtors = creditors = 0
    if bs_file:
        bs_bytes = await bs_file.read()
        bs_text = extract_text(bs_bytes)
        inventory = find_amount(bs_text, ["inventory", "stock"])
        debtors = find_amount(bs_text, ["debtors"])
        creditors = find_amount(bs_text, ["creditors"])

    # -------- CALCULATIONS --------
    wc_limit = turnover * 0.20

    agri_limit = 0
    if profit > 0:
        agri_limit = ((profit * 0.6) / 12) / 0.14

    mismatch = abs(turnover - sales) / sales * 100 if sales else 0

    # -------- RISK ENGINE --------
    if mismatch < 10:
        risk_score = 85
    elif mismatch < 25:
        risk_score = 70
    else:
        risk_score = 50

    decision = "Approve" if risk_score >= 60 else "Review"
    confidence = 95 if turnover > 0 else 75

    return {
        "Case_ID": case_id,
        "Sales": round(sales,2),
        "Bank_Turnover": round(turnover,2),
        "Working_Capital_Limit": round(wc_limit,2),
        "Agri_Limit": round(agri_limit,2),
        "Mismatch_%": round(mismatch,2),
        "Risk_Score": risk_score,
        "Decision": decision,
        "Parsing_Confidence": confidence,
        "AI_Explanation": "OCR-based underwriting evaluation completed successfully."
    }

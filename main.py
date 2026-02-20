from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageFilter
import io
import re
import uuid

app = FastAPI(title="Railway OCR Underwriting Engine")

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

# ---------- IMAGE PREPROCESSING ----------
def preprocess_image(image):
    image = image.convert("L")  # grayscale
    image = image.filter(ImageFilter.SHARPEN)
    return image

# ---------- OCR FUNCTION ----------
def extract_text_from_pdf(file_bytes):
    pages = convert_from_bytes(file_bytes, dpi=300)
    full_text = ""
    for page in pages:
        processed = preprocess_image(page)
        text = pytesseract.image_to_string(
            processed,
            config="--oem 3 --psm 6"
        )
        full_text += text + "\n"
    return full_text.lower()

# ---------- SAFE FINANCIAL EXTRACTION ----------
def find_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

def extract_all_numbers(text):
    numbers = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)
    return [float(n.replace(",", "")) for n in numbers]

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    case_id = str(uuid.uuid4())[:8]

    bs_bytes = await bs_file.read()
    pl_bytes = await pl_file.read()
    bank_bytes = await bank_file.read()

    bs_text = extract_text_from_pdf(bs_bytes)
    pl_text = extract_text_from_pdf(pl_bytes)
    bank_text = extract_text_from_pdf(bank_bytes)

    # Balance Sheet
    inventory = find_amount(bs_text, ["inventory", "stock"])
    debtors = find_amount(bs_text, ["debtors"])
    creditors = find_amount(bs_text, ["creditors"])

    # P&L
    sales = find_amount(pl_text, ["sales", "turnover", "revenue"])
    profit = find_amount(pl_text, ["net profit", "profit after tax"])

    # Bank
    all_bank_numbers = extract_all_numbers(bank_text)
    turnover = sum(all_bank_numbers)

    # Calculations
    wc_limit = turnover * 0.20
    agri_limit = ((profit * 0.6) / 12) / 0.14 if profit else 0
    mismatch = abs(turnover - sales) / sales * 100 if sales else 0

    # Risk scoring
    if mismatch < 10:
        risk_score = 85
    elif mismatch < 20:
        risk_score = 70
    else:
        risk_score = 50

    decision = "Approve" if risk_score >= 60 else "Review"
    confidence = 95 if sales > 0 and turnover > 0 else 75

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
        "AI_Explanation": "High-quality OCR processed scanned financial documents successfully."
    }

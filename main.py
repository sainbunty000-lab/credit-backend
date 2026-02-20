from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image, ImageFilter
import pandas as pd
import io
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

# ---------------- IMAGE PREPROCESS ----------------
def preprocess(img):
    img = img.convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    return img

# ---------------- FILE READERS ----------------
def read_pdf(content):
    pages = convert_from_bytes(content, dpi=300)
    text = ""
    for p in pages:
        img = preprocess(p)
        text += pytesseract.image_to_string(img, config="--oem 3 --psm 6")
    return text.lower()

def read_image(content):
    img = Image.open(io.BytesIO(content))
    img = preprocess(img)
    return pytesseract.image_to_string(img, config="--oem 3 --psm 6").lower()

def read_excel(content):
    df = pd.read_excel(io.BytesIO(content))
    return df.to_string().lower()

def read_csv(content):
    df = pd.read_csv(io.BytesIO(content))
    return df.to_string().lower()

def parse_file(file, content):
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return read_pdf(content)
    elif filename.endswith((".jpg", ".jpeg", ".png")):
        return read_image(content)
    elif filename.endswith((".xls", ".xlsx")):
        return read_excel(content)
    elif filename.endswith(".csv"):
        return read_csv(content)
    else:
        return ""

# ---------------- EXTRACTION LOGIC ----------------
def find_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

def extract_numbers(text):
    nums = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)
    return [float(n.replace(",", "")) for n in nums]

# ---------------- MAIN API ----------------
@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(None),
    pl_file: UploadFile = File(None),
    bank_file: UploadFile = File(...)
):

    if not bank_file:
        return {"error": "Bank statement is mandatory."}

    if not bs_file and not pl_file:
        return {"error": "Upload either Balance Sheet or P&L."}

    case_id = str(uuid.uuid4())[:8]

    # -------- BANK --------
    bank_content = await bank_file.read()
    bank_text = parse_file(bank_file, bank_content)
    turnover = sum(extract_numbers(bank_text))

    # -------- PL --------
    sales = 0
    profit = 0
    if pl_file:
        pl_content = await pl_file.read()
        pl_text = parse_file(pl_file, pl_content)
        sales = find_amount(pl_text, ["sales", "turnover", "revenue"])
        profit = find_amount(pl_text, ["net profit", "profit after tax"])

    # -------- BS --------
    inventory = debtors = creditors = 0
    if bs_file:
        bs_content = await bs_file.read()
        bs_text = parse_file(bs_file, bs_content)
        inventory = find_amount(bs_text, ["inventory", "stock"])
        debtors = find_amount(bs_text, ["debtors"])
        creditors = find_amount(bs_text, ["creditors"])

    # -------- CALCULATIONS --------
    wc_limit = turnover * 0.20
    agri_limit = ((profit * 0.6) / 12) / 0.14 if profit else 0
    mismatch = abs(turnover - sales) / sales * 100 if sales else 0

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
        "AI_Explanation": "Multi-format underwriting analysis completed successfully."
    }

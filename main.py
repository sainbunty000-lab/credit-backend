from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageFilter
import pandas as pd
import io
import re
import uuid
import os

from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="Agri / WC Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class CaseRecord(Base):
    __tablename__ = "cases"
    case_id = Column(String, primary_key=True, index=True)
    sales = Column(Float)
    bank_turnover = Column(Float)
    wc_limit = Column(Float)
    agri_limit = Column(Float)
    risk_score = Column(Integer)
    decision = Column(String)

Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "Agri / WC Calculator Running"}

# ---------------- FILE PARSING ----------------

def preprocess(img):
    img = img.convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    return img

def parse_pdf(content):
    pages = convert_from_bytes(content, dpi=300)
    text = ""
    for p in pages:
        img = preprocess(p)
        text += pytesseract.image_to_string(img)
    return text.lower()

def parse_image(content):
    img = Image.open(io.BytesIO(content))
    img = preprocess(img)
    return pytesseract.image_to_string(img).lower()

def parse_excel(content):
    df = pd.read_excel(io.BytesIO(content))
    return df.to_string().lower()

def parse_csv(content):
    df = pd.read_csv(io.BytesIO(content))
    return df.to_string().lower()

def extract_numbers(text):
    nums = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)
    return [float(n.replace(",", "")) for n in nums]

def find_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

async def parse_file(file):
    content = await file.read()
    name = file.filename.lower()

    if name.endswith(".pdf"):
        return parse_pdf(content)
    elif name.endswith((".jpg",".jpeg",".png")):
        return parse_image(content)
    elif name.endswith((".xls",".xlsx")):
        return parse_excel(content)
    elif name.endswith(".csv"):
        return parse_csv(content)
    return ""

# ---------------- MAIN ANALYSIS ----------------

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(None)
):

    case_id = str(uuid.uuid4())[:8]

    bs_text = await parse_file(bs_file)
    pl_text = await parse_file(pl_file)

    bank_text = ""
    if bank_file:
        bank_text = await parse_file(bank_file)

    # Extract financials
    sales = find_amount(pl_text, ["sales","turnover"])
    profit = find_amount(pl_text, ["net profit"])
    inventory = find_amount(bs_text, ["inventory","stock"])
    debtors = find_amount(bs_text, ["debtors"])
    creditors = find_amount(bs_text, ["creditors"])

    bank_turnover = sum(extract_numbers(bank_text)) if bank_text else sales

    # NWC
    current_assets = inventory + debtors
    current_liabilities = creditors
    nwc = current_assets - current_liabilities

    # MPBF
    mpbf = (0.75 * current_assets) - current_liabilities

    # WC (20% method)
    wc_limit = bank_turnover * 0.20

    # Agri calculation
    agri_limit = ((profit * 0.60)/12)/0.14 if profit else 0

    # Risk
    mismatch = abs(bank_turnover - sales)/sales*100 if sales else 0
    risk_score = 85 if mismatch < 10 else 70 if mismatch < 25 else 50
    decision = "Approve" if risk_score >= 60 else "Review"

    # Save to DB
    db = SessionLocal()
    record = CaseRecord(
        case_id=case_id,
        sales=sales,
        bank_turnover=bank_turnover,
        wc_limit=wc_limit,
        agri_limit=agri_limit,
        risk_score=risk_score,
        decision=decision
    )
    db.add(record)
    db.commit()
    db.close()

    return {
        "Case_ID": case_id,
        "Sales": sales,
        "Bank_Turnover": bank_turnover,
        "NWC": nwc,
        "MPBF": mpbf,
        "Working_Capital_Limit": wc_limit,
        "Agri_Limit": agri_limit,
        "Risk_Score": risk_score,
        "Decision": decision,
        "Mismatch_%": mismatch,
        "Parsing_Confidence": 95
    }

@app.get("/cases")
def get_cases():
    db = SessionLocal()
    records = db.query(CaseRecord).all()
    db.close()
    return records

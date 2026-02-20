from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd
import io
import re
import uuid
import os

app = FastAPI(title="Agri / WC Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATABASE SETUP ----------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300
    )
else:
    engine = create_engine("sqlite:///./local.db")

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class CaseRecord(Base):
    __tablename__ = "cases"
    case_id = Column(String, primary_key=True)
    sales = Column(Float)
    wc_limit = Column(Float)
    agri_limit = Column(Float)
    risk_score = Column(Integer)
    decision = Column(String)

Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"status": "Agri / WC Calculator Running"}

# ---------------- FILE PARSING ----------------

def extract_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

async def parse_file(file):
    content = await file.read()
    name = file.filename.lower()

    if name.endswith((".xls", ".xlsx")):
        df = pd.read_excel(io.BytesIO(content))
        return df.to_string().lower()

    elif name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
        return df.to_string().lower()

    else:
        return content.decode(errors="ignore").lower()

# ---------------- ANALYSIS ----------------

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(None)
):

    case_id = str(uuid.uuid4())[:8]

    bs_text = await parse_file(bs_file)
    pl_text = await parse_file(pl_file)

    sales = extract_amount(pl_text, ["sales", "turnover"])
    net_profit = extract_amount(pl_text, ["net profit"])
    inventory = extract_amount(bs_text, ["inventory", "stock"])
    debtors = extract_amount(bs_text, ["debtors"])
    creditors = extract_amount(bs_text, ["creditors"])

    current_assets = inventory + debtors
    current_liabilities = creditors
    nwc = current_assets - current_liabilities
    current_ratio = (current_assets / current_liabilities) if current_liabilities else 0
    mpbf = (0.75 * current_assets) - current_liabilities
    wc_limit = sales * 0.20 if sales else 0
    agri_limit = ((net_profit * 0.60)/12)/0.14 if net_profit else 0

    risk_score = 80
    if current_ratio < 1:
        risk_score -= 20
    if net_profit <= 0:
        risk_score -= 20

    decision = "Approve" if risk_score >= 60 else "Review"

    memo = f"""
    Turnover assessed at {sales}.
    Net Working Capital: {nwc}.
    Current Ratio: {round(current_ratio,2)}.
    MPBF (Tandon II): {mpbf}.
    WC (20% method): {wc_limit}.
    Agriculture Eligibility: {agri_limit}.
    Risk Score: {risk_score}.
    Decision: {decision}.
    """

    db = SessionLocal()
    record = CaseRecord(
        case_id=case_id,
        sales=sales,
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
        "NWC": nwc,
        "Current_Ratio": current_ratio,
        "MPBF": mpbf,
        "Working_Capital_Limit": wc_limit,
        "Agri_Limit": agri_limit,
        "Risk_Score": risk_score,
        "Decision": decision,
        "Memo": memo
    }

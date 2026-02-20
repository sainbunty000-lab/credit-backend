from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import re

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

# ---------------- SAFE DATABASE INIT ----------------

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None
Base = declarative_base()

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    class CaseRecord(Base):
        __tablename__ = "cases"
        case_id = Column(String, primary_key=True, index=True)
        sales = Column(Float)
        wc_limit = Column(Float)
        agri_limit = Column(Float)
        risk_score = Column(Integer)
        decision = Column(String)

    Base.metadata.create_all(bind=engine)

# ---------------- HEALTH CHECK ----------------

@app.get("/")
def home():
    return {"status": "Agri / WC Calculator Running"}

# ---------------- SIMPLE TEXT PARSER ----------------

def extract_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+(?:\.\d+)?)"
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

# ---------------- MAIN ANALYSIS ----------------

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(None)
):

    case_id = str(uuid.uuid4())[:8]

    bs_text = (await bs_file.read()).decode(errors="ignore")
    pl_text = (await pl_file.read()).decode(errors="ignore")

    sales = extract_amount(pl_text, ["sales", "turnover"])
    profit = extract_amount(pl_text, ["net profit"])
    inventory = extract_amount(bs_text, ["inventory", "stock"])
    debtors = extract_amount(bs_text, ["debtors"])
    creditors = extract_amount(bs_text, ["creditors"])

    current_assets = inventory + debtors
    nwc = current_assets - creditors
    mpbf = (0.75 * current_assets) - creditors
    wc_limit = sales * 0.20 if sales else 0
    agri_limit = ((profit * 0.60)/12)/0.14 if profit else 0

    risk_score = 80 if sales > 0 else 50
    decision = "Approve" if risk_score >= 60 else "Review"

    if SessionLocal:
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
        "MPBF": mpbf,
        "Working_Capital_Limit": wc_limit,
        "Agri_Limit": agri_limit,
        "Risk_Score": risk_score,
        "Decision": decision
    }

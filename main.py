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

# ---------------- DATABASE (AUTO SAFE) ----------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine("sqlite:///./agri_wc.db")  # fallback

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

# ---------------- FILE PARSER ----------------

def parse_excel(content):
    df = pd.read_excel(io.BytesIO(content))
    return df.to_string().lower()

def parse_csv(content):
    df = pd.read_csv(io.BytesIO(content))
    return df.to_string().lower()

def parse_text(content):
    return content.decode(errors="ignore").lower()

async def parse_file(file):
    content = await file.read()
    name = file.filename.lower()

    if name.endswith((".xls",".xlsx")):
        return parse_excel(content)
    elif name.endswith(".csv"):
        return parse_csv(content)
    else:
        return parse_text(content)

def find_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
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

    bs_text = await parse_file(bs_file)
    pl_text = await parse_file(pl_file)

    bank_text = ""
    if bank_file:
        bank_text = await parse_file(bank_file)

    # ---- Extract Core Values ----

    sales = find_amount(pl_text, ["sales","turnover"])
    net_profit = find_amount(pl_text, ["net profit"])
    ebitda = find_amount(pl_text, ["ebitda"])
    inventory = find_amount(bs_text, ["inventory","stock"])
    debtors = find_amount(bs_text, ["debtors"])
    creditors = find_amount(bs_text, ["creditors"])
    total_debt = find_amount(bs_text, ["loan","borrowings"])

    # ---- NWC ----
    current_assets = inventory + debtors
    current_liabilities = creditors
    nwc = current_assets - current_liabilities

    # ---- Current Ratio ----
    current_ratio = (current_assets / current_liabilities) if current_liabilities else 0

    # ---- MPBF (Tandon II) ----
    mpbf = (0.75 * current_assets) - current_liabilities

    # ---- Working Capital (20% Method) ----
    wc_limit = sales * 0.20 if sales else 0

    # ---- DSCR ----
    dscr = (net_profit + total_debt*0.1) / total_debt if total_debt else 0

    # ---- Agri Limit (Profit Based) ----
    agri_limit = ((net_profit * 0.60)/12)/0.14 if net_profit else 0

    # ---- EBITDA Funding ----
    ebitda_limit = ebitda * 4 if ebitda else 0

    # ---- Banking Hygiene ----
    banking_score = 85
    if bank_text and "bounce" in bank_text:
        banking_score = 60

    # ---- Risk Score ----
    risk_score = 80
    if current_ratio < 1:
        risk_score -= 20
    if dscr < 1.2:
        risk_score -= 20
    if banking_score < 70:
        risk_score -= 20

    decision = "Approve" if risk_score >= 60 else "Review"

    # ---- Memo Paragraph ----

    memo = f"""
    The financial analysis of the applicant indicates annual turnover of {sales}.
    Net working capital stands at {nwc} with current ratio of {round(current_ratio,2)}.
    MPBF eligibility computed under Tandon II method is {mpbf}.
    DSCR is assessed at {round(dscr,2)}.
    Based on EBITDA multiple method, eligible funding is {ebitda_limit}.
    Banking hygiene score evaluated at {banking_score}.
    Overall risk score computed at {risk_score}.
    Final recommendation: {decision}.
    """

    # ---- Save ----

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
        "DSCR": dscr,
        "EBITDA_Limit": ebitda_limit,
        "Banking_Score": banking_score,
        "Risk_Score": risk_score,
        "Decision": decision,
        "Memo": memo
    }

@app.get("/cases")
def get_cases():
    db = SessionLocal()
    records = db.query(CaseRecord).all()
    db.close()
    return records

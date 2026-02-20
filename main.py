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

# ---------------- DATABASE ----------------

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    except Exception as e:
        print("DB CONNECTION ERROR:", e)
        engine = create_engine("sqlite:///./agri_wc.db")
else:
    engine = create_engine("sqlite:///./agri_wc.db")

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ---------------- ADVANCED PARSER ----------------

def clean_number(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0.0

def extract_from_dataframe(df):
    df = df.astype(str)
    flat = df.values.flatten()
    text = " ".join(flat).lower()

    def find(keywords):
        for key in keywords:
            pattern = rf"{key}[^0-9\-]*(-?\d[\d,\.]*)"
            match = re.search(pattern, text)
            if match:
                return clean_number(match.group(1))
        return 0

    return {
        "sales": find(["sales", "turnover", "revenue"]),
        "net_profit": find(["net profit", "profit after tax"]),
        "inventory": find(["inventory", "stock"]),
        "debtors": find(["debtors", "receivables"]),
        "creditors": find(["creditors", "payables"])
    }

async def parse_file(file: UploadFile):

    if not file:
        return {}

    try:
        content = await file.read()
        name = file.filename.lower()

        if name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl", header=None)

        elif name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), header=None)

        else:
            return {}

        df = df.fillna("")
        df = df.astype(str)

        flat_text = " ".join(df.values.flatten()).lower()

        def find(keywords):
            for key in keywords:
                pattern = rf"{key}[^0-9\-]*(-?\d[\d,\.]*)"
                match = re.search(pattern, flat_text)
                if match:
                    return float(match.group(1).replace(",", ""))
            return 0

        return {
            "sales": find(["sales", "turnover", "revenue"]),
            "profit": find(["net profit", "profit after tax"]),
            "inventory": find(["inventory", "stock"]),
            "debtors": find(["debtors", "receivables"]),
            "creditors": find(["creditors", "payables"])
        }

    except Exception as e:
        print("PARSE ERROR:", str(e))
        return {}

# ---------------- ANALYSIS ----------------

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(None)
):

    case_id = str(uuid.uuid4())[:8]

    bs_data = await parse_file(bs_file)
pl_data = await parse_file(pl_file)
bank_data = await parse_file(bank_file) if bank_file else {}

sales = pl_data.get("sales", 0)
net_profit = pl_data.get("profit", 0)
inventory = bs_data.get("inventory", 0)
debtors = bs_data.get("debtors", 0)
creditors = bs_data.get("creditors", 0)

    current_assets = inventory + debtors
    current_liabilities = creditors
    nwc = current_assets - current_liabilities
    current_ratio = (current_assets / current_liabilities) if current_liabilities else 0
    mpbf = (0.75 * current_assets) - current_liabilities
    wc_limit = sales * 0.20
    agri_limit = ((net_profit * 0.60)/12)/0.14 if net_profit else 0

    # -------- Risk Model --------
    risk_score = 100
    fraud_flags = []

    if current_ratio < 1.25:
        risk_score -= 15
        fraud_flags.append("Weak Current Ratio")

    if net_profit <= 0:
        risk_score -= 25
        fraud_flags.append("Negative Profit")

    if sales <= 0:
        risk_score -= 25
        fraud_flags.append("Sales Not Found")

    if nwc <= 0:
        risk_score -= 15
        fraud_flags.append("Negative Working Capital")

    risk_score = max(risk_score, 0)
    decision = "Approve" if risk_score >= 70 else "Review"

    memo = f"""
    The annual turnover is assessed at {sales}.
    Net Working Capital computed at {nwc}.
    Current Ratio stands at {round(current_ratio,2)}.
    MPBF eligibility under Tandon II method calculated at {mpbf}.
    Working Capital limit (20% turnover) derived at {wc_limit}.
    Agriculture eligibility assessed at {agri_limit}.
    Overall risk score evaluated at {risk_score}.
    Fraud flags observed: {", ".join(fraud_flags) if fraud_flags else "None"}.
    Final credit recommendation: {decision}.
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
        "Fraud_Flags": fraud_flags,
        "Memo": memo
    }

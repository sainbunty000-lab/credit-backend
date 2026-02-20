from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import re
import uuid
import os

app = FastAPI(title="Agri / WC Calculator")

@app.get("/")
def home():
    return {"status": "Agri / WC Calculator Running"}

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

        df = df.fillna("").astype(str)
        flat_text = " ".join(df.values.flatten()).lower()

        def find(keywords):
            for key in keywords:
                pattern = rf"{key}[^0-9\-]*(-?\d[\d,\.]*)"
                match = re.search(pattern, flat_text)
                if match:
                    return float(match.group(1).replace(",", ""))
            return 0.0

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
    agri_limit = ((net_profit * 0.60) / 12) / 0.14 if net_profit else 0

    risk_score = 80
    if current_ratio < 1:
        risk_score -= 20
    if net_profit <= 0:
        risk_score -= 20

    decision = "Approve" if risk_score >= 60 else "Review"

    return {
        "Case_ID": case_id,
        "Sales": sales,
        "NWC": nwc,
        "Current_Ratio": round(current_ratio, 2),
        "MPBF": mpbf,
        "Working_Capital_Limit": wc_limit,
        "Agri_Limit": agri_limit,
        "Risk_Score": risk_score,
        "Decision": decision
    }

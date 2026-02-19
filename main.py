from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pdfplumber
import uuid
import io

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- UTILITIES ----------------

def read_excel(file_bytes):
    return pd.read_excel(io.BytesIO(file_bytes))

def read_pdf_table(file_bytes):
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        tables = []
        for page in pdf.pages:
            tables += page.extract_tables()
    return tables

def safe_number(val):
    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0

# ---------------- CORE PARSER ----------------

def parse_pl(df):
    data = {}
    for col in df.columns:
        lower = col.lower()
        if "sales" in lower or "turnover" in lower:
            data["sales"] = safe_number(df[col].iloc[-1])
        if "profit" in lower:
            data["profit"] = safe_number(df[col].iloc[-1])
        if "depreciation" in lower:
            data["depreciation"] = safe_number(df[col].iloc[-1])
    return data

def parse_bs(df):
    data = {}
    for col in df.columns:
        lower = col.lower()
        if "inventory" in lower or "stock" in lower:
            data["inventory"] = safe_number(df[col].iloc[-1])
        if "debtor" in lower:
            data["debtors"] = safe_number(df[col].iloc[-1])
        if "creditor" in lower:
            data["creditors"] = safe_number(df[col].iloc[-1])
    return data

def parse_bank_pdf(file_bytes):
    tables = read_pdf_table(file_bytes)
    credits = 0
    for table in tables:
        for row in table:
            for cell in row:
                if cell and "cr" in str(cell).lower():
                    try:
                        val = safe_number(cell)
                        credits += val
                    except:
                        pass
    return credits

# ---------------- RISK ENGINE ----------------

def risk_score(current_ratio, mismatch):
    score = 80
    if current_ratio < 1:
        score -= 20
    if mismatch > 20:
        score -= 25
    return max(score, 30)

# ---------------- MAIN ENDPOINT ----------------

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    case_id = str(uuid.uuid4())[:8]

    # Read Files
    bs_bytes = await bs_file.read()
    pl_bytes = await pl_file.read()
    bank_bytes = await bank_file.read()

    bs_df = read_excel(bs_bytes)
    pl_df = read_excel(pl_bytes)

    bs_data = parse_bs(bs_df)
    pl_data = parse_pl(pl_df)
    bank_turnover = parse_bank_pdf(bank_bytes)

    sales = pl_data.get("sales", 0)
    profit = pl_data.get("profit", 0)
    depreciation = pl_data.get("depreciation", 0)
    inventory = bs_data.get("inventory", 0)
    debtors = bs_data.get("debtors", 0)
    creditors = bs_data.get("creditors", 0)

    # Calculations
    working_capital_limit = sales * 0.20
    current_ratio = (inventory + debtors) / creditors if creditors else 0
    profit_margin = (profit / sales * 100) if sales else 0
    mismatch = abs(bank_turnover - sales) / sales * 100 if sales else 0

    risk = risk_score(current_ratio, mismatch)
    decision = "Approve" if risk >= 60 else "Review"

    parsing_confidence = 90 if sales and inventory else 65

    return {
        "Case_ID": case_id,
        "Bank_Turnover": round(bank_turnover,2),
        "Working_Capital_Limit": round(working_capital_limit,2),
        "Current_Ratio": round(current_ratio,2),
        "Profit_Margin": round(profit_margin,2),
        "Mismatch_%": round(mismatch,2),
        "Risk_Score": risk,
        "Decision": decision,
        "Parsing_Confidence": parsing_confidence
    }

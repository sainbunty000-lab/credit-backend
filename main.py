from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pdfplumber
import io
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# SAFE FILE READERS
# --------------------------------------------------

def read_excel(file_bytes):
    return pd.read_excel(io.BytesIO(file_bytes))

def read_pdf_table(file_bytes):
    tables = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                tables.append(df)
    if tables:
        return pd.concat(tables, ignore_index=True)
    return pd.DataFrame()

# --------------------------------------------------
# VALIDATION LAYER
# --------------------------------------------------

def validate_numeric(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0

# --------------------------------------------------
# FINANCIAL RATIO ENGINE
# --------------------------------------------------

def ratio_engine(pl_df, bs_df):

    revenue = validate_numeric(pl_df.iloc[:, -1].sum())
    expenses = validate_numeric(pl_df.iloc[:, -2].sum())

    profit = revenue - expenses

    total_assets = validate_numeric(bs_df.iloc[:, -1].sum())
    total_liabilities = validate_numeric(bs_df.iloc[:, -2].sum())

    current_ratio = (
        total_assets / total_liabilities
        if total_liabilities != 0 else 0
    )

    profit_margin = (
        (profit / revenue) * 100
        if revenue != 0 else 0
    )

    return profit_margin, current_ratio, profit

# --------------------------------------------------
# BANK ANALYSIS
# --------------------------------------------------

def bank_engine(bank_df):

    if bank_df.empty:
        return 0

    amounts = []

    for col in bank_df.columns:
        try:
            numeric = pd.to_numeric(bank_df[col], errors='coerce')
            amounts.append(numeric.sum())
        except:
            continue

    turnover = max(amounts) if amounts else 0
    return turnover

# --------------------------------------------------
# WORKING CAPITAL ENGINE
# --------------------------------------------------

def working_capital_engine(turnover):
    return turnover * 0.20

# --------------------------------------------------
# AGRICULTURE ENGINE
# --------------------------------------------------

def agriculture_engine(profit):
    monthly_surplus = (profit * 0.6) / 12
    limit = monthly_surplus / 0.14 if monthly_surplus > 0 else 0
    return limit

# --------------------------------------------------
# FRAUD ENGINE
# --------------------------------------------------

def fraud_engine(mismatch, current_ratio):
    flags = []

    if mismatch > 30:
        flags.append("High turnover mismatch detected")

    if current_ratio < 0.8:
        flags.append("Liquidity stress observed")

    if not flags:
        flags.append("No major red flags")

    return flags

# --------------------------------------------------
# AI EXPLANATION
# --------------------------------------------------

def ai_explanation(risk, decision):
    if risk >= 75:
        return "Strong financial profile with stable performance."
    elif risk >= 50:
        return "Moderate financial stability with manageable risk."
    else:
        return "High financial risk observed. Careful review recommended."

# --------------------------------------------------
# MAIN ANALYSIS ROUTE
# --------------------------------------------------

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

    # Detect file type
    bs_df = read_excel(bs_bytes)
    pl_df = read_excel(pl_bytes)

    if bank_file.filename.endswith(".pdf"):
        bank_df = read_pdf_table(bank_bytes)
    else:
        bank_df = read_excel(bank_bytes)

    profit_margin, current_ratio, profit = ratio_engine(pl_df, bs_df)

    turnover = bank_engine(bank_df)

    wc_limit = working_capital_engine(turnover)
    agri_limit = agriculture_engine(profit)

    mismatch = abs(turnover - pl_df.iloc[:, -1].sum()) / (pl_df.iloc[:, -1].sum() + 1) * 100

    risk_score = (
        (profit_margin * 0.4) +
        (current_ratio * 20 * 0.3) +
        ((100 - mismatch) * 0.3)
    )

    decision = "Approve" if risk_score >= 60 else "Review"

    fraud_flags = fraud_engine(mismatch, current_ratio)

    confidence = 85 if not bank_df.empty else 60

    explanation = ai_explanation(risk_score, decision)

    return {
        "Case_ID": case_id,
        "Profit_Margin": round(profit_margin, 2),
        "Current_Ratio": round(current_ratio, 2),
        "Bank_Turnover": round(turnover, 2),
        "Working_Capital_Limit": round(wc_limit, 2),
        "Agri_Limit": round(agri_limit, 2),
        "Mismatch_%": round(mismatch, 2),
        "Risk_Score": round(risk_score, 2),
        "Decision": decision,
        "Fraud_Flags": fraud_flags,
        "Parsing_Confidence": confidence,
        "AI_Explanation": explanation
    }

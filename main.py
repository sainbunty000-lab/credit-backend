from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pdfplumber
import io
import uuid

app = FastAPI(title="Ultra Stable Underwriting Engine")

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ SAFE UTILITIES ------------------

def safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0.0

def read_excel_safe(file_bytes):
    try:
        return pd.read_excel(io.BytesIO(file_bytes))
    except:
        return pd.DataFrame()

def read_pdf_safe(file_bytes):
    try:
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
    except:
        return pd.DataFrame()

# ------------------ PL PARSER ------------------

def parse_pl(df):
    sales = 0
    profit = 0

    if df.empty:
        return sales, profit

    for col in df.columns:
        col_lower = str(col).lower()

        if "sales" in col_lower or "turnover" in col_lower or "revenue" in col_lower:
            sales = safe_float(df[col].sum())

        if "profit" in col_lower or "net" in col_lower:
            profit = safe_float(df[col].sum())

    return sales, profit

# ------------------ BS PARSER ------------------

def parse_bs(df):
    inventory = 0
    debtors = 0
    creditors = 0

    if df.empty:
        return inventory, debtors, creditors

    for col in df.columns:
        col_lower = str(col).lower()

        if "inventory" in col_lower or "stock" in col_lower:
            inventory = safe_float(df[col].sum())

        if "debtor" in col_lower:
            debtors = safe_float(df[col].sum())

        if "creditor" in col_lower:
            creditors = safe_float(df[col].sum())

    return inventory, debtors, creditors

# ------------------ BANK PARSER ------------------

def parse_bank(df):
    turnover = 0

    if df.empty:
        return turnover

    for col in df.columns:
        try:
            numeric = pd.to_numeric(df[col], errors="coerce")
            col_sum = numeric.sum()
            if col_sum > turnover:
                turnover = col_sum
        except:
            continue

    return safe_float(turnover)

# ------------------ RISK ENGINE ------------------

def calculate_risk(profit_margin, current_ratio, mismatch):
    score = 0

    # Profit margin
    if profit_margin > 15:
        score += 35
    elif profit_margin > 8:
        score += 25
    else:
        score += 15

    # Liquidity
    if current_ratio >= 1.5:
        score += 30
    elif current_ratio >= 1.0:
        score += 20
    else:
        score += 10

    # Mismatch
    if mismatch < 10:
        score += 35
    elif mismatch < 25:
        score += 20
    else:
        score += 5

    return score

# ------------------ MAIN ROUTE ------------------

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    try:
        case_id = str(uuid.uuid4())[:8]

        bs_bytes = await bs_file.read()
        pl_bytes = await pl_file.read()
        bank_bytes = await bank_file.read()

        # Detect formats
        bs_df = read_excel_safe(bs_bytes)
        if bs_df.empty and bs_file.filename.endswith(".pdf"):
            bs_df = read_pdf_safe(bs_bytes)

        pl_df = read_excel_safe(pl_bytes)
        if pl_df.empty and pl_file.filename.endswith(".pdf"):
            pl_df = read_pdf_safe(pl_bytes)

        if bank_file.filename.endswith(".pdf"):
            bank_df = read_pdf_safe(bank_bytes)
        else:
            bank_df = read_excel_safe(bank_bytes)

        # Parse
        sales, profit = parse_pl(pl_df)
        inventory, debtors, creditors = parse_bs(bs_df)
        turnover = parse_bank(bank_df)

        # Ratios
        current_ratio = (inventory + debtors) / creditors if creditors else 0
        profit_margin = (profit / sales * 100) if sales else 0
        mismatch = abs(turnover - sales) / sales * 100 if sales else 0

        # Engines
        wc_limit = turnover * 0.20
        agri_limit = ((profit * 0.6) / 12) / 0.14 if profit > 0 else 0

        risk_score = calculate_risk(profit_margin, current_ratio, mismatch)
        decision = "Approve" if risk_score >= 60 else "Review"

        fraud_flags = []
        if mismatch > 30:
            fraud_flags.append("High turnover mismatch detected")
        if current_ratio < 0.8:
            fraud_flags.append("Liquidity stress observed")
        if not fraud_flags:
            fraud_flags.append("No major red flags")

        confidence = 90 if not bank_df.empty else 60

        explanation = (
            "Strong profile." if risk_score >= 75 else
            "Moderate profile." if risk_score >= 60 else
            "High risk profile."
        )

        return {
            "Case_ID": case_id,
            "Profit_Margin": round(profit_margin, 2),
            "Current_Ratio": round(current_ratio, 2),
            "Bank_Turnover": round(turnover, 2),
            "Working_Capital_Limit": round(wc_limit, 2),
            "Agri_Limit": round(agri_limit, 2),
            "Mismatch_%": round(mismatch, 2),
            "Risk_Score": risk_score,
            "Decision": decision,
            "Fraud_Flags": fraud_flags,
            "Parsing_Confidence": confidence,
            "AI_Explanation": explanation
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Server handled error safely"
        }

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pdfplumber
import io
import uuid
import traceback

app = FastAPI(title="Enterprise Underwriting Engine")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SAFE HELPERS ----------------

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
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    tables.append(df)
        if tables:
            return pd.concat(tables, ignore_index=True)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# ---------------- PARSERS ----------------

def parse_pl(df):
    sales = 0
    profit = 0

    if df.empty:
        return sales, profit

    for col in df.columns:
        col_name = str(col).lower()

        if any(word in col_name for word in ["sales","turnover","revenue"]):
            sales = safe_float(pd.to_numeric(df[col], errors="coerce").sum())

        if any(word in col_name for word in ["profit","net"]):
            profit = safe_float(pd.to_numeric(df[col], errors="coerce").sum())

    return sales, profit

def parse_bs(df):
    inventory = 0
    debtors = 0
    creditors = 0

    if df.empty:
        return inventory, debtors, creditors

    for col in df.columns:
        col_name = str(col).lower()

        if any(word in col_name for word in ["inventory","stock"]):
            inventory = safe_float(pd.to_numeric(df[col], errors="coerce").sum())

        if "debtor" in col_name:
            debtors = safe_float(pd.to_numeric(df[col], errors="coerce").sum())

        if "creditor" in col_name:
            creditors = safe_float(pd.to_numeric(df[col], errors="coerce").sum())

    return inventory, debtors, creditors

def parse_bank(df):
    if df.empty:
        return 0

    max_sum = 0

    for col in df.columns:
        try:
            numeric = pd.to_numeric(df[col], errors="coerce")
            col_sum = numeric.sum()
            if col_sum > max_sum:
                max_sum = col_sum
        except:
            continue

    return safe_float(max_sum)

# ---------------- RISK ENGINE ----------------

def risk_engine(profit_margin, current_ratio, mismatch):

    score = 0

    # Profit strength
    if profit_margin > 15:
        score += 35
    elif profit_margin > 8:
        score += 25
    else:
        score += 15

    # Liquidity
    if current_ratio >= 1.5:
        score += 30
    elif current_ratio >= 1:
        score += 20
    else:
        score += 10

    # Turnover match
    if mismatch < 10:
        score += 35
    elif mismatch < 25:
        score += 20
    else:
        score += 5

    return score

# ---------------- MAIN ROUTE ----------------

@app.get("/")
def health():
    return {"status": "Backend running"}

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

        # Read BS
        bs_df = read_excel_safe(bs_bytes)
        if bs_df.empty:
            bs_df = read_pdf_safe(bs_bytes)

        # Read PL
        pl_df = read_excel_safe(pl_bytes)
        if pl_df.empty:
            pl_df = read_pdf_safe(pl_bytes)

        # Read Bank
        bank_df = read_excel_safe(bank_bytes)
        if bank_df.empty:
            bank_df = read_pdf_safe(bank_bytes)

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

        risk_score = risk_engine(profit_margin, current_ratio, mismatch)
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
            "Strong financial profile."
            if risk_score >= 75 else
            "Moderate financial stability."
            if risk_score >= 60 else
            "High financial risk detected."
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
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "Safe error handled"
        }

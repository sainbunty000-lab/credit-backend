from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import uuid
import pandas as pd
import pdfplumber
import io
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = FastAPI(title="Enterprise Structured Underwriting Engine")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("cases.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    agri_limit REAL,
    wc_limit REAL,
    risk_score INTEGER,
    decision TEXT,
    created_at TEXT
)
""")
conn.commit()

# ---------------- BANK PARSER ----------------
def parse_bank_statement(file_bytes, filename):

    confidence = 0
    credit_total = 0
    balances = []
    bounce_count = 0

    def detect_columns(headers):
        credit_col = None
        balance_col = None

        for idx, col in enumerate(headers):
            col_lower = str(col).lower()

            if any(k in col_lower for k in ["credit", "deposit", "cr"]):
                credit_col = idx

            if "balance" in col_lower:
                balance_col = idx

        return credit_col, balance_col

    # -------- EXCEL --------
    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_bytes))
        headers = list(df.columns.astype(str))
        credit_col, balance_col = detect_columns(headers)

        if credit_col is None or balance_col is None:
            return {"error": "Bank columns not detected", "confidence": 0}

        confidence += 40

        for _, row in df.iterrows():
            try:
                val = float(str(row[headers[credit_col]]).replace(",", ""))
                if val > 0:
                    credit_total += val
            except:
                pass

            try:
                bal = float(str(row[headers[balance_col]]).replace(",", ""))
                balances.append(bal)
            except:
                pass

        if credit_total > 0:
            confidence += 30

        if len(balances) > 10:
            confidence += 20

    # -------- PDF --------
    elif filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    headers = table[0]
                    credit_col, balance_col = detect_columns(headers)

                    if credit_col is not None and balance_col is not None:
                        confidence += 40

                        for row in table[1:]:
                            try:
                                val = float(str(row[credit_col]).replace(",", ""))
                                if val > 0:
                                    credit_total += val
                            except:
                                pass

                            try:
                                bal = float(str(row[balance_col]).replace(",", ""))
                                balances.append(bal)
                            except:
                                pass

        if credit_total > 0:
            confidence += 30

        if len(balances) > 10:
            confidence += 20

    # Bounce Detection
    text_sample = file_bytes.decode(errors="ignore").lower()
    bounce_count = len(re.findall(r"return|bounce|insufficient", text_sample))
    confidence += 10

    return {
        "credit_total": credit_total,
        "balances": balances,
        "bounce_count": bounce_count,
        "confidence": min(confidence, 100)
    }

# ---------------- ELIGIBILITY MODEL ----------------
class FinancialInput(BaseModel):
    sales: float
    pat: float
    stock: float
    debtors: float
    creditors: float
    bounce: int

def calculate_models(data):

    wc_gap = (data.stock + data.debtors) - data.creditors
    wc_limit = min(data.sales * 0.20, max(0, wc_gap * 0.75))

    margin = (data.pat / data.sales) * 100 if data.sales else 0
    current_ratio = (data.stock + data.debtors) / data.creditors if data.creditors else 0

    score = 0
    score += 30 if margin > 10 else 20 if margin > 5 else 10
    score += 30 if current_ratio >= 1.5 else 20 if current_ratio >= 1.2 else 10
    score += 30 if data.bounce == 0 else 20 if data.bounce <= 2 else 5

    decision = "Approve" if score >= 60 else "Review"

    return wc_limit, score, decision, margin, current_ratio

# ---------------- FULL ANALYSIS ----------------
@app.post("/full-analysis")
async def full_analysis(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    bank_bytes = await bank_file.read()
    bank_data = parse_bank_statement(bank_bytes, bank_file.filename)

    if bank_data.get("error"):
        return bank_data

    bank_turnover = bank_data["credit_total"]
    bounce = bank_data["bounce_count"]
    parsing_confidence = bank_data["confidence"]

    # Simplified structured PL & BS extraction
    pl_df = pd.read_excel(io.BytesIO(await pl_file.read()))
    bs_df = pd.read_excel(io.BytesIO(await bs_file.read()))

    sales = pl_df.iloc[:,1].sum()
    pat = pl_df.iloc[:,-1].sum()

    stock = bs_df.iloc[:,1].sum()
    debtors = bs_df.iloc[:,2].sum()
    creditors = bs_df.iloc[:,3].sum()

    mismatch = abs(bank_turnover - sales) / sales * 100 if sales else 0

    data = FinancialInput(
        sales=sales,
        pat=pat,
        stock=stock,
        debtors=debtors,
        creditors=creditors,
        bounce=bounce
    )

    wc_limit, score, decision, margin, cr = calculate_models(data)

    case_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, 0, wc_limit, score, decision, created_at)
    )
    conn.commit()

    return {
        "Case_ID": case_id,
        "Parsing_Confidence": parsing_confidence,
        "Bank_Turnover": bank_turnover,
        "Mismatch_%": round(mismatch,2),
        "Working_Capital_Limit": round(wc_limit,2),
        "Risk_Score": score,
        "Decision": decision,
        "Profit_Margin": round(margin,2),
        "Current_Ratio": round(cr,2)
    }

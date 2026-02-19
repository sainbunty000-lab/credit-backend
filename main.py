from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pandas as pd
import pdfplumber
import io
import re
import uuid

app = FastAPI(title="Enterprise Underwriting Engine")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SAFE BANK PARSER ----------------
def parse_bank(file_bytes, filename):

    credit_total = 0
    bounce_count = 0
    confidence = 0

    try:

        # ---------- EXCEL ----------
        if filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
            headers = [str(h).lower() for h in df.columns]

            credit_col = None
            balance_col = None

            for i, col in enumerate(headers):
                if "credit" in col or "deposit" in col:
                    credit_col = df.columns[i]
                if "balance" in col:
                    balance_col = df.columns[i]

            if credit_col is None:
                return {"error": "Credit column not detected", "confidence": 0}

            confidence += 40

            credit_total = pd.to_numeric(df[credit_col], errors="coerce").fillna(0).sum()
            confidence += 40

        # ---------- PDF ----------
        elif filename.lower().endswith(".pdf"):

            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        headers = [str(h).lower() for h in table[0]]

                        credit_index = None

                        for i, col in enumerate(headers):
                            if "credit" in col or "deposit" in col:
                                credit_index = i

                        if credit_index is not None:
                            confidence += 40

                            for row in table[1:]:
                                try:
                                    val = float(str(row[credit_index]).replace(",", ""))
                                    if val > 0:
                                        credit_total += val
                                except:
                                    pass

            if credit_total > 0:
                confidence += 40

        # ---------- Bounce Detection ----------
        text = file_bytes.decode(errors="ignore").lower()
        bounce_count = len(re.findall(r"return|bounce|insufficient", text))
        confidence += 20

        return {
            "credit_total": float(credit_total),
            "bounce_count": bounce_count,
            "confidence": min(confidence, 100)
        }

    except Exception as e:
        return {"error": str(e), "confidence": 0}


# ---------------- SAFE PL PARSER ----------------
def parse_pl(file_bytes):
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
        df = df.fillna(0)

        numeric_df = df.select_dtypes(include="number")

        sales = numeric_df.sum().sum()
        pat = numeric_df.iloc[:, -1].sum()

        return float(sales), float(pat)

    except:
        return 0.0, 0.0


# ---------------- SAFE BS PARSER ----------------
def parse_bs(file_bytes):
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
        df = df.fillna(0)

        numeric_df = df.select_dtypes(include="number")

        total_assets = numeric_df.sum().sum()
        stock = numeric_df.iloc[:, 0].sum() if numeric_df.shape[1] > 0 else 0
        debtors = numeric_df.iloc[:, 1].sum() if numeric_df.shape[1] > 1 else 0
        creditors = numeric_df.iloc[:, 2].sum() if numeric_df.shape[1] > 2 else 0

        return float(stock), float(debtors), float(creditors)

    except:
        return 0.0, 0.0, 0.0


# ---------------- ELIGIBILITY CALCULATION ----------------
def calculate_wc(sales, stock, debtors, creditors):

    wc_gap = (stock + debtors) - creditors
    wc_limit = min(sales * 0.20, max(0, wc_gap * 0.75))

    return wc_limit


def calculate_risk(pat, sales, bounce, stock, debtors, creditors):

    score = 0

    margin = (pat / sales) * 100 if sales else 0
    current_ratio = (stock + debtors) / creditors if creditors else 0

    if margin > 10:
        score += 30
    elif margin > 5:
        score += 20
    else:
        score += 10

    if current_ratio >= 1.5:
        score += 30
    elif current_ratio >= 1.2:
        score += 20
    else:
        score += 10

    if bounce == 0:
        score += 30
    elif bounce <= 2:
        score += 20
    else:
        score += 10

    decision = "Approve" if score >= 60 else "Review"

    return score, decision, margin, current_ratio


# ---------------- FULL ANALYSIS ----------------
@app.post("/full-analysis")
async def full_analysis(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    try:

        bank_bytes = await bank_file.read()
        pl_bytes = await pl_file.read()
        bs_bytes = await bs_file.read()

        bank_data = parse_bank(bank_bytes, bank_file.filename)

        if bank_data.get("error"):
            return bank_data

        sales, pat = parse_pl(pl_bytes)
        stock, debtors, creditors = parse_bs(bs_bytes)

        wc_limit = calculate_wc(sales, stock, debtors, creditors)

        score, decision, margin, current_ratio = calculate_risk(
            pat, sales,
            bank_data["bounce_count"],
            stock, debtors, creditors
        )

        mismatch = abs(bank_data["credit_total"] - sales) / sales * 100 if sales else 0

        return {
            "Case_ID": str(uuid.uuid4()),
            "Bank_Turnover": bank_data["credit_total"],
            "Parsing_Confidence": bank_data["confidence"],
            "Mismatch_%": round(mismatch,2),
            "Working_Capital_Limit": round(wc_limit,2),
            "Risk_Score": score,
            "Decision": decision,
            "Profit_Margin": round(margin,2),
            "Current_Ratio": round(current_ratio,2)
        }

    except Exception as e:
        return {"error": str(e)}

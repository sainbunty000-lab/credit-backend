from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import re

app = FastAPI(title="Agri / WC Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# BANK STATEMENT ANALYZER
# ---------------------------

def clean_number(val):
    try:
        val = str(val).replace(",", "")
        return float(re.findall(r"-?\d+\.?\d*", val)[0])
    except:
        return 0


async def analyze_bank_statement(file: UploadFile):

    if not file:
        return {}

    content = await file.read()

    df = pd.read_excel(io.BytesIO(content), header=None)

    total_credit = 0
    balance_list = []
    bounce_count = 0

    for row in df.values:
        for cell in row:
            value = clean_number(cell)
            if value > 0:
                total_credit += value

            text = str(cell).lower()
            if "bounce" in text or "return" in text:
                bounce_count += 1

            if "balance" in text:
                balance_list.append(value)

    avg_balance = sum(balance_list) / len(balance_list) if balance_list else 0

    return {
        "Total_Credit": total_credit,
        "Avg_Balance": avg_balance,
        "Bounce_Count": bounce_count
    }

# ---------------------------
# MAIN ANALYSIS
# ---------------------------

@app.post("/analyze")
async def analyze(
    sales: float = Form(...),
    net_profit: float = Form(...),
    depreciation: float = Form(...),
    inventory: float = Form(...),
    debtors: float = Form(...),
    creditors: float = Form(...),
    emi: float = Form(...),
    bank_file: UploadFile = File(None)
):

    # ---------------- Financial Calculations ----------------

    current_assets = inventory + debtors
    current_liabilities = creditors

    nwc = current_assets - current_liabilities
    current_ratio = current_assets / current_liabilities if current_liabilities else 0

    wc_gap = inventory + debtors - creditors
    mpbf = max(0, (0.75 * wc_gap) - nwc)

    turnover_limit = 0.20 * sales
    wc_limit = max(mpbf, turnover_limit)

    agri_limit = (((net_profit * 0.60) / 12) - emi) / 0.14
    agri_limit = max(0, agri_limit)

    # ---------------- Banking Analysis ----------------

    bank_data = await analyze_bank_statement(bank_file)

    hygiene_score = 100
    if bank_data.get("Bounce_Count", 0) > 2:
        hygiene_score -= 30

    if bank_data.get("Avg_Balance", 0) < emi * 2:
        hygiene_score -= 20

    # ---------------- Risk Scoring ----------------

    risk_score = 100

    if current_ratio < 1:
        risk_score -= 30

    if nwc < 0:
        risk_score -= 20

    if hygiene_score < 70:
        risk_score -= 20

    risk_score = max(risk_score, 0)

    decision = "Approve"
    if risk_score < 50:
        decision = "Reject"
    elif risk_score < 70:
        decision = "Review"

    return {
        "NWC": nwc,
        "Current_Ratio": round(current_ratio, 2),
        "MPBF": mpbf,
        "Working_Capital_Limit": wc_limit,
        "Agri_Limit": agri_limit,
        "Banking_Summary": bank_data,
        "Banking_Hygiene_Score": hygiene_score,
        "Risk_Score": risk_score,
        "Decision": decision
    }

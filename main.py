from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI(title="Credit Engine vFinal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe(v):
    try:
        return float(v)
    except:
        return 0.0


# ============================
# CENTRAL RISK ENGINE
# ============================

def risk_engine(dscr, hygiene, wc, agri):
    score = 0

    # DSCR 40%
    if dscr >= 1.5:
        score += 40
    elif dscr >= 1.25:
        score += 30
    elif dscr >= 1:
        score += 20
    else:
        score += 10

    # Banking hygiene 30%
    score += hygiene * 0.30

    # Eligibility strength 20%
    if wc > 0:
        score += 10
    if agri > 0:
        score += 10

    # Cushion 10%
    if wc > agri:
        score += 10
    else:
        score += 5

    return round(score)


def rating(score):
    if score >= 85: return "AAA"
    if score >= 75: return "AA"
    if score >= 65: return "A"
    if score >= 55: return "BBB"
    if score >= 45: return "BB"
    return "B"


# ============================
# MAIN CALCULATION ENGINE
# ============================

@app.post("/analyze")
async def analyze(data: dict):

    # Inputs
    turnover = safe(data.get("turnover"))
    inventory = safe(data.get("inventory"))
    debtors = safe(data.get("debtors"))
    creditors = safe(data.get("creditors"))

    net_profit = safe(data.get("net_profit"))
    depreciation = safe(data.get("depreciation"))
    tax_paid = safe(data.get("tax_paid"))
    monthly_emi = safe(data.get("monthly_emi"))
    loan_required = safe(data.get("loan_required"))
    undoc = safe(data.get("undocumented_income"))

    hygiene = safe(data.get("hygiene_score"))

    # ====================
    # WORKING CAPITAL
    # ====================
    wc_turnover = turnover * 0.20
    wcg = (inventory + debtors) - creditors
    mpbf = wcg * 0.75 if wcg > 0 else 0
    wc_final = min(wc_turnover, mpbf) if wc_turnover and mpbf else max(wc_turnover, mpbf)

    # ====================
    # TERM LOAN
    # ====================
    cash_accrual = net_profit + depreciation
    annual_emi = monthly_emi * 12
    dscr = cash_accrual / annual_emi if annual_emi > 0 else 0
    surplus = cash_accrual - annual_emi
    tl_eligible = surplus * 6 if surplus > 0 else 0

    # ====================
    # AGRICULTURE (Your Logic)
    # ====================
    nca = net_profit + depreciation - tax_paid
    scaling = 0.70 if loan_required > 3000000 else 0.60
    scaled_income = nca * scaling
    monthly_surplus = (scaled_income/12) - monthly_emi + ((undoc*0.42)/12)
    agri_eligible = monthly_surplus / 0.14 if monthly_surplus > 0 else 0

    # ====================
    # RISK & RATING
    # ====================
    risk_score = risk_engine(dscr, hygiene, wc_final, agri_eligible)
    internal_rating = rating(risk_score)

    final_limit = max(wc_final, tl_eligible, agri_eligible)

    return {
        "wc": round(wc_final,2),
        "mpbf": round(mpbf,2),
        "dscr": round(dscr,2),
        "tl_eligible": round(tl_eligible,2),
        "agri_eligible": round(agri_eligible,2),
        "risk_score": risk_score,
        "rating": internal_rating,
        "final_limit": round(final_limit,2)
    }


# ============================
# BANKING PERFIOS
# ============================

@app.post("/banking")
async def banking(file: UploadFile = File(...)):

    content = await file.read()

    if file.filename.lower().endswith(("xls","xlsx")):
        df = pd.read_excel(io.BytesIO(content))
    else:
        df = pd.read_csv(io.BytesIO(content))

    df.columns = [str(c).lower() for c in df.columns]

    total_credit = 0
    total_debit = 0

    for col in df.columns:
        if "credit" in col or "cr" in col:
            total_credit += pd.to_numeric(df[col], errors="coerce").fillna(0).sum()
        if "debit" in col or "dr" in col:
            total_debit += pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

    bounce = df.astype(str).apply(
        lambda r: r.str.contains("return|bounce|insufficient|dishonour", case=False).any(),
        axis=1
    ).sum()

    hygiene = 90 if bounce == 0 else 70 if bounce <= 3 else 50

    return {
        "total_credit": round(total_credit,2),
        "total_debit": round(total_debit,2),
        "bounce_count": int(bounce),
        "hygiene_score": hygiene
    }

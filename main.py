from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io

app = FastAPI(title="Agri / WC Calculator")

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

# ------------------------------
# MAIN FINANCIAL ENGINE
# ------------------------------

@app.post("/analyze")
async def analyze(data: dict):

    # WC
    turnover = safe(data.get("turnover"))
    inventory = safe(data.get("inventory"))
    debtors = safe(data.get("debtors"))
    creditors = safe(data.get("creditors"))

    wc_turnover = turnover * 0.20
    wcg = (inventory + debtors) - creditors
    mpbf = wcg * 0.75 if wcg > 0 else 0
    wc_final = min(wc_turnover, mpbf) if wc_turnover and mpbf else max(wc_turnover, mpbf)

    # TL
    net_profit = safe(data.get("net_profit"))
    depreciation = safe(data.get("depreciation"))
    emi = safe(data.get("monthly_emi"))

    cash_accrual = net_profit + depreciation
    annual_emi = emi * 12
    dscr = cash_accrual / annual_emi if annual_emi > 0 else 0
    surplus = cash_accrual - annual_emi
    tl_eligible = surplus * 6 if surplus > 0 else 0

    # AGRI
    tax_paid = safe(data.get("tax_paid"))
    undoc = safe(data.get("undocumented_income"))

    nca = net_profit + depreciation - tax_paid
    scaling = 0.70 if turnover > 3000000 else 0.60
    scaled_income = nca * scaling
    monthly_surplus = (scaled_income/12) - emi + ((undoc*0.42)/12)
    agri_eligible = monthly_surplus / 0.14 if monthly_surplus > 0 else 0

    return {
        "wc": round(wc_final,2),
        "wc_turnover": round(wc_turnover,2),
        "mpbf": round(mpbf,2),
        "cash_accrual": round(cash_accrual,2),
        "dscr": round(dscr,2),
        "tl_eligible": round(tl_eligible,2),
        "nca": round(nca,2),
        "agri_eligible": round(agri_eligible,2)
    }

# ------------------------------
# BANKING PERFIOS ENGINE
# ------------------------------

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

    avg_credit = total_credit / 6 if total_credit else 0
    hygiene = 90 if bounce == 0 else 70 if bounce <= 3 else 50

    return {
        "total_credit": round(total_credit,2),
        "total_debit": round(total_debit,2),
        "avg_monthly_credit": round(avg_credit,2),
        "bounce_count": int(bounce),
        "hygiene_score": hygiene
    }

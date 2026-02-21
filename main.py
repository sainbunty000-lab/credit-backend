from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import re

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

@app.post("/analyze")
async def analyze(data: dict):

    turnover = safe(data.get("turnover"))
    inventory = safe(data.get("inventory"))
    debtors = safe(data.get("debtors"))
    creditors = safe(data.get("creditors"))
    net_profit = safe(data.get("net_profit"))
    depreciation = safe(data.get("depreciation"))
    emi = safe(data.get("monthly_emi"))
    tax_paid = safe(data.get("tax_paid"))
    undoc = safe(data.get("undocumented_income"))

    # WC
    wc_turnover = turnover * 0.20
    wcg = (inventory + debtors) - creditors
    wc_mpbf = wcg * 0.75 if wcg > 0 else 0
    wc_final = min(wc_turnover, wc_mpbf) if wc_turnover and wc_mpbf else max(wc_turnover, wc_mpbf)

    # DSCR
    annual_emi = emi * 12
    dscr = (net_profit + depreciation) / annual_emi if annual_emi > 0 else 0

    # Agriculture
    nca = net_profit + depreciation - tax_paid
    scaling = 0.70 if turnover > 3000000 else 0.60
    scaled = nca * scaling
    monthly_surplus = (scaled/12) - emi + ((undoc*0.42)/12)
    agri_eligible = (monthly_surplus/0.14) if monthly_surplus > 0 else 0

    return {
        "wc": round(wc_final,2),
        "mpbf": round(wc_mpbf,2),
        "dscr": round(dscr,2),
        "agri": round(agri_eligible,2)
    }

@app.post("/banking")
async def banking(file: UploadFile = File(...)):
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content)) if file.filename.endswith(("xls","xlsx")) else pd.read_csv(io.BytesIO(content))

    credit_cols = [c for c in df.columns if "credit" in c.lower()]
    debit_cols = [c for c in df.columns if "debit" in c.lower()]

    total_credit = df[credit_cols[0]].sum() if credit_cols else 0
    bounce_count = df.astype(str).apply(lambda row: row.str.contains("return|bounce|insufficient|dishonour", case=False).any(), axis=1).sum()

    months = 6
    avg_monthly_credit = total_credit / months if months else 0

    hygiene = 90 if bounce_count == 0 else 70 if bounce_count <= 3 else 50

    return {
        "total_credit": round(total_credit,2),
        "avg_monthly_credit": round(avg_monthly_credit,2),
        "bounce_count": int(bounce_count),
        "hygiene_score": hygiene
    }

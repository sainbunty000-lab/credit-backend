from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agri / WC Calculator - V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe(v):
    try:
        return float(v)
    except:
        return 0.0

@app.post("/analyze")
async def analyze(payload: dict):

    # ===================== WORKING CAPITAL =====================
    turnover = safe(payload.get("turnover"))
    inventory = safe(payload.get("inventory"))
    debtors = safe(payload.get("debtors"))
    creditors = safe(payload.get("creditors"))

    current_assets = inventory + debtors
    current_liabilities = creditors

    wc_turnover = 0.20 * turnover
    mpbf = 0.75 * (current_assets - current_liabilities)
    nwc = current_assets - current_liabilities
    current_ratio = (current_assets / current_liabilities) if current_liabilities > 0 else 0

    wc_limit = min(wc_turnover, mpbf) if mpbf > 0 else 0

    # ===================== TERM LOAN =====================
    tl_profit = safe(payload.get("tl_profit"))
    tl_dep = safe(payload.get("tl_dep"))
    tl_emi = safe(payload.get("tl_emi"))
    tl_tenure = safe(payload.get("tl_tenure", 5))

    cash_accrual = tl_profit + tl_dep
    annual_emi = tl_emi * 12

    dscr = (cash_accrual / annual_emi) if annual_emi > 0 else 0
    surplus = cash_accrual - annual_emi
    tl_limit = surplus * tl_tenure if surplus > 0 else 0

    # ===================== AGRICULTURE =====================
    ag_profit = safe(payload.get("ag_profit"))
    ag_dep = safe(payload.get("ag_dep"))
    ag_tax = safe(payload.get("ag_tax"))
    ag_emi = safe(payload.get("ag_emi"))
    loan_required = safe(payload.get("loan_required"))
    undoc = safe(payload.get("undoc"))

    nca = ag_profit + ag_dep - ag_tax
    scaling = 0.70 if loan_required > 3000000 else 0.60
    scaled_income = nca * scaling

    monthly_surplus = (scaled_income / 12) - ag_emi + ((0.42 * undoc) / 12)
    agri_limit = monthly_surplus * 60 if monthly_surplus > 0 else 0

    # ===================== COMBINED =====================
    total_exposure = wc_limit + tl_limit + agri_limit

    # ===================== SIMPLE RISK MODEL =====================
    hygiene = safe(payload.get("hygiene", 80))
    score = 0

    if wc_limit > 0: score += 20
    if tl_limit > 0: score += 20
    if agri_limit > 0: score += 20
    if dscr > 1.5: score += 20
    score += (hygiene / 100) * 20

    risk_score = round(min(score, 100))

    if risk_score >= 85:
        rating = "AAA"
    elif risk_score >= 75:
        rating = "AA"
    elif risk_score >= 65:
        rating = "A"
    elif risk_score >= 55:
        rating = "BBB"
    else:
        rating = "BB"

    # ===================== CAM NARRATIVE =====================
    narrative = f"""
Working Capital assessed at ₹{round(wc_limit)} based on Turnover method (₹{round(wc_turnover)})
and MPBF (₹{round(mpbf)}). Current Ratio stands at {round(current_ratio,2)}.

Term Loan evaluated with DSCR of {round(dscr,2)}.
Eligible TL computed at ₹{round(tl_limit)}.

Agriculture eligibility derived using NCA model with scaling {scaling}.
Eligible exposure ₹{round(agri_limit)}.

Combined Exposure recommended at ₹{round(total_exposure)}.
Composite Risk Score {risk_score} with internal rating {rating}.
"""

    return {
        "wc_limit": round(wc_limit),
        "mpbf": round(mpbf),
        "current_ratio": round(current_ratio,2),
        "tl_limit": round(tl_limit),
        "dscr": round(dscr,2),
        "agri_limit": round(agri_limit),
        "total_exposure": round(total_exposure),
        "risk_score": risk_score,
        "rating": rating,
        "narrative": narrative
    }

@app.get("/")
def health():
    return {"status": "V1 Production Running"}

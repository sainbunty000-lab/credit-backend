from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import math

app = FastAPI(title="Agri / WC Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- SAFE PARSER ----------------

def safe(value):
    try:
        return float(value)
    except:
        return 0.0

# ---------------- MAIN ANALYSIS ----------------

@app.post("/analyze")
async def analyze(payload: dict):

    # ---------------- INPUTS ----------------

    turnover = safe(payload.get("turnover"))
    inventory = safe(payload.get("inventory"))
    debtors = safe(payload.get("debtors"))
    creditors = safe(payload.get("creditors"))

    tl_profit = safe(payload.get("tl_profit"))
    tl_dep = safe(payload.get("tl_depreciation"))
    tl_emi = safe(payload.get("tl_monthly_emi"))

    ag_profit = safe(payload.get("ag_profit"))
    ag_dep = safe(payload.get("ag_depreciation"))
    ag_tax = safe(payload.get("ag_tax"))
    ag_emi = safe(payload.get("ag_monthly_emi"))
    loan_required = safe(payload.get("loan_required"))
    undoc = safe(payload.get("undocumented_income"))

    stress_wc = safe(payload.get("stress_wc", 20))
    stress_tl = safe(payload.get("stress_tl", 20))
    stress_agri = safe(payload.get("stress_agri", 14))

    hygiene = safe(payload.get("hygiene_score", 80))

    # ---------------- WORKING CAPITAL ----------------

    wc_turnover = turnover * (stress_wc / 100)
    mpbf = 0.75 * ((inventory + debtors) - creditors)
    wc_limit = max(0, min(wc_turnover, mpbf))

    # ---------------- TERM LOAN ----------------

    cash_accrual = tl_profit + tl_dep
    annual_emi = tl_emi * 12
    dscr = cash_accrual / annual_emi if annual_emi > 0 else 0

    tl_surplus = cash_accrual - annual_emi
    tl_limit = max(0, tl_surplus * (stress_tl / 10))

    # ---------------- AGRICULTURE ----------------

    nca = ag_profit + ag_dep - ag_tax
    scaling = 0.70 if loan_required > 3000000 else 0.60
    scaled_income = nca * scaling

    monthly_surplus = (scaled_income / 12) - ag_emi + ((undoc * 0.42) / 12)
    agri_limit = monthly_surplus / (stress_agri / 100) if monthly_surplus > 0 else 0

    # ---------------- RISK ENGINE ----------------

    score = 0

    if wc_limit > 0:
        score += 20
    if tl_limit > 0:
        score += 20
    if agri_limit > 0:
        score += 20

    if dscr > 1.5:
        score += 20
    elif dscr > 1.2:
        score += 15

    score += hygiene * 0.2
    risk_score = min(100, round(score))

    # ---------------- RATING ----------------

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

    # ---------------- CAM NARRATIVE ----------------

    cam_narrative = f"""
    The borrower’s working capital eligibility is assessed at ₹{round(wc_limit)} 
    based on turnover stress method and MPBF evaluation.

    Term loan repayment capacity evaluated with DSCR of {round(dscr,2)} 
    resulting in eligible term exposure of ₹{round(tl_limit)}.

    Agriculture eligibility computed using NCA model with scaling factor {scaling} 
    and stress factor {stress_agri}% giving final agri limit of ₹{round(agri_limit)}.

    Banking hygiene score considered at {hygiene}, leading to final internal rating {rating} 
    with composite risk score {risk_score}.
    """

    return {
        "wc_limit": round(wc_limit),
        "tl_limit": round(tl_limit),
        "agri_limit": round(agri_limit),
        "risk_score": risk_score,
        "rating": rating,
        "cam_narrative": cam_narrative
    }


@app.get("/")
def health():
    return {"status": "Agri / WC Calculator Running"}

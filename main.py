from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Agri / WC Calculator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreditInput(BaseModel):
    # WC
    turnover: Optional[float] = 0
    inventory: Optional[float] = 0
    debtors: Optional[float] = 0
    creditors: Optional[float] = 0

    # TL
    net_profit: Optional[float] = 0
    depreciation: Optional[float] = 0
    monthly_emi: Optional[float] = 0

    # AGRI
    tax_paid: Optional[float] = 0
    undocumented_income: Optional[float] = 0
    requested_loan: Optional[float] = 0


@app.post("/analyze")
def analyze(data: CreditInput):

    # Safe values
    turnover = data.turnover or 0
    inventory = data.inventory or 0
    debtors = data.debtors or 0
    creditors = data.creditors or 0

    net_profit = data.net_profit or 0
    depreciation = data.depreciation or 0
    monthly_emi = data.monthly_emi or 0

    tax_paid = data.tax_paid or 0
    undocumented = data.undocumented_income or 0
    requested = data.requested_loan or 0

    # =========================
    # WORKING CAPITAL (RBI)
    # =========================
    turnover_method = 0.20 * turnover

    tca = inventory + debtors
    ocl = creditors
    wc_gap = tca - ocl
    borrower_margin = 0.25 * tca
    mpbf = max(0, wc_gap - borrower_margin)

    wc_eligible = min(turnover_method, mpbf) if turnover_method and mpbf else max(turnover_method, mpbf)
    current_ratio = (tca / ocl) if ocl else 0

    # =========================
    # TERM LOAN (DSCR)
    # =========================
    annual_installment = monthly_emi * 12
    cash_accrual = net_profit + depreciation
    dscr = (cash_accrual / annual_installment) if annual_installment else 0

    # =========================
    # AGRICULTURE (YOUR MODEL)
    # =========================
    nca = net_profit + depreciation - tax_paid
    scaling = 0.70 if requested > 3000000 else 0.60
    scaled_income = nca * scaling
    adjusted_undoc = undocumented * 0.42

    monthly_surplus = (scaled_income / 12) - monthly_emi + (adjusted_undoc / 12)
    agri_eligible = (monthly_surplus / 0.14) if monthly_surplus > 0 else 0

    # =========================
    # FINAL
    # =========================
    candidates = [v for v in [wc_eligible, agri_eligible, requested] if v > 0]
    final_recommendation = min(candidates) if candidates else 0

    return {
        "wc_eligible": round(wc_eligible, 2),
        "mpbf": round(mpbf, 2),
        "turnover_method": round(turnover_method, 2),
        "current_ratio": round(current_ratio, 2),
        "dscr": round(dscr, 2),
        "agri_eligible": round(agri_eligible, 2),
        "monthly_surplus": round(monthly_surplus, 2),
        "final_recommendation": round(final_recommendation, 2)
    }

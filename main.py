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

# -----------------------------
# REQUEST MODEL
# -----------------------------

class CreditInput(BaseModel):
    # Financial
    turnover: Optional[float] = 0
    net_profit: Optional[float] = 0
    depreciation: Optional[float] = 0
    tax_paid: Optional[float] = 0
    inventory: Optional[float] = 0
    debtors: Optional[float] = 0
    creditors: Optional[float] = 0
    
    # Term Loan
    annual_installment: Optional[float] = 0
    
    # Agriculture
    undocumented_income: Optional[float] = 0
    existing_emi: Optional[float] = 0
    requested_loan: Optional[float] = 0

# -----------------------------
# ENGINE
# -----------------------------

@app.post("/analyze")
def analyze(data: CreditInput):

    # --- Working Capital (RBI) ---
    turnover_wc = 0.20 * (data.turnover or 0)

    tca = (data.inventory or 0) + (data.debtors or 0)
    ocl = (data.creditors or 0)
    wc_gap = tca - ocl
    borrower_margin = 0.25 * tca
    mpbf = max(0, wc_gap - borrower_margin)

    wc_eligible = min(turnover_wc, mpbf) if turnover_wc and mpbf else max(turnover_wc, mpbf)

    current_ratio = (tca / ocl) if ocl else 0

    # --- Term Loan (DSCR RBI Principle) ---
    cash_accrual = (data.net_profit or 0) + (data.depreciation or 0)
    dscr = (cash_accrual / data.annual_installment) if data.annual_installment else 0

    # --- Agriculture (Your Model) ---
    nca = (data.net_profit or 0) + (data.depreciation or 0) - (data.tax_paid or 0)

    scaling = 0.70 if (data.requested_loan or 0) > 3000000 else 0.60
    scaled_income = nca * scaling

    adjusted_undoc = (data.undocumented_income or 0) * 0.42

    monthly_surplus = (scaled_income / 12) - (data.existing_emi or 0) + (adjusted_undoc / 12)

    agri_eligible = (monthly_surplus / 0.14) if monthly_surplus > 0 else 0

    # --- Final Recommendation ---
    final_recommend = min(
        x for x in [
            wc_eligible,
            agri_eligible,
            data.requested_loan or 0
        ] if x > 0
    ) if any([wc_eligible, agri_eligible]) else 0

    return {
        "working_capital": round(wc_eligible,2),
        "mpbf": round(mpbf,2),
        "turnover_method": round(turnover_wc,2),
        "current_ratio": round(current_ratio,2),
        "dscr": round(dscr,2),
        "agriculture_eligible": round(agri_eligible,2),
        "monthly_surplus": round(monthly_surplus,2),
        "final_recommendation": round(final_recommend,2)
    }

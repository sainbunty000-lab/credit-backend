
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Credit Underwriting API")


class FinancialInput(BaseModel):
    sales: float
    pat: float
    dep: float
    stock: float
    debtors: float
    creditors: float
    loan_req: float
    emi: float
    undocumented: float
    bounce: int


@app.get("/")
def home():
    return {"message": "Credit Underwriting API Running Successfully"}


def calculate_nca(pat, dep):
    return pat + dep


def income_model(pat, dep, loan_req, emi, undocumented):
    nca = calculate_nca(pat, dep)
    scale = 0.7 if loan_req > 3000000 else 0.6
    surplus = (nca * scale / 12) - emi + (undocumented * 0.42 / 12)
    return max(0, surplus / 0.14)


def turnover_model(sales):
    return sales * 0.20


def mpbf(stock, debtors, creditors):
    gap = (stock + debtors) - creditors
    return max(0, gap * 0.75)


def final_limit(income, turnover, mpbf_val):
    return min(income, turnover, mpbf_val)


def risk_score(margin, current_ratio, bounce):
    score = 0

    if margin > 10:
        score += 20
    elif margin > 5:
        score += 15
    else:
        score += 8

    if current_ratio >= 1.5:
        score += 20
    elif current_ratio >= 1.2:
        score += 15
    else:
        score += 8

    if bounce == 0:
        score += 20
    elif bounce <= 2:
        score += 15
    else:
        score += 5

    return score


@app.post("/analyze")
def analyze(data: FinancialInput):

    margin = (data.pat / data.sales) * 100 if data.sales > 0 else 0
    current_ratio = (data.stock + data.debtors) / data.creditors if data.creditors > 0 else 0

    income = income_model(
        data.pat,
        data.dep,
        data.loan_req,
        data.emi,
        data.undocumented
    )

    turnover = turnover_model(data.sales)
    mpbf_val = mpbf(data.stock, data.debtors, data.creditors)

    final = final_limit(income, turnover, mpbf_val)

    score = risk_score(margin, current_ratio, data.bounce)

    decision = "Approve" if score >= 60 else "Review"

    return {
        "NCA": data.pat + data.dep,
        "Income_Model": round(income, 2),
        "Turnover_Model": round(turnover, 2),
        "MPBF": round(mpbf_val, 2),
        "Final_Limit": round(final, 2),
        "Risk_Score": score,
        "Decision": decision
    }

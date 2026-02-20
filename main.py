from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Agri / WC Calculator Running"}

def extract_amount(text, keywords):
    for key in keywords:
        pattern = rf"{key}[^0-9]*([\d,]+\.\d+|[\d,]+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0

@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(None)
):

    bs_content = (await bs_file.read()).decode(errors="ignore").lower()
    pl_content = (await pl_file.read()).decode(errors="ignore").lower()

    sales = extract_amount(pl_content, ["sales","turnover"])
    profit = extract_amount(pl_content, ["net profit"])
    inventory = extract_amount(bs_content, ["inventory","stock"])
    debtors = extract_amount(bs_content, ["debtors"])
    creditors = extract_amount(bs_content, ["creditors"])

    current_assets = inventory + debtors
    current_liabilities = creditors
    nwc = current_assets - current_liabilities
    current_ratio = current_assets / current_liabilities if current_liabilities else 0
    mpbf = (0.75 * current_assets) - current_liabilities
    wc_limit = sales * 0.20 if sales else 0
    agri_limit = ((profit * 0.60)/12)/0.14 if profit else 0

    risk_score = 80
    if current_ratio < 1:
        risk_score -= 20
    if profit <= 0:
        risk_score -= 20

    decision = "Approve" if risk_score >= 60 else "Review"

    return {
        "Case_ID": str(uuid.uuid4())[:8],
        "Sales": sales,
        "NWC": nwc,
        "Current_Ratio": current_ratio,
        "MPBF": mpbf,
        "Working_Capital_Limit": wc_limit,
        "Agri_Limit": agri_limit,
        "Risk_Score": risk_score,
        "Decision": decision
    }

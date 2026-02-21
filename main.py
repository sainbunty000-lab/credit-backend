from fastapi import FastAPI, UploadFile, File
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

# ---------------------------------
# SMART NUMBER CLEANER
# ---------------------------------

def clean_number(value):
    try:
        value = str(value)
        value = re.sub(r"[^\d\.-]", "", value)
        return float(value)
    except:
        return 0.0


# ---------------------------------
# UNIVERSAL FINANCIAL PARSER
# ---------------------------------

def extract_financial_data(df):

    df = df.fillna("")
    df = df.astype(str)

    rows = df.values.tolist()

    keywords = {
        "sales": ["sales", "by sales", "sales account", "turnover"],
        "profit": ["net profit", "to net profit"],
        "closing_stock": ["closing stock"],
        "debtors": ["sundry debtors"],
        "creditors": ["sundry creditors"],
        "current_assets": ["current asset"],
        "current_liabilities": ["current liabilities"]
    }

    result = {k: 0 for k in keywords.keys()}

    for row in rows:
        row_lower = [str(x).lower() for x in row]

        for key, word_list in keywords.items():
            for word in word_list:
                for i, cell in enumerate(row_lower):
                    if word in cell:

                        # Look for numeric in same row
                        for value in row:
                            number = clean_number(value)
                            if number > 0:
                                result[key] = number
                                break

    return result


# ---------------------------------
# FILE PARSER (MULTI-SHEET)
# ---------------------------------

async def parse_file(file: UploadFile):

    if not file:
        return {}

    content = await file.read()
    name = file.filename.lower()
    final_data = {}

    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):

            excel = pd.ExcelFile(io.BytesIO(content))

            for sheet in excel.sheet_names:
                df = excel.parse(sheet, header=None)
                data = extract_financial_data(df)

                for k, v in data.items():
                    if v > 0:
                        final_data[k] = v

        elif name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), header=None)
            final_data = extract_financial_data(df)

    except Exception as e:
        print("PARSE ERROR:", e)

    return final_data


# ---------------------------------
# ANALYSIS ENGINE
# ---------------------------------

@app.get("/")
def home():
    return {"status": "Agri / WC Calculator Running"}


@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(None)
):

    bs_data = await parse_file(bs_file)
    pl_data = await parse_file(pl_file)

    data = {**bs_data, **pl_data}

    sales = data.get("sales", 0)
    profit = data.get("profit", 0)
    inventory = data.get("closing_stock", 0)
    debtors = data.get("debtors", 0)
    creditors = data.get("creditors", 0)
    current_assets = data.get("current_assets", inventory + debtors)
    current_liabilities = data.get("current_liabilities", creditors)

    # Financial Calculations

    nwc = current_assets - current_liabilities
    current_ratio = (
        current_assets / current_liabilities
        if current_liabilities > 0 else 0
    )

    wc_gap = inventory + debtors - creditors
    mpbf = max(0, (0.75 * wc_gap) - nwc)
    turnover_limit = 0.20 * sales
    wc_limit = max(mpbf, turnover_limit)
    agri_limit = 0.30 * wc_limit

    # Risk Scoring

    risk_score = 100

    if current_ratio < 1:
        risk_score -= 30
    elif current_ratio < 1.33:
        risk_score -= 15

    if profit <= 0:
        risk_score -= 25

    if sales == 0:
        risk_score -= 20

    if nwc < 0:
        risk_score -= 20

    risk_score = max(0, risk_score)

    decision = "Approve"
    if risk_score < 50:
        decision = "Reject"
    elif risk_score < 70:
        decision = "Review"

    return {
        "Sales": round(sales, 2),
        "NWC": round(nwc, 2),
        "Current_Ratio": round(current_ratio, 2),
        "MPBF": round(mpbf, 2),
        "Working_Capital_Limit": round(wc_limit, 2),
        "Agri_Limit": round(agri_limit, 2),
        "Risk_Score": risk_score,
        "Decision": decision
    }

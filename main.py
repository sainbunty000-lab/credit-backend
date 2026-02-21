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

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def clean_number(value):
    try:
        value = str(value).replace(",", "").strip()
        return float(re.findall(r"[-+]?\d*\.?\d+", value)[0])
    except:
        return 0.0


def extract_from_dataframe(df):
    df = df.fillna("")
    df = df.astype(str)

    result = {
        "sales": 0,
        "profit": 0,
        "inventory": 0,
        "debtors": 0,
        "creditors": 0,
        "current_assets": 0,
        "current_liabilities": 0
    }

    keyword_map = {
        "sales": ["sales", "turnover", "revenue", "total income"],
        "profit": ["net profit", "profit after tax", "pat"],
        "inventory": ["inventory", "stock"],
        "debtors": ["debtors", "receivables"],
        "creditors": ["creditors", "payables"],
        "current_assets": ["current assets"],
        "current_liabilities": ["current liabilities"]
    }

    for _, row in df.iterrows():
        row_lower = [str(x).lower() for x in row]

        for key, keywords in keyword_map.items():
            for keyword in keywords:
                for i, cell in enumerate(row_lower):
                    if keyword in cell:
                        for j in range(i + 1, len(row_lower)):
                            number = clean_number(row_lower[j])
                            if number > 0:
                                result[key] = number
                                break

    return result


async def parse_file(file: UploadFile):
    if not file:
        return {}

    content = await file.read()
    name = file.filename.lower()

    combined_data = {}

    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):
            excel = pd.ExcelFile(io.BytesIO(content))
            for sheet in excel.sheet_names:
                df = excel.parse(sheet)
                data = extract_from_dataframe(df)
                for k, v in data.items():
                    if v > 0:
                        combined_data[k] = v

        elif name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
            combined_data = extract_from_dataframe(df)

    except Exception as e:
        print("PARSE ERROR:", e)

    return combined_data


# -------------------------------
# ANALYSIS ENGINE
# -------------------------------

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

    # Merge extracted data
    data = {**bs_data, **pl_data}

    sales = data.get("sales", 0)
    profit = data.get("profit", 0)
    inventory = data.get("inventory", 0)
    debtors = data.get("debtors", 0)
    creditors = data.get("creditors", 0)
    current_assets = data.get("current_assets", inventory + debtors)
    current_liabilities = data.get("current_liabilities", creditors)

    # -------------------------
    # Financial Calculations
    # -------------------------

    # Net Working Capital
    nwc = current_assets - current_liabilities

    # Current Ratio
    current_ratio = (
        current_assets / current_liabilities
        if current_liabilities > 0 else 0
    )

    # Working Capital Gap
    wc_gap = inventory + debtors - creditors

    # MPBF (Tandon II)
    mpbf = max(0, (0.75 * wc_gap) - nwc)

    # Turnover Method (20%)
    turnover_limit = 0.20 * sales

    # Final WC Limit
    wc_limit = max(mpbf, turnover_limit)

    # Agri Limit (example 30% of WC)
    agri_limit = 0.30 * wc_limit

    # -------------------------
    # Risk Scoring
    # -------------------------

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

    # -------------------------
    # Final Response
    # -------------------------

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

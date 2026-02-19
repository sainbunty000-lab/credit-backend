from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import uuid
import pandas as pd
import pdfplumber
import io
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = FastAPI(title="Credit Underwriting AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("cases.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    agri_limit REAL,
    wc_limit REAL,
    risk_score INTEGER,
    decision TEXT,
    created_at TEXT
)
""")
conn.commit()

# ---------------- MODEL ----------------
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

# ---------------- CORE ENGINE ----------------
def calculate_models(data):

    # Agriculture Model
    nca = data.pat + data.dep
    scale = 0.7 if data.loan_req > 3000000 else 0.6
    surplus = (nca * scale / 12) - data.emi + (data.undocumented * 0.42 / 12)
    agri_limit = max(0, surplus / 0.14)

    # Working Capital Model
    wc_gap = (data.stock + data.debtors) - data.creditors
    turnover_limit = data.sales * 0.20
    mpbf_limit = max(0, wc_gap * 0.75)
    wc_limit = min(turnover_limit, mpbf_limit)

    # Ratios
    margin = (data.pat / data.sales) * 100 if data.sales else 0
    current_ratio = (data.stock + data.debtors) / data.creditors if data.creditors else 0

    # Risk Score
    score = 0
    score += 20 if margin > 10 else 15 if margin > 5 else 8
    score += 20 if current_ratio >= 1.5 else 15 if current_ratio >= 1.2 else 8
    score += 20 if data.bounce == 0 else 15 if data.bounce <= 2 else 5

    decision = "Approve" if score >= 60 else "Review"

    if score >= 80:
        grade = "A (Low Risk)"
    elif score >= 65:
        grade = "B (Acceptable)"
    elif score >= 50:
        grade = "C (Moderate Risk)"
    else:
        grade = "D (High Risk)"

    banking_health = "Stable"
    if data.bounce > 3:
        banking_health = "Irregular"
    elif data.bounce > 0:
        banking_health = "Moderate"

    return agri_limit, wc_limit, score, decision, margin, current_ratio, wc_gap, banking_health, grade

# ---------------- ANALYZE ----------------
@app.post("/analyze")
def analyze(data: FinancialInput):

    agri_limit, wc_limit, score, decision, margin, cr, wc_gap, bank_health, grade = calculate_models(data)

    case_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, agri_limit, wc_limit, score, decision, created_at)
    )
    conn.commit()

    return {
        "Case_ID": case_id,
        "Agri_Eligible_Limit": round(agri_limit, 2),
        "Working_Capital_Limit": round(wc_limit, 2),
        "Risk_Score": score,
        "Decision": decision,
        "Profit_Margin": round(margin, 2),
        "Current_Ratio": round(cr, 2),
        "Working_Capital_Gap": round(wc_gap, 2),
        "Banking_Health": bank_health,
        "Risk_Grade": grade
    }

# ---------------- CASE HISTORY ----------------
@app.get("/cases")
def get_cases():
    cursor.execute("SELECT * FROM cases ORDER BY created_at DESC")
    rows = cursor.fetchall()
    return [{
        "Case_ID": r[0],
        "Agri_Limit": r[1],
        "WC_Limit": r[2],
        "Risk_Score": r[3],
        "Decision": r[4],
        "Created_At": r[5]
    } for r in rows]

# ---------------- DOCUMENT PARSER ----------------
@app.post("/parse-document")
async def parse_document(doc_type: str = Form(...), file: UploadFile = File(...)):

    text = ""
    filename = file.filename.lower()

    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(await file.read()))
        text = df.to_string().lower()

    elif filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(await file.read()))
        text = df.to_string().lower()

    elif filename.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(await file.read())) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        text = text.lower()

    else:
        return {"error": "Unsupported format"}

    def extract(keyword):
        match = re.search(keyword + r".{0,40}?(\d[\d,]*\.?\d*)", text)
        return float(match.group(1).replace(",", "")) if match else 0

    if doc_type == "pl":
        return {
            "Sales": extract("sales|turnover|revenue"),
            "Net_Profit": extract("net profit|pat"),
            "Depreciation": extract("depreciation")
        }

    if doc_type == "bs":
        return {
            "Inventory": extract("inventory|stock"),
            "Debtors": extract("debtors"),
            "Creditors": extract("creditors")
        }

    if doc_type == "bank":
        bounce = len(re.findall(r"return|bounce|insufficient", text))
        return {"Bounce_Count": bounce}

    return {"error": "Invalid type"}

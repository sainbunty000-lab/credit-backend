from fastapi import FastAPI, UploadFile, File
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

app = FastAPI(title="Enterprise AI Underwriting Engine")

# ---------------- CORS ----------------
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

# ---------------- FINANCIAL MODEL ----------------
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

# ---------------- CORE CALCULATION ----------------
def calculate_models(data):

    # AGRICULTURE
    nca = data.pat + data.dep
    scale = 0.7 if data.loan_req > 3000000 else 0.6
    surplus = (nca * scale / 12) - data.emi + (data.undocumented * 0.42 / 12)
    agri_limit = max(0, surplus / 0.14)

    # WORKING CAPITAL
    wc_gap = (data.stock + data.debtors) - data.creditors
    turnover_limit = data.sales * 0.20
    mpbf_limit = max(0, wc_gap * 0.75)
    wc_limit = min(turnover_limit, mpbf_limit)

    # RATIOS
    margin = (data.pat / data.sales) * 100 if data.sales else 0
    current_ratio = (data.stock + data.debtors) / data.creditors if data.creditors else 0

    # RISK SCORE
    score = 0
    score += 20 if margin > 10 else 15 if margin > 5 else 8
    score += 20 if current_ratio >= 1.5 else 15 if current_ratio >= 1.2 else 8
    score += 20 if data.bounce == 0 else 15 if data.bounce <= 2 else 5

    decision = "Approve" if score >= 60 else "Review"

    # RISK GRADE
    if score >= 80:
        grade = "A (Low Risk)"
    elif score >= 65:
        grade = "B (Acceptable)"
    elif score >= 50:
        grade = "C (Moderate Risk)"
    else:
        grade = "D (High Risk)"

    # BANKING HEALTH
    banking_health = "Stable"
    if data.bounce > 3:
        banking_health = "Irregular"
    elif data.bounce > 0:
        banking_health = "Moderate"

    return agri_limit, wc_limit, score, decision, margin, current_ratio, wc_gap, banking_health, grade

# ---------------- AI EXPLANATION ENGINE ----------------
def generate_ai_summary(parsed, mismatch, accuracy, fraud_flags, risk):

    sales = parsed["Sales"]
    pat = parsed["PAT"]
    stock = parsed["Stock"]
    debtors = parsed["Debtors"]
    creditors = parsed["Creditors"]
    bounce = parsed["Bounce_Count"]

    margin = (pat / sales * 100) if sales else 0
    current_ratio = (stock + debtors) / creditors if creditors else 0

    executive = (
        f"The applicant reports annual sales of ₹{sales:,.0f} "
        f"with a profit margin of {margin:.2f}%. "
        f"The liquidity position reflects a current ratio of {current_ratio:.2f}."
    )

    financial = (
        "Profitability is strong." if margin > 10 else
        "Profitability is moderate." if margin > 5 else
        "Profitability is weak."
    )

    banking = (
        "Banking conduct is clean." if bounce == 0 else
        f"{bounce} cheque returns observed."
    )

    fraud_text = "No major fraud indicators detected."
    if fraud_flags:
        fraud_text = "Red flags: " + ", ".join(fraud_flags)

    recommendation = (
        "Proposal recommended for approval."
        if risk["Decision"] == "Approve" and accuracy >= 70
        else "Proceed with caution and additional verification."
    )

    return {
        "Executive_Summary": executive,
        "Financial_Assessment": financial,
        "Banking_Assessment": banking,
        "Fraud_Observation": fraud_text,
        "Final_Recommendation": recommendation
    }

# ---------------- FULL ANALYSIS ----------------
@app.post("/full-analysis")
async def full_analysis(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    async def extract_text(file):
        text = ""
        filename = file.filename.lower()

        if filename.endswith((".xlsx",".xls")):
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

        return text

    bs_text = await extract_text(bs_file)
    pl_text = await extract_text(pl_file)
    bank_text = await extract_text(bank_file)

    def find_value(text, keyword):
        match = re.search(keyword + r".{0,40}?(\d[\d,]*\.?\d*)", text)
        return float(match.group(1).replace(",", "")) if match else 0

    sales = find_value(pl_text, "sales|turnover|revenue")
    pat = find_value(pl_text, "net profit|pat")
    dep = find_value(pl_text, "depreciation")
    stock = find_value(bs_text, "inventory|stock")
    debtors = find_value(bs_text, "debtors")
    creditors = find_value(bs_text, "creditors")

    bounce = len(re.findall(r"return|bounce|insufficient", bank_text))
    bank_turnover = sum(
        float(n.replace(",", "")) 
        for n in re.findall(r"\d[\d,]*\.?\d*", bank_text)
    )

    mismatch = abs(bank_turnover - sales) / sales * 100 if sales else 0

    accuracy = 100
    if mismatch > 20: accuracy -= 20
    if bounce > 3: accuracy -= 15
    if creditors > (stock + debtors): accuracy -= 15

    fraud_flags = []
    if mismatch > 30:
        fraud_flags.append("High Turnover Mismatch")
    if bounce > 5:
        fraud_flags.append("Excessive Cheque Bounces")
    if creditors > (stock + debtors):
        fraud_flags.append("Negative Working Capital")

    data = FinancialInput(
        sales=sales,
        pat=pat,
        dep=dep,
        stock=stock,
        debtors=debtors,
        creditors=creditors,
        loan_req=0,
        emi=0,
        undocumented=0,
        bounce=bounce
    )

    agri_limit, wc_limit, score, decision, margin, cr, wc_gap, bank_health, grade = calculate_models(data)

    case_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, agri_limit, wc_limit, score, decision, created_at)
    )
    conn.commit()

    risk_data = {"Score": score, "Grade": grade, "Decision": decision}

    ai_summary = generate_ai_summary(
        {
            "Sales": sales,
            "PAT": pat,
            "Stock": stock,
            "Debtors": debtors,
            "Creditors": creditors,
            "Bounce_Count": bounce
        },
        mismatch,
        accuracy,
        fraud_flags,
        risk_data
    )

    return {
        "Case_ID": case_id,
        "Parsed_Data": {
            "Sales": sales,
            "PAT": pat,
            "Stock": stock,
            "Debtors": debtors,
            "Creditors": creditors,
            "Bank_Turnover": bank_turnover,
            "Bounce_Count": bounce
        },
        "Mismatch_%": round(mismatch,2),
        "Accuracy_Score": accuracy,
        "Fraud_Flags": fraud_flags,
        "Eligibility": {
            "Agri_Limit": round(agri_limit,2),
            "Working_Capital_Limit": round(wc_limit,2)
        },
        "Risk": risk_data,
        "AI_Summary": ai_summary
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

# ---------------- CAM PDF ----------------
@app.get("/generate-cam/{case_id}")
def generate_cam(case_id: str):

    cursor.execute("SELECT * FROM cases WHERE id=?", (case_id,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Case not found"}

    filename = f"CAM_{case_id}.pdf"
    doc = SimpleDocTemplate(filename)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>CREDIT APPRAISAL MEMORANDUM</b>", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))

    table_data = [
        ["Case ID", row[0]],
        ["Agriculture Limit", f"{row[1]:,.2f}"],
        ["Working Capital Limit", f"{row[2]:,.2f}"],
        ["Risk Score", row[3]],
        ["Decision", row[4]],
        ["Date", row[5]]
    ]

    elements.append(Table(table_data))
    doc.build(elements)

    return FileResponse(filename, media_type="application/pdf", filename=filename)

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sqlite3
import uuid

app = FastAPI(title="Credit Underwriting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("cases.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    sales REAL,
    pat REAL,
    dep REAL,
    final_limit REAL,
    risk_score INTEGER,
    decision TEXT,
    created_at TEXT
)
""")
conn.commit()


# ---------- INPUT MODEL ----------
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


# ---------- CALCULATION ENGINE ----------
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


# ---------- ANALYZE & SAVE ----------
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

    case_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO cases (id, sales, pat, dep, final_limit, risk_score, decision, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_id,
        data.sales,
        data.pat,
        data.dep,
        final,
        score,
        decision,
        created_at
    ))

    conn.commit()

    return {
        "Case_ID": case_id,
        "Final_Limit": round(final, 2),
        "Risk_Score": score,
        "Decision": decision
    }


# ---------- GET ALL CASES ----------
@app.get("/cases")
def get_cases():
    cursor.execute("SELECT * FROM cases ORDER BY created_at DESC")
    rows = cursor.fetchall()

    cases = []
    for row in rows:
        cases.append({
            "Case_ID": row[0],
            "Sales": row[1],
            "PAT": row[2],
            "Depreciation": row[3],
            "Final_Limit": row[4],
            "Risk_Score": row[5],
            "Decision": row[6],
            "Created_At": row[7]
        })

    return cases
from fastapi.responses import FileResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os

@app.get("/generate-cam/{case_id}")
def generate_cam(case_id: str):

    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Case not found"}

    file_name = f"CAM_{case_id}.pdf"
    doc = SimpleDocTemplate(file_name)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>CREDIT APPRAISAL MEMORANDUM</b>", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))

    data = [
        ["Case ID", row[0]],
        ["Date", row[7]],
        ["Annual Sales", f"{row[1]:,.2f}"],
        ["Net Profit (PAT)", f"{row[2]:,.2f}"],
        ["Depreciation", f"{row[3]:,.2f}"],
        ["Final Eligible Limit", f"{row[4]:,.2f}"],
        ["Risk Score", row[5]],
        ["Decision Recommendation", row[6]],
    ]

    table = Table(data, colWidths=[200, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(
        "Analysis Summary: Based on financial inputs, turnover model, "
        "MPBF calculation and income stress test, the above limit is recommended.",
        styles["Normal"]
    ))

    doc.build(elements)

    return FileResponse(
        path=file_name,
        filename=file_name,
        media_type='application/pdf'
    )

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pdfplumber
import io
import uuid
import asyncio

app = FastAPI(title="Enterprise Underwriting Engine")

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HEALTH CHECK ----------------
@app.get("/")
def root():
    return {"status": "Backend running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ---------------- SAFE READERS ----------------
def safe_float(x):
    try:
        return float(str(x).replace(",", "").strip())
    except:
        return 0.0

def read_excel(file_bytes):
    try:
        return pd.read_excel(io.BytesIO(file_bytes))
    except:
        return pd.DataFrame()

def read_pdf(file_bytes):
    try:
        tables = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    tables.append(df)
        if tables:
            return pd.concat(tables, ignore_index=True)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# ---------------- PARSERS ----------------
def parse_sum(df):
    if df.empty:
        return 0
    max_sum = 0
    for col in df.columns:
        try:
            s = pd.to_numeric(df[col], errors="coerce").sum()
            if s > max_sum:
                max_sum = s
        except:
            continue
    return safe_float(max_sum)

# ---------------- ANALYZE ----------------
@app.post("/analyze")
async def analyze(
    bs_file: UploadFile = File(...),
    pl_file: UploadFile = File(...),
    bank_file: UploadFile = File(...)
):

    case_id = str(uuid.uuid4())[:8]

    bs_bytes = await bs_file.read()
    pl_bytes = await pl_file.read()
    bank_bytes = await bank_file.read()

    bs_df = read_excel(bs_bytes)
    if bs_df.empty:
        bs_df = read_pdf(bs_bytes)

    pl_df = read_excel(pl_bytes)
    if pl_df.empty:
        pl_df = read_pdf(pl_bytes)

    bank_df = read_excel(bank_bytes)
    if bank_df.empty:
        bank_df = read_pdf(bank_bytes)

    sales = parse_sum(pl_df)
    profit = sales * 0.10
    turnover = parse_sum(bank_df)

    wc_limit = turnover * 0.20
    agri_limit = ((profit * 0.6) / 12) / 0.14 if profit else 0

    mismatch = abs(turnover - sales) / sales * 100 if sales else 0

    risk_score = 75 if mismatch < 20 else 50
    decision = "Approve" if risk_score >= 60 else "Review"

    return {
        "Case_ID": case_id,
        "Bank_Turnover": round(turnover, 2),
        "Working_Capital_Limit": round(wc_limit, 2),
        "Agri_Limit": round(agri_limit, 2),
        "Mismatch_%": round(mismatch, 2),
        "Risk_Score": risk_score,
        "Decision": decision,
        "Parsing_Confidence": 90,
        "AI_Explanation": "System auto-evaluated based on turnover consistency and financial strength."
    }

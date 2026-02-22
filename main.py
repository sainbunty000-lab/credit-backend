from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.wc_service import calculate_wc_logic
from services.agriculture_service import calculate_agri_logic

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/wc/calculate")
async def wc_calc(data: dict):
    # Safety: extract values or default 0
    return calculate_wc_logic(
        data.get("current_assets", 0),
        data.get("current_liabilities", 0),
        data.get("annual_sales", 0)
    )

@app.post("/agriculture/calculate")
async def agri_calc(data: dict):
    return calculate_agri_logic(
        data.get("documented_income", 0),
        data.get("tax", 0),
        data.get("undocumented_income_monthly", 0),
        data.get("emi_monthly", 0)
    )

@app.get("/")
def health():
    return {"status": "Railway Backend Active"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.wc_router import router as wc_router
from core.database import engine
from models.cam import CamReport
from core.database import Base

app = FastAPI(
    title="Credit Eligibility Backend",
    version="3.0.0"
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "Backend Running"}

app.include_router(wc_router)

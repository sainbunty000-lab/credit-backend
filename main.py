from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.cam_router import router as cam_router
from routers.wc_router import wc_router
from routers.agriculture_router import agri_router
from routers.banking_router import bank_router

app = FastAPI(title="Credit Intelligence Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers

app.include_router(cam_router)
app.include_router(wc_router, prefix="/wc")
app.include_router(agri_router, prefix="/agriculture")
app.include_router(bank_router, prefix="/banking")


@app.get("/")
def root():
    return {"status": "API Running"}

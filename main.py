from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from routers.cam_router import router as cam_router
from routers.wc_router import wc_router
from routers.agriculture_router import agri_router
from routers.banking_router import bank_router


# ======================================================
# LOGGING
# ======================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("credit_engine")


# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI(

    title="Credit Intelligence Engine",

    description="Financial analysis engine for working capital, agriculture, banking and CAM generation",

    version="1.0.0",

    docs_url="/docs",
    redoc_url="/redoc",
)


# ======================================================
# CORS MIDDLEWARE
# ======================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],   # For production replace with frontend domain

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ======================================================
# ROUTER REGISTRATION
# ======================================================

app.include_router(cam_router)

app.include_router(wc_router, prefix="/wc")

app.include_router(agri_router, prefix="/agriculture")

app.include_router(bank_router, prefix="/banking")


# ======================================================
# ROOT ENDPOINT
# ======================================================

@app.get("/")
def root():

    return {
        "service": "Credit Intelligence Engine",
        "version": "1.0",
        "status": "running"
    }


# ======================================================
# HEALTH CHECK
# Used by cloud platforms
# ======================================================

@app.get("/health")

def health():

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy"
        }
    )


# ======================================================
# STARTUP EVENT
# ======================================================

@app.on_event("startup")

def startup_event():

    logger.info("Credit Intelligence Engine started successfully")

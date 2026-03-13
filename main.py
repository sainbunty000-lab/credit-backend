import time
import logging
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers.cam_router import router as cam_router
from routers.wc_router import wc_router
from routers.agriculture_router import agri_router
from routers.banking_router import bank_router


# ======================================================
# LOGGING CONFIGURATION
# ======================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("credit_engine")


# ======================================================
# FASTAPI APPLICATION
# ======================================================

app = FastAPI(

    title="Credit Intelligence Engine",

    description="""
    Financial analysis engine supporting:

    • Working Capital Analysis  
    • Agriculture Loan Eligibility  
    • Bank Statement Behaviour Analysis  
    • Credit Appraisal Memo Generation  
    """,

    version="1.0.0",

    docs_url="/docs",

    redoc_url="/redoc",

    openapi_url="/openapi.json"
)


# ======================================================
# CORS CONFIGURATION
# ======================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["http://localhost:5173/"],  # Replace with frontend domain in production

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ======================================================
# REQUEST TIMER MIDDLEWARE
# Useful for monitoring performance
# ======================================================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):

    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(round(process_time, 4))

    return response


# ======================================================
# ROUTERS
# ======================================================

app.include_router(cam_router)

app.include_router(wc_router, prefix="/wc")

app.include_router(agri_router, prefix="/agriculture")

app.include_router(bank_router, prefix="/banking")


# ======================================================
# ROOT ENDPOINT
# ======================================================

@app.get("/", tags=["System"])

def root():

    return {
        "service": "Credit Intelligence Engine",
        "version": "1.0.0",
        "modules": [
            "Working Capital Analysis",
            "Agriculture Eligibility",
            "Bank Statement Analysis",
            "CAM Generation"
        ],
        "status": "running"
    }


# ======================================================
# HEALTH CHECK
# Used by Railway / GCP / Kubernetes
# ======================================================

@app.get("/health", tags=["System"])

def health():

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "credit_engine"
        }
    )


# ======================================================
# GLOBAL ERROR HANDLER
# Prevents server crashes
# ======================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unhandled error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )

# ======================================================
# STARTUP EVENT
# ======================================================

@app.on_event("startup")
async def startup_event():

    logger.info("Credit Intelligence Engine started successfully")


# ======================================================
# SHUTDOWN EVENT
# ======================================================

@app.on_event("shutdown")
async def shutdown_event():

    logger.info("Credit Intelligence Engine shutting down")

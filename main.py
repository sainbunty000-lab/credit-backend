import time
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

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
# LIFESPAN (replaces deprecated @app.on_event)
# ======================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Credit Intelligence Engine started successfully")
    yield
    logger.info("Credit Intelligence Engine shutting down")


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

    openapi_url="/openapi.json",

    lifespan=lifespan,
)


# ======================================================
# CORS CONFIGURATION
# Allow configuring origins via ALLOWED_ORIGINS env var
# (comma-separated list) for production deployments.
# ======================================================

origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

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
# Each router already defines its own prefix – do NOT
# pass an extra prefix= here or paths will be doubled.
# ======================================================

app.include_router(cam_router)

app.include_router(wc_router)

app.include_router(agri_router)

app.include_router(bank_router)


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
# Used by GCP Cloud Run / Kubernetes
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


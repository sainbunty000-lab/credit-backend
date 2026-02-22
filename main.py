from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.wc_router import router as wc_router

app = FastAPI(
    title="Credit Eligibility Backend",
    version="1.0.0"
)

# Allow frontend access (important for React later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/")
def health_check():
    return {"status": "Backend Running Successfully"}

# Test DB endpoint (optional if you already have it)
@app.get("/test-db")
def test_db():
    return {"status": "Database Connected"}

# Include Working Capital Router
app.include_router(wc_router)

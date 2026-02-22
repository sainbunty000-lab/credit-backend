from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.wc_router import router as wc_router

app = FastAPI(
    title="Credit Eligibility Backend",
    version="1.0.0"
)

# CORS (for frontend later)
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

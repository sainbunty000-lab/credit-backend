from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import wc, agriculture, banking, cam
from core.database import engine, Base

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Credit Analysis Engine API")

# Allow Frontend access (Adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(wc.router, tags=["Working Capital"])
app.include_router(agriculture.router, tags=["Agriculture"])
app.include_router(banking.router, tags=["Banking"])
app.include_router(cam.router, tags=["CAM Storage"])

@app.get("/")
def health_check():
    return {"status": "Online", "engine": "Gemini-V1-Credit"}

from fastapi import FastAPI
from core.database import engine, Base
from models.cam import CamReport
from routers import wc, agriculture, banking, cam

app = FastAPI(title="CAM Backend")

Base.metadata.create_all(bind=engine)

app.include_router(wc.router)
app.include_router(agriculture.router)
app.include_router(banking.router)
app.include_router(cam.router)

@app.get("/")
def root():
    return {"status": "Backend Running"}

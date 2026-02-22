from fastapi import FastAPI
from core.database import engine
from sqlalchemy import text

app = FastAPI()

from routers.wc_router import router as wc_router
app.include_router(wc_router)
@app.get("/")
def health_check():
    return {"status": "Backend running 🚀"}

@app.get("/test-db")
def test_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": "Connected Successfully ✅"}

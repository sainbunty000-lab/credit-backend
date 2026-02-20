from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Agri / WC Calculator Running"}

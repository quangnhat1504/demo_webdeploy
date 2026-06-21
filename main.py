from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Backend đang hoạt động!"}
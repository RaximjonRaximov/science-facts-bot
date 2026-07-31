from fastapi import FastAPI
from app.main import build_app

app: FastAPI = build_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

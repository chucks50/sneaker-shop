from fastapi import FastAPI

app = FastAPI(title="Sneaker Shop API", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is running"}


@app.get("/")
def root():
    return {"message": "Sneaker Shop API"}

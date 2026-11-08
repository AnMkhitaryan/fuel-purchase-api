from fastapi import FastAPI

app = FastAPI(title="Fuel Purchase API")


@app.get("/health")
def health():
    return {"status": "ok"}
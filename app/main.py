
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.errors import register_error_handlers
from app.routers import admin, purchases


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Fuel Purchase API", lifespan=lifespan)
register_error_handlers(app)
app.include_router(admin.router)
app.include_router(purchases.router)


@app.get("/health")
def health():
    return {"status": "ok"}

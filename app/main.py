from fastapi import FastAPI
from app.api.endpoints import router
from app.models.video import Base
from sqlalchemy import create_engine
from app.core.config import settings

app = FastAPI(title="Highlight Detector")

engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Highlight Detector API"}
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.routes.process import router as process_router
from app.services.ocr_service import OCRService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ocr_service = OCRService()
    yield


app = FastAPI(
    title="ttb-alc-lbl-processor",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(process_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
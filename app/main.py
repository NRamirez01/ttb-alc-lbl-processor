from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.process import router as process_router
from app.services.ocr_service import OCRService


from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ocr_service = OCRService()
    yield


app = FastAPI(
    title="ttb-alc-lbl-processor",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS), name="assets")


if FRONTEND_DIST.exists():
    @app.get("/")
    def frontend_index():
        return FileResponse(FRONTEND_DIST / "index.html")


app.include_router(process_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=6333, reload=False)
"""MedExtract Clinical Assistant — FastAPI Application Entry Point"""
import os
import sys
import asyncio

# langextract is shipped as a subdirectory (langextract/langextract/).
# Add that inner directory to sys.path so `import langextract` resolves to
# the real package, not the outer namespace folder that shadows it.
_lx_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "langextract")
if _lx_path not in sys.path:
    sys.path.insert(0, _lx_path)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import analyze


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORT_DIR, exist_ok=True)
    init_db()
    print("✓ MedExtract Clinical Assistant started")
    print(f"  Host : {settings.HOST}:{settings.PORT}")
    print(f"  DB   : {settings.DB_PATH}")
    try:
        yield
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("✓ MedExtract shutting down")


app = FastAPI(
    title="MedExtract Clinical Assistant",
    description=(
        "Structured clinical data extraction from medical documents "
        "using LangExtract + Google Gemini. Supports 10 document types "
        "with character-offset source verification."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/api/v1", tags=["MedExtract"])


@app.get("/health")
async def health_check():
    return JSONResponse(content={
        "status":  "healthy",
        "service": "medextract-clinical-assistant",
        "version": "2.0.0",
    })


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

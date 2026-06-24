# main.py  –  DocReview Graphic Era Hospital | FastAPI Application
from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config.settings import get_settings
from config.database import connect_db, close_db
from routes.auth_routes import router as auth_router
from routes.doctor_routes import router as doctor_router
from routes.review_routes import router as review_router
from fastapi.middleware.cors import CORSMiddleware



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s  –  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger   = logging.getLogger("docreview")
settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    print()
    print("🏥  DocReview – Graphic Era Hospital")
    print("─────────────────────────────────────────────")
    print(f"🚀  FastAPI  →  http://{settings.app_host}:{settings.app_port}")
    print(f"📡  Swagger  →  http://localhost:{settings.app_port}/docs")
    print()
    if settings.skip_db:
        logger.warning("⚠️  SKIP_DB enabled — starting without MongoDB")
        yield
        return

    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="DocReview – Graphic Era Hospital",
    description="Patient auth, doctor listing, and verified review submission API.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [
    settings.client_origin,
    "http://127.0.0.1:5500", "http://localhost:5500",
    "http://127.0.0.1:5501", "http://localhost:5501",
    f"http://localhost:{settings.app_port}",
    f"http://127.0.0.1:{settings.app_port}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception):
    logger.error("Unhandled: %s", exc, exc_info=True)
    msg = str(exc) if settings.environment == "development" else "Internal server error"
    return JSONResponse(status_code=500, content={"success": False, "message": msg})


# ── Routers ────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(doctor_router)
app.include_router(review_router)


@app.get("/api/health", tags=["System"])
async def health():
    return {"success": True, "message": "🏥 DocReview API running", "version": "2.0.0"}


@app.get("/", tags=["System"])
async def root():
    return {
        "message": "DocReview – Graphic Era Hospital API v2",
        "endpoints": {
            "auth":         "/api/auth/...",
            "doctors":      "/api/doctors",
            "reviews":      "POST /api/reviews",
            "verify":       "POST /api/appointments/verify",
            "my_appts":     "GET  /api/appointments/mine?doctor_id=...",
            "docs":         "/docs",
        },
    }


import os
if os.path.isdir("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.environment == "development"),
        log_level="info",
    )

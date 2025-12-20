import os
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import async_engine as engine, Base, create_all_tables
from app.api.v1 import api_router

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app.main")

app = FastAPI(title="Bizio / Ecomt CRM", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

# Global exception handler to catch and log all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions, log them, and return a 500 response.
    This helps debugging on Render by showing the full stack trace in logs.
    """
    error_traceback = traceback.format_exc()
    logger.error(f"Unhandled exception on {request.method} {request.url.path}:\n{error_traceback}")
    
    # In production, you might want to hide the traceback from the response
    # For now, we include it for debugging
    is_debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "path": str(request.url.path),
            "traceback": error_traceback if is_debug else "Check server logs for details"
        }
    )

origins = os.getenv("CORS_ORIGINS", "*")
if origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup():
    try:
        create_tables = os.getenv("CREATE_TABLES_ON_STARTUP", "true").lower() in ("1", "true", "yes")
        if create_tables:
            logger.info("Creating DB tables (dev mode)...")
            await create_all_tables()
            logger.info("DB tables created")
        else:
            logger.info("Skipping automatic table creation (CREATE_TABLES_ON_STARTUP=false)")
    except Exception:
        logger.exception("Failed to create DB tables on startup")


@app.get("/", tags=["health"])
async def root():
    return {"service": "Bizio / Ecomt CRM", "status": "ok"}


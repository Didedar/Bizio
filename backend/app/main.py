import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import async_engine as engine, Base, create_all_tables
from app.api.v1 import api_router

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("app.main")

app = FastAPI(title="Bizio / Ecomt CRM", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

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

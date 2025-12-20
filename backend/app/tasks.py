# Celery tasks wrapper for both app and worker usage
import os
from celery import Celery
from sqlalchemy import text
from sqlalchemy.pool import NullPool

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ecomt:ecomtpass@postgres:5432/ecomt")

celery_app = Celery("ecomt_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# For worker tasks we will use sync SQLAlchemy engine (simple approach for Celery)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# create sync engine for worker operations
sync_engine = create_engine(DATABASE_URL.replace("+asyncpg", ""), poolclass=NullPool)
SyncSession = sessionmaker(bind=sync_engine)

@celery_app.task(name="recalc_deal_margin")
def recalc_deal_margin(deal_id: int):
    """
    Task: recalc margin for deal (example heavy task).
    This is synchronous code — Celery worker runs it.
    """
    session = SyncSession()
    try:
        # simple raw SQL for demo (or use ORM mapped classes)
        r = session.execute(text("SELECT id, total_price, total_cost FROM deals WHERE id = :id"), {"id": deal_id}).fetchone()
        if not r:
            return {"status": "not_found", "deal_id": deal_id}
        total_price = float(r[1] or 0)
        total_cost = float(r[2] or 0)
        margin = total_price - total_cost
        session.execute(text("UPDATE deals SET margin = :m WHERE id = :id"), {"m": margin, "id": deal_id})
        session.commit()
        return {"status": "ok", "deal_id": deal_id, "margin": margin}
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# Provide async-friendly .delay wrapper importable from services
recalc_deal_margin_async = recalc_deal_margin

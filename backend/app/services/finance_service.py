import calendar
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance import calculate_financials


async def calculate_monthly_finances(
    db: AsyncSession,
    tenant_id: int,
    year: int,
    month: int
) -> Dict[str, Any]:
    """
    Рассчитывает финансовые показатели за указанный месяц.
    """
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Use timezone-aware datetimes for PostgreSQL compatibility
    start_datetime = datetime.combine(first_day, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(last_day, datetime.max.time(), tzinfo=timezone.utc)
    
    return await calculate_financials(
        db=db,
        tenant_id=tenant_id,
        start_date=start_datetime,
        end_date=end_datetime
    )


async def calculate_period_finances(
    db: AsyncSession,
    tenant_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Рассчитывает финансовые показатели за произвольный период.
    """
    # Use timezone-aware datetimes for PostgreSQL compatibility
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
    
    return await calculate_financials(
        db=db,
        tenant_id=tenant_id,
        start_date=start_datetime,
        end_date=end_datetime
    )
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from . import models

logger = logging.getLogger(__name__)


def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware (UTC). Returns None if input is None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0.00")


def quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def aggregate_revenue_and_cogs(
    db: AsyncSession,
    tenant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Decimal]:
    """
    Агрегирует выручку (revenue) и себестоимость (COGS) из закрытых сделок.
    Фильтрует по статусу 'final_account' и опционально по датам closed_at.
    """
    
    # Ensure dates are timezone-aware for PostgreSQL compatibility
    start_date = ensure_timezone_aware(start_date)
    end_date = ensure_timezone_aware(end_date)
    
    logger.info(f"🔍 aggregate_revenue_and_cogs called with tenant_id={tenant_id}, start_date={start_date}, end_date={end_date}")
    
    # Сначала проверим КАКИЕ сделки есть для этого tenant_id
    debug_query = select(models.Deal).where(models.Deal.tenant_id == tenant_id)
    debug_result = await db.execute(debug_query)
    all_deals = debug_result.scalars().all()
    logger.info(f"📊 Total deals for tenant_id={tenant_id}: {len(all_deals)}")
    
    if all_deals:
        for deal in all_deals[:5]:  # Показываем первые 5
            logger.info(f"  Deal ID={deal.id}, status={deal.status}, total_price={deal.total_price}, closed_at={deal.closed_at}")
    
    # Фильтруем только завершённые сделки (final_account) по дате closed_at
    base_filter = [
        models.Deal.tenant_id == tenant_id,
        models.Deal.status == models.DealStatus.final_account,
    ]
    
    if start_date:
        base_filter.append(models.Deal.closed_at >= start_date)
    if end_date:
        base_filter.append(models.Deal.closed_at <= end_date)

    logger.info(f"🔎 Filtering with: tenant_id={tenant_id}, status=final_account, closed_at range=[{start_date}, {end_date}]")

    revenue_query = select(
        func.coalesce(func.sum(models.Deal.total_price), 0)
    ).where(*base_filter)
    
    cogs_query = select(
        func.coalesce(func.sum(models.Deal.total_cost), 0)
    ).where(*base_filter)
    
    revenue_result = await db.execute(revenue_query)
    cogs_result = await db.execute(cogs_query)
    
    revenue = to_decimal(revenue_result.scalar_one())
    cogs = to_decimal(cogs_result.scalar_one())
    
    logger.info(f"💰 Result: revenue={revenue}, cogs={cogs}")
    
    return {"revenue": revenue, "cogs": cogs}


async def get_expenses_totals(
    db: AsyncSession,
    tenant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Decimal]:
    """
    Получает суммы фиксированных и переменных расходов из таблицы Expense.
    """
    query = select(models.Expense).where(models.Expense.tenant_id == tenant_id)
    
    if start_date:
        query = query.where(models.Expense.date >= start_date)
    if end_date:
        query = query.where(models.Expense.date <= end_date)
    
    result = await db.execute(query)
    expenses = result.scalars().all()
    
    fixed = Decimal("0.00")
    variable = Decimal("0.00")
    
    for expense in expenses:
        amount = to_decimal(expense.amount)
        if expense.is_fixed:
            fixed += amount
        else:
            variable += amount
    
    return {"fixed": fixed, "variable": variable, "total": fixed + variable}


async def get_tax_rate(db: AsyncSession, tenant_id: int) -> Decimal:
    """
    Получает налоговую ставку из настроек финансов.
    """
    query = select(models.FinancialSettings).where(
        models.FinancialSettings.tenant_id == tenant_id
    )
    result = await db.execute(query)
    settings = result.scalar_one_or_none()
    
    if settings and settings.tax_rate:
        return to_decimal(settings.tax_rate)
    return Decimal("0.00")


async def calculate_financials(
    db: AsyncSession,
    tenant_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    *,
    opex: Optional[Decimal] = None,
    fixed_costs: Optional[Decimal] = None,
    variable_costs: Optional[Decimal] = None,
    taxes_percent: Optional[Decimal] = None,
    revenue_override: Optional[Decimal] = None,
    cogs_override: Optional[Decimal] = None,
) -> Dict[str, Any]:
    """
    Вычисляет все финансовые показатели:
    - Выручка (Revenue)
    - Себестоимость (COGS)
    - Валовая прибыль (Gross Profit)
    - OPEX
    - EBIT
    - Налоги
    - Чистая прибыль (Net Profit)
    - Точка безубыточности (Break-even Revenue)
    """
    
    # 1. Получаем Revenue и COGS
    if revenue_override is not None and cogs_override is not None:
        revenue = to_decimal(revenue_override)
        cogs = to_decimal(cogs_override)
    else:
        agg = await aggregate_revenue_and_cogs(db, tenant_id, start_date, end_date)
        revenue = to_decimal(revenue_override) if revenue_override is not None else agg["revenue"]
        cogs = to_decimal(cogs_override) if cogs_override is not None else agg["cogs"]
    
    # 2. Получаем расходы из БД
    expenses = await get_expenses_totals(db, tenant_id, start_date, end_date)
    db_fixed = expenses["fixed"]
    db_variable = expenses["variable"]
    db_total_expenses = expenses["total"]
    
    # 3. Налоговая ставка
    if taxes_percent is not None:
        tax_rate = to_decimal(taxes_percent)
    else:
        tax_rate = await get_tax_rate(db, tenant_id)
    
    # 4. Manual overrides для расчетов
    manual_opex = to_decimal(opex) if opex is not None else Decimal("0.00")
    manual_fixed = to_decimal(fixed_costs) if fixed_costs is not None else Decimal("0.00")
    manual_variable = to_decimal(variable_costs) if variable_costs is not None else None
    
    # 5. Расчеты
    
    # Валовая прибыль
    gross_profit = quantize(revenue - cogs)
    gross_margin_pct = quantize(
        (gross_profit / revenue * 100) if revenue > 0 else Decimal("0.00")
    )
    
    # OPEX = manual_opex + расходы из БД
    total_opex = manual_opex + db_total_expenses
    
    # EBIT = Валовая прибыль - OPEX
    ebit = quantize(gross_profit - total_opex)
    
    # Налоги (только если EBIT > 0)
    if ebit > 0 and tax_rate > 0:
        taxes = quantize(ebit * tax_rate / 100)
    else:
        taxes = Decimal("0.00")
    
    # Общие расходы для отображения
    total_expenses = quantize(cogs + total_opex + manual_fixed)
    
    # Чистая прибыль
    net_profit = quantize(revenue - total_expenses - taxes)
    net_margin_pct = quantize(
        (net_profit / revenue * 100) if revenue > 0 else Decimal("0.00")
    )
    
    # 6. Точка безубыточности
    # Break-even Revenue = Fixed Costs / Contribution Margin Ratio
    # Contribution Margin = Revenue - Variable Costs
    # Contribution Margin Ratio = Contribution Margin / Revenue
    
    total_fixed = manual_fixed + db_fixed
    total_variable = manual_variable if manual_variable is not None else (cogs + db_variable)
    
    if revenue > 0:
        contribution_margin = revenue - total_variable
        if contribution_margin > 0:
            contribution_ratio = contribution_margin / revenue
            break_even_revenue = quantize(total_fixed / contribution_ratio)
        else:
            break_even_revenue = None
    else:
        break_even_revenue = None
    
    return {
        "revenue": quantize(revenue),
        "cogs": quantize(cogs),
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "opex": quantize(total_opex),
        "ebit": ebit,
        "taxes_percent": tax_rate,
        "taxes": taxes,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "net_margin_pct": net_margin_pct,
        "fixed_costs": quantize(total_fixed),
        "variable_costs": quantize(total_variable),
        "break_even_revenue": break_even_revenue,
    }

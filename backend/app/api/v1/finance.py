# app/api/v1/finance.py

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app import models, schemas
from app.finance import calculate_financials
from app.services.finance_service import calculate_monthly_finances, calculate_period_finances

router = APIRouter(tags=["finance"])

# --- Expenses CRUD ---

@router.post("/expenses", response_model=schemas.ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: schemas.ExpenseCreate,
    tenant_id: int = Query(..., description="Tenant ID"),
    user_id: Optional[int] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db),
):

    db_expense = models.Expense(
        tenant_id=tenant_id,
        user_id=user_id,
        **expense.model_dump()
    )
    db.add(db_expense)
    await db.commit()
    await db.refresh(db_expense)
    return db_expense

@router.get("/expenses", response_model=List[schemas.ExpenseRead])
async def get_expenses(
    tenant_id: int = Query(..., description="Tenant ID"),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):

    query = select(models.Expense).where(models.Expense.tenant_id == tenant_id)
    if start:
        # Convert datetime to date for proper comparison with Date column
        query = query.where(models.Expense.date >= start.date())
    if end:
        query = query.where(models.Expense.date <= end.date())
    if category:
        query = query.where(models.Expense.category == category)

    query = query.order_by(models.Expense.date.desc())

    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db),
):

    query = select(models.Expense).where(models.Expense.id == expense_id, models.Expense.tenant_id == tenant_id)
    result = await db.execute(query)
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    await db.delete(expense)
    await db.commit()

@router.put("/expenses/{expense_id}", response_model=schemas.ExpenseRead)
async def update_expense(
    expense_id: int,
    expense_update: schemas.ExpenseUpdate,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing expense."""
    query = select(models.Expense).where(
        models.Expense.id == expense_id,
        models.Expense.tenant_id == tenant_id
    )
    result = await db.execute(query)
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Update only provided fields
    update_data = expense_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    await db.commit()
    await db.refresh(expense)
    return expense

# --- Settings ---

@router.get("/settings", response_model=schemas.FinancialSettingsRead)
async def get_financial_settings(
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.FinancialSettings).where(models.FinancialSettings.tenant_id == tenant_id)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:

        settings = models.FinancialSettings(tenant_id=tenant_id, tax_rate=Decimal("0.00"))
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings

@router.put("/settings", response_model=schemas.FinancialSettingsRead)
async def update_financial_settings(
    settings_in: schemas.FinancialSettingsCreate,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.FinancialSettings).where(models.FinancialSettings.tenant_id == tenant_id)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()

    if not settings:
        settings = models.FinancialSettings(tenant_id=tenant_id)
        db.add(settings)

    if settings_in.tax_rate is not None:
        settings.tax_rate = settings_in.tax_rate
    if settings_in.currency is not None:
        settings.currency = settings_in.currency

    await db.commit()
    await db.refresh(settings)
    return settings

# --- Dashboard ---

@router.get("/dashboard", response_model=schemas.FinanceDashboard)
async def finance_dashboard(
    tenant_id: int,
    start: Optional[datetime] = Query(None, description="Start date, ISO format"),
    end: Optional[datetime] = Query(None, description="End date, ISO format"),
    opex: Optional[Decimal] = Query(None, description="Manual OPEX adjustment"),
    fixed: Optional[Decimal] = Query(None, description="Manual Fixed Costs adjustment"),
    variable: Optional[Decimal] = Query(None, description="Manual Variable Costs adjustment"),
    tax: Optional[Decimal] = Query(None, alias="tax_percent"),
    db: AsyncSession = Depends(get_db),
):

    try:
        res = await calculate_financials(
            db,
            tenant_id,
            start_date=start,
            end_date=end,
            opex=opex,
            fixed_costs=fixed,
            variable_costs=variable,
            taxes_percent=tax,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/monthly", response_model=schemas.FinanceDashboard)
async def monthly_finance_dashboard(
    tenant_id: int = Query(..., description="Tenant ID"),
    year: int = Query(..., description="Year (e.g., 2025)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: AsyncSession = Depends(get_db)
):

    try:
        report = await calculate_monthly_finances(db, tenant_id, year, month)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/period", response_model=schemas.FinanceDashboard)
async def period_finance_dashboard(
    tenant_id: int = Query(..., description="Tenant ID"),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    try:
        report = await calculate_period_finances(db, tenant_id, start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

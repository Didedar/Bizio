# app/api/v1/dashboard.py
"""
Dashboard API for aggregated business statistics and analytics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.db import get_db
from app import models
from pydantic import BaseModel


router = APIRouter(tags=["dashboard"])


# ============================================================================
# Response Schemas
# ============================================================================

class DealStatusCount(BaseModel):
    status: str
    count: int
    label: str


class MonthlyRevenue(BaseModel):
    month: str
    revenue: float
    expenses: float
    profit: float


class TopProduct(BaseModel):
    id: int
    title: str
    category: Optional[str]
    total_quantity: int
    total_revenue: float


class RecentDeal(BaseModel):
    id: int
    title: str
    status: str
    total_price: float
    client_name: Optional[str]
    created_at: str


class DashboardStats(BaseModel):
    # Summary metrics
    total_revenue: float
    total_deals: int
    total_products: int
    total_clients: int
    
    # Comparison metrics (vs last month)
    revenue_change_pct: float
    deals_change_pct: float
    
    # Breakdown data
    deals_by_status: List[DealStatusCount]
    revenue_by_month: List[MonthlyRevenue]
    top_products: List[TopProduct]
    recent_deals: List[RecentDeal]


# ============================================================================
# Status label mapping
# ============================================================================

STATUS_LABELS = {
    'new': 'New',
    'preparing_document': 'Document Preparation',
    'prepaid_account': 'Prepaid Account',
    'at_work': 'At Work',
    'final_account': 'Final Account',
}


# ============================================================================
# Dashboard API Endpoint
# ============================================================================

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated dashboard statistics including:
    - Total revenue, deals, products, clients
    - Deals by status distribution
    - Monthly revenue breakdown (last 6 months)
    - Top selling products
    - Recent deals
    """
    
    # Current period (this month)
    now = datetime.utcnow()
    current_month_start = datetime(now.year, now.month, 1)
    
    # Last month
    last_month_end = current_month_start - timedelta(days=1)
    last_month_start = datetime(last_month_end.year, last_month_end.month, 1)
    
    # 6 months ago
    six_months_ago = now - timedelta(days=180)
    
    # =========================================================================
    # Total Revenue (from all deals or closed deals)
    # =========================================================================
    revenue_stmt = (
        select(func.coalesce(func.sum(models.Deal.total_price), 0))
        .where(models.Deal.tenant_id == tenant_id)
    )
    result = await db.execute(revenue_stmt)
    total_revenue = float(result.scalar() or 0)
    
    # Current month revenue
    current_month_revenue_stmt = (
        select(func.coalesce(func.sum(models.Deal.total_price), 0))
        .where(
            and_(
                models.Deal.tenant_id == tenant_id,
                models.Deal.created_at >= current_month_start
            )
        )
    )
    result = await db.execute(current_month_revenue_stmt)
    current_month_revenue = float(result.scalar() or 0)
    
    # Last month revenue
    last_month_revenue_stmt = (
        select(func.coalesce(func.sum(models.Deal.total_price), 0))
        .where(
            and_(
                models.Deal.tenant_id == tenant_id,
                models.Deal.created_at >= last_month_start,
                models.Deal.created_at < current_month_start
            )
        )
    )
    result = await db.execute(last_month_revenue_stmt)
    last_month_revenue = float(result.scalar() or 0)
    
    # Calculate revenue change percentage
    if last_month_revenue > 0:
        revenue_change_pct = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    else:
        revenue_change_pct = 100 if current_month_revenue > 0 else 0
    
    # =========================================================================
    # Total Deals
    # =========================================================================
    deals_stmt = (
        select(func.count())
        .select_from(models.Deal)
        .where(models.Deal.tenant_id == tenant_id)
    )
    result = await db.execute(deals_stmt)
    total_deals = result.scalar() or 0
    
    # Current month deals
    current_month_deals_stmt = (
        select(func.count())
        .select_from(models.Deal)
        .where(
            and_(
                models.Deal.tenant_id == tenant_id,
                models.Deal.created_at >= current_month_start
            )
        )
    )
    result = await db.execute(current_month_deals_stmt)
    current_month_deals = result.scalar() or 0
    
    # Last month deals
    last_month_deals_stmt = (
        select(func.count())
        .select_from(models.Deal)
        .where(
            and_(
                models.Deal.tenant_id == tenant_id,
                models.Deal.created_at >= last_month_start,
                models.Deal.created_at < current_month_start
            )
        )
    )
    result = await db.execute(last_month_deals_stmt)
    last_month_deals = result.scalar() or 0
    
    # Calculate deals change percentage
    if last_month_deals > 0:
        deals_change_pct = ((current_month_deals - last_month_deals) / last_month_deals) * 100
    else:
        deals_change_pct = 100 if current_month_deals > 0 else 0
    
    # =========================================================================
    # Total Products
    # =========================================================================
    products_stmt = (
        select(func.count())
        .select_from(models.Product)
        .where(models.Product.tenant_id == tenant_id)
    )
    result = await db.execute(products_stmt)
    total_products = result.scalar() or 0
    
    # =========================================================================
    # Total Clients
    # =========================================================================
    clients_stmt = (
        select(func.count())
        .select_from(models.Client)
        .where(models.Client.tenant_id == tenant_id)
    )
    result = await db.execute(clients_stmt)
    total_clients = result.scalar() or 0
    
    # =========================================================================
    # Deals by Status
    # =========================================================================
    status_stmt = (
        select(
            models.Deal.status,
            func.count().label('count')
        )
        .where(models.Deal.tenant_id == tenant_id)
        .group_by(models.Deal.status)
    )
    result = await db.execute(status_stmt)
    status_rows = result.fetchall()
    
    deals_by_status = [
        DealStatusCount(
            status=row.status,
            count=row.count,
            label=STATUS_LABELS.get(row.status, row.status)
        )
        for row in status_rows
    ]
    
    # =========================================================================
    # Revenue by Month (last 6 months)
    # =========================================================================
    revenue_by_month = []
    
    for i in range(5, -1, -1):
        # Calculate month boundaries
        month_date = now - timedelta(days=30 * i)
        month_start = datetime(month_date.year, month_date.month, 1)
        if month_date.month == 12:
            month_end = datetime(month_date.year + 1, 1, 1)
        else:
            month_end = datetime(month_date.year, month_date.month + 1, 1)
        
        # Revenue for this month
        month_revenue_stmt = (
            select(func.coalesce(func.sum(models.Deal.total_price), 0))
            .where(
                and_(
                    models.Deal.tenant_id == tenant_id,
                    models.Deal.created_at >= month_start,
                    models.Deal.created_at < month_end
                )
            )
        )
        result = await db.execute(month_revenue_stmt)
        month_revenue = float(result.scalar() or 0)
        
        # Cost (COGS) for this month
        month_cost_stmt = (
            select(func.coalesce(func.sum(models.Deal.total_cost), 0))
            .where(
                and_(
                    models.Deal.tenant_id == tenant_id,
                    models.Deal.created_at >= month_start,
                    models.Deal.created_at < month_end
                )
            )
        )
        result = await db.execute(month_cost_stmt)
        month_cost = float(result.scalar() or 0)
        
        # Expenses for this month
        expenses_stmt = (
            select(func.coalesce(func.sum(models.Expense.amount), 0))
            .where(
                and_(
                    models.Expense.tenant_id == tenant_id,
                    models.Expense.date >= month_start,
                    models.Expense.date < month_end
                )
            )
        )
        result = await db.execute(expenses_stmt)
        month_expenses = float(result.scalar() or 0) + month_cost
        
        month_name = month_start.strftime('%b %Y')
        
        revenue_by_month.append(MonthlyRevenue(
            month=month_name,
            revenue=month_revenue,
            expenses=month_expenses,
            profit=month_revenue - month_expenses
        ))
    
    # =========================================================================
    # Top Products (by quantity sold)
    # =========================================================================
    top_products_stmt = (
        select(
            models.Product.id,
            models.Product.title,
            models.Product.category,
            func.coalesce(func.sum(models.DealItem.quantity), 0).label('total_quantity'),
            func.coalesce(func.sum(models.DealItem.total_price), 0).label('total_revenue')
        )
        .join(models.DealItem, models.DealItem.product_id == models.Product.id, isouter=True)
        .where(models.Product.tenant_id == tenant_id)
        .group_by(models.Product.id, models.Product.title, models.Product.category)
        .order_by(func.coalesce(func.sum(models.DealItem.total_price), 0).desc())
        .limit(5)
    )
    result = await db.execute(top_products_stmt)
    top_product_rows = result.fetchall()
    
    top_products = [
        TopProduct(
            id=row.id,
            title=row.title,
            category=row.category,
            total_quantity=int(row.total_quantity),
            total_revenue=float(row.total_revenue)
        )
        for row in top_product_rows
    ]
    
    # =========================================================================
    # Recent Deals (last 10)
    # =========================================================================
    from sqlalchemy.orm import selectinload
    
    recent_deals_stmt = (
        select(models.Deal)
        .options(selectinload(models.Deal.client))
        .where(models.Deal.tenant_id == tenant_id)
        .order_by(models.Deal.created_at.desc())
        .limit(10)
    )
    result = await db.execute(recent_deals_stmt)
    recent_deal_rows = result.scalars().all()
    
    recent_deals = [
        RecentDeal(
            id=deal.id,
            title=deal.title,
            status=deal.status,
            total_price=float(deal.total_price),
            client_name=deal.client.name if deal.client else None,
            created_at=deal.created_at.isoformat()
        )
        for deal in recent_deal_rows
    ]
    
    # =========================================================================
    # Return Complete Dashboard Stats
    # =========================================================================
    return DashboardStats(
        total_revenue=total_revenue,
        total_deals=total_deals,
        total_products=total_products,
        total_clients=total_clients,
        revenue_change_pct=round(revenue_change_pct, 1),
        deals_change_pct=round(deals_change_pct, 1),
        deals_by_status=deals_by_status,
        revenue_by_month=revenue_by_month,
        top_products=top_products,
        recent_deals=recent_deals
    )

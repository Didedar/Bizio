# app/api/v1/deals.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app import crud, schemas
from app.services.crm_service import create_deal_with_items, calculate_deal_profit

router = APIRouter(tags=["deals"])

# ============================================================================
# Deal CRUD
# ============================================================================

@router.post("/", response_model=schemas.DealRead, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: schemas.DealCreate,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models

    client = await crud.get_client(db, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if payload.items:
        try:
            deal = await create_deal_with_items(db, tenant_id, payload)
            # Relationships already loaded by create_deal_with_items
            return deal
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        deal = await crud.create_deal(db, tenant_id, payload)
        # Reload with items relationship (even if empty) for consistent serialization
        stmt = (
            select(models.Deal)
            .options(
                selectinload(models.Deal.client),
                selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records),
                selectinload(models.Deal.responsible),
                selectinload(models.Deal.observers)
            )
            .where(models.Deal.id == deal.id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()

@router.get("/", response_model=List[schemas.DealRead])
async def list_deals(
    tenant_id: int = Query(..., description="Tenant ID"),
    skip: int = 0,
    limit: int = 50,
    status_filter: str = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models

    stmt = (
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{deal_id}", response_model=schemas.DealRead)
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models

    stmt = (
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.id == deal_id)
    )
    result = await db.execute(stmt)
    d = result.scalar_one_or_none()
    
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return d

@router.put("/{deal_id}", response_model=schemas.DealRead)
async def update_deal(
    deal_id: int,
    payload: schemas.DealUpdate,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models

    existing = await crud.get_deal(db, deal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Deal not found")

    if payload.client_id is not None:
        client = await crud.get_client(db, payload.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

    updated = await crud.update_deal(db, deal_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Reload with relationships
    stmt = (
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.id == deal_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()

@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(deal_id: int, db: AsyncSession = Depends(get_db)):

    existing = await crud.get_deal(db, deal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Deal not found")
    await crud.delete_deal(db, deal_id)

@router.post("/{deal_id}/status", response_model=schemas.DealRead)
async def update_deal_status(
    deal_id: int,
    status: str = Query(..., description="New status: new, in_progress, won, lost, cancelled"),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models

    try:
        d = await crud.update_deal_status(db, deal_id, status)
        if not d:
            raise HTTPException(status_code=404, detail="Deal not found")
        
        # Reload with relationships
        stmt = (
            select(models.Deal)
            .options(
                selectinload(models.Deal.client),
                selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records)
            )
            .where(models.Deal.id == deal_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Deal Items Management
# ============================================================================

@router.post("/{deal_id}/items", response_model=schemas.DealRead, status_code=status.HTTP_201_CREATED)
async def add_items_to_deal(
    deal_id: int,
    items: List[schemas.DealItemCreate],
    db: AsyncSession = Depends(get_db)
):

    from app.services.crm_service import calculate_fifo_cost, deduct_inventory_fifo
    from app import models
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from decimal import Decimal

    deal = await crud.get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    total_price_added = Decimal("0")
    total_cost_added = Decimal("0")

    for item_data in items:

        product = await crud.get_product(db, item_data.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")

        unit_price = item_data.unit_price if item_data.unit_price is not None else product.default_price
        if unit_price is None:
            raise HTTPException(
                status_code=400,
                detail=f"No unit_price provided and product {product.id} has no default_price"
            )

        unit_price = Decimal(unit_price)
        quantity = Decimal(item_data.quantity)

        try:
            unit_cost = await calculate_fifo_cost(db, item_data.product_id, quantity)
        except ValueError as e:

            if product.default_cost:
                unit_cost = Decimal(product.default_cost)
            else:
                raise HTTPException(status_code=400, detail=str(e))

        deal_item = models.DealItem(
            deal_id=deal_id,
            product_id=item_data.product_id,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=unit_cost,
            total_price=quantity * unit_price,
            total_cost=quantity * unit_cost
        )

        db.add(deal_item)

        await deduct_inventory_fifo(db, item_data.product_id, quantity)

        total_price_added += deal_item.total_price
        total_cost_added += deal_item.total_cost

    deal.total_price += total_price_added
    deal.total_cost += total_cost_added
    deal.margin = deal.total_price - deal.total_cost

    await db.commit()

    # Reload deal with relationships
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app import models
    
    stmt = (
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.id == deal_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()

@router.delete("/{deal_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_deal_item(
    deal_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await crud.remove_deal_item(db, deal_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")

# ============================================================================
# Deal Profit Analysis
# ============================================================================

@router.get("/{deal_id}/profit", response_model=schemas.DealProfitAnalysis)
async def get_deal_profit(deal_id: int, db: AsyncSession = Depends(get_db)):

    try:
        analysis = await calculate_deal_profit(db, deal_id)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

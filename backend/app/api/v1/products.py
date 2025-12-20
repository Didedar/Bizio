from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app import crud, schemas
from app.services.crm_service import receive_inventory

router = APIRouter(tags=["products"])


@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: schemas.ProductCreate,
    tenant_id: int = Query(..., description="Tenant ID"),
    db: AsyncSession = Depends(get_db)
):

    product_dict = product.model_dump()
    created = await crud.create_product(db, tenant_id, product_dict)
    return created

@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    tenant_id: int = Query(..., description="Tenant ID"),
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="Search by title"),
    db: AsyncSession = Depends(get_db)
):

    products = await crud.list_products(db, tenant_id, skip, limit, qstr=search)
    return products

@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):

    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.ProductRead)
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db)
):

    existing = await crud.get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    updated = await crud.update_product(db, product_id, update_data)
    return updated

@router.patch("/{product_id}", response_model=schemas.ProductRead)
async def patch_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    existing = await crud.get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)
    if not update_data:
        return existing

    updated = await crud.update_product(db, product_id, update_data)
    return updated

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):

    existing = await crud.get_product(db, product_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    await crud.delete_product(db, product_id)

@router.post("/cleanup-orphan-inventory")
async def cleanup_orphan_inventory(
    db: AsyncSession = Depends(get_db)
):
    """Remove inventory records that reference deleted products."""
    result = await crud.cleanup_orphan_inventory(db)
    return result

# ============================================================================
# Inventory Management
# ============================================================================

@router.post("/{product_id}/inventory/receive", response_model=schemas.InventoryItemRead, status_code=status.HTTP_201_CREATED)
async def receive_product_inventory(
    product_id: int,
    tenant_id: int = Query(..., description="Tenant ID"),
    quantity: Decimal = Query(..., description="Quantity received (4 decimal places)"),
    unit_cost: Decimal = Query(..., description="Unit cost (2 decimal places)"),
    received_date: date = Query(..., description="Date received"),
    currency: str = Query("KZT", description="Currency"),
    supplier_id: Optional[int] = Query(None, description="Supplier ID"),
    reference: Optional[str] = Query(None, description="PO number, invoice, etc."),
    location: Optional[str] = Query(None, description="Warehouse location"),
    db: AsyncSession = Depends(get_db)
):
    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inventory_item = await receive_inventory(
        db=db,
        tenant_id=tenant_id,
        product_id=product_id,
        quantity=quantity,
        unit_cost=unit_cost,
        received_date=received_date,
        currency=currency,
        supplier_id=supplier_id,
        reference=reference,
        location=location
    )

    return inventory_item

@router.get("/{product_id}/inventory", response_model=List[schemas.InventoryRead])
async def get_product_inventory(
    product_id: int,
    location: Optional[str] = Query(None, description="Filter by location"),
    db: AsyncSession = Depends(get_db)
):
    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inventory_records = await crud.get_inventory(db, product_id, location)
    return inventory_records

@router.get("/{product_id}/inventory/receipts", response_model=List[schemas.InventoryItemRead])
async def get_product_inventory_receipts(
    product_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from app import models

    product = await crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = (
        select(models.InventoryItem)
        .where(models.InventoryItem.product_id == product_id)
        .order_by(models.InventoryItem.received_date.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    receipts = result.scalars().all()

    return receipts

import logging
from decimal import Decimal
from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas, crud

logger = logging.getLogger(__name__)

async def calculate_fifo_cost(
    db: AsyncSession,
    product_id: int,
    quantity: Decimal
) -> Decimal:

    query = (
        select(models.InventoryItem)
        .where(
            and_(
                models.InventoryItem.product_id == product_id,
                models.InventoryItem.remaining_quantity > 0
            )
        )
        .order_by(models.InventoryItem.received_date.asc())
    )

    result = await db.execute(query)
    inventory_items = result.scalars().all()

    if not inventory_items:

        product = await crud.get_product(db, product_id)
        if product and product.default_cost:
            logger.warning(f"No inventory items for product {product_id}, using default cost {product.default_cost}")
            return Decimal(product.default_cost)
        else:
            raise ValueError(f"No inventory available for product {product_id} and no default cost set")

    total_cost = Decimal("0")
    total_quantity = Decimal("0")
    remaining_needed = Decimal(quantity)

    for item in inventory_items:
        if remaining_needed <= 0:
            break

        take_quantity = min(item.remaining_quantity, remaining_needed)

        total_cost += take_quantity * Decimal(item.unit_cost)
        total_quantity += take_quantity

        remaining_needed -= take_quantity

    if remaining_needed > 0:

        raise ValueError(
            f"Insufficient inventory for product {product_id}. "
            f"Needed {quantity}, available {total_quantity}"
        )

    unit_cost = (total_cost / total_quantity).quantize(Decimal("0.01"))

    logger.info(
        f"FIFO cost calculated for product {product_id}: "
        f"quantity={quantity}, unit_cost={unit_cost}"
    )

    return unit_cost

async def deduct_inventory_fifo(
    db: AsyncSession,
    product_id: int,
    quantity: Decimal
) -> None:

    query = (
        select(models.InventoryItem)
        .where(
            and_(
                models.InventoryItem.product_id == product_id,
                models.InventoryItem.remaining_quantity > 0
            )
        )
        .order_by(models.InventoryItem.received_date.asc())
    )

    result = await db.execute(query)
    inventory_items = result.scalars().all()

    remaining_to_deduct = Decimal(quantity)

    for item in inventory_items:
        if remaining_to_deduct <= 0:
            break

        deduct_from_this_batch = min(item.remaining_quantity, remaining_to_deduct)
        item.remaining_quantity -= deduct_from_this_batch
        remaining_to_deduct -= deduct_from_this_batch

        logger.debug(
            f"Deducted {deduct_from_this_batch} from InventoryItem {item.id}, "
            f"remaining: {item.remaining_quantity}"
        )

    await crud.adjust_inventory(db, product_id, -quantity)

    logger.info(f"Deducted {quantity} units of product {product_id} using FIFO")

async def receive_inventory(
    db: AsyncSession,
    tenant_id: int,
    product_id: int,
    quantity: Decimal,
    unit_cost: Decimal,
    received_date: date,
    currency: str = "KZT",
    supplier_id: Optional[int] = None,
    reference: Optional[str] = None,
    location: Optional[str] = None
) -> models.InventoryItem:

    inventory_item = models.InventoryItem(
        product_id=product_id,
        tenant_id=tenant_id,
        quantity=quantity,
        remaining_quantity=quantity,
        unit_cost=unit_cost,
        currency=currency,
        received_date=received_date,
        supplier_id=supplier_id,
        reference=reference,
        location=location
    )

    db.add(inventory_item)

    await crud.adjust_inventory(db, product_id, quantity, location)

    await db.commit()
    await db.refresh(inventory_item)

    logger.info(
        f"Received inventory: product_id={product_id}, quantity={quantity}, "
        f"unit_cost={unit_cost}, reference={reference}"
    )

    return inventory_item

async def create_deal_with_items(
    db: AsyncSession,
    tenant_id: int,
    deal_data: schemas.DealCreate
) -> models.Deal:

    client = await crud.get_client(db, deal_data.client_id)
    if not client:
        raise ValueError(f"Client {deal_data.client_id} not found")

    # Start with provided total_price and total_cost, or 0 if not provided
    initial_total_price = Decimal(deal_data.total_price or 0)
    initial_total_cost = Decimal(deal_data.total_cost or 0)
    
    # Normalize empty strings to None for optional fields
    source = deal_data.source if deal_data.source and deal_data.source.strip() else None
    source_details = deal_data.source_details if deal_data.source_details and deal_data.source_details.strip() else None
    deal_type = deal_data.deal_type if deal_data.deal_type and deal_data.deal_type.strip() else None
    comments = deal_data.comments if deal_data.comments and deal_data.comments.strip() else None
    
    deal = models.Deal(
        tenant_id=tenant_id,
        client_id=deal_data.client_id,
        title=deal_data.title,
        currency=deal_data.currency,
        status=models.DealStatus(deal_data.status) if deal_data.status else models.DealStatus.new,
        extra_data=deal_data.extra_data,
        total_price=initial_total_price,
        total_cost=initial_total_cost,
        margin=initial_total_price - initial_total_cost,
        # Additional fields
        start_date=deal_data.start_date,
        completion_date=deal_data.completion_date,
        source=source,
        source_details=source_details,
        deal_type=deal_type,
        is_available_to_all=deal_data.is_available_to_all if deal_data.is_available_to_all is not None else True,
        responsible_id=deal_data.responsible_id if deal_data.responsible_id and deal_data.responsible_id != 0 else None,
        comments=comments,
        recurring_settings=deal_data.recurring_settings,
    )

    db.add(deal)
    await db.flush()
    
    # Handle observers (many-to-many relationship)
    if deal_data.observer_ids:
        observer_users = await db.execute(
            select(models.User).where(models.User.id.in_(deal_data.observer_ids))
        )
        deal.observers = list(observer_users.scalars().all())

    # Calculate totals from items (add to initial values if provided)
    items_total_price = Decimal("0")
    items_total_cost = Decimal("0")

    for item_data in deal_data.items or []:

        product = await crud.get_product(db, item_data.product_id)
        if not product:
            raise ValueError(f"Product {item_data.product_id} not found")

        unit_price = item_data.unit_price if item_data.unit_price is not None else product.default_price
        if unit_price is None:
            raise ValueError(f"No unit_price provided and product {product.id} has no default_price")

        unit_price = Decimal(unit_price)
        quantity = Decimal(item_data.quantity)

        try:
            unit_cost = await calculate_fifo_cost(db, item_data.product_id, quantity)
        except ValueError as e:
            logger.error(f"Failed to calculate FIFO cost: {e}")

            if product.default_cost:
                unit_cost = Decimal(product.default_cost)
                logger.warning(f"Using product default cost {unit_cost} for product {product.id}")
            else:
                raise ValueError(f"Cannot determine cost for product {product.id}: {e}")

        deal_item = models.DealItem(
            deal_id=deal.id,
            product_id=item_data.product_id,
            quantity=quantity,
            unit_price=unit_price,
            unit_cost=unit_cost,
            total_price=quantity * unit_price,
            total_cost=quantity * unit_cost
        )

        db.add(deal_item)

        await deduct_inventory_fifo(db, item_data.product_id, quantity)

        items_total_price += deal_item.total_price
        items_total_cost += deal_item.total_cost

    # If items were provided, use items totals (they override initial values)
    # Otherwise keep initial values (from payload.total_price/total_cost)
    if deal_data.items and len(deal_data.items) > 0:
        # Items take precedence - use calculated totals from items
        deal.total_price = items_total_price
        deal.total_cost = items_total_cost
    # else: keep initial values (already set from payload)
    
    deal.margin = deal.total_price - deal.total_cost

    await db.commit()

    query = await db.execute(
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.items).selectinload(models.DealItem.product).selectinload(models.Product.inventory_records),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.id == deal.id)
    )

    deal = query.scalar_one()

    logger.info(
        f"Created deal {deal.id} with {len(deal.items)} items, "
        f"total_price={deal.total_price}, total_cost={deal.total_cost}, margin={deal.margin}"
    )

    return deal

async def calculate_deal_profit(
    db: AsyncSession,
    deal_id: int
) -> Dict[str, Any]:

    query = await db.execute(
        select(models.Deal)
        .options(selectinload(models.Deal.items))
        .where(models.Deal.id == deal_id)
    )

    deal = query.scalar_one_or_none()

    if not deal:
        raise ValueError(f"Deal {deal_id} not found")

    revenue = Decimal(deal.total_price or 0)
    cost = Decimal(deal.total_cost or 0)
    profit = revenue - cost
    profit_margin_pct = (profit / revenue * Decimal("100")).quantize(Decimal("0.01")) if revenue > 0 else Decimal("0")

    return {
        "deal_id": deal.id,
        "revenue": revenue,
        "cost": cost,
        "profit": profit,
        "profit_margin_pct": profit_margin_pct,
        "items_count": len(deal.items)
    }


async def recalculate_deal_totals(
    db: AsyncSession,
    deal_id: int
) -> models.Deal:
    """
    Recalculate deal total_price, total_cost and margin from deal items.
    Use this when items are modified outside the normal flow or to fix data inconsistencies.
    """
    query = await db.execute(
        select(models.Deal)
        .options(selectinload(models.Deal.items))
        .where(models.Deal.id == deal_id)
    )
    deal = query.scalar_one_or_none()
    
    if not deal:
        raise ValueError(f"Deal {deal_id} not found")
    
    # Sum up totals from all items
    total_price = Decimal("0")
    total_cost = Decimal("0")
    
    for item in deal.items:
        total_price += Decimal(item.total_price or 0)
        total_cost += Decimal(item.total_cost or 0)
    
    # Update deal totals
    deal.total_price = total_price
    deal.total_cost = total_cost
    deal.margin = total_price - total_cost
    
    await db.commit()
    await db.refresh(deal)
    
    logger.info(
        f"Recalculated deal {deal.id} totals: "
        f"total_price={deal.total_price}, total_cost={deal.total_cost}, margin={deal.margin}"
    )
    
    return deal


async def recalculate_all_deals_totals(
    db: AsyncSession,
    tenant_id: Optional[int] = None
) -> int:
    """
    Recalculate totals for all deals (optionally filtered by tenant).
    Returns the number of deals updated.
    """
    query = select(models.Deal).options(selectinload(models.Deal.items))
    if tenant_id:
        query = query.where(models.Deal.tenant_id == tenant_id)
    
    result = await db.execute(query)
    deals = result.scalars().all()
    
    updated_count = 0
    for deal in deals:
        total_price = Decimal("0")
        total_cost = Decimal("0")
        
        for item in deal.items:
            total_price += Decimal(item.total_price or 0)
            total_cost += Decimal(item.total_cost or 0)
        
        if deal.total_price != total_price or deal.total_cost != total_cost:
            deal.total_price = total_price
            deal.total_cost = total_cost
            deal.margin = total_price - total_cost
            updated_count += 1
            logger.info(
                f"Updated deal {deal.id}: total_price={total_price}, "
                f"total_cost={total_cost}, margin={deal.margin}"
            )
    
    await db.commit()
    return updated_count

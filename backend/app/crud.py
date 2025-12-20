from typing import List, Optional, Dict, Any
from decimal import Decimal
import re
import random
import string
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text
from . import models, schemas

def generate_tenant_code(name: str) -> str:
    code = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))
    code = re.sub(r'-+', '-', code)
    code = code.strip('-')
    code = code[:50]
    if len(code) < 3:
        code = code + '-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return code

async def create_tenant(db: AsyncSession, name: str, code: Optional[str] = None, timezone: Optional[str] = None, currency: str = "KZT"):
    if not code:
        base_code = generate_tenant_code(name)
        code = base_code
        counter = 1
        while True:
            existing = await db.execute(select(models.Tenant).where(models.Tenant.code == code))
            if existing.scalar_one_or_none() is None:
                break
            code = f"{base_code}-{counter}"
            counter += 1
    else:
        existing = await db.execute(select(models.Tenant).where(models.Tenant.code == code))
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"Tenant code '{code}' already exists")
    
    obj = models.Tenant(name=name, code=code, timezone=timezone, currency=currency)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

async def get_tenant(db: AsyncSession, tenant_id: int):
    q = await db.execute(select(models.Tenant).where(models.Tenant.id == tenant_id))
    return q.scalar_one_or_none()

async def get_tenant_by_code(db: AsyncSession, code: str):
    q = await db.execute(select(models.Tenant).where(models.Tenant.code == code))
    return q.scalar_one_or_none()

async def list_tenants(db: AsyncSession, skip: int = 0, limit: int = 50):
    q = await db.execute(select(models.Tenant).offset(skip).limit(limit))
    return q.scalars().all()

async def create_user(db: AsyncSession, email: str, full_name: Optional[str], hashed_password: Optional[str], role=models.UserRole.manager):
    user = models.User(email=email, full_name=full_name, hashed_password=hashed_password, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str):
    q = await db.execute(select(models.User).where(models.User.email == email))
    return q.scalar_one_or_none()

async def get_user(db: AsyncSession, user_id: int):
    q = await db.execute(select(models.User).where(models.User.id == user_id))
    return q.scalar_one_or_none()

async def create_client(db: AsyncSession, tenant_id: int, payload: schemas.ClientCreate):
    metadata_value = getattr(payload, "metadata", None) or getattr(payload, "extra_data", None)
    
    obj = models.Client(
        tenant_id=tenant_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=getattr(payload, "address", None),
        extra_data=metadata_value,
    )
    db.add(obj)
    
    try:
        await db.commit()
        await db.refresh(obj)
    except Exception:
        await db.rollback()
        raise
        
    setattr(obj, "deals_count", 0)
    return obj

async def list_clients(db: AsyncSession, tenant_id: int, skip: int = 0, limit: int = 50):
    q = await db.execute(
        select(models.Client)
        .options(selectinload(models.Client.deals))
        .where(models.Client.tenant_id == tenant_id)
        .order_by(models.Client.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    clients = q.scalars().all()
    
    # Set deals_count
    for client in clients:
        setattr(client, "deals_count", len(client.deals))
        
    return clients

async def get_client(db: AsyncSession, client_id: int):
    q = await db.execute(
        select(models.Client)
        .options(selectinload(models.Client.deals))
        .where(models.Client.id == client_id)
    )
    client = q.scalar_one_or_none()
    
    if client:
        setattr(client, "deals_count", len(client.deals))
        
    return client

async def update_client(db: AsyncSession, client_id: int, changes: Dict[str, Any]):
    await db.execute(update(models.Client).where(models.Client.id == client_id).values(**changes))
    await db.commit()
    return await get_client(db, client_id)

async def delete_client(db: AsyncSession, client_id: int):
    await db.execute(delete(models.Client).where(models.Client.id == client_id))
    await db.commit()
    return True

async def get_or_create_client(db: AsyncSession, tenant_id: int, name: str, email: Optional[str] = None, phone: Optional[str] = None, external_id: Optional[str] = None):
    q = select(models.Client).where(
        and_(
            models.Client.tenant_id == tenant_id,
            or_(
                models.Client.external_id == external_id if external_id else text("false"),
                models.Client.email == email if email else text("false"),
                models.Client.phone == phone if phone else text("false")
            )
        )
    )
    res = await db.execute(q)
    client = res.scalar_one_or_none()
    if client:
        return client
    payload = schemas.ClientCreate(name=name, email=email, phone=phone)
    return await create_client(db, tenant_id, payload)

async def create_product(db: AsyncSession, tenant_id: int, product_data: Dict[str, Any]):
    obj = models.Product(
        tenant_id=tenant_id,
        sku=product_data.get("sku"),
        title=product_data["title"],
        description=product_data.get("description"),
        category=product_data.get("category"),
        default_cost=product_data.get("default_cost"),
        default_price=product_data.get("default_price"),
        currency=product_data.get("currency", "KZT"),
        images=product_data.get("images"),
        extra_data=product_data.get("metadata")
    )
    db.add(obj)
    await db.commit()
    
    # Reload with inventory_records relationship for quantity property
    result = await db.execute(
        select(models.Product)
        .options(selectinload(models.Product.inventory_records))
        .where(models.Product.id == obj.id)
    )
    return result.scalar_one()

async def get_product(db: AsyncSession, product_id: int):
    q = await db.execute(
        select(models.Product)
        .options(selectinload(models.Product.inventory_records))
        .where(models.Product.id == product_id)
    )
    return q.scalar_one_or_none()

async def list_products(db: AsyncSession, tenant_id: int, skip: int = 0, limit: int = 50, qstr: Optional[str] = None):
    q = select(models.Product).options(selectinload(models.Product.inventory_records)).where(models.Product.tenant_id == tenant_id)
    if qstr:
        q = q.where(models.Product.title.ilike(f"%{qstr}%"))
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()

async def update_product(db: AsyncSession, product_id: int, changes: Dict[str, Any]):
    await db.execute(update(models.Product).where(models.Product.id == product_id).values(**changes))
    await db.commit()
    return await get_product(db, product_id)

async def delete_product(db: AsyncSession, product_id: int):
    # Explicitly delete related inventory records first to prevent orphans
    await db.execute(delete(models.InventoryItem).where(models.InventoryItem.product_id == product_id))
    await db.execute(delete(models.Inventory).where(models.Inventory.product_id == product_id))
    # Now delete the product
    await db.execute(delete(models.Product).where(models.Product.id == product_id))
    await db.commit()
    return True


async def cleanup_orphan_inventory(db: AsyncSession):
    """Remove inventory records that reference non-existent products."""
    from sqlalchemy import not_, exists
    
    # Delete orphan InventoryItem records
    orphan_items_query = delete(models.InventoryItem).where(
        not_(exists().where(models.Product.id == models.InventoryItem.product_id))
    )
    result_items = await db.execute(orphan_items_query)
    
    # Delete orphan Inventory records
    orphan_inv_query = delete(models.Inventory).where(
        not_(exists().where(models.Product.id == models.Inventory.product_id))
    )
    result_inv = await db.execute(orphan_inv_query)
    
    await db.commit()
    return {
        "deleted_inventory_items": result_items.rowcount,
        "deleted_inventory_records": result_inv.rowcount
    }

async def get_inventory(db: AsyncSession, product_id: int, location: Optional[str] = None):
    q = select(models.Inventory).where(models.Inventory.product_id == product_id)
    if location:
        q = q.where(models.Inventory.location == location)
    res = await db.execute(q)
    return res.scalars().all()

async def adjust_inventory(db: AsyncSession, product_id: int, delta: Decimal, location: Optional[str] = None):
    q = select(models.Inventory).where(models.Inventory.product_id == product_id)
    if location:
        q = q.where(models.Inventory.location == location)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if row:
        new_qty = Decimal(row.quantity or 0) + Decimal(delta)
        await db.execute(update(models.Inventory).where(models.Inventory.id == row.id).values(quantity=new_qty))
    else:
        inv = models.Inventory(product_id=product_id, location=location, quantity=delta)
        db.add(inv)
    await db.commit()
    return await get_inventory(db, product_id, location)

async def reserve_inventory(db: AsyncSession, product_id: int, qty: Decimal, location: Optional[str] = None) -> bool:
    q = select(models.Inventory).where(models.Inventory.product_id == product_id)
    if location:
        q = q.where(models.Inventory.location == location)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        return False
    available = Decimal(row.quantity or 0) - Decimal(row.reserved or 0)
    if available < qty:
        return False
    new_reserved = Decimal(row.reserved or 0) + qty
    await db.execute(update(models.Inventory).where(models.Inventory.id == row.id).values(reserved=new_reserved))
    await db.commit()
    return True

async def release_reserved_inventory(db: AsyncSession, product_id: int, qty: Decimal, location: Optional[str] = None):
    q = select(models.Inventory).where(models.Inventory.product_id == product_id)
    if location:
        q = q.where(models.Inventory.location == location)
    res = await db.execute(q)
    row = res.scalar_one_or_none()
    if not row:
        return False
    new_reserved = max(Decimal(row.reserved or 0) - qty, Decimal("0"))
    await db.execute(update(models.Inventory).where(models.Inventory.id == row.id).values(reserved=new_reserved))
    await db.commit()
    return True

async def create_supplier(db: AsyncSession, tenant_id: int, name: str, contact: Optional[Dict] = None, rating: Optional[Decimal] = None, lead_time_days: Optional[int] = None):
    s = models.Supplier(tenant_id=tenant_id, name=name, contact=contact, rating=rating, lead_time_days=lead_time_days)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s

async def get_supplier(db: AsyncSession, supplier_id: int):
    q = await db.execute(select(models.Supplier).where(models.Supplier.id == supplier_id))
    return q.scalar_one_or_none()

async def list_suppliers(db: AsyncSession, tenant_id: int, skip: int = 0, limit: int = 50):
    q = await db.execute(select(models.Supplier).where(models.Supplier.tenant_id == tenant_id).offset(skip).limit(limit))
    return q.scalars().all()

async def create_supplier_offer(db: AsyncSession, supplier_id: int, product_id: int, price: Decimal, currency: str = "CNY", moq: Optional[int] = None, lead_time_days: Optional[int] = None):
    offer = models.SupplierOffer(supplier_id=supplier_id, product_id=product_id, price=price, currency=currency, moq=moq, lead_time_days=lead_time_days)
    db.add(offer)
    await db.commit()
    await db.refresh(offer)
    return offer

async def create_purchase_order(db: AsyncSession, tenant_id: int, supplier_id: int, items: List[Dict[str, Any]], reference: Optional[str] = None, eta: Optional[str] = None, currency: str = "CNY"):
    po = models.PurchaseOrder(tenant_id=tenant_id, supplier_id=supplier_id, reference=reference, currency=currency, eta=eta)
    db.add(po)
    await db.flush()
    total = Decimal("0")
    for it in items:
        item = models.PurchaseOrderItem(purchase_order_id=po.id, product_id=it["product_id"], qty=int(it["qty"]), unit_price=Decimal(it["unit_price"]), currency=it.get("currency", currency))
        db.add(item)
        total += Decimal(it["qty"]) * Decimal(it["unit_price"])
    po.total_amount = total
    await db.commit()
    await db.refresh(po)
    return po

async def create_deal(db: AsyncSession, tenant_id: int, payload: schemas.DealCreate):
    status_enum = None
    if payload.status:
        try:
            status_enum = models.DealStatus(payload.status)
        except ValueError:
            status_enum = models.DealStatus.new
    
    # Normalize empty strings to None for optional fields
    source = payload.source if payload.source and payload.source.strip() else None
    source_details = payload.source_details if payload.source_details and payload.source_details.strip() else None
    deal_type = payload.deal_type if payload.deal_type and payload.deal_type.strip() else None
    comments = payload.comments if payload.comments and payload.comments.strip() else None
    
    obj = models.Deal(
        tenant_id=tenant_id,
        client_id=payload.client_id,
        title=payload.title,
        total_price=payload.total_price or Decimal("0"),
        total_cost=payload.total_cost or Decimal("0"),
        currency=payload.currency,
        status=status_enum if status_enum else models.DealStatus.new,
        start_date=payload.start_date,
        completion_date=payload.completion_date,
        source=source,
        source_details=source_details,
        deal_type=deal_type,
        is_available_to_all=payload.is_available_to_all if payload.is_available_to_all is not None else True,
        responsible_id=payload.responsible_id if payload.responsible_id and payload.responsible_id != 0 else None,
        comments=comments,
        recurring_settings=payload.recurring_settings,
    )
    if payload.extra_data:
        obj.extra_data = payload.extra_data
    try:
        obj.margin = Decimal(payload.total_price or 0) - Decimal(payload.total_cost or 0)
    except Exception:
        obj.margin = Decimal("0.00")
    
    db.add(obj)
    await db.flush()  # Flush to get the deal ID
    
    # Handle observers (many-to-many relationship)
    if payload.observer_ids:
        observer_users = await db.execute(
            select(models.User).where(models.User.id.in_(payload.observer_ids))
        )
        obj.observers = list(observer_users.scalars().all())
    
    await db.commit()
    await db.refresh(obj)
    
    q = await db.execute(
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.id == obj.id)
    )
    return q.scalar_one()

async def list_deals(db: AsyncSession, tenant_id: int, skip: int = 0, limit: int = 50):
    q = await db.execute(
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.tenant_id == tenant_id)
        .offset(skip)
        .limit(limit)
    )
    return q.scalars().all()

async def get_deal(db: AsyncSession, deal_id: int):
    q = await db.execute(
        select(models.Deal)
        .options(
            selectinload(models.Deal.client),
            selectinload(models.Deal.responsible),
            selectinload(models.Deal.observers)
        )
        .where(models.Deal.id == deal_id)
    )
    return q.scalar_one_or_none()

async def update_deal_status(db: AsyncSession, deal_id: int, status: str):
    from datetime import datetime, timezone
    try:
        status_enum = models.DealStatus(status)
    except ValueError:
        raise ValueError(f"Invalid status: {status}")
    
    update_values = {'status': status_enum}
    
    # Set closed_at when deal is finalized (moved to final_account status)
    if status_enum == models.DealStatus.final_account:
        update_values['closed_at'] = datetime.now(timezone.utc)
    
    await db.execute(update(models.Deal).where(models.Deal.id == deal_id).values(**update_values))
    await db.commit()
    return await get_deal(db, deal_id)

async def update_deal(db: AsyncSession, deal_id: int, payload: schemas.DealUpdate):
    update_data: Dict[str, Any] = {}
    
    if payload.title is not None:
        update_data['title'] = payload.title
    if payload.client_id is not None:
        update_data['client_id'] = payload.client_id
    if payload.status is not None:
        try:
            status_enum = models.DealStatus(payload.status)
            update_data['status'] = status_enum
            # Set closed_at when deal is finalized (moved to final_account status)
            if status_enum == models.DealStatus.final_account:
                from datetime import datetime, timezone
                update_data['closed_at'] = datetime.now(timezone.utc)
        except ValueError:
            raise ValueError(f"Invalid status: {payload.status}")
    if payload.total_price is not None:
        update_data['total_price'] = payload.total_price
    if payload.total_cost is not None:
        update_data['total_cost'] = payload.total_cost
    if payload.currency is not None:
        update_data['currency'] = payload.currency
    if payload.extra_data is not None:
        update_data['extra_data'] = payload.extra_data
    
    # Additional fields
    if payload.start_date is not None:
        update_data['start_date'] = payload.start_date
    if payload.completion_date is not None:
        update_data['completion_date'] = payload.completion_date
    if payload.source is not None:
        # Normalize empty string to None
        update_data['source'] = payload.source.strip() if payload.source.strip() else None
    if payload.source_details is not None:
        update_data['source_details'] = payload.source_details.strip() if payload.source_details.strip() else None
    if payload.deal_type is not None:
        update_data['deal_type'] = payload.deal_type.strip() if payload.deal_type.strip() else None
    if payload.is_available_to_all is not None:
        update_data['is_available_to_all'] = payload.is_available_to_all
    if payload.responsible_id is not None:
        # Convert 0 to None
        update_data['responsible_id'] = payload.responsible_id if payload.responsible_id != 0 else None
    if payload.comments is not None:
        update_data['comments'] = payload.comments.strip() if payload.comments.strip() else None
    if payload.recurring_settings is not None:
        update_data['recurring_settings'] = payload.recurring_settings
    
    if payload.total_price is not None or payload.total_cost is not None:
        deal = await get_deal(db, deal_id)
        if deal:
            final_price = payload.total_price if payload.total_price is not None else deal.total_price
            final_cost = payload.total_cost if payload.total_cost is not None else deal.total_cost
            try:
                update_data['margin'] = Decimal(final_price) - Decimal(final_cost)
            except Exception:
                update_data['margin'] = Decimal("0.00")
    
    # Handle observers update
    deal = await get_deal(db, deal_id)
    if deal and payload.observer_ids is not None:
        if payload.observer_ids:
            observer_users = await db.execute(
                select(models.User).where(models.User.id.in_(payload.observer_ids))
            )
            deal.observers = list(observer_users.scalars().all())
        else:
            deal.observers = []
    
    if not update_data and payload.observer_ids is None:
        return await get_deal(db, deal_id)
    
    await db.execute(update(models.Deal).where(models.Deal.id == deal_id).values(**update_data))
    await db.commit()
    return await get_deal(db, deal_id)

async def delete_deal(db: AsyncSession, deal_id: int):
    await db.execute(delete(models.Deal).where(models.Deal.id == deal_id))
    await db.commit()
    return True


async def remove_deal_item(db: AsyncSession, deal_id: int, item_id: int):
    # Get item to confirm existence and deal ownership
    stmt = select(models.DealItem).where(models.DealItem.id == item_id, models.DealItem.deal_id == deal_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        return False
    
    # Delete the item
    await db.delete(item)
    await db.flush()
    
    # Recalculate deal totals from remaining items
    stmt_items = select(models.DealItem).where(models.DealItem.deal_id == deal_id)
    result_items = await db.execute(stmt_items)
    items = result_items.scalars().all()
    
    total_price = sum((i.total_price for i in items), Decimal("0"))
    total_cost = sum((i.total_cost for i in items), Decimal("0"))
    
    # Update deal
    update_stmt = (
        update(models.Deal)
        .where(models.Deal.id == deal_id)
        .values(
            total_price=total_price,
            total_cost=total_cost,
            margin=total_price - total_cost
        )
    )
    await db.execute(update_stmt)
    await db.commit()
    
    return True



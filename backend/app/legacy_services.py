import logging
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from . import crud, models, schemas
from .tasks import recalc_deal_margin_async

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


async def create_client_service(db: AsyncSession, tenant_id: int, payload: schemas.ClientCreate) -> models.Client:
    try:
        client = await crud.create_client(db, tenant_id=tenant_id, payload=payload)
        logger.info("Created client %s (id=%s)", client.name, client.id)
        await crud.create_audit_log(db, tenant_id=tenant_id, user_id=None, action="client.create",
                                    entity="client", entity_id=str(client.id), diff={"name": client.name})
        return client
    except Exception as e:
        logger.exception("Failed to create client: %s", e)
        raise ServiceError("Failed to create client") from e


async def create_deal_and_schedule(db: AsyncSession, tenant_id: int, payload: schemas.DealCreate) -> models.Deal:
    client = await crud.get_client(db, payload.client_id)
    if not client:
        raise ServiceError(f"Client id={payload.client_id} not found")

    try:
        deal = await crud.create_deal(db, tenant_id=tenant_id, payload=payload)
        logger.info("Created deal id=%s client_id=%s total=%s", deal.id, deal.client_id, deal.total_price)
    except Exception as e:
        logger.exception("Error creating deal: %s", e)
        raise ServiceError("Error creating deal") from e

    try:
        recalc_deal_margin_async.delay(deal.id)
        logger.info("Scheduled recalc_deal_margin for deal %s", deal.id)
    except Exception as e:
        logger.exception("Failed to schedule background job for deal %s: %s", deal.id, e)

    try:
        await crud.create_audit_log(db, tenant_id=tenant_id, user_id=None, action="deal.create",
                                    entity="deal", entity_id=str(deal.id), diff={
                                        "total_price": str(deal.total_price),
                                        "total_cost": str(deal.total_cost)
                                    })
    except Exception:
        logger.exception("Failed to create audit log for deal %s", getattr(deal, "id", None))

    return deal


# NOTE: The following functions are commented out because they reference Order/Invoice models
# that do not exist in the current codebase. If you need order/invoice functionality,
# you should either:
# 1. Use Deal models (recommended - already implemented in crm_service.py)
# 2. Create proper Order/Invoice models, schemas, and CRUD operations

# async def create_order_and_invoice(db: AsyncSession,
#                                    tenant_id: int,
#                                    payload: schemas.OrderCreate,
#                                    create_invoice: bool = True) -> models.Order:
#     client = await crud.get_client(db, payload.client_id)
#     if not client:
#         raise ServiceError(f"Client id={payload.client_id} not found")
#
#     items = [it.dict() for it in payload.items]
#
#     try:
#         order = await crud.create_order(db, tenant_id=tenant_id, client_id=payload.client_id,
#                                         channel=payload.channel, items=items, external_id=payload.external_id)
#         logger.info("Order created id=%s external_id=%s", order.id, order.external_id)
#     except Exception as e:
#         logger.exception("Failed to create order: %s", e)
#         raise ServiceError("Failed to create order") from e
#
#     if create_invoice:
#         try:
#             inv = await crud.create_invoice_for_order(db, order.id, amount=order.total_amount, currency=order.currency)
#             logger.info("Invoice %s created for order %s", inv.id, order.id)
#             await crud.create_audit_log(db, tenant_id=tenant_id, user_id=None, action="invoice.create",
#                                         entity="invoice", entity_id=str(inv.id), diff={"order_id": order.id, "amount": str(inv.amount)})
#         except Exception as e:
#             logger.exception("Failed to create invoice for order %s: %s", order.id, e)
#     return order


# async def record_payment_and_finalize(db: AsyncSession,
#                                       tenant_id: int,
#                                       invoice_id: int,
#                                       payment_payload: schemas.PaymentCreate) -> models.Payment:
#     try:
#         payment = await crud.record_payment(db, invoice_id=invoice_id, external_id=payment_payload.external_id,
#                                             amount=payment_payload.amount, currency=payment_payload.currency,
#                                             status=payment_payload.status)
#         logger.info("Payment recorded id=%s invoice_id=%s amount=%s", payment.id, invoice_id, payment.amount)
#     except Exception as e:
#         logger.exception("Failed to record payment: %s", e)
#         raise ServiceError("Failed to record payment") from e
#
#     try:
#         if payment.status == "succeeded":
#             await db.execute(
#                 "UPDATE invoices SET status = 'paid' WHERE id = :id",
#                 {"id": invoice_id}
#             )
#             await db.commit()
#             try:
#                 invoice = await crud.get_invoice(db, invoice_id)
#             except AttributeError:
#                 invoice = None
#
#             if invoice and getattr(invoice, "order_id", None):
#                 try:
#                     await db.execute("UPDATE orders SET status = 'paid' WHERE id = :id", {"id": invoice.order_id})
#                     await db.commit()
#                 except Exception:
#                     logger.exception("Failed to update order status for order %s", invoice.order_id)
#
#     except Exception as e:
#         logger.exception("Error during payment finalization: %s", e)
#
#     try:
#         await crud.create_audit_log(db, tenant_id=tenant_id, user_id=None, action="payment.record",
#                                     entity="payment", entity_id=str(payment.id), diff={"amount": str(payment.amount)})
#     except Exception:
#         logger.exception("Failed to write audit log for payment %s", getattr(payment, "id", None))
#
#     return payment


# NOTE: PurchaseOrder functionality is commented out because PurchaseOrderCreate schema doesn't exist
# async def create_purchase_order_service(db: AsyncSession,
#                                         tenant_id: int,
#                                         payload: schemas.PurchaseOrderCreate) -> models.PurchaseOrder:
#     supplier = await crud.get_supplier(db, payload.supplier_id)
#     if not supplier:
#         raise ServiceError(f"Supplier id={payload.supplier_id} not found")
#
#     items = [it.dict() for it in payload.items]
#     try:
#         po = await crud.create_purchase_order(db, tenant_id=tenant_id, supplier_id=payload.supplier_id,
#                                               items=items, reference=payload.reference, eta=payload.eta, currency=payload.currency)
#         logger.info("PurchaseOrder created id=%s supplier=%s total=%s", po.id, payload.supplier_id, po.total_amount)
#         await crud.create_audit_log(db, tenant_id=tenant_id, user_id=None, action="purchase_order.create",
#                                     entity="purchase_order", entity_id=str(po.id), diff={"total_amount": str(po.total_amount)})
#         return po
#     except Exception as e:
#         logger.exception("Failed to create purchase order: %s", e)
#         raise ServiceError("Failed to create purchase order") from e


async def adjust_inventory_service(db: AsyncSession, product_id: int, delta: Decimal, location: Optional[str] = None):
    try:
        res = await crud.adjust_inventory(db, product_id, delta, location)
        logger.info("Inventory adjusted for product %s delta=%s", product_id, delta)
        return res
    except Exception as e:
        logger.exception("Failed to adjust inventory: %s", e)
        raise ServiceError("Failed to adjust inventory") from e


async def reserve_inventory_service(db: AsyncSession, product_id: int, qty: Decimal, location: Optional[str] = None) -> bool:
    ok = await crud.reserve_inventory(db, product_id, qty, location)
    if not ok:
        logger.warning("Not enough stock to reserve product %s qty=%s", product_id, qty)
    else:
        logger.info("Reserved %s of product %s", qty, product_id)
    return ok


def schedule_recalc_margin(deal_id: int):
    try:
        recalc_deal_margin_async.delay(deal_id)
        logger.info("Scheduled recalc_deal_margin for deal %s", deal_id)
    except Exception:
        logger.exception("Failed to schedule recalc_deal_margin for %s", deal_id)

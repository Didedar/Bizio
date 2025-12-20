from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.db import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String, nullable=False)
    contact = Column(JSON, nullable=True)
    rating = Column(Numeric(precision=3, scale=2), nullable=True)
    lead_time_days = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="suppliers")
    offers = relationship("SupplierOffer", back_populates="supplier", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    inventory_items = relationship("InventoryItem", back_populates="supplier")

    __table_args__ = (
        Index('ix_suppliers_tenant', 'tenant_id'),
    )

    def __repr__(self):
        return f"<Supplier(id={self.id}, name={self.name})>"

class SupplierOffer(Base):

    __tablename__ = "supplier_offers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    price = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, default="CNY")
    moq = Column(Integer, nullable=True)
    lead_time_days = Column(Integer, nullable=True)

    valid_until = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="offers")
    product = relationship("Product", back_populates="supplier_offers")

    __table_args__ = (
        Index('ix_supplier_offers_supplier', 'supplier_id'),
        Index('ix_supplier_offers_product', 'product_id'),
    )

    def __repr__(self):
        return f"<SupplierOffer(id={self.id}, supplier_id={self.supplier_id}, product_id={self.product_id}, price={self.price})>"

class PurchaseOrder(Base):

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)

    reference = Column(String, nullable=True)
    total_amount = Column(Numeric(precision=18, scale=2), default=Decimal("0"))
    currency = Column(String, default="CNY")
    status = Column(String, default="pending")

    eta = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    received_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_purchase_orders_tenant', 'tenant_id'),
        Index('ix_purchase_orders_supplier', 'supplier_id'),
    )

    def __repr__(self):
        return f"<PurchaseOrder(id={self.id}, reference={self.reference}, total={self.total_amount})>"

class PurchaseOrderItem(Base):

    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)

    qty = Column(Integer, nullable=False)
    unit_price = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, default="CNY")

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")

    __table_args__ = (
        Index('ix_purchase_order_items_po', 'purchase_order_id'),
        Index('ix_purchase_order_items_product', 'product_id'),
    )

    def __repr__(self):
        return f"<PurchaseOrderItem(id={self.id}, product_id={self.product_id}, qty={self.qty})>"

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index, JSON, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sku = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    
    default_cost = Column(Numeric(precision=18, scale=2), nullable=True)
    default_price = Column(Numeric(precision=18, scale=2), nullable=True)
    currency = Column(String, default="KZT")
    
    images = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    tenant = relationship("Tenant", back_populates="products")
    deal_items = relationship("DealItem", back_populates="product")
    inventory_records = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="product", cascade="all, delete-orphan")
    supplier_offers = relationship("SupplierOffer", back_populates="product")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")

    __table_args__ = (
        Index('ix_products_tenant_sku', 'tenant_id', 'sku'),
        Index('ix_products_tenant_category', 'tenant_id', 'category'),
    )

    @property
    def quantity(self) -> Decimal:
        """
        Total quantity across all inventory locations.
        """
        total = Decimal("0")
        for inv in self.inventory_records:
            total += inv.quantity
        return total
    
    def __repr__(self):
        return f"<Product(id={self.id}, sku={self.sku}, title={self.title})>"


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    location = Column(String, nullable=True)
    
    quantity = Column(Numeric(precision=18, scale=4), default=Decimal("0"), nullable=False)
    reserved = Column(Numeric(precision=18, scale=4), default=Decimal("0"), nullable=False)
    

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="inventory_records")

    __table_args__ = (
        UniqueConstraint('product_id', 'location', name='uq_product_location'),
        Index('ix_inventory_product', 'product_id'),
    )

    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, location={self.location}, qty={self.quantity})>"


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    quantity = Column(Numeric(precision=18, scale=4), nullable=False)
    remaining_quantity = Column(Numeric(precision=18, scale=4), nullable=False)
    
    unit_cost = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, default="KZT")
    
    received_date = Column(Date, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    reference = Column(String, nullable=True)
    location = Column(String, nullable=True)
    

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inventory_items")
    tenant = relationship("Tenant", back_populates="inventory_items")
    supplier = relationship("Supplier", back_populates="inventory_items")


    __table_args__ = (
        Index('ix_inventory_items_product_date', 'product_id', 'received_date'),
        Index('ix_inventory_items_tenant', 'tenant_id'),
    )

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, product_id={self.product_id}, remaining={self.remaining_quantity}, cost={self.unit_cost})>"
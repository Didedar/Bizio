from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum, Index, JSON, Boolean, Table, Text, func
from sqlalchemy.orm import relationship
from app.db import Base


def utc_now():
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class DealStatus(str, PyEnum):
    new = "new"
    preparing_document = "preparing_document"
    prepaid_account = "prepaid_account"
    at_work = "at_work"
    final_account = "final_account"


# Association table for deal observers (many-to-many)
deal_observer_association = Table(
    'deal_observer_association',
    Base.metadata,
    Column('deal_id', Integer, ForeignKey('deals.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
)


class Deal(Base):

    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    
    total_price = Column(Numeric(precision=18, scale=2), default=Decimal("0"), nullable=False)
    total_cost = Column(Numeric(precision=18, scale=2), default=Decimal("0"), nullable=False)
    margin = Column(Numeric(precision=18, scale=2), default=Decimal("0"), nullable=False)
    currency = Column(String, default="KZT")
    
    status = Column(Enum(DealStatus), default=DealStatus.new, nullable=False, index=True)
    
    # Additional fields
    start_date = Column(DateTime(timezone=True), nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(128), nullable=True, index=True)
    source_details = Column(String(1024), nullable=True)
    deal_type = Column(String(64), nullable=True)  # Sale, Service, etc.
    is_available_to_all = Column(Boolean, default=True, nullable=False)
    responsible_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    comments = Column(Text, nullable=True)
    recurring_settings = Column(JSON, nullable=True)  # Store recurring deal settings
    
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utc_now)
    closed_at = Column(DateTime(timezone=True), nullable=True)


    tenant = relationship("Tenant", back_populates="deals")
    client = relationship("Client", back_populates="deals")
    items = relationship("DealItem", back_populates="deal", cascade="all, delete-orphan")
    responsible = relationship("User", foreign_keys=[responsible_id])
    observers = relationship("User", secondary=deal_observer_association, back_populates="observed_deals")

    __table_args__ = (
        Index('ix_deals_tenant_status', 'tenant_id', 'status'),
        Index('ix_deals_tenant_created', 'tenant_id', 'created_at'),
        Index('ix_deals_client', 'client_id'),
    )

    def __repr__(self):
        return f"<Deal(id={self.id}, title={self.title}, status={self.status}, margin={self.margin})>"


class DealItem(Base):
    __tablename__ = "deal_items"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity = Column(Numeric(precision=18, scale=4), nullable=False)
    
    unit_price = Column(Numeric(precision=18, scale=2), nullable=False)
    unit_cost = Column(Numeric(precision=18, scale=2), nullable=False)
    
    total_price = Column(Numeric(precision=18, scale=2), nullable=False)
    total_cost = Column(Numeric(precision=18, scale=2), nullable=False)
    

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=utc_now)

    deal = relationship("Deal", back_populates="items")
    product = relationship("Product", back_populates="deal_items")

    __table_args__ = (
        Index('ix_deal_items_deal', 'deal_id'),
        Index('ix_deal_items_product', 'product_id'),
    )

    def __repr__(self):
        profit = self.total_price - self.total_cost if self.total_price and self.total_cost else Decimal("0")
        return f"<DealItem(id={self.id}, product_id={self.product_id}, qty={self.quantity}, profit={profit})>"

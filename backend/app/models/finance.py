from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Boolean, Enum, JSON, Index
from sqlalchemy.orm import relationship
from app.db import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    

    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String, default="KZT")
    category = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False, index=True)
    days_until_payment = Column(Integer, nullable=True)
    
    is_fixed = Column(Boolean, default=False)
    
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="expenses")
    user = relationship("User", back_populates="expenses")


    __table_args__ = (
        Index('ix_expenses_tenant_date', 'tenant_id', 'date'),
        Index('ix_expenses_tenant_category', 'tenant_id', 'category'),
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, amount={self.amount}, category={self.category}, date={self.date})>"


class FinancialSettings(Base):
    __tablename__ = "financial_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    tax_rate = Column(Numeric(precision=5, scale=2), default=Decimal("0.00"))
    
    currency = Column(String, default="KZT")
    fiscal_year_start_month = Column(Integer, default=1)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FinancialSettings(tenant_id={self.tenant_id}, tax_rate={self.tax_rate})>"


class AllocationType(str, PyEnum):
    by_revenue = "by_revenue"
    by_quantity = "by_quantity"
    by_margin = "by_margin"
    manual = "manual"


class AllocationRule(Base):
    __tablename__ = "allocation_rules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    

    name = Column(String, nullable=False)
    allocation_type = Column(Enum(AllocationType), nullable=False)
    target_category = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_allocation_rules_tenant', 'tenant_id'),
    )

    def __repr__(self):
        return f"<AllocationRule(id={self.id}, name={self.name}, type={self.allocation_type})>"
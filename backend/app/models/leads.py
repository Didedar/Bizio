from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base  


class LeadStatus(str, Enum):
    new = "new"
    in_work = "in_work"
    qualified = "qualified"
    converted = "converted"
    lost = "lost"


class LeadPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)

    source = Column(String(128), nullable=True, index=True)
    source_details = Column(String(1024), nullable=True)

    goal = Column(String(512), nullable=True)
    product_interest = Column(String(256), nullable=True)

    status = Column(String(32), nullable=False, default=LeadStatus.new.value, index=True)
    priority = Column(String(16), nullable=True, default=LeadPriority.medium.value, index=True)

    responsible_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    notes = Column(String(2000), nullable=True)
    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    tenant = relationship("Tenant", back_populates="leads")
    client = relationship("Client", back_populates="leads", foreign_keys=[client_id])
    responsible = relationship("User", foreign_keys=[responsible_id])

    __table_args__ = (
        Index("ix_leads_tenant_status", "tenant_id", "status"),
        Index("ix_leads_tenant_responsible", "tenant_id", "responsible_id"),
    )

    def __repr__(self) -> str:
        return f"<Lead id={self.id} client_id={self.client_id} status={self.status}>"

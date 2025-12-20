from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.db import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    
    external_id = Column(String, nullable=True, index=True)
    
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="clients")
    deals = relationship("Deal", back_populates="client", cascade="all, delete-orphan")


    __table_args__ = (
        Index('ix_clients_tenant_email', 'tenant_id', 'email'),
        Index('ix_clients_tenant_external', 'tenant_id', 'external_id'),
    )

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, email={self.email})>"

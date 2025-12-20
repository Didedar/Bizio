from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class ClientBase(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class ClientCreate(ClientBase):
    metadata: Optional[dict] = None  
    extra_data: Optional[dict] = None  


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    extra_data: Optional[dict] = None


class ClientRead(ClientBase):
    id: int
    tenant_id: int
    external_id: Optional[str] = None
    extra_data: Optional[dict] = None
    deals_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class LeadBase(BaseModel):
    client_id: int
    source: Optional[str] = None          # Instagram, TikTok, Website
    source_details: Optional[str] = None  # конкретный пост, ссылка, кампания
    goal: Optional[str] = None            # что хочет клиент
    product_interest: Optional[str] = None
    priority: Optional[str] = Field(None, description="low, medium, high")
    status: Optional[str] = Field("new", description="new, in_work, qualified, lost")
    responsible_id: Optional[int] = None
    notes: Optional[str] = None
    extra_data: Optional[dict] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    source: Optional[str] = None
    source_details: Optional[str] = None
    goal: Optional[str] = None
    product_interest: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    responsible_id: Optional[int] = None
    notes: Optional[str] = None
    extra_data: Optional[dict] = None

class LeadRead(LeadBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


    
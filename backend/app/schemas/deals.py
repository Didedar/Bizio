from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .products import ProductRead
from .clients import ClientRead
from .users import UserSimple

class DealItemBase(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0, description="Quantity sold")
    unit_price: Optional[Decimal] = Field(None, description="Selling price (defaults to product.default_price)")
    unit_cost: Optional[Decimal] = Field(None, description="Cost snapshot (calculated via FIFO if not provided)")

class DealItemCreate(DealItemBase):
    pass


class DealItemUpdate(BaseModel):
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None)
    unit_cost: Optional[Decimal] = Field(None)


class DealItemRead(DealItemBase):
    id: int
    deal_id: int
    unit_cost: Decimal = Field(..., description="FIFO cost snapshot")
    unit_price: Decimal = Field(..., description="Selling price snapshot")
    total_price: Decimal = Field(..., description="quantity * unit_price")
    total_cost: Decimal = Field(..., description="quantity * unit_cost")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    product: Optional[ProductRead] = None  
    
    model_config = ConfigDict(from_attributes=True)


class DealBase(BaseModel):
    client_id: int
    title: str
    currency: str = "KZT"
    status: Optional[str] = "new"  
    extra_data: Optional[dict] = None


class DealCreate(DealBase):
    total_price: Optional[Decimal] = Field(None, description="Total price (required if no items)")
    total_cost: Optional[Decimal] = Field(None, description="Total cost (required if no items)")
    items: Optional[List[DealItemCreate]] = Field(default_factory=list, description="Deal line items")
    start_date: Optional[datetime] = Field(None, description="Deal start date (ISO string or datetime)")
    completion_date: Optional[datetime] = Field(None, description="Expected completion date (ISO string or datetime)")
    source: Optional[str] = Field(default=None, description="Deal source (e.g., Website, Referral)")
    source_details: Optional[str] = Field(default=None, description="Additional source details")
    deal_type: Optional[str] = Field(default=None, description="Deal type (e.g., Sale, Service)")
    is_available_to_all: Optional[bool] = Field(default=True, description="Whether deal is visible to all users")
    responsible_id: Optional[int] = Field(default=None, description="ID of responsible user")
    comments: Optional[str] = Field(default=None, description="Additional comments")
    recurring_settings: Optional[dict] = Field(default=None, description="Recurring deal settings")
    observer_ids: Optional[List[int]] = Field(default_factory=list, description="List of observer user IDs")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    @field_validator('total_price', 'total_cost', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            try:
                return Decimal(v)
            except (ValueError, TypeError):
                return None
        return v
    
    @field_validator('start_date', 'completion_date', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        from datetime import timezone as tz
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            # Ensure datetime is timezone-aware
            if v.tzinfo is None:
                return v.replace(tzinfo=tz.utc)
            return v
        if isinstance(v, str):
            try:
                # Try parsing ISO format (handles both with and without timezone)
                if 'Z' in v:
                    v = v.replace('Z', '+00:00')
                parsed = datetime.fromisoformat(v)
                # Ensure timezone-aware
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=tz.utc)
                return parsed
            except ValueError:
                # Try other common formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d']:
                    try:
                        parsed = datetime.strptime(v, fmt)
                        return parsed.replace(tzinfo=tz.utc)
                    except ValueError:
                        continue
                return None
        return v
    
    @field_validator('responsible_id', mode='before')
    @classmethod
    def parse_responsible_id(cls, v):
        if v is None or v == 0 or v == '':
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None


class DealUpdate(BaseModel):
    client_id: Optional[int] = None
    title: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    extra_data: Optional[dict] = None
    total_price: Optional[Decimal] = Field(None)
    total_cost: Optional[Decimal] = Field(None)
    
    # Additional fields
    start_date: Optional[datetime] = Field(None)
    completion_date: Optional[datetime] = Field(None)
    source: Optional[str] = Field(None)
    source_details: Optional[str] = Field(None)
    deal_type: Optional[str] = Field(None)
    is_available_to_all: Optional[bool] = Field(None)
    responsible_id: Optional[int] = Field(None)
    comments: Optional[str] = Field(None)
    recurring_settings: Optional[dict] = Field(None)
    observer_ids: Optional[List[int]] = Field(None)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    @field_validator('total_price', 'total_cost', mode='before')
    @classmethod
    def convert_to_decimal(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            try:
                return Decimal(v)
            except (ValueError, TypeError):
                return None
        return v
    
    @field_validator('start_date', 'completion_date', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        from datetime import timezone as tz
        if v is None or v == '':
            return None
        if isinstance(v, datetime):
            # Ensure datetime is timezone-aware
            if v.tzinfo is None:
                return v.replace(tzinfo=tz.utc)
            return v
        if isinstance(v, str):
            try:
                if 'Z' in v:
                    v = v.replace('Z', '+00:00')
                parsed = datetime.fromisoformat(v)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=tz.utc)
                return parsed
            except ValueError:
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d']:
                    try:
                        parsed = datetime.strptime(v, fmt)
                        return parsed.replace(tzinfo=tz.utc)
                    except ValueError:
                        continue
                return None
        return v
    
    @field_validator('responsible_id', mode='before')
    @classmethod
    def parse_responsible_id(cls, v):
        if v is None or v == 0 or v == '':
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None


class DealRead(DealBase):
    id: int
    tenant_id: int
    total_price: Decimal = Field(..., description="Total revenue")
    total_cost: Decimal = Field(..., description="Total COGS")
    margin: Decimal = Field(..., description="Profit (total_price - total_cost)")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    items: List[DealItemRead] = Field(default_factory=list, description="Deal line items")
    client: Optional[ClientRead] = None
    
    # Additional fields
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    source: Optional[str] = None
    source_details: Optional[str] = None
    deal_type: Optional[str] = None
    is_available_to_all: bool = True
    responsible_id: Optional[int] = None
    comments: Optional[str] = None
    recurring_settings: Optional[dict] = None
    responsible: Optional[UserSimple] = None
    observers: List[UserSimple] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class DealProfitAnalysis(BaseModel):
    deal_id: int
    revenue: Decimal = Field(..., description="Total revenue")
    cost: Decimal = Field(..., description="Total cost (COGS)")
    profit: Decimal = Field(..., description="Gross profit")
    profit_margin_pct: Decimal = Field(..., description="Profit margin as percentage")
    items_count: int = Field(..., description="Number of line items")
    
    model_config = ConfigDict(from_attributes=True)

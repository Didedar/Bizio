from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ProductBase(BaseModel):
    sku: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    default_cost: Optional[Decimal] = Field(None)
    default_price: Optional[Decimal] = Field(None)
    currency: str = "KZT"
    images: Optional[List[str]] = None 


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    default_cost: Optional[Decimal] = Field(None)
    default_price: Optional[Decimal] = Field(None)
    currency: Optional[str] = None
    images: Optional[List[str]] = None


class ProductRead(ProductBase):
    id: int
    tenant_id: int
    quantity: Decimal = Field(default=Decimal("0"), description="Total quantity in stock across all locations")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class InventoryItemBase(BaseModel):
    quantity: Decimal = Field(..., description="Quantity received")
    unit_cost: Decimal = Field(..., description="Cost per unit at time of receipt")
    currency: str = "KZT"
    received_date: date
    supplier_id: Optional[int] = None
    reference: Optional[str] = Field(None, description="PO number, invoice number, etc.")
    location: Optional[str] = Field(None, description="Warehouse location")


class InventoryItemCreate(InventoryItemBase):
    product_id: int


class InventoryItemRead(InventoryItemBase):
    id: int
    product_id: int
    tenant_id: int
    remaining_quantity: Decimal = Field(..., description="Quantity still available for FIFO")
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class InventoryRead(BaseModel):
    id: int
    product_id: int
    location: Optional[str] = None
    quantity: Decimal = Field(..., description="Total quantity in stock")
    reserved: Decimal = Field(..., description="Quantity reserved for orders")
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class InventoryWithHistory(InventoryRead):
    receipts: List[InventoryItemRead] = Field(default_factory=list, description="Inventory receipt history")
    
    model_config = ConfigDict(from_attributes=True)

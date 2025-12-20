from datetime import datetime  
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "manager"  


class UserCreate(UserBase):
    password: Optional[str] = None 


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    tenants: Optional[List["TenantRead"]] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserSimple(UserBase):
    """Simplified user schema without tenants relationship for use in nested objects"""
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class TenantBase(BaseModel):
    name: str
    timezone: Optional[str] = None
    currency: str = "KZT"


class TenantCreate(TenantBase):
    code: Optional[str] = None  


class TenantRead(TenantBase):
    id: int
    code: str
    is_active: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Rebuild models to resolve forward references
UserRead.model_rebuild()
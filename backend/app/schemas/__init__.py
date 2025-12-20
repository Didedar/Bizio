# app/schemas/__init__.py
"""
Central schemas module - exports all Pydantic schemas for easy imports.

Usage:
    from app import schemas
    user_data = schemas.UserCreate(...)
    deal = schemas.DealRead(...)
"""

# Import all schemas
from .users import UserBase, UserCreate, UserUpdate, UserRead, TenantBase, TenantCreate, TenantRead
from .clients import ClientBase, ClientCreate, ClientUpdate, ClientRead
from .products import (
    ProductBase, ProductCreate, ProductUpdate, ProductRead,
    InventoryItemBase, InventoryItemCreate, InventoryItemRead,
    InventoryRead, InventoryWithHistory
)
from .deals import (
    DealItemBase, DealItemCreate, DealItemUpdate, DealItemRead,
    DealBase, DealCreate, DealUpdate, DealRead,
    DealProfitAnalysis
)
from .finance import (
    ExpenseBase, ExpenseCreate, ExpenseUpdate, ExpenseRead,
    FinancialSettingsBase, FinancialSettingsCreate, FinancialSettingsRead,
    FinanceDashboard, MonthlyFinanceRequest
)

# Export all schemas
__all__ = [
    # Users and tenants
    "UserBase", "UserCreate", "UserUpdate", "UserRead",
    "TenantBase", "TenantCreate", "TenantRead",
    
    # Clients
    "ClientBase", "ClientCreate", "ClientUpdate", "ClientRead",
    
    # Products and inventory
    "ProductBase", "ProductCreate", "ProductUpdate", "ProductRead",
    "InventoryItemBase", "InventoryItemCreate", "InventoryItemRead",
    "InventoryRead", "InventoryWithHistory",
    
    # Deals
    "DealItemBase", "DealItemCreate", "DealItemUpdate", "DealItemRead",
    "DealBase", "DealCreate", "DealUpdate", "DealRead",
    "DealProfitAnalysis",
    
    # Finance
    "ExpenseBase", "ExpenseCreate", "ExpenseUpdate", "ExpenseRead",
    "FinancialSettingsBase", "FinancialSettingsCreate", "FinancialSettingsRead",
    "FinanceDashboard", "MonthlyFinanceRequest",
]

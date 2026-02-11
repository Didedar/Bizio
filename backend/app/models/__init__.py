# app/models/__init__.py
"""
Central models module - exports all SQLAlchemy models for easy imports.

Usage:
    from app import models
    user = models.User(...)
    deal = models.Deal(...)
"""

# Import all models
from .users import Tenant, User, UserRole
from .clients import Client
from .products import Product, Inventory, InventoryItem
from .deals import Deal, DealItem, DealStatus
from .finance import Expense, FinancialSettings, AllocationRule, AllocationType
from .suppliers import Supplier, SupplierOffer, PurchaseOrder, PurchaseOrderItem
from .copilot import (
    Document, DocumentType, DocumentChunk,
    CopilotConversation, CopilotMessage, MessageRole,
    DataFixSuggestion, DataFixStatus
)

# Export all models for "from app import models" usage
__all__ = [
    # Users and tenants
    "Tenant",
    "User",
    "UserRole",
    
    # Clients
    "Client",
    
    # Products and inventory
    "Product",
    "Inventory",
    "InventoryItem",
    
    # Deals
    "Deal",
    "DealItem",
    "DealStatus",
    
    # Finance
    "Expense",
    "FinancialSettings",
    "AllocationRule",
    "AllocationType",
    
    # Suppliers
    "Supplier",
    "SupplierOffer",
    "PurchaseOrder",
    "PurchaseOrderItem",
    
    # Copilot
    "Document",
    "DocumentType",
    "DocumentChunk",
    "CopilotConversation",
    "CopilotMessage",
    "MessageRole",
    "DataFixSuggestion",
    "DataFixStatus",
]

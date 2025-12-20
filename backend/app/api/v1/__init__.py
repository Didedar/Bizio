# app/api/v1/__init__.py
from fastapi import APIRouter

from . import auth, finance, users, products, deals, clients, dashboard

api_router = APIRouter()

# Active routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# TODO: Create these API modules:
# api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
# api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
# api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
# api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])

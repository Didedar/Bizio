# app/services/integrations/__init__.py
"""
Marketplace integration adapters
"""
from .base import MarketplaceAdapter
from .wildberries import WildberriesAdapter
from .kaspi import KaspiAdapter

__all__ = ['MarketplaceAdapter', 'WildberriesAdapter', 'KaspiAdapter']


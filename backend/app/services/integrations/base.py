# app/services/integrations/base.py
"""
Base adapter class for marketplace integrations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime


class MarketplaceAdapter(ABC):
    """
    Abstract base class for marketplace integrations.
    All marketplace adapters must implement these methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration
        Args:
            config: Dict containing API keys, tokens, etc.
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with marketplace API
        Returns: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def sync_orders(self, start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch orders from marketplace
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
        Returns: List of order dictionaries
        """
        pass
    
    @abstractmethod
    async def sync_products(self) -> List[Dict[str, Any]]:
        """
        Fetch products from marketplace
        Returns: List of product dictionaries
        """
        pass
    
    @abstractmethod
    async def update_stock(self, product_sku: str, quantity: int) -> bool:
        """
        Update product stock quantity on marketplace
        Args:
            product_sku: Product SKU
            quantity: New stock quantity
        Returns: True if successful
        """
        pass
    
    @abstractmethod
    async def update_price(self, product_sku: str, price: Decimal) -> bool:
        """
        Update product price on marketplace
        Args:
            product_sku: Product SKU
            price: New price
        Returns: True if successful
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status from marketplace
        Args:
            order_id: External order ID
        Returns: Order status information
        """
        pass
    
    def normalize_order(self, raw_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize marketplace-specific order format to internal format
        Override in subclass if needed
        """
        return {
            'external_id': raw_order.get('id'),
            'channel': self.get_marketplace_name(),
            'status': 'created',
            'total_amount': Decimal(str(raw_order.get('total', 0))),
            'currency': raw_order.get('currency', 'KZT'),
            'items': self.normalize_order_items(raw_order.get('items', []))
        }
    
    def normalize_order_items(self, raw_items: List[Dict]) -> List[Dict[str, Any]]:
        """
        Normalize order items to internal format
        """
        items = []
        for item in raw_items:
            items.append({
                'product_id': None,  # Will be matched by SKU
                'title': item.get('name', ''),
                'qty': int(item.get('quantity', 1)),
                'unit_price': Decimal(str(item.get('price', 0))),
                'unit_cost': Decimal('0'),  # Unknown from marketplace
                'currency': item.get('currency', 'KZT')
            })
        return items
    
    @abstractmethod
    def get_marketplace_name(self) -> str:
        """Return marketplace name (e.g., 'wildberries', 'kaspi')"""
        pass


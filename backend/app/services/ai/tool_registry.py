# app/services/ai/tool_registry.py
"""
Function calling tools for the BIZIO AI Copilot.
Each tool is a function that can be called by Gemini to get real data.
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Literal, Tuple
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from fuzzywuzzy import fuzz

from app import models

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL DEFINITIONS (for Gemini function calling)
# =============================================================================

COPILOT_TOOLS = [
    {
        "name": "query_db",
        "description": "Query the database with filters and aggregations. Use this for listing records, counting items, or getting specific data.",
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "enum": ["products", "expenses", "deals", "suppliers", "inventory", "clients"],
                    "description": "Which table to query"
                },
                "filters": {
                    "type": "object",
                    "description": "Filter conditions. Use field_gte, field_lte for ranges, field_like for text search. Example: {\"category\": \"electronics\", \"date_gte\": \"2026-01-01\"}"
                },
                "aggregations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Aggregations like ['sum:amount', 'count:id', 'avg:price']"
                },
                "group_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields to group by, e.g. ['category', 'month']"
                },
                "order_by": {
                    "type": "string",
                    "description": "Field to order by. Prefix with - for DESC. E.g. '-amount'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum rows to return (default 50)"
                }
            },
            "required": ["table"]
        }
    },
    {
        "name": "calculate_metrics",
        "description": "Calculate financial metrics from live data. ALWAYS use this for any numeric calculations instead of computing yourself.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric_type": {
                    "type": "string",
                    "enum": [
                        "revenue", "cogs", "gross_profit", "gross_margin",
                        "net_profit", "net_margin", "break_even",
                        "inventory_value", "days_of_stock", "margin_by_product",
                        "total_expenses", "average_order_value"
                    ],
                    "description": "Type of metric to calculate"
                },
                "date_range": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Date range as [start_date, end_date] in YYYY-MM-DD format"
                },
                "filters": {
                    "type": "object",
                    "description": "Additional filters like {\"category\": \"electronics\"}"
                }
            },
            "required": ["metric_type"]
        }
    },
    {
        "name": "get_inventory_status",
        "description": "Get inventory status including dead stock detection. Use this to find slow-moving or unsold items.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Specific product IDs to check"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by product category"
                },
                "low_stock_threshold": {
                    "type": "integer",
                    "description": "Flag items with quantity below this"
                },
                "days_without_sale": {
                    "type": "integer",
                    "description": "Find products with no sales in this many days"
                }
            }
        }
    },
    {
        "name": "analyze_expenses",
        "description": "Analyze expenses with trend detection and anomaly finding. Use for expense summaries and spike detection.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_range": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Date range as [start_date, end_date] in YYYY-MM-DD format"
                },
                "group_by": {
                    "type": "string",
                    "enum": ["category", "day", "week", "month"],
                    "description": "How to group expenses"
                },
                "compare_with_previous": {
                    "type": "boolean",
                    "description": "Compare with previous period"
                }
            },
            "required": ["date_range"]
        }
    },
    {
        "name": "find_duplicates",
        "description": "Find potential duplicate records using fuzzy matching. Use for data quality checks.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "enum": ["products", "suppliers", "clients"],
                    "description": "Type of entities to check"
                },
                "similarity_threshold": {
                    "type": "number",
                    "description": "Similarity threshold 0-1 (default 0.85)"
                }
            },
            "required": ["entity_type"]
        }
    },
    {
        "name": "suggest_pricing",
        "description": "Calculate suggested prices to achieve target margin.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_margin_percent": {
                    "type": "number",
                    "description": "Target margin percentage (e.g., 30 for 30%)"
                },
                "category": {
                    "type": "string",
                    "description": "Optional: filter by product category"
                },
                "only_below_target": {
                    "type": "boolean",
                    "description": "Only show products currently below target margin"
                }
            },
            "required": ["target_margin_percent"]
        }
    },
    {
        "name": "create_task",
        "description": "Create an actionable task based on insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Task description with context"
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority"
                },
                "related_entities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Related records like ['product#123', 'expense#456']"
                }
            },
            "required": ["title", "description"]
        }
    },
    {
        "name": "suggest_data_fixes",
        "description": "Propose data quality fixes (merges, corrections). User must approve before applying.",
        "parameters": {
            "type": "object",
            "properties": {
                "fix_type": {
                    "type": "string",
                    "enum": ["merge_duplicates", "fill_missing", "correct_category"],
                    "description": "Type of fix to propose"
                },
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "suggested_value": {"type": "string"}
                        }
                    },
                    "description": "Entities to fix with suggested values"
                }
            },
            "required": ["fix_type", "entities"]
        }
    }
]


# =============================================================================
# TOOL IMPLEMENTATIONS
# =============================================================================

class ToolRegistry:
    """Registry and executor for AI Copilot tools."""
    
    def __init__(self, db: AsyncSession, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        try:
            method = getattr(self, f"_tool_{tool_name}", None)
            if not method:
                return {"error": f"Unknown tool: {tool_name}"}
            
            result = await method(**arguments)
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {
                "success": False,
                "tool_name": tool_name,
                "error": str(e)
            }

    async def _tool_query_db(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        aggregations: Optional[List[str]] = None,
        group_by: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Query database with filters and aggregations."""
        
        # Map table names to models
        table_map = {
            "products": models.Product,
            "expenses": models.Expense,
            "deals": models.Deal,
            "suppliers": models.Supplier,
            "inventory": models.InventoryItem,
            "clients": models.Client
        }
        
        model = table_map.get(table)
        if not model:
            return {"error": f"Unknown table: {table}"}
        
        # Build base query
        query = select(model).where(model.tenant_id == self.tenant_id)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if key.endswith("_gte"):
                    field_name = key[:-4]
                    if hasattr(model, field_name):
                        query = query.where(getattr(model, field_name) >= value)
                elif key.endswith("_lte"):
                    field_name = key[:-4]
                    if hasattr(model, field_name):
                        query = query.where(getattr(model, field_name) <= value)
                elif key.endswith("_like"):
                    field_name = key[:-5]
                    if hasattr(model, field_name):
                        query = query.where(getattr(model, field_name).ilike(f"%{value}%"))
                elif hasattr(model, key):
                    query = query.where(getattr(model, key) == value)
        
        # Apply ordering
        if order_by:
            desc = order_by.startswith("-")
            field_name = order_by.lstrip("-")
            if hasattr(model, field_name):
                order_col = getattr(model, field_name)
                query = query.order_by(order_col.desc() if desc else order_col)
        
        # Apply limit
        query = query.limit(min(limit, 100))
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.scalars().all()
        
        # Convert to dicts
        data = []
        for row in rows:
            row_dict = {}
            for col in row.__table__.columns:
                val = getattr(row, col.name)
                if isinstance(val, (datetime, date)):
                    val = val.isoformat()
                elif isinstance(val, Decimal):
                    val = float(val)
                row_dict[col.name] = val
            data.append(row_dict)
        
        return {
            "rows": data,
            "total": len(data),
            "table": table,
            "sources": [f"{table}#{row['id']}" for row in data]
        }

    async def _tool_calculate_metrics(
        self,
        metric_type: str,
        date_range: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate financial metrics."""
        
        start_date = None
        end_date = None
        if date_range and len(date_range) == 2:
            start_date = datetime.strptime(date_range[0], "%Y-%m-%d").date()
            end_date = datetime.strptime(date_range[1], "%Y-%m-%d").date()
        
        if metric_type == "revenue":
            query = select(func.sum(models.Deal.total_price)).where(
                models.Deal.tenant_id == self.tenant_id,
                models.Deal.status != 'cancelled'
            )
            if start_date and end_date:
                query = query.where(models.Deal.created_at >= start_date, models.Deal.created_at <= end_date)
            result = await self.db.execute(query)
            value = result.scalar() or Decimal(0)
            return {
                "value": float(value),
                "metric": "revenue",
                "formula": "SUM(deals.total_price) WHERE status != 'cancelled'",
                "date_range": date_range,
                "sources": ["deals"]
            }
        
        elif metric_type == "cogs":
            query = select(func.sum(models.Deal.total_cost)).where(
                models.Deal.tenant_id == self.tenant_id,
                models.Deal.status != 'cancelled'
            )
            if start_date and end_date:
                query = query.where(models.Deal.created_at >= start_date, models.Deal.created_at <= end_date)
            result = await self.db.execute(query)
            value = result.scalar() or Decimal(0)
            return {
                "value": float(value),
                "metric": "cogs",
                "formula": "SUM(deals.total_cost)",
                "date_range": date_range,
                "sources": ["deals"]
            }
        
        elif metric_type == "gross_profit":
            revenue = await self._tool_calculate_metrics("revenue", date_range, filters)
            cogs = await self._tool_calculate_metrics("cogs", date_range, filters)
            value = revenue["value"] - cogs["value"]
            return {
                "value": value,
                "metric": "gross_profit",
                "formula": "revenue - COGS",
                "inputs": {"revenue": revenue["value"], "cogs": cogs["value"]},
                "date_range": date_range,
                "sources": ["deals"]
            }
        
        elif metric_type == "gross_margin":
            revenue = await self._tool_calculate_metrics("revenue", date_range, filters)
            gross_profit = await self._tool_calculate_metrics("gross_profit", date_range, filters)
            if revenue["value"] > 0:
                value = (gross_profit["value"] / revenue["value"]) * 100
            else:
                value = 0
            return {
                "value": round(value, 2),
                "metric": "gross_margin_percent",
                "formula": "(gross_profit / revenue) * 100",
                "inputs": {"gross_profit": gross_profit["value"], "revenue": revenue["value"]},
                "date_range": date_range,
                "sources": ["deals"]
            }
        
        elif metric_type == "total_expenses":
            query = select(func.sum(models.Expense.amount)).where(
                models.Expense.tenant_id == self.tenant_id
            )
            if start_date and end_date:
                query = query.where(models.Expense.date >= start_date, models.Expense.date <= end_date)
            if filters and filters.get("category"):
                query = query.where(models.Expense.category == filters["category"])
            result = await self.db.execute(query)
            value = result.scalar() or Decimal(0)
            return {
                "value": float(value),
                "metric": "total_expenses",
                "formula": "SUM(expenses.amount)",
                "date_range": date_range,
                "sources": ["expenses"]
            }
        
        elif metric_type == "inventory_value":
            query = select(
                func.sum(models.InventoryItem.remaining_quantity * models.InventoryItem.unit_cost)
            ).where(models.InventoryItem.tenant_id == self.tenant_id)
            result = await self.db.execute(query)
            value = result.scalar() or Decimal(0)
            return {
                "value": float(value),
                "metric": "inventory_value",
                "formula": "SUM(remaining_quantity * unit_cost)",
                "sources": ["inventory_items"]
            }
        
        elif metric_type == "average_order_value":
            query = select(func.avg(models.Deal.total_price)).where(
                models.Deal.tenant_id == self.tenant_id,
                models.Deal.status != 'cancelled'
            )
            if start_date and end_date:
                query = query.where(models.Deal.created_at >= start_date, models.Deal.created_at <= end_date)
            result = await self.db.execute(query)
            value = result.scalar() or Decimal(0)
            return {
                "value": float(value),
                "metric": "average_order_value",
                "formula": "AVG(deals.total_price)",
                "date_range": date_range,
                "sources": ["deals"]
            }
        
        return {"error": f"Unknown metric type: {metric_type}"}

    async def _tool_get_inventory_status(
        self,
        product_ids: Optional[List[int]] = None,
        category: Optional[str] = None,
        low_stock_threshold: Optional[int] = None,
        days_without_sale: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get inventory status with dead stock detection."""
        
        # Get products with inventory
        query = (
            select(models.Product)
            .where(models.Product.tenant_id == self.tenant_id)
        )
        
        if product_ids:
            query = query.where(models.Product.id.in_(product_ids))
        if category:
            query = query.where(models.Product.category == category)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        items = []
        total_value = Decimal(0)
        dead_stock_value = Decimal(0)
        
        for product in products:
            # Get inventory quantity
            inv_query = select(func.sum(models.Inventory.quantity)).where(
                models.Inventory.product_id == product.id
            )
            inv_result = await self.db.execute(inv_query)
            qty = inv_result.scalar() or Decimal(0)
            
            # Get last sale date
            last_sale_query = select(func.max(models.Deal.created_at)).join(
                models.DealItem
            ).where(models.DealItem.product_id == product.id)
            last_sale_result = await self.db.execute(last_sale_query)
            last_sale = last_sale_result.scalar()
            
            days_since_sale = None
            if last_sale:
                days_since_sale = (datetime.utcnow() - last_sale).days
            else:
                days_since_sale = 9999  # Never sold
            
            cost = product.default_cost or Decimal(0)
            value = qty * cost
            total_value += value
            
            is_dead_stock = False
            if days_without_sale and days_since_sale >= days_without_sale:
                is_dead_stock = True
                dead_stock_value += value
            
            # Apply filters
            if low_stock_threshold and qty >= low_stock_threshold:
                continue
            if days_without_sale and days_since_sale < days_without_sale:
                continue
            
            items.append({
                "product_id": product.id,
                "sku": product.sku,
                "title": product.title,
                "category": product.category,
                "current_qty": float(qty),
                "last_sale_date": last_sale.isoformat() if last_sale else None,
                "days_since_sale": days_since_sale if days_since_sale != 9999 else None,
                "never_sold": days_since_sale == 9999,
                "value_at_cost": float(value),
                "is_dead_stock": is_dead_stock
            })
        
        return {
            "items": items,
            "total_value": float(total_value),
            "dead_stock_value": float(dead_stock_value),
            "count": len(items),
            "sources": [f"product#{item['product_id']}" for item in items]
        }

    async def _tool_analyze_expenses(
        self,
        date_range: List[str],
        group_by: str = "category",
        compare_with_previous: bool = False
    ) -> Dict[str, Any]:
        """Analyze expenses with trends."""
        
        start_date = datetime.strptime(date_range[0], "%Y-%m-%d").date()
        end_date = datetime.strptime(date_range[1], "%Y-%m-%d").date()
        
        # Current period expenses
        query = select(models.Expense).where(
            models.Expense.tenant_id == self.tenant_id,
            models.Expense.date >= start_date,
            models.Expense.date <= end_date
        )
        result = await self.db.execute(query)
        expenses = result.scalars().all()
        
        total = sum(e.amount for e in expenses)
        
        # Group by category
        breakdown = {}
        for expense in expenses:
            cat = expense.category or "Uncategorized"
            breakdown[cat] = breakdown.get(cat, Decimal(0)) + expense.amount
        
        # Convert to list with percentages
        breakdown_list = []
        for cat, amount in breakdown.items():
            pct = (amount / total * 100) if total > 0 else 0
            breakdown_list.append({
                "category": cat,
                "amount": float(amount),
                "percentage": round(float(pct), 1)
            })
        
        breakdown_list.sort(key=lambda x: x["amount"], reverse=True)
        
        trends = []
        if compare_with_previous:
            # Calculate previous period
            period_days = (end_date - start_date).days
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_days)
            
            prev_query = select(models.Expense).where(
                models.Expense.tenant_id == self.tenant_id,
                models.Expense.date >= prev_start,
                models.Expense.date <= prev_end
            )
            prev_result = await self.db.execute(prev_query)
            prev_expenses = prev_result.scalars().all()
            
            prev_breakdown = {}
            for expense in prev_expenses:
                cat = expense.category or "Uncategorized"
                prev_breakdown[cat] = prev_breakdown.get(cat, Decimal(0)) + expense.amount
            
            # Calculate trends
            for cat, amount in breakdown.items():
                prev_amount = prev_breakdown.get(cat, Decimal(0))
                if prev_amount > 0:
                    change_pct = ((amount - prev_amount) / prev_amount * 100)
                else:
                    change_pct = 100 if amount > 0 else 0
                
                if abs(change_pct) > 10:  # Only significant changes
                    trends.append({
                        "category": cat,
                        "current": float(amount),
                        "previous": float(prev_amount),
                        "change_pct": round(float(change_pct), 1),
                        "direction": "up" if change_pct > 0 else "down"
                    })
        
        # Detect anomalies (expenses > 2x average for category)
        anomalies = []
        for cat, amount in breakdown.items():
            cat_expenses = [e for e in expenses if (e.category or "Uncategorized") == cat]
            if len(cat_expenses) > 1:
                avg = amount / len(cat_expenses)
                for e in cat_expenses:
                    if e.amount > avg * 2:
                        anomalies.append({
                            "expense_id": e.id,
                            "date": e.date.isoformat(),
                            "amount": float(e.amount),
                            "category": cat,
                            "reason": f"Amount is {float(e.amount/avg):.1f}x the category average"
                        })
        
        return {
            "total": float(total),
            "breakdown": breakdown_list,
            "trends": trends,
            "anomalies": anomalies[:5],  # Limit to top 5
            "expense_count": len(expenses),
            "date_range": date_range,
            "sources": [f"expense#{e.id}" for e in expenses]
        }

    async def _tool_find_duplicates(
        self,
        entity_type: str,
        similarity_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """Find duplicate records using fuzzy matching."""
        
        threshold = int(similarity_threshold * 100)
        
        if entity_type == "products":
            query = select(models.Product).where(models.Product.tenant_id == self.tenant_id)
            result = await self.db.execute(query)
            items = result.scalars().all()
            
            duplicates = []
            checked = set()
            
            for i, item1 in enumerate(items):
                for item2 in items[i+1:]:
                    if (item1.id, item2.id) in checked:
                        continue
                    
                    # Compare titles
                    score = fuzz.ratio(item1.title.lower(), item2.title.lower())
                    if score >= threshold:
                        duplicates.append({
                            "ids": [item1.id, item2.id],
                            "names": [item1.title, item2.title],
                            "skus": [item1.sku, item2.sku],
                            "similarity_score": score / 100,
                            "suggested_action": "merge" if score >= 95 else "review"
                        })
                        checked.add((item1.id, item2.id))
            
            return {
                "entity_type": entity_type,
                "duplicate_groups": duplicates,
                "count": len(duplicates),
                "sources": [f"product#{d['ids'][0]}" for d in duplicates]
            }
        
        elif entity_type == "suppliers":
            query = select(models.Supplier).where(models.Supplier.tenant_id == self.tenant_id)
            result = await self.db.execute(query)
            items = result.scalars().all()
            
            duplicates = []
            for i, item1 in enumerate(items):
                for item2 in items[i+1:]:
                    score = fuzz.ratio(item1.name.lower(), item2.name.lower())
                    if score >= threshold:
                        duplicates.append({
                            "ids": [item1.id, item2.id],
                            "names": [item1.name, item2.name],
                            "similarity_score": score / 100,
                            "suggested_action": "merge" if score >= 95 else "review"
                        })
            
            return {
                "entity_type": entity_type,
                "duplicate_groups": duplicates,
                "count": len(duplicates),
                "sources": [f"supplier#{d['ids'][0]}" for d in duplicates]
            }
        
        elif entity_type == "clients":
            query = select(models.Client).where(models.Client.tenant_id == self.tenant_id)
            result = await self.db.execute(query)
            items = result.scalars().all()
            
            duplicates = []
            for i, item1 in enumerate(items):
                for item2 in items[i+1:]:
                    score = fuzz.ratio(item1.name.lower(), item2.name.lower())
                    if score >= threshold:
                        duplicates.append({
                            "ids": [item1.id, item2.id],
                            "names": [item1.name, item2.name],
                            "emails": [item1.email, item2.email],
                            "similarity_score": score / 100,
                            "suggested_action": "merge" if score >= 95 else "review"
                        })
            
            return {
                "entity_type": entity_type,
                "duplicate_groups": duplicates,
                "count": len(duplicates),
                "sources": [f"client#{d['ids'][0]}" for d in duplicates]
            }
        
        return {"error": f"Unknown entity type: {entity_type}"}

    async def _tool_suggest_pricing(
        self,
        target_margin_percent: float,
        category: Optional[str] = None,
        only_below_target: bool = True
    ) -> Dict[str, Any]:
        """Calculate suggested prices for target margin."""
        
        query = select(models.Product).where(models.Product.tenant_id == self.tenant_id)
        if category:
            query = query.where(models.Product.category == category)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        suggestions = []
        target_margin = target_margin_percent / 100
        
        for product in products:
            if not product.default_cost or product.default_cost <= 0:
                continue
            
            cost = float(product.default_cost)
            current_price = float(product.default_price) if product.default_price else 0
            
            # Calculate current margin
            if current_price > 0:
                current_margin = (current_price - cost) / current_price
            else:
                current_margin = 0
            
            # Calculate suggested price for target margin
            # margin = (price - cost) / price
            # price * margin = price - cost
            # price - price * margin = cost
            # price * (1 - margin) = cost
            # price = cost / (1 - margin)
            suggested_price = cost / (1 - target_margin)
            
            if only_below_target and current_margin >= target_margin:
                continue
            
            suggestions.append({
                "product_id": product.id,
                "sku": product.sku,
                "title": product.title,
                "category": product.category,
                "cost": cost,
                "current_price": current_price,
                "current_margin_pct": round(current_margin * 100, 1),
                "suggested_price": round(suggested_price, 2),
                "price_increase": round(suggested_price - current_price, 2) if current_price else suggested_price
            })
        
        return {
            "target_margin_percent": target_margin_percent,
            "suggestions": suggestions,
            "count": len(suggestions),
            "formula": "suggested_price = cost / (1 - target_margin)",
            "sources": [f"product#{s['product_id']}" for s in suggestions]
        }

    async def _tool_create_task(
        self,
        title: str,
        description: str,
        due_date: Optional[str] = None,
        priority: str = "medium",
        related_entities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create an actionable task. (Placeholder - would need Task model)"""
        
        # For now, return a task object that the frontend can display
        # In a full implementation, this would save to a Task table
        
        task_id = f"task_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "task_created": True,
            "task": {
                "id": task_id,
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
                "related_entities": related_entities or [],
                "status": "pending"
            },
            "message": f"Task '{title}' created successfully"
        }

    async def _tool_suggest_data_fixes(
        self,
        fix_type: str,
        entities: List[Dict]
    ) -> Dict[str, Any]:
        """Store data fix suggestions for user approval."""
        
        # Create a DataFixSuggestion record
        from app.models import DataFixSuggestion, DataFixStatus
        
        suggestion = DataFixSuggestion(
            tenant_id=self.tenant_id,
            fix_type=fix_type,
            entity_type=entities[0].get("type", "unknown") if entities else "unknown",
            changes=entities,
            status=DataFixStatus.pending,
            affected_records=len(entities)
        )
        
        self.db.add(suggestion)
        await self.db.flush()
        
        return {
            "suggestion_id": suggestion.id,
            "fix_type": fix_type,
            "affected_records": len(entities),
            "status": "pending_approval",
            "message": "Data fix suggestion created. User approval required before applying.",
            "requires_approval": True
        }

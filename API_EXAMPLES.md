# API Examples

Complete examples of API usage with curl and Python.

## Authentication

### Register New User

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "full_name": "John Doe",
    "tenant_name": "My Company"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "manager",
  "is_active": true,
  "created_at": "2025-01-27T10:00:00Z"
}
```

### Login

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Get Current User

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Tenants

### Create Tenant

```bash
curl -X POST "http://localhost:8000/api/v1/tenants/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Tech Store LLC",
    "timezone": "Asia/Almaty",
    "currency": "KZT"
  }'
```

### List Tenants

```bash
curl -X GET "http://localhost:8000/api/v1/tenants/?skip=0&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Clients (Customers)

### Create Client

```bash
curl -X POST "http://localhost:8000/api/v1/clients/?tenant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Acme Corporation",
    "email": "contact@acme.com",
    "phone": "+77001234567",
    "address": "123 Main St, Almaty"
  }'
```

### List Clients

```bash
curl -X GET "http://localhost:8000/api/v1/clients/?tenant_id=1&skip=0&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Client

```bash
curl -X PATCH "http://localhost:8000/api/v1/clients/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "phone": "+77007654321",
    "address": "456 New St, Almaty"
  }'
```

## Products

### Create Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/?tenant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Laptop Dell XPS 15",
    "sku": "DELL-XPS-15",
    "description": "High-performance laptop",
    "category": "Electronics",
    "default_cost": "850000.00",
    "default_price": "1200000.00",
    "currency": "KZT"
  }'
```

### List Products

```bash
curl -X GET "http://localhost:8000/api/v1/products/?tenant_id=1&q=laptop&skip=0&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Product

```bash
curl -X GET "http://localhost:8000/api/v1/products/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Orders

### Create Order

```bash
curl -X POST "http://localhost:8000/api/v1/orders/?tenant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "client_id": 1,
    "channel": "web",
    "external_id": "WEB-12345",
    "items": [
      {
        "product_id": 1,
        "title": "Laptop Dell XPS 15",
        "qty": 2,
        "unit_price": "1200000.00",
        "unit_cost": "850000.00",
        "currency": "KZT"
      }
    ]
  }'
```

**Response:**
```json
{
  "id": 1,
  "tenant_id": 1,
  "client_id": 1,
  "external_id": "WEB-12345",
  "channel": "web",
  "status": "created",
  "total_amount": "2400000.00",
  "currency": "KZT",
  "created_at": "2025-01-27T10:30:00Z"
}
```

## Deals

### Create Deal

```bash
curl -X POST "http://localhost:8000/api/v1/deals/?tenant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "client_id": 1,
    "title": "Corporate IT Equipment Deal",
    "total_price": "5000000.00",
    "total_cost": "3000000.00",
    "currency": "KZT"
  }'
```

### Update Deal Status

```bash
curl -X POST "http://localhost:8000/api/v1/deals/1/status?status=negotiation" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Finance

### Get Financial Summary

**Basic request:**
```bash
curl -X GET "http://localhost:8000/api/v1/finance/summary?tenant_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**With date range and expenses:**
```bash
curl -X GET "http://localhost:8000/api/v1/finance/summary?tenant_id=1&start=2025-01-01T00:00:00&end=2025-01-31T23:59:59&opex=500000&fixed=200000&variable=1500000&tax_percent=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "revenue": "2400000.00",
  "cogs": "1700000.00",
  "gross_profit": "700000.00",
  "gross_margin_pct": "29.17",
  "opex": "500000.00",
  "ebit": "200000.00",
  "taxes_percent": "10.00",
  "taxes": "20000.00",
  "total_expenses": "2400000.00",
  "net_profit": "-20000.00",
  "net_margin_pct": "-0.83",
  "fixed_costs": "200000.00",
  "variable_costs": "1500000.00",
  "break_even_revenue": "533333.33"
}
```

## Suppliers

### Create Supplier

```bash
curl -X POST "http://localhost:8000/api/v1/suppliers/?tenant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "China Electronics Co",
    "contact": {
      "email": "sales@chinaelectronics.cn",
      "phone": "+86-123-456-7890",
      "wechat": "chinaelec"
    },
    "rating": "4.5",
    "lead_time_days": 30
  }'
```

### Create Purchase Order

```bash
curl -X POST "http://localhost:8000/api/v1/purchase_orders/?tenant_id=1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "supplier_id": 1,
    "reference": "PO-2025-001",
    "currency": "CNY",
    "items": [
      {
        "product_id": 1,
        "qty": 50,
        "unit_price": "5000.00",
        "currency": "CNY"
      }
    ]
  }'
```

## Inventory

### Get Product Inventory

```bash
curl -X GET "http://localhost:8000/api/v1/inventory/product/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Adjust Inventory

```bash
curl -X POST "http://localhost:8000/api/v1/inventory/adjust" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "product_id": 1,
    "delta": "100",
    "location": "Warehouse A"
  }'
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
login_response = requests.post(
    f"{BASE_URL}/auth/token",
    data={
        "username": "demo@bizio.com",
        "password": "demo123"
    }
)
token = login_response.json()["access_token"]

# Set up headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Create a product
product_data = {
    "title": "iPhone 15 Pro",
    "sku": "IPHONE-15-PRO",
    "default_cost": "500000.00",
    "default_price": "750000.00",
    "category": "Smartphones"
}
product_response = requests.post(
    f"{BASE_URL}/products/?tenant_id=1",
    json=product_data,
    headers=headers
)
product = product_response.json()
print(f"Created product: {product['id']}")

# Create an order
order_data = {
    "client_id": 1,
    "channel": "web",
    "items": [
        {
            "product_id": product["id"],
            "title": product["title"],
            "qty": 5,
            "unit_price": product["default_price"],
            "unit_cost": product["default_cost"]
        }
    ]
}
order_response = requests.post(
    f"{BASE_URL}/orders/?tenant_id=1",
    json=order_data,
    headers=headers
)
order = order_response.json()
print(f"Created order: {order['id']}, Total: {order['total_amount']} KZT")

# Get financial summary
finance_response = requests.get(
    f"{BASE_URL}/finance/summary",
    params={
        "tenant_id": 1,
        "opex": 100000,
        "fixed": 50000,
        "tax_percent": 10
    },
    headers=headers
)
finance = finance_response.json()
print(f"Revenue: {finance['revenue']} KZT")
print(f"Net Profit: {finance['net_profit']} KZT")
print(f"Net Margin: {finance['net_margin_pct']}%")
```

## Error Handling

### Authentication Error (401)

```json
{
  "detail": "Could not validate credentials"
}
```

### Not Found (404)

```json
{
  "detail": "Product not found"
}
```

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

## Rate Limiting

When rate limiting is enabled, excessive requests will return:

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

**Response headers:**
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time until limit resets

## Pagination

List endpoints support pagination:

```bash
curl -X GET "http://localhost:8000/api/v1/products/?tenant_id=1&skip=0&limit=50"
```

Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50, max: 100)


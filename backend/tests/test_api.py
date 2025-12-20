# tests/test_api.py
"""
Integration tests for API endpoints
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root health check endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_create_tenant(client: AsyncClient):
    """Test tenant creation"""
    response = await client.post(
        "/api/v1/tenants/",
        json={
            "name": "Test Company",
            "timezone": "UTC",
            "currency": "USD"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["currency"] == "USD"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
            "tenant_name": "New Company"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data  # password should not be in response


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, demo_user):
    """Test user login"""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "testpass"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials"""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, demo_tenant):
    """Test product creation"""
    response = await client.post(
        f"/api/v1/products/?tenant_id={demo_tenant.id}",
        json={
            "title": "New Product",
            "sku": "PROD-001",
            "default_cost": "50.00",
            "default_price": "75.00",
            "category": "Electronics"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Product"
    assert data["sku"] == "PROD-001"


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, demo_tenant, demo_client, demo_product):
    """Test order creation"""
    response = await client.post(
        f"/api/v1/orders/?tenant_id={demo_tenant.id}",
        json={
            "client_id": demo_client.id,
            "channel": "web",
            "items": [
                {
                    "product_id": demo_product.id,
                    "title": demo_product.title,
                    "qty": 2,
                    "unit_price": "150.00",
                    "unit_cost": "100.00"
                }
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == demo_client.id
    assert data["total_amount"] == "300.00"  # 2 * 150


@pytest.mark.asyncio
async def test_finance_summary(client: AsyncClient, demo_tenant, demo_client, demo_product):
    """Test finance summary endpoint with real orders"""
    # First create some orders
    await client.post(
        f"/api/v1/orders/?tenant_id={demo_tenant.id}",
        json={
            "client_id": demo_client.id,
            "channel": "web",
            "items": [
                {
                    "product_id": demo_product.id,
                    "title": demo_product.title,
                    "qty": 10,
                    "unit_price": "150.00",
                    "unit_cost": "100.00"
                }
            ]
        }
    )
    
    # Now get finance summary
    response = await client.get(
        f"/api/v1/finance/summary?tenant_id={demo_tenant.id}&opex=500&fixed=200&variable=1000&tax_percent=10"
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify financial calculations
    assert "revenue" in data
    assert "cogs" in data
    assert "gross_profit" in data
    assert "net_profit" in data
    assert "break_even_revenue" in data
    
    # Revenue should be 1500 (10 * 150)
    assert Decimal(data["revenue"]) == Decimal("1500.00")
    # COGS should be 1000 (10 * 100)
    assert Decimal(data["cogs"]) == Decimal("1000.00")


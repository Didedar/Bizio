import pytest
from httpx import AsyncClient
from decimal import Decimal
from app.main import app

# Use a dedicated tenant_id for testing to avoid conflicts
TEST_TENANT_ID = 9999

@pytest.mark.asyncio
async def test_create_expense(client: AsyncClient, db_session):
    # 1. Create Expense
    payload = {
        "category": "Test Category",
        "amount": 100.50,
        "date": "2023-10-27T10:00:00",
        "description": "Test Expense",
        "is_fixed": True
    }
    response = await client.post(f"/api/v1/finance/expenses?tenant_id={TEST_TENANT_ID}", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == payload["category"]
    assert Decimal(str(data["amount"])) == Decimal("100.50")
    assert data["is_fixed"] is True
    return data["id"]

@pytest.mark.asyncio
async def test_get_expenses(client: AsyncClient, db_session):
    # Create one first to ensure there is data
    await test_create_expense(client, db_session)
    
    response = await client.get(f"/api/v1/finance/expenses?tenant_id={TEST_TENANT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

@pytest.mark.asyncio
async def test_delete_expense(client: AsyncClient, db_session):
    # Create an expense to delete
    expense_id = await test_create_expense(client, db_session)
    
    # Delete it
    response = await client.delete(f"/api/v1/finance/expenses/{expense_id}?tenant_id={TEST_TENANT_ID}")
    assert response.status_code == 204
    
    # Verify it's gone
    # We need to fetch list and check it's not there, or try to delete again (should be 404)
    response = await client.delete(f"/api/v1/finance/expenses/{expense_id}?tenant_id={TEST_TENANT_ID}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_financial_settings_lifecycle(client: AsyncClient, db_session):
    # 1. Get Settings (should create default)
    response = await client.get(f"/api/v1/finance/settings?tenant_id={TEST_TENANT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["tax_rate"])) == Decimal("0.00") # Default
    assert data["currency"] == "KZT" # Default

    # 2. Update Settings (PUT)
    payload = {
        "tax_rate": 12.5,
        "currency": "USD"
    }
    response = await client.put(f"/api/v1/finance/settings?tenant_id={TEST_TENANT_ID}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["tax_rate"])) == Decimal("12.50")
    assert data["currency"] == "USD"

    # 3. Verify Update Persisted
    response = await client.get(f"/api/v1/finance/settings?tenant_id={TEST_TENANT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert Decimal(str(data["tax_rate"])) == Decimal("12.50")
    assert data["currency"] == "USD"

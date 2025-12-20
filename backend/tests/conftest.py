# tests/conftest.py
"""
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import Base, get_db
from app import models, crud
from app.core.security import get_password_hash

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests"""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for testing API endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def demo_tenant(db_session: AsyncSession):
    """Create a demo tenant for testing"""
    tenant = await crud.create_tenant(
        db_session,
        name="Test Tenant",
        timezone="UTC",
        currency="KZT"
    )
    return tenant


@pytest.fixture
async def demo_user(db_session: AsyncSession, demo_tenant):
    """Create a demo user for testing"""
    user = await crud.create_user(
        db_session,
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass"),
        role=models.UserRole.admin
    )
    user.tenants.append(demo_tenant)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def demo_client(db_session: AsyncSession, demo_tenant):
    """Create a demo client for testing"""
    from app import schemas
    client = await crud.create_client(
        db_session,
        tenant_id=demo_tenant.id,
        payload=schemas.ClientCreate(
            name="Test Client",
            email="client@example.com",
            phone="+77001234567"
        )
    )
    return client


@pytest.fixture
async def demo_product(db_session: AsyncSession, demo_tenant):
    """Create a demo product for testing"""
    from decimal import Decimal
    product = await crud.create_product(
        db_session,
        tenant_id=demo_tenant.id,
        product_data={
            "title": "Test Product",
            "sku": "TEST-001",
            "default_cost": Decimal("100.00"),
            "default_price": Decimal("150.00"),
            "category": "Test"
        }
    )
    return product


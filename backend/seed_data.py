#!/usr/bin/env python3
# backend/seed_data.py
"""
Seed script to create demo tenant, users, products, and orders for testing.
Run: python seed_data.py
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import insert

from app.db import AsyncSessionLocal
from app import crud, models
from app.core.security import get_password_hash

async def seed_demo_data():
    """Create demo data for testing"""
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding demo data...")
        
        # 1. Create demo tenant
        print("Creating demo tenant...")
        tenant = await crud.create_tenant(
            db, 
            name="Demo Company Ltd",
            timezone="Asia/Almaty",
            currency="KZT"
        )
        print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
        
        # 2. Create demo user
        print("Creating demo user...")
        user = await crud.create_user(
            db,
            email="demo@bizio.com",
            full_name="Demo Admin",
            hashed_password=get_password_hash("demo123"),
            role=models.UserRole.admin
        )
        # Associate user with tenant using raw SQL or direct access
        # Using async-safe approach
        from app.models.users import user_tenant_association
        tenant_user_link = insert(user_tenant_association).values(
            tenant_id=tenant.id,
            user_id=user.id
        )
        await db.execute(tenant_user_link)
        await db.commit()
        print(f"✓ Created user: {user.email} (password: demo123)")
        
        # 3. Create demo clients
        print("Creating demo clients...")
        clients = []
        for i in range(1, 4):
            client = await crud.create_client(
                db,
                tenant_id=tenant.id,
                payload=type('obj', (object,), {
                    'name': f'Client {i}',
                    'email': f'client{i}@example.com',
                    'phone': f'+7700000000{i}',
                    'address': f'Almaty, Kazakhstan, Street {i}'
                })
            )
            clients.append(client)
            print(f"  ✓ Created client: {client.name}")
        
        # 4. Create demo products
        print("Creating demo products...")
        products = []
        product_data = [
            {"title": "Laptop MacBook Pro", "sku": "LAP-001", "default_cost": Decimal("500000"), "default_price": Decimal("750000"), "category": "Electronics"},
            {"title": "Wireless Mouse", "sku": "MOU-002", "default_cost": Decimal("3000"), "default_price": Decimal("5000"), "category": "Accessories"},
            {"title": "USB-C Hub", "sku": "HUB-003", "default_cost": Decimal("5000"), "default_price": Decimal("8000"), "category": "Accessories"},
            {"title": "Monitor 27 inch", "sku": "MON-004", "default_cost": Decimal("80000"), "default_price": Decimal("120000"), "category": "Electronics"},
            {"title": "Keyboard Mechanical", "sku": "KEY-005", "default_cost": Decimal("15000"), "default_price": Decimal("22000"), "category": "Accessories"},
        ]
        
        for pd in product_data:
            product = await crud.create_product(db, tenant.id, pd)
            products.append(product)
            print(f"  ✓ Created product: {product.title} (SKU: {product.sku})")
        
        # 5. Create demo orders
        print("Creating demo orders...")
        for i, client in enumerate(clients):
            # Create 2 orders per client
            for j in range(2):
                items = [
                    {
                        "product_id": products[i % len(products)].id,
                        "title": products[i % len(products)].title,
                        "qty": j + 1,
                        "unit_price": products[i % len(products)].default_price,
                        "unit_cost": products[i % len(products)].default_cost,
                    }
                ]
                
                order = await crud.create_order(
                    db,
                    tenant_id=tenant.id,
                    client_id=client.id,
                    channel="web",
                    items=items,
                    external_id=f"ORD-{i}-{j}"
                )
                print(f"  ✓ Created order #{order.id} for {client.name}: {order.total_amount} KZT")
        
        # 6. Create demo supplier
        print("Creating demo supplier...")
        supplier = await crud.create_supplier(
            db,
            tenant_id=tenant.id,
            name="China Supplier Co",
            contact={"email": "supplier@china.com", "phone": "+86123456789"},
            rating=Decimal("4.5"),
            lead_time_days=30
        )
        print(f"✓ Created supplier: {supplier.name}")
        
        # 7. Create demo deals
        print("Creating demo deals...")
        deal = await crud.create_deal(
            db,
            tenant_id=tenant.id,
            payload=type('obj', (object,), {
                'client_id': clients[0].id,
                'title': 'Corporate IT Equipment Deal',
                'total_price': Decimal("1500000"),
                'total_cost': Decimal("900000"),
                'currency': 'KZT'
            })
        )
        print(f"✓ Created deal: {deal.title}")
        
        print("\n✅ Demo data seeded successfully!")
        print("\n📋 Summary:")
        print(f"  • Tenant: {tenant.name} (ID: {tenant.id})")
        print(f"  • User: {user.email} / demo123")
        print(f"  • Clients: {len(clients)}")
        print(f"  • Products: {len(products)}")
        print(f"  • Orders: {len(clients) * 2}")
        print("\n🚀 You can now login with: demo@bizio.com / demo123")
        print("📊 Test finance endpoint: GET /api/v1/finance/summary?tenant_id=1")

if __name__ == "__main__":
    try:
        asyncio.run(seed_demo_data())
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        sys.exit(1)


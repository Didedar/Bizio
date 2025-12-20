#!/usr/bin/env python3
"""
Скрипт для создания демо-сделки для tenant_id=2
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, '/Users/sabyrhandarhan/develop/Python projects/Bizio/backend')

from app.models.deals import Deal, DealStatus
from app.models.clients import Client
from app.models.users import Tenant

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

async def create_demo_deal_for_tenant_2():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Проверяем существует ли tenant_id=2
        from sqlalchemy import select
        result = await session.execute(select(Tenant).where(Tenant.id == 2))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            print("❌ Tenant с id=2 не найден. Создаем...")
            tenant = Tenant(
                id=2,
                name="Демо Компания 2",
                email="demo2@example.com",
                is_active=True
            )
            session.add(tenant)
            await session.commit()
            print(f"✅ Создан tenant: {tenant.name}")
        else:
            print(f"✅ Найден tenant: {tenant.name}")
        
        # Проверяем есть ли клиент для tenant_id=2
        result = await session.execute(
            select(Client).where(Client.tenant_id == 2).limit(1)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            print("❌ Клиент для tenant_id=2 не найден. Создаем...")
            client = Client(
                tenant_id=2,
                name="Демо Клиент",
                email="client@example.com",
                phone="+7 123 456 7890"
            )
            session.add(client)
            await session.commit()
            await session.refresh(client)
            print(f"✅ Создан клиент: {client.name}")
        else:
            print(f"✅ Найден клиент: {client.name}")
        
        # Создаем сделки с разными статусами
        deals_to_create = [
            {
                "title": "Сделка 1 - Завершена",
                "status": DealStatus.final_account,
                "total_price": Decimal("50000.00"),
                "total_cost": Decimal("30000.00"),
            },
            {
                "title": "Сделка 2 - В работе",
                "status": DealStatus.at_work,
                "total_price": Decimal("75000.00"),
                "total_cost": Decimal("45000.00"),
            },
            {
                "title": "Сделка 3 - Новая",
                "status": DealStatus.new,
                "total_price": Decimal("100000.00"),
                "total_cost": Decimal("60000.00"),
            }
        ]
        
        print("\n📝 Создаем демо-сделки для tenant_id=2...")
        for deal_data in deals_to_create:
            deal = Deal(
                tenant_id=2,
                client_id=client.id,
                title=deal_data["title"],
                status=deal_data["status"],
                total_price=deal_data["total_price"],
                total_cost=deal_data["total_cost"],
                margin=deal_data["total_price"] - deal_data["total_cost"],
                currency="KZT",
                created_at=datetime.utcnow()
            )
            session.add(deal)
            print(f"  ✅ {deal.title} (статус: {deal.status}, выручка: {deal.total_price})")
        
        await session.commit()
        
        print("\n" + "="*60)
        print("🎉 Демо-данные успешно созданы для tenant_id=2!")
        print("="*60)
        print("Теперь у вас есть:")
        print("  - 1 сделка в статусе 'final_account' (50,000 тг)")
        print("  - 1 сделка в статусе 'at_work' (75,000 тг)")
        print("  - 1 сделка в статусе 'new' (100,000 тг)")
        print("="*60 + "\n")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_demo_deal_for_tenant_2())

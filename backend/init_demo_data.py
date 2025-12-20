"""
Скрипт для создания демо-данных в базе данных.
Создаёт клиентов, продукты, сделки со статусом final_account для тестирования финансов.
Запуск: cd backend && python init_demo_data.py
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"


async def init_demo_data():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("🚀 Создание демо-данных для тестирования финансов...")
        
        # Получаем первый tenant
        result = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_row = result.fetchone()
        if not tenant_row:
            print("❌ Нет tenant'ов в базе! Сначала зарегистрируйтесь в системе.")
            return
        
        tenant_id = tenant_row[0]
        print(f"✅ Используем tenant_id: {tenant_id}")
        
        # Проверяем есть ли уже клиенты
        result = await db.execute(text("SELECT COUNT(*) FROM clients WHERE tenant_id = :tid"), {"tid": tenant_id})
        client_count = result.scalar()
        
        if client_count == 0:
            print("📝 Создаём демо-клиентов...")
            
            clients_data = [
                ("ТОО Альфа-Трейд", "alpha@example.com", "+7 777 111 2233", "Алматы, ул. Абая 1"),
                ("ИП Бета Сервис", "beta@example.com", "+7 777 222 3344", "Астана, ул. Кенесары 5"),
                ("ТОО Гамма Продукт", "gamma@example.com", "+7 777 333 4455", "Караганда, ул. Мира 10"),
            ]
            
            for name, email, phone, address in clients_data:
                await db.execute(text("""
                    INSERT INTO clients (tenant_id, name, email, phone, address, created_at, updated_at)
                    VALUES (:tid, :name, :email, :phone, :address, :now, :now)
                """), {
                    "tid": tenant_id, 
                    "name": name, 
                    "email": email, 
                    "phone": phone, 
                    "address": address,
                    "now": datetime.utcnow()
                })
            
            await db.commit()
            print(f"   ✅ Создано {len(clients_data)} клиентов")
        else:
            print(f"✅ Клиенты уже есть: {client_count}")
        
        # Получаем ID первого клиента
        result = await db.execute(text("SELECT id FROM clients WHERE tenant_id = :tid LIMIT 1"), {"tid": tenant_id})
        client_row = result.fetchone()
        client_id = client_row[0]
        
        # Проверяем есть ли сделки
        result = await db.execute(text("SELECT COUNT(*) FROM deals WHERE tenant_id = :tid"), {"tid": tenant_id})
        deal_count = result.scalar()
        
        if deal_count == 0:
            print("📝 Создаём демо-сделки...")
            
            # Создаем сделки за последние 3 месяца
            now = datetime.utcnow()
            deals_data = [
                # (title, total_price, total_cost, status, days_ago)
                ("Поставка оборудования #001", 500000, 350000, "final_account", 60),
                ("Услуги консалтинга #002", 250000, 50000, "final_account", 45),
                ("Продажа товаров #003", 180000, 120000, "final_account", 30),
                ("Контракт на обслуживание #004", 300000, 80000, "final_account", 20),
                ("Поставка материалов #005", 450000, 280000, "final_account", 10),
                ("Новый проект #006", 200000, 100000, "final_account", 5),
                # Активные сделки
                ("Переговоры #007", 150000, 75000, "new", 3),
                ("В работе #008", 280000, 140000, "at_work", 2),
                ("Ожидание предоплаты #009", 320000, 160000, "prepaid_account", 1),
            ]
            
            for title, price, cost, status, days_ago in deals_data:
                created = now - timedelta(days=days_ago)
                margin = price - cost
                await db.execute(text("""
                    INSERT INTO deals (
                        tenant_id, client_id, title, total_price, total_cost, margin, 
                        currency, status, created_at, updated_at, is_available_to_all
                    )
                    VALUES (
                        :tid, :cid, :title, :price, :cost, :margin, 
                        'KZT', :status, :created, :created, 1
                    )
                """), {
                    "tid": tenant_id,
                    "cid": client_id,
                    "title": title,
                    "price": price,
                    "cost": cost,
                    "margin": margin,
                    "status": status,
                    "created": created
                })
            
            await db.commit()
            print(f"   ✅ Создано {len(deals_data)} сделок")
        else:
            print(f"ℹ️  Сделки уже есть: {deal_count}")
        
        # Итоговая статистика
        print("\n📊 Финальная статистика:")
        
        result = await db.execute(text("""
            SELECT status, COUNT(*), COALESCE(SUM(total_price), 0), COALESCE(SUM(total_cost), 0)
            FROM deals WHERE tenant_id = :tid
            GROUP BY status
        """), {"tid": tenant_id})
        
        for row in result.fetchall():
            status, count, revenue, cogs = row
            print(f"   {status}: {count} сделок, Revenue={revenue:,.0f}, COGS={cogs:,.0f}")
        
        # Финансовые показатели для final_account
        result = await db.execute(text("""
            SELECT 
                COALESCE(SUM(total_price), 0) as revenue,
                COALESCE(SUM(total_cost), 0) as cogs
            FROM deals 
            WHERE tenant_id = :tid AND status = 'final_account'
        """), {"tid": tenant_id})
        
        row = result.fetchone()
        revenue = Decimal(str(row[0]))
        cogs = Decimal(str(row[1]))
        gross_profit = revenue - cogs
        
        print(f"\n💰 Финансовые показатели (final_account):")
        print(f"   Revenue:      {revenue:>12,.0f} KZT")
        print(f"   COGS:         {cogs:>12,.0f} KZT")
        print(f"   Gross Profit: {gross_profit:>12,.0f} KZT")
        print(f"   Margin:       {(gross_profit/revenue*100) if revenue else 0:>12.1f}%")
        
        print("\n✅ Демо-данные созданы! Обновите страницу финансов.")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_demo_data())

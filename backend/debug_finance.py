"""
Отладочный скрипт для диагностики проблем с финансовой аналитикой.
Запуск: cd backend && python debug_finance.py
"""

import asyncio
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Настройки подключения (возьмем из .env или hardcode для отладки)
DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

async def debug_finance():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("🔍 ОТЛАДКА ФИНАНСОВОЙ АНАЛИТИКИ")
        print("=" * 80)
        
        # 1. Проверяем все tenant_id
        result = await db.execute(text("SELECT DISTINCT tenant_id FROM deals"))
        tenants = result.scalars().all()
        print(f"\n📋 Найденные tenant_id в сделках: {tenants}")
        
        # 2. Проверяем все уникальные статусы в базе данных  
        result = await db.execute(text("SELECT DISTINCT status FROM deals"))
        statuses = result.scalars().all()
        print(f"\n📊 Уникальные статусы сделок в БД: {statuses}")
        
        # 3. Общая статистика по сделкам
        result = await db.execute(text("""
            SELECT 
                status, 
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as total_revenue,
                COALESCE(SUM(total_cost), 0) as total_cogs
            FROM deals 
            GROUP BY status
            ORDER BY status
        """))
        rows = result.fetchall()
        
        print("\n📈 Статистика по статусам:")
        print("-" * 60)
        print(f"{'Статус':<20} | {'Кол-во':<8} | {'Revenue':<15} | {'COGS':<15}")
        print("-" * 60)
        for row in rows:
            status, count, revenue, cogs = row
            print(f"{str(status):<20} | {count:<8} | {revenue:<15} | {cogs:<15}")
        print("-" * 60)
        
        # 4. Проверяем сделки со статусом final_account
        result = await db.execute(text("""
            SELECT id, tenant_id, title, status, total_price, total_cost, created_at, closed_at
            FROM deals 
            WHERE status = 'final_account'
            ORDER BY created_at DESC
            LIMIT 20
        """))
        final_deals = result.fetchall()
        
        print(f"\n✅ Сделки со статусом 'final_account': {len(final_deals)}")
        if final_deals:
            print("-" * 100)
            print(f"{'ID':<6} | {'Tenant':<8} | {'Title':<25} | {'Revenue':<12} | {'COGS':<12} | {'Created':<20}")
            print("-" * 100)
            for deal in final_deals:
                deal_id, tenant_id, title, status, price, cost, created, closed = deal
                title_short = (title[:22] + "...") if len(str(title)) > 25 else title
                created_str = created.strftime("%Y-%m-%d %H:%M") if created else "N/A"
                print(f"{deal_id:<6} | {tenant_id:<8} | {title_short:<25} | {price or 0:<12} | {cost or 0:<12} | {created_str:<20}")
        else:
            print("   ⚠️  НЕТ СДЕЛОК СО СТАТУСОМ 'final_account'!")
            print("   💡 Сделки должны иметь статус 'final_account' чтобы учитываться в финансах")
        
        # 5. Проверяем даты
        result = await db.execute(text("""
            SELECT 
                MIN(created_at) as earliest,
                MAX(created_at) as latest
            FROM deals
        """))
        dates = result.fetchone()
        if dates and dates[0]:
            print(f"\n📅 Диапазон дат сделок:")
            print(f"   Самая ранняя: {dates[0]}")
            print(f"   Самая поздняя: {dates[1]}")
        
        # 6. Проверка расходов
        result = await db.execute(text("""
            SELECT 
                tenant_id,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as total_amount
            FROM expenses
            GROUP BY tenant_id
        """))
        expenses = result.fetchall()
        print(f"\n💸 Расходы (expenses) по tenant_id:")
        if expenses:
            for exp in expenses:
                print(f"   Tenant {exp[0]}: {exp[1]} записей, сумма: {exp[2]}")
        else:
            print("   ⚠️  Расходов нет в базе")
        
        # 7. Тестируем расчет финансов для первого tenant_id
        if tenants:
            tenant_id = tenants[0]
            print(f"\n🧮 Тестовый расчет финансов для tenant_id={tenant_id}:")
            
            # Текущий месяц
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            
            result = await db.execute(text("""
                SELECT 
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(total_cost), 0) as cogs
                FROM deals 
                WHERE tenant_id = :tenant_id 
                AND status = 'final_account'
                AND created_at >= :start_date
            """), {"tenant_id": tenant_id, "start_date": start_of_month})
            
            row = result.fetchone()
            print(f"   Период: {start_of_month.date()} - {now.date()}")
            print(f"   Revenue: {row[0]}")
            print(f"   COGS: {row[1]}")
            print(f"   Gross Profit: {Decimal(str(row[0])) - Decimal(str(row[1]))}")
            
            # Весь год
            start_of_year = datetime(now.year, 1, 1)
            result = await db.execute(text("""
                SELECT 
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(total_cost), 0) as cogs
                FROM deals 
                WHERE tenant_id = :tenant_id 
                AND status = 'final_account'
                AND created_at >= :start_date
            """), {"tenant_id": tenant_id, "start_date": start_of_year})
            
            row = result.fetchone()
            print(f"\n   Период: {start_of_year.date()} - {now.date()} (весь год)")
            print(f"   Revenue: {row[0]}")
            print(f"   COGS: {row[1]}")
            print(f"   Gross Profit: {Decimal(str(row[0])) - Decimal(str(row[1]))}")
            
            # Без фильтра по дате
            result = await db.execute(text("""
                SELECT 
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(total_cost), 0) as cogs
                FROM deals 
                WHERE tenant_id = :tenant_id 
                AND status = 'final_account'
            """), {"tenant_id": tenant_id})
            
            row = result.fetchone()
            print(f"\n   БЕЗ ФИЛЬТРА ПО ДАТЕ:")
            print(f"   Revenue: {row[0]}")
            print(f"   COGS: {row[1]}")
            print(f"   Gross Profit: {Decimal(str(row[0])) - Decimal(str(row[1]))}")
        
        print("\n" + "=" * 80)
        print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 80)
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_finance())

#!/usr/bin/env python3
"""
Скрипт для проверки tenant_id в сделках
"""
import asyncio
import sys
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, '/Users/sabyrhandarhan/develop/Python projects/Bizio/backend')

from app.models.deals import Deal

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

async def check_tenant_ids():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Проверяем какие tenant_id есть в сделках
        query = select(
            Deal.tenant_id,
            func.count(Deal.id).label('count'),
            func.sum(Deal.total_price).label('total_revenue')
        ).group_by(Deal.tenant_id)
        
        result = await session.execute(query)
        rows = result.all()
        
        print("\n" + "="*60)
        print("📊 СДЕЛКИ ПО TENANT_ID:")
        print("="*60)
        
        if not rows:
            print("❌ В базе НЕТ сделок!")
        else:
            for row in rows:
                print(f"tenant_id={row.tenant_id}: {row.count} сделок, выручка={row.total_revenue}")
        
        print("="*60)
        
        # Проверяем статусы сделок
        print("\n📋 СДЕЛКИ ПО СТАТУСАМ:")
        print("="*60)
        
        status_query = select(
            Deal.tenant_id,
            Deal.status,
            func.count(Deal.id).label('count')
        ).group_by(Deal.tenant_id, Deal.status)
        
        status_result = await session.execute(status_query)
        status_rows = status_result.all()
        
        for row in status_rows:
            print(f"tenant_id={row.tenant_id}, status={row.status}: {row.count} сделок")
        
        print("="*60 + "\n")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_tenant_ids())

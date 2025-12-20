"""
Fix Script: Recalculate deal totals from items.
Run: cd backend && python fix_deal_totals.py
"""

import asyncio
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

async def fix_deal_totals():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("🔧 FIXING DEAL TOTALS FROM ITEMS")
        print("=" * 80)
        
        # Get all deals with items
        result = await db.execute(text("""
            SELECT 
                d.id, 
                d.title, 
                d.total_price as old_total_price, 
                d.total_cost as old_total_cost,
                COALESCE(SUM(di.total_price), 0) as items_total_price,
                COALESCE(SUM(di.total_cost), 0) as items_total_cost
            FROM deals d
            LEFT JOIN deal_items di ON di.deal_id = d.id
            GROUP BY d.id
        """))
        
        deals = result.fetchall()
        
        print(f"\n📋 Found {len(deals)} deals to check")
        print("-" * 80)
        
        fixed_count = 0
        for deal in deals:
            deal_id, title, old_price, old_cost, items_price, items_cost = deal
            
            old_price = Decimal(str(old_price or 0))
            old_cost = Decimal(str(old_cost or 0))
            items_price = Decimal(str(items_price or 0))
            items_cost = Decimal(str(items_cost or 0))
            
            # Check if there's a mismatch
            if old_price != items_price or old_cost != items_cost:
                new_margin = items_price - items_cost
                
                print(f"\n🔄 Deal {deal_id}: {title}")
                print(f"   OLD: total_price={old_price:,.2f}, total_cost={old_cost:,.2f}, margin={(old_price - old_cost):,.2f}")
                print(f"   NEW: total_price={items_price:,.2f}, total_cost={items_cost:,.2f}, margin={new_margin:,.2f}")
                
                # Update the deal
                await db.execute(text("""
                    UPDATE deals 
                    SET total_price = :price, total_cost = :cost, margin = :margin
                    WHERE id = :deal_id
                """), {
                    "price": float(items_price),
                    "cost": float(items_cost),
                    "margin": float(new_margin),
                    "deal_id": deal_id
                })
                
                fixed_count += 1
                print(f"   ✅ FIXED!")
            else:
                print(f"✓ Deal {deal_id}: {title} - OK (already correct)")
        
        await db.commit()
        
        print("\n" + "=" * 80)
        print(f"🏁 DONE! Fixed {fixed_count} deals.")
        print("=" * 80)
        
        # Verify the fix
        print("\n📊 Verification - Deal status after fix:")
        result = await db.execute(text("""
            SELECT id, title, total_price, total_cost, margin, status 
            FROM deals 
            WHERE status = 'final_account'
        """))
        
        for row in result.fetchall():
            deal_id, title, price, cost, margin, status = row
            print(f"   Deal {deal_id}: price={price:,.2f}, cost={cost:,.2f}, margin={margin:,.2f}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_deal_totals())

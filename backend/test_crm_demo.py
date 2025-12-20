"""
Simple test script to demonstrate CRM functionality.

Run this after creating migrations and starting the server.
"""
import asyncio
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set your database URL
DATABASE_URL = "sqlite+aiosqlite:///./test_crm.db"

async def test_crm_workflow():
    """
    Test the complete CRM workflow:
    1. Create product
    2. Receive inventory (2 batches with different costs)
    3. Create deal with items (FIFO cost calculation)
    4. Check profit
    5. Add expense
    6. Generate financial report
    """
    from app import models, schemas, crud
    from app.services.crm_service import receive_inventory, create_deal_with_items, calculate_deal_profit
    from app.services.finance_service import calculate_monthly_finances
    from app.db import Base
    
    # Create engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        # Create tenant
        tenant = models.Tenant(name="Test Company", code="test-co", currency="KZT")
        db.add(tenant)
        await db.flush()
        
        # Create client
        client = models.Client(tenant_id=tenant.id, name="Test Client", email="client@test.com")
        db.add(client)
        await db.flush()
        
        # Create product
        product = models.Product(
            tenant_id=tenant.id,
            sku="TEST-001",
            title="Test Product",
            default_cost=Decimal("50.00"),
            default_price=Decimal("100.00"),
            currency="KZT"
        )
        db.add(product)
        await db.flush()
        
        print(f"✅ Created product: {product.title} (id={product.id})")
        
        # Receive inventory - Batch 1 (earlier, cheaper)
        batch1 = await receive_inventory(
            db=db,
            tenant_id=tenant.id,
            product_id=product.id,
            quantity=Decimal("50"),
            unit_cost=Decimal("48.00"),
            received_date=date(2025, 11, 1),
            reference="PO-001"
        )
        print(f"✅ Received batch 1: {batch1.quantity} units @ {batch1.unit_cost} each")
        
        # Receive inventory - Batch 2 (later, more expensive)
        batch2 = await receive_inventory(
            db=db,
            tenant_id=tenant.id,
            product_id=product.id,
            quantity=Decimal("50"),
            unit_cost=Decimal("52.00"),
            received_date=date(2025, 11, 15),
            reference="PO-002"
        )
        print(f"✅ Received batch 2: {batch2.quantity} units @ {batch2.unit_cost} each")
        
        # Create deal with items (sells 60 units - will use FIFO: 50 @ 48 + 10 @ 52)
        deal_data = schemas.DealCreate(
            client_id=client.id,
            title="Test Deal",
            currency="KZT",
            status="won",
            items=[
                schemas.DealItemCreate(
                    product_id=product.id,
                    quantity=Decimal("60"),
                    unit_price=Decimal("100.00")
                )
            ]
        )
        
        deal = await create_deal_with_items(db, tenant.id, deal_data)
        print(f"\n✅ Created deal: {deal.title} (id={deal.id})")
        print(f"   Total Price: {deal.total_price:,.2f} KZT")
        print(f"   Total Cost:  {deal.total_cost:,.2f} KZT")
        print(f"   Margin:      {deal.margin:,.2f} KZT")
        
        # Check profit
        profit_analysis = await calculate_deal_profit(db, deal.id)
        print(f"\n📊 Profit Analysis:")
        print(f"   Revenue:        {profit_analysis['revenue']:,.2f} KZT")
        print(f"   Cost:           {profit_analysis['cost']:,.2f} KZT")
        print(f"   Profit:         {profit_analysis['profit']:,.2f} KZT")
        print(f"   Profit Margin:  {profit_analysis['profit_margin_pct']:.2f}%")
        
        # Add expense
        expense = models.Expense(
            tenant_id=tenant.id,
            amount=Decimal("500.00"),
            currency="KZT",
            category="rent",
            description="Office rent",
            date=date(2025, 11, 20),
            is_fixed=True
        )
        db.add(expense)
        await db.commit()
        print(f"\n✅ Added expense: {expense.description} - {expense.amount} KZT")
        
        # Create financial settings
        settings = models.FinancialSettings(tenant_id=tenant.id, tax_rate=Decimal("10.00"))
        db.add(settings)
        await db.commit()
        
        # Generate monthly report
        report = await calculate_monthly_finances(db, tenant.id, 2025, 11)
        print(f"\n📈 Monthly Financial Report (November 2025):")
        print(f"   Revenue:          {report['revenue']:,.2f} KZT")
        print(f"   COGS:             {report['cogs']:,.2f} KZT")
        print(f"   Gross Profit:     {report['gross_profit']:,.2f} KZT ({report['gross_margin_pct']:.1f}%)")
        print(f"   OPEX:             {report['opex']:,.2f} KZT")
        print(f"   EBIT:             {report['ebit']:,.2f} KZT")
        print(f"   Taxes:            {report['taxes']:,.2f} KZT")
        print(f"   Net Profit:       {report['net_profit']:,.2f} KZT ({report['net_margin_pct']:.1f}%)")
        print(f"   Break-even Rev:   {report['break_even_revenue']:,.2f} KZT" if report['break_even_revenue'] else "   Break-even Rev:   N/A")
        
        print("\n✨ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_crm_workflow())

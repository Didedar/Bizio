# tests/test_finance.py
"""
Unit tests for finance module
"""
import pytest
from decimal import Decimal
from app.finance import calculate_financials


@pytest.mark.asyncio
async def test_calculate_financials_zero_revenue(db_session):
    """Test finance calculation with zero revenue"""
    result = await calculate_financials(
        db_session,
        tenant_id=999,  # non-existent tenant
        revenue_override=Decimal("0.00"),
        cogs_override=Decimal("0.00"),
        opex=Decimal("10000.00"),
        fixed_costs=Decimal("5000.00"),
        taxes_percent=Decimal("10.00")
    )
    
    assert result["revenue"] == Decimal("0.00")
    assert result["cogs"] == Decimal("0.00")
    assert result["gross_profit"] == Decimal("0.00")
    assert result["gross_margin_pct"] == Decimal("0.00")
    assert result["net_profit"] < 0  # Loss due to expenses


@pytest.mark.asyncio
async def test_calculate_financials_with_profit(db_session):
    """Test finance calculation with positive revenue"""
    result = await calculate_financials(
        db_session,
        tenant_id=999,
        revenue_override=Decimal("1000000.00"),
        cogs_override=Decimal("600000.00"),
        opex=Decimal("150000.00"),
        fixed_costs=Decimal("50000.00"),
        variable_costs=Decimal("600000.00"),
        taxes_percent=Decimal("10.00")
    )
    
    assert result["revenue"] == Decimal("1000000.00")
    assert result["cogs"] == Decimal("600000.00")
    assert result["gross_profit"] == Decimal("400000.00")
    assert result["gross_margin_pct"] == Decimal("40.00")
    
    # EBIT = Gross Profit - OPEX = 400000 - 150000 = 250000
    assert result["ebit"] == Decimal("250000.00")
    
    # Taxes = 10% of EBIT = 25000
    assert result["taxes"] == Decimal("25000.00")
    
    # Net Profit = Revenue - (COGS + OPEX + Fixed) - Taxes
    # = 1000000 - (600000 + 150000 + 50000) - 25000 = 175000
    assert result["net_profit"] == Decimal("175000.00")


@pytest.mark.asyncio
async def test_break_even_calculation(db_session):
    """Test break-even point calculation"""
    result = await calculate_financials(
        db_session,
        tenant_id=999,
        revenue_override=Decimal("500000.00"),
        cogs_override=Decimal("300000.00"),
        opex=Decimal("50000.00"),
        fixed_costs=Decimal("100000.00"),
        variable_costs=Decimal("300000.00"),
        taxes_percent=Decimal("0.00")
    )
    
    # Break-even revenue = fixed_costs / contribution_margin_ratio
    # Contribution margin = Revenue - Variable costs = 500000 - 300000 = 200000
    # Contribution margin ratio = 200000 / 500000 = 0.4
    # Break-even = 100000 / 0.4 = 250000
    assert result["break_even_revenue"] == Decimal("250000.00")


@pytest.mark.asyncio
async def test_negative_ebit_no_taxes(db_session):
    """Test that taxes are zero when EBIT is negative"""
    result = await calculate_financials(
        db_session,
        tenant_id=999,
        revenue_override=Decimal("100000.00"),
        cogs_override=Decimal("80000.00"),
        opex=Decimal("50000.00"),
        fixed_costs=Decimal("10000.00"),
        taxes_percent=Decimal("10.00")
    )
    
    # Gross profit = 100000 - 80000 = 20000
    # EBIT = 20000 - 50000 = -30000 (negative)
    assert result["ebit"] < 0
    # No taxes on negative EBIT
    assert result["taxes"] == Decimal("0.00")


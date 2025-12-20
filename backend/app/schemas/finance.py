from datetime import datetime, date as date_type
from decimal import Decimal
from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class ExpenseBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Expense amount (2 decimal places)")
    currency: str = "KZT"
    category: str = Field(..., description="Expense category: rent, salaries, marketing, utilities, etc.")
    description: Optional[str] = None
    date: date_type
    days_until_payment: Optional[int] = Field(None, description="Number of days until payment is due")
    is_fixed: bool = Field(False, description="True for fixed costs (rent, salaries), False for variable")

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, description="Expense amount (2 decimal places)")
    currency: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Union[date_type, None] = None
    days_until_payment: Optional[int] = None
    is_fixed: Optional[bool] = None

class ExpenseRead(ExpenseBase):
    id: int
    tenant_id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FinancialSettingsBase(BaseModel):
    tax_rate: Decimal = Field(Decimal("0.00"), ge=0, le=100, description="Tax rate as percentage (2 decimal places)")
    currency: str = "KZT"
    fiscal_year_start_month: int = Field(1, ge=1, le=12, description="Month when fiscal year starts (1=January)")


class FinancialSettingsCreate(BaseModel):
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Tax rate as percentage (2 decimal places)")
    currency: Optional[str] = None


class FinancialSettingsRead(FinancialSettingsBase):
    id: int
    tenant_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FinanceDashboard(BaseModel):
    revenue: Decimal = Field(..., description="Total revenue from deals (2 decimal places)")
    cogs: Decimal = Field(..., description="Cost of Goods Sold (2 decimal places)")
    gross_profit: Decimal = Field(..., description="Revenue - COGS (2 decimal places)")
    gross_margin_pct: Decimal = Field(..., description="Gross profit margin percentage (2 decimal places)")
    
    opex: Decimal = Field(..., description="Operating expenses (OPEX) (2 decimal places)")
    
    ebit: Decimal = Field(..., description="Earnings Before Interest and Taxes (2 decimal places)")
    taxes_percent: Decimal = Field(..., description="Tax rate applied (2 decimal places)")
    taxes: Decimal = Field(..., description="Tax amount (2 decimal places)")
    
    total_expenses: Decimal = Field(..., description="Total expenses (COGS + OPEX + Fixed) (2 decimal places)")
    net_profit: Decimal = Field(..., description="Net profit after all expenses and taxes (2 decimal places)")
    net_margin_pct: Decimal = Field(..., description="Net profit margin percentage (2 decimal places)")
    
    fixed_costs: Decimal = Field(..., description="Fixed costs (2 decimal places)")
    variable_costs: Decimal = Field(..., description="Variable costs (2 decimal places)")

    break_even_revenue: Optional[Decimal] = Field(None, description="Revenue needed to break even (2 decimal places)")
    
    model_config = ConfigDict(from_attributes=True)

class MonthlyFinanceRequest(BaseModel):
    tenant_id: int
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
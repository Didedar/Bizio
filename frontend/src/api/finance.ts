import client from './client';
import { Expense, ExpenseCreate, FinanceDashboardMetrics } from '../types';

export const getExpenses = async (tenantId: number, params?: { start?: string; end?: string; category?: string }) => {
    const response = await client.get<Expense[]>('/finance/expenses', {
        params: { tenant_id: tenantId, ...params },
    });
    return response.data;
};

export const createExpense = async (tenantId: number, expense: ExpenseCreate) => {
    const response = await client.post<Expense>('/finance/expenses', expense, {
        params: { tenant_id: tenantId },
    });
    return response.data;
};

export const deleteExpense = async (tenantId: number, expenseId: number) => {
    await client.delete(`/finance/expenses/${expenseId}`, {
        params: { tenant_id: tenantId },
    });
};

export const updateExpense = async (tenantId: number, expenseId: number, expense: Partial<ExpenseCreate>) => {
    const response = await client.put<Expense>(`/finance/expenses/${expenseId}`, expense, {
        params: { tenant_id: tenantId },
    });
    return response.data;
};

export const getFinanceDashboard = async (
    tenantId: number,
    params?: {
        start?: string;
        end?: string;
        opex?: number;
        fixed?: number;
        variable?: number;
        tax_percent?: number;
    }
) => {
    const response = await client.get<any>('/finance/dashboard', {
        params: { tenant_id: tenantId, ...params },
    });

    // Convert string decimals to numbers for frontend
    const data = response.data;
    const metrics: FinanceDashboardMetrics = {
        revenue: parseFloat(data.revenue),
        cogs: parseFloat(data.cogs),
        gross_profit: parseFloat(data.gross_profit),
        gross_margin_pct: parseFloat(data.gross_margin_pct),
        opex: parseFloat(data.opex),
        ebit: parseFloat(data.ebit),
        taxes: parseFloat(data.taxes),
        net_profit: parseFloat(data.net_profit),
        net_margin_pct: parseFloat(data.net_margin_pct),
        fixed_costs: parseFloat(data.fixed_costs),
        variable_costs: data.variable_costs ? parseFloat(data.variable_costs) : undefined,
        break_even_revenue: data.break_even_revenue ? parseFloat(data.break_even_revenue) : undefined,
    };

    return metrics;
};

export const getFinancialSettings = async (tenantId: number) => {
    const response = await client.get<any>('/finance/settings', {
        params: { tenant_id: tenantId },
    });
    return {
        ...response.data,
        tax_rate: parseFloat(response.data.tax_rate),
    };
};

export const updateFinancialSettings = async (tenantId: number, settings: { tax_rate?: number; currency?: string }) => {
    const response = await client.put<any>('/finance/settings', settings, {
        params: { tenant_id: tenantId },
    });
    return {
        ...response.data,
        tax_rate: parseFloat(response.data.tax_rate),
    };
};

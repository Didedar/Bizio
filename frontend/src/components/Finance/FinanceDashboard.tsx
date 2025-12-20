import React, { useEffect, useState } from 'react';
import { FinanceDashboardMetrics, Expense } from '../../types';
import { getFinanceDashboard, getExpenses, createExpense, deleteExpense, updateExpense } from '../../api/finance';
import ExpenseForm from './ExpenseForm';
import FinancialSettingsModal from './FinancialSettingsModal';

interface FinanceDashboardProps {
  tenantId: number;
}

const FinanceDashboard: React.FC<FinanceDashboardProps> = ({ tenantId }) => {
  const [metrics, setMetrics] = useState<FinanceDashboardMetrics | null>(null);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [deleteExpenseId, setDeleteExpenseId] = useState<number | null>(null);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);

  // Date filter state
  const [startDate, setStartDate] = useState<string>(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );

  const fetchData = async () => {
    setLoading(true);
    try {
      // Create proper datetime strings with time components
      // Start of day for start date, end of day for end date
      const startDateTime = `${startDate}T00:00:00`;
      const endDateTime = `${endDate}T23:59:59`;

      const [metricsData, expensesData] = await Promise.all([
        getFinanceDashboard(tenantId, { start: startDateTime, end: endDateTime }),
        getExpenses(tenantId, { start: startDateTime, end: endDateTime })
      ]);
      setMetrics(metricsData);
      setExpenses(expensesData);
    } catch (error) {
      console.error("Failed to fetch finance data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tenantId) {
      fetchData();
    }
  }, [tenantId, startDate, endDate]);

  const handleCreateExpense = async (expenseData: any) => {
    try {
      await createExpense(tenantId, expenseData);
      setShowExpenseModal(false);
      await fetchData(); // Refresh data
    } catch (error) {
      console.error("Failed to create expense", error);
    }
  };

  const handleUpdateExpense = async (expenseData: any) => {
    if (!editingExpense) return;
    try {
      await updateExpense(tenantId, editingExpense.id, expenseData);
      setEditingExpense(null);
      await fetchData();
    } catch (error) {
      console.error("Failed to update expense", error);
    }
  };

  const handleDeleteExpense = async () => {
    if (deleteExpenseId === null) return;

    try {
      await deleteExpense(tenantId, deleteExpenseId);
      setDeleteExpenseId(null);
      await fetchData();
    } catch (error) {
      console.error("Failed to delete expense", error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'KZT' }).format(amount);
  };

  const formatPercent = (percent: number) => {
    return `${percent.toFixed(2)}%`;
  };

  if (loading && !metrics) {
    return <div className="loading">Loading financial data...</div>;
  }

  // Empty State Check
  const isEmptyState = expenses.length === 0 && metrics?.revenue === 0 && metrics?.cogs === 0;

  return (
    <div className="finance-dashboard">
      <div className="dashboard-header">
        <div className="date-filters">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="date-input"
          />
          <span className="separator">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="date-input"
          />
          <button onClick={fetchData} className="btn-refresh">Refresh</button>
        </div>
        <div className="header-actions">
          <button onClick={() => setShowSettingsModal(true)} className="btn-settings">
            Settings
          </button>
          <button onClick={() => setShowExpenseModal(true)} className="btn-add-expense">
            + Add Expense
          </button>
        </div>
      </div>

      {isEmptyState ? (
        <div className="empty-state">
          <div className="empty-state-content">
            <h2>Welcome to Financial Analytics</h2>
            <p>It looks like you don't have any financial data yet.</p>
            <p>Start by adding your expenses (Rent, Salaries, etc.) or configuring your settings.</p>
            <div className="empty-state-actions">
              <button onClick={() => setShowExpenseModal(true)} className="btn-primary-large">
                Add Your First Expense
              </button>
              <button onClick={() => setShowSettingsModal(true)} className="btn-secondary-large">
                Configure Settings
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          {metrics && (
            <div className="metrics-grid">
              <div className="metric-card">
                <h3>Revenue</h3>
                <div className="metric-value">{formatCurrency(metrics.revenue)}</div>
              </div>
              <div className="metric-card">
                <h3>COGS</h3>
                <div className="metric-value">{formatCurrency(metrics.cogs)}</div>
              </div>
              <div className="metric-card">
                <h3>Gross Profit</h3>
                <div className="metric-value">{formatCurrency(metrics.gross_profit)}</div>
                <div className="metric-sub">{formatPercent(metrics.gross_margin_pct)} Margin</div>
              </div>
              <div className="metric-card">
                <h3>OPEX</h3>
                <div className="metric-value">{formatCurrency(metrics.opex)}</div>
              </div>
              <div className="metric-card highlight">
                <h3>Net Profit</h3>
                <div className="metric-value">{formatCurrency(metrics.net_profit)}</div>
                <div className="metric-sub">{formatPercent(metrics.net_margin_pct)} Margin</div>
              </div>
              <div className="metric-card">
                <h3>Break-even Revenue</h3>
                <div className="metric-value">
                  {metrics.break_even_revenue ? formatCurrency(metrics.break_even_revenue) : 'N/A'}
                </div>
              </div>
            </div>
          )}

          <div className="expenses-section">
            <h3>Recent Expenses</h3>
            <div className="expenses-table-container">
              <table className="expenses-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Type</th>
                    <th>Days Until Payment</th>
                    <th>Amount</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.length === 0 ? (
                    <tr><td colSpan={7} className="text-center">No expenses found for this period</td></tr>
                  ) : (
                    expenses.map(exp => (
                      <tr key={exp.id}>
                        <td>{new Date(exp.date).toLocaleDateString()}</td>
                        <td>{exp.category}</td>
                        <td>{exp.description}</td>
                        <td>{exp.is_fixed ? <span className="badge fixed">Fixed</span> : <span className="badge variable">Variable</span>}</td>
                        <td>{exp.days_until_payment ? `${exp.days_until_payment} days` : '-'}</td>
                        <td className="amount-col">{formatCurrency(exp.amount)}</td>
                        <td>
                          <button onClick={() => setEditingExpense(exp)} className="btn-edit">Edit</button>
                          <button onClick={() => setDeleteExpenseId(exp.id)} className="btn-delete">Delete</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {showExpenseModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Add New Expense</h2>
            <ExpenseForm onSubmit={handleCreateExpense} onCancel={() => setShowExpenseModal(false)} />
          </div>
        </div>
      )}

      {showSettingsModal && (
        <FinancialSettingsModal
          tenantId={tenantId}
          onClose={() => setShowSettingsModal(false)}
          onSave={fetchData}
        />
      )}

      {deleteExpenseId !== null && (
        <div className="modal-overlay">
          <div className="modal-content delete-modal">
            <h2>Confirm Deletion</h2>
            <p>Are you sure you want to delete this expense? This action cannot be undone.</p>
            <div className="modal-actions">
              <button onClick={() => setDeleteExpenseId(null)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleDeleteExpense} className="btn-danger">
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {editingExpense && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Edit Expense</h2>
            <ExpenseForm
              onSubmit={handleUpdateExpense}
              onCancel={() => setEditingExpense(null)}
              initialData={{
                category: editingExpense.category,
                amount: editingExpense.amount,
                currency: editingExpense.currency,
                date: editingExpense.date.split('T')[0],
                description: editingExpense.description || '',
                days_until_payment: editingExpense.days_until_payment,
                is_fixed: editingExpense.is_fixed,
              }}
            />
          </div>
        </div>
      )}

      <style>{`
        .finance-dashboard {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 16px;
        }
        .date-filters {
          display: flex;
          align-items: center;
          gap: 12px;
          background: white;
          padding: 8px 16px;
          border-radius: 8px;
          border: 1px solid #e5e7eb;
        }
        .header-actions {
          display: flex;
          gap: 12px;
        }
        .date-input {
          border: 1px solid #d1d5db;
          border-radius: 4px;
          padding: 4px 8px;
        }
        .btn-refresh {
          background: none;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          padding: 4px 12px;
          cursor: pointer;
        }
        .btn-settings {
          background: white;
          border: 1px solid #d1d5db;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          color: #374151;
        }
        .btn-add-expense {
          background-color: #3b82f6;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
        }
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
        }
        .metric-card {
          background: white;
          padding: 20px;
          border-radius: 12px;
          border: 1px solid #e5e7eb;
          box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .metric-card h3 {
          font-size: 14px;
          color: #6b7280;
          margin: 0 0 8px 0;
        }
        .metric-value {
          font-size: 24px;
          font-weight: 700;
          color: #111827;
        }
        .metric-sub {
          font-size: 12px;
          color: #10b981;
          margin-top: 4px;
        }
        .metric-card.highlight {
          background: #eff6ff;
          border-color: #bfdbfe;
        }
        .metric-card.highlight .metric-value {
          color: #1d4ed8;
        }
        
        .expenses-section {
          background: white;
          border-radius: 12px;
          border: 1px solid #e5e7eb;
          padding: 20px;
        }
        .expenses-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 16px;
        }
        .expenses-table th, .expenses-table td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid #f3f4f6;
        }
        .expenses-table th {
          font-weight: 600;
          color: #6b7280;
          font-size: 14px;
        }
        .amount-col {
          font-family: monospace;
          font-weight: 600;
        }
        .badge {
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }
        .badge.fixed {
          background-color: #e0e7ff;
          color: #4338ca;
        }
        .badge.variable {
          background-color: #fef3c7;
          color: #d97706;
        }
        .btn-delete {
          color: #ef4444;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 14px;
        }
        .btn-delete:hover {
          text-decoration: underline;
        }
        .btn-edit {
          color: #3b82f6;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 14px;
          margin-right: 12px;
        }
        .btn-edit:hover {
          text-decoration: underline;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }
        .modal-content {
          background: white;
          padding: 24px;
          border-radius: 12px;
          width: 100%;
          max-width: 500px;
        }
        .modal-content h2 {
          margin-top: 0;
        }
        .delete-modal {
          max-width: 400px;
        }
        .delete-modal p {
          color: #6b7280;
          margin: 16px 0 24px 0;
          line-height: 1.5;
        }
        .modal-actions {
          display: flex;
          gap: 12px;
          justify-content: flex-end;
        }
        .btn-danger {
          background-color: #ef4444;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
        }
        .btn-danger:hover {
          background-color: #dc2626;
        }
        .btn-secondary {
          background-color: white;
          color: #374151;
          border: 1px solid #d1d5db;
          padding: 8px 16px;
          border-radius: 6px;
          font-weight: 500;
          cursor: pointer;
        }
        .btn-secondary:hover {
          background-color: #f9fafb;
        }
        
        .empty-state {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 400px;
          background: white;
          border-radius: 12px;
          border: 1px dashed #d1d5db;
        }
        .empty-state-content {
          text-align: center;
          max-width: 400px;
        }
        .empty-state-content h2 {
          color: #111827;
          margin-bottom: 12px;
        }
        .empty-state-content p {
          color: #6b7280;
          margin-bottom: 24px;
        }
        .empty-state-actions {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        .btn-primary-large {
          background-color: #3b82f6;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 600;
          font-size: 16px;
          cursor: pointer;
          width: 100%;
        }
        .btn-secondary-large {
          background-color: white;
          color: #374151;
          border: 1px solid #d1d5db;
          padding: 12px 24px;
          border-radius: 8px;
          font-weight: 600;
          font-size: 16px;
          cursor: pointer;
          width: 100%;
        }
      `}</style>
    </div>
  );
};

export default FinanceDashboard;

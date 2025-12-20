import React, { useState, useEffect } from 'react';
import { ExpenseCreate } from '../../types';

interface ExpenseFormProps {
  onSubmit: (expense: ExpenseCreate) => Promise<void>;
  onCancel: () => void;
  initialData?: Partial<ExpenseCreate & { amount: number }>;
}

const ExpenseForm: React.FC<ExpenseFormProps> = ({ onSubmit, onCancel, initialData }) => {
  const [category, setCategory] = useState(initialData?.category || '');
  const [amount, setAmount] = useState(initialData?.amount?.toString() || '');
  const [date, setDate] = useState(initialData?.date || new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState(initialData?.description || '');
  const [daysUntilPayment, setDaysUntilPayment] = useState(initialData?.days_until_payment?.toString() || '');
  const [isFixed, setIsFixed] = useState(initialData?.is_fixed || false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialData) {
      setCategory(initialData.category || '');
      setAmount(initialData.amount?.toString() || '');
      setDate(initialData.date || new Date().toISOString().split('T')[0]);
      setDescription(initialData.description || '');
      setDaysUntilPayment(initialData.days_until_payment?.toString() || '');
      setIsFixed(initialData.is_fixed || false);
    }
  }, [initialData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const expenseData: any = {
        category,
        amount: parseFloat(amount),
        date: date,
        is_fixed: isFixed,
      };

      // Only include optional fields if they have values
      if (description && description.trim()) {
        expenseData.description = description;
      }
      if (daysUntilPayment) {
        expenseData.days_until_payment = parseInt(daysUntilPayment);
      }

      await onSubmit(expenseData);
      // Reset form or close modal
      if (!initialData) {
        setCategory('');
        setAmount('');
        setDescription('');
        setDaysUntilPayment('');
        setIsFixed(false);
      }
    } catch (error) {
      console.error("Failed to submit expense", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="expense-form">
      <div className="form-group">
        <label>Category</label>
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          required
          placeholder="e.g. Rent, Salary"
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label>Amount</label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
          min="0"
          step="0.01"
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label>Date</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
          className="form-input"
        />
      </div>

      <div className="form-group">
        <label>Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="form-textarea"
        />
      </div>

      <div className="form-group">
        <label>Days Until Payment (optional)</label>
        <input
          type="number"
          value={daysUntilPayment}
          onChange={(e) => setDaysUntilPayment(e.target.value)}
          min="0"
          step="1"
          placeholder="e.g. 30"
          className="form-input"
        />
      </div>

      <div className="form-group checkbox-group">
        <label>
          <input
            type="checkbox"
            checked={isFixed}
            onChange={(e) => setIsFixed(e.target.checked)}
          />
          Fixed Cost (e.g. Rent)
        </label>
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-secondary" disabled={loading}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Saving...' : initialData ? 'Save Changes' : 'Add Expense'}
        </button>
      </div>

      <style>{`
        .expense-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .form-group label {
          font-size: 14px;
          font-weight: 500;
          color: #374151;
        }
        .form-input, .form-textarea {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
        }
        .form-textarea {
          min-height: 80px;
          resize: vertical;
        }
        .checkbox-group label {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }
        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 8px;
        }
        .btn-primary {
          background-color: #3b82f6;
          color: white;
          padding: 8px 16px;
          border-radius: 6px;
          border: none;
          font-weight: 500;
          cursor: pointer;
        }
        .btn-primary:disabled {
          background-color: #93c5fd;
        }
        .btn-secondary {
          background-color: white;
          color: #374151;
          padding: 8px 16px;
          border-radius: 6px;
          border: 1px solid #d1d5db;
          font-weight: 500;
          cursor: pointer;
        }
      `}</style>
    </form>
  );
};

export default ExpenseForm;

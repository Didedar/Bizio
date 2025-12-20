import React, { useState, useEffect } from 'react';
import { getFinancialSettings, updateFinancialSettings } from '../../api/finance';

interface FinancialSettingsModalProps {
    tenantId: number;
    onClose: () => void;
    onSave: () => void;
}

const FinancialSettingsModal: React.FC<FinancialSettingsModalProps> = ({ tenantId, onClose, onSave }) => {
    const [taxRate, setTaxRate] = useState<string>('0');
    const [currency, setCurrency] = useState<string>('KZT');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const settings = await getFinancialSettings(tenantId);
                setTaxRate(settings.tax_rate.toString());
                setCurrency(settings.currency);
            } catch (error) {
                console.error("Failed to fetch settings", error);
            }
        };
        fetchSettings();
    }, [tenantId]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await updateFinancialSettings(tenantId, {
                tax_rate: parseFloat(taxRate),
                currency,
            });
            onSave();
            onClose();
        } catch (error) {
            console.error("Failed to save settings", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2>Financial Settings</h2>
                <form onSubmit={handleSubmit} className="settings-form">
                    <div className="form-group">
                        <label>Tax Rate (%)</label>
                        <input
                            type="number"
                            value={taxRate}
                            onChange={(e) => setTaxRate(e.target.value)}
                            min="0"
                            max="100"
                            step="0.01"
                            className="form-input"
                        />
                        <small>This tax rate will be applied to your EBIT to calculate Net Profit.</small>
                    </div>

                    <div className="form-group">
                        <label>Currency</label>
                        <select
                            value={currency}
                            onChange={(e) => setCurrency(e.target.value)}
                            className="form-input"
                        >
                            <option value="KZT">KZT (Kazakhstani Tenge)</option>
                            <option value="USD">USD (US Dollar)</option>
                            <option value="EUR">EUR (Euro)</option>
                            <option value="RUB">RUB (Russian Ruble)</option>
                            <option value="CNY">CNY (Chinese Yuan)</option>
                        </select>
                    </div>

                    <div className="form-actions">
                        <button type="button" onClick={onClose} className="btn-secondary" disabled={loading}>Cancel</button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? 'Saving...' : 'Save Settings'}
                        </button>
                    </div>
                </form>
            </div>
            <style>{`
        .settings-form {
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
        .form-group small {
          font-size: 12px;
          color: #6b7280;
        }
        .form-input {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
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
        </div>
    );
};

export default FinancialSettingsModal;

import React from 'react';
import FinanceDashboard from '../components/Finance/FinanceDashboard';
import { useAuth } from '../contexts/AuthContext';

const FinancePage: React.FC = () => {
    const { user } = useAuth();

    if (!user || !user.tenants || user.tenants.length === 0) {
        return <div>No tenant found for this user.</div>;
    }

    // Use the first tenant for now. In a multi-tenant app, this would be selected from a context or dropdown.
    const tenantId = user.tenants[0].id;

    return (
        <div className="finance-page">
            <div className="page-header">
                <h1>Finance & Analytics</h1>
            </div>
            <FinanceDashboard tenantId={tenantId} />

            <style>{`
        .finance-page {
          padding: 24px;
          background-color: #f9fafb;
          min-height: 100vh;
        }
        .page-header {
          margin-bottom: 24px;
        }
        .page-header h1 {
          font-size: 24px;
          font-weight: 600;
          color: #111827;
          margin: 0;
        }
      `}</style>
        </div>
    );
};

export default FinancePage;

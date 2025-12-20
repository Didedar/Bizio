import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css';

interface HeaderProps {
  isSidebarCollapsed?: boolean;
}

const Header: React.FC<HeaderProps> = ({ isSidebarCollapsed = false }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isCrmPage = location.pathname.startsWith('/crm');

  const crmTabs = [
    { id: 'deals', label: 'Deals', path: '/crm/deals' },
    { id: 'contacts', label: 'Contacts', path: '/crm/contacts' },
    { id: 'accounts', label: 'Accounts', path: '/crm/accounts' },
    { id: 'products', label: 'Products', path: '/crm/products' },
    { id: 'inventory', label: 'Inventory', path: '/crm/inventory' },
  ];

  const handleTabClick = (tab: typeof crmTabs[0]) => {
    if (tab.path) {
      navigate(tab.path);
    }
  };

  // Don't show tabs if not on CRM page
  if (!isCrmPage) {
    return (
      <div className={`app-header ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <div className="header-left"></div>
      </div>
    );
  }

  return (
    <div className={`app-header ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="header-left">
        <nav className="header-nav">
          {crmTabs.map((tab) => {
            const isActive = location.pathname === tab.path;
            return (
              <button
                key={tab.id}
                className={`header-tab ${isActive ? 'active' : ''}`}
                onClick={() => handleTabClick(tab)}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

export default Header;


import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css';

interface HeaderProps {
  isSidebarCollapsed?: boolean;
  onMenuClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ isSidebarCollapsed = false, onMenuClick }) => {
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

  const MenuButton = () => (
    <button className="mobile-menu-btn" onClick={onMenuClick} aria-label="Open menu">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M3 6H21M3 12H21M3 18H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    </button>
  );

  // Don't show tabs if not on CRM page
  if (!isCrmPage) {
    return (
      <div className={`app-header ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <MenuButton />
        <div className="header-left"></div>
      </div>
    );
  }

  return (
    <div className={`app-header ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <MenuButton />
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

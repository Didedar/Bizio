import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Sidebar.css';

interface SidebarProps {
  currentSection?: string;
  onSectionChange?: (section: string) => void;
  onCollapseChange?: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentSection, onSectionChange, onCollapseChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [crmExpanded, setCrmExpanded] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Auto-expand CRM menu when on CRM pages
  useEffect(() => {
    if (location.pathname.startsWith('/crm')) {
      setCrmExpanded(true);
      onSectionChange?.('crm');
    }
  }, [location.pathname, onSectionChange]);

  const handleToggle = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    onCollapseChange?.(newState);
  };

  const getInitials = () => {
    if (!user?.full_name) {
      return user?.email?.charAt(0).toUpperCase() || 'U';
    }
    const parts = user.full_name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
    }
    return user.full_name.charAt(0).toUpperCase();
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  const handleCrmClick = () => {
    if (isCollapsed) {
      navigate('/crm/deals');
      onSectionChange?.('crm');
    } else {
      setCrmExpanded(!crmExpanded);
      if (!crmExpanded) {
        navigate('/crm/deals');
        onSectionChange?.('crm');
      }
    }
  };

  const handleCrmSubItemClick = (path: string) => {
    navigate(path);
    onSectionChange?.('crm');
  };

  const crmSubItems = [
    { id: 'deals', label: 'Deals', path: '/crm/deals' },
    { id: 'contacts', label: 'Contacts', path: '/crm/contacts' },
    { id: 'accounts', label: 'Accounts', path: '/crm/accounts' },
    { id: 'products', label: 'Products', path: '/crm/products' },
    { id: 'inventory', label: 'Inventory', path: '/crm/inventory' },
  ];

  const menuItems = {
    overview: [
      { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
      { id: 'crm', label: 'CRM', icon: 'briefcase' },
      { id: 'finance', label: 'Finance', icon: 'chart' },
      { id: 'automatization', label: 'Automatization', icon: 'gear' },
      { id: 'ai-agent', label: 'AI Agent', icon: 'robot' },
      { id: 'monitoring', label: 'Monitoring', icon: 'bar-chart' },
    ],
    tools: [
      { id: 'notification', label: 'Notification', icon: 'bell' },
      { id: 'inbox', label: 'Inbox', icon: 'inbox' },
      { id: 'integration', label: 'Integration', icon: 'puzzle' },
      { id: 'reporting', label: 'Reporting', icon: 'document' },
    ],
    metrics: [
      { id: 'active', label: 'Active', icon: 'check' },
      { id: 'past', label: 'Past', icon: 'clock' },
    ],
  };

  const getIcon = (iconName: string) => {
    const icons: Record<string, JSX.Element> = {
      grid: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 3H9V9H3V3Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M11 3H17V9H11V3Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M3 11H9V17H3V11Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M11 11H17V17H11V11Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      briefcase: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 6H17C17.5523 6 18 6.44772 18 7V16C18 16.5523 17.5523 17 17 17H3C2.44772 17 2 16.5523 2 16V7C2 6.44772 2.44772 6 3 6Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M6 6V4C6 3.44772 6.44772 3 7 3H13C13.5523 3 14 3.44772 14 4V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M10 10V13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      chart: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 17L9 11L13 15L17 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M17 11V17H3V3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      gear: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 12C11.1046 12 12 11.1046 12 10C12 8.89543 11.1046 8 10 8C8.89543 8 8 8.89543 8 10C8 11.1046 8.89543 12 10 12Z" stroke="currentColor" strokeWidth="1.5" />
          <path d="M15.6569 12.3431L14.9497 14.9497L12.3431 15.6569C11.8434 15.8434 11.375 16.125 10.9645 16.4853L10 17.4497L9.03553 16.4853C8.625 16.125 8.15662 15.8434 7.65685 15.6569L5.05025 14.9497L4.34315 12.3431C4.15662 11.8434 3.875 11.375 3.51472 10.9645L2.55025 10L3.51472 9.03553C3.875 8.625 4.15662 8.15662 4.34315 7.65685L5.05025 5.05025L7.65685 4.34315C8.15662 4.15662 8.625 3.875 9.03553 3.51472L10 2.55025L10.9645 3.51472C11.375 3.875 11.8434 4.15662 12.3431 4.34315L14.9497 5.05025L15.6569 7.65685C15.8434 8.15662 16.125 8.625 16.4853 9.03553L17.4497 10L16.4853 10.9645C16.125 11.375 15.8434 11.8434 15.6569 12.3431Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      robot: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 2V4M4 6H2M18 6H16M4 10C4 12.2091 5.79086 14 8 14H12C14.2091 14 16 12.2091 16 10M4 10C4 7.79086 5.79086 6 8 6H12C14.2091 6 16 7.79086 16 10M4 10V16C4 17.1046 4.89543 18 6 18H8M16 10V16C16 17.1046 15.1046 18 14 18H12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="8" cy="10" r="1" fill="currentColor" />
          <circle cx="12" cy="10" r="1" fill="currentColor" />
        </svg>
      ),
      'bar-chart': (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 17H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <path d="M5 12V17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M9 8V17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M13 4V17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M17 10V17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      bell: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 2C8.34315 2 7 3.34315 7 5V8C7 9.65685 6.34315 11 5 12V14H15V12C13.6569 11 13 9.65685 13 8V5C13 3.34315 11.6569 2 10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M8 14V15C8 16.6569 9.34315 18 11 18C12.6569 18 14 16.6569 14 15V14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      inbox: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 4H17C17.5523 4 18 4.44772 18 5V15C18 15.5523 17.5523 16 17 16H3C2.44772 16 2 15.5523 2 15V5C2 4.44772 2.44772 4 3 4Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M2 5L10 10L18 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      puzzle: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M8 2H12C13.1046 2 14 2.89543 14 4V6H16C17.1046 6 18 6.89543 18 8V12C18 13.1046 17.1046 14 16 14H14V16C14 17.1046 13.1046 18 12 18H8C6.89543 18 6 17.1046 6 16V14H4C2.89543 14 2 13.1046 2 12V8C2 6.89543 2.89543 6 4 6H6V4C6 2.89543 6.89543 2 8 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      document: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M4 2H12L16 6V18C16 18.5523 15.5523 19 15 19H4C3.44772 19 3 18.5523 3 18V3C3 2.44772 3.44772 2 4 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 2V6H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      check: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" />
          <path d="M7 10L9 12L13 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      clock: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" />
          <path d="M10 6V10L13 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      question: (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" />
          <path d="M10 14V14.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M10 8C10 7.44772 10.4477 7 11 7C11.5523 7 12 7.44772 12 8C12 8.55228 11.5523 9 11 9H10V10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
    };
    return icons[iconName] || null;
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <button className="sidebar-toggle" onClick={handleToggle}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
        {!isCollapsed && <div className="sidebar-logo">Bizio</div>}
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <div className="nav-section-title">Overview</div>
          {menuItems.overview.map((item) => {
            if (item.id === 'crm') {
              return (
                <div key={item.id}>
                  <button
                    className={`nav-item ${currentSection === item.id ? 'active' : ''}`}
                    onClick={handleCrmClick}
                  >
                    <span className="nav-icon">{getIcon(item.icon)}</span>
                    {!isCollapsed && <span className="nav-label">{item.label}</span>}
                    {!isCollapsed && (
                      <span className={`nav-arrow ${crmExpanded ? 'expanded' : ''}`}>
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </span>
                    )}
                  </button>
                  {!isCollapsed && crmExpanded && (
                    <div className="nav-submenu">
                      {crmSubItems.map((subItem) => {
                        const isActive = location.pathname === subItem.path;
                        return (
                          <button
                            key={subItem.id}
                            className={`nav-subitem ${isActive ? 'active' : ''}`}
                            onClick={() => handleCrmSubItemClick(subItem.path)}
                          >
                            <span className="nav-label">{subItem.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            }
            return (
              <button
                key={item.id}
                className={`nav-item ${currentSection === item.id ? 'active' : ''}`}
                onClick={() => {
                  onSectionChange?.(item.id);
                  navigate(`/${item.id}`);
                }}
              >
                <span className="nav-icon">{getIcon(item.icon)}</span>
                {!isCollapsed && <span className="nav-label">{item.label}</span>}
              </button>
            );
          })}
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Tools</div>
          {menuItems.tools.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${currentSection === item.id ? 'active' : ''}`}
              onClick={() => {
                onSectionChange?.(item.id);
                navigate(`/${item.id}`);
              }}
            >
              <span className="nav-icon">{getIcon(item.icon)}</span>
              {!isCollapsed && <span className="nav-label">{item.label}</span>}
            </button>
          ))}
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Metrics</div>
          {menuItems.metrics.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${currentSection === item.id ? 'active' : ''}`}
              onClick={() => {
                onSectionChange?.(item.id);
                navigate(`/${item.id}`);
              }}
            >
              <span className="nav-icon">{getIcon(item.icon)}</span>
              {!isCollapsed && <span className="nav-label">{item.label}</span>}
            </button>
          ))}
        </div>
      </nav>

      <div className="sidebar-footer">
        <button className="nav-item">
          <span className="nav-icon">{getIcon('question')}</span>
          {!isCollapsed && <span className="nav-label">Help Center</span>}
        </button>
        <button className="nav-item">
          <span className="nav-icon">{getIcon('gear')}</span>
          {!isCollapsed && <span className="nav-label">Settings</span>}
        </button>
        {!isCollapsed && user && (
          <div className="sidebar-user" onClick={handleProfileClick}>
            <div className="user-avatar">
              <span>{getInitials()}</span>
            </div>
            <div className="user-info">
              <div className="user-name">{user.full_name || user.email}</div>
              <div className="user-plan">{user.tenants && user.tenants.length > 0 ? user.tenants[0].name : 'No tenant'}</div>
              <div className="user-email">{user.email}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;


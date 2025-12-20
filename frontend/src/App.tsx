import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DealsPage from './pages/DealsPage';
import ContactsPage from './pages/ContactsPage';
import AccountsPage from './pages/AccountsPage';
import ProductsPage from './pages/ProductsPage';
import InventoryPage from './pages/InventoryPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProfilePage from './pages/ProfilePage';
import FinancePage from './pages/FinancePage';
import DashboardPage from './pages/DashboardPage';
import ComingSoonPage from './pages/ComingSoonPage';
import { DealModalProvider } from './contexts/DealModalContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import './App.css';



interface ProtectedRouteProps {
  children: React.ReactElement;
}


interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <p className="loading-text">Loading...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function AppContent() {
  const [currentSection, setCurrentSection] = useState('crm');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const location = useLocation();


  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  // Determine current section from URL
  React.useEffect(() => {
    const path = location.pathname;
    if (path.startsWith('/crm')) {
      setCurrentSection('crm');
    } else if (path.startsWith('/dashboard')) {
      setCurrentSection('dashboard');
    } else if (path.startsWith('/finance')) {
      setCurrentSection('finance');
    } else if (path.startsWith('/automatization')) {
      setCurrentSection('automatization');
    } else if (path.startsWith('/ai-agent')) {
      setCurrentSection('ai-agent');
    } else if (path.startsWith('/monitoring')) {
      setCurrentSection('monitoring');
    } else if (path.startsWith('/notification')) {
      setCurrentSection('notification');
    } else if (path.startsWith('/inbox')) {
      setCurrentSection('inbox');
    } else if (path.startsWith('/integration')) {
      setCurrentSection('integration');
    } else if (path.startsWith('/reporting')) {
      setCurrentSection('reporting');
    } else if (path.startsWith('/active')) {
      setCurrentSection('active');
    } else if (path.startsWith('/past')) {
      setCurrentSection('past');
    }
  }, [location.pathname]);

  // Don't show sidebar and header on auth pages
  if (isAuthPage) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Routes>
    );
  }

  return (
    <div className="app">
      <Sidebar
        currentSection={currentSection}
        onSectionChange={setCurrentSection}
        onCollapseChange={setIsSidebarCollapsed}
      />
      <div className={`app-main ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <Header
          isSidebarCollapsed={isSidebarCollapsed}
        />
        <div className="app-content">
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/crm/deals" replace />
                </ProtectedRoute>
              }
            />
            {/* CRM Routes */}
            <Route
              path="/crm/deals"
              element={
                <ProtectedRoute>
                  <DealsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/crm/contacts"
              element={
                <ProtectedRoute>
                  <ContactsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/crm/accounts"
              element={
                <ProtectedRoute>
                  <AccountsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/crm/products"
              element={
                <ProtectedRoute>
                  <ProductsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/crm/inventory"
              element={
                <ProtectedRoute>
                  <InventoryPage />
                </ProtectedRoute>
              }
            />
            {/* Legacy routes - redirect to CRM */}
            <Route
              path="/deals"
              element={
                <ProtectedRoute>
                  <Navigate to="/crm/deals" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contacts"
              element={
                <ProtectedRoute>
                  <Navigate to="/crm/contacts" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/accounts"
              element={
                <ProtectedRoute>
                  <Navigate to="/crm/accounts" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/products"
              element={
                <ProtectedRoute>
                  <Navigate to="/crm/products" replace />
                </ProtectedRoute>
              }
            />
            {/* Profile */}
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            {/* Dashboard */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            {/* Coming Soon Pages */}
            <Route
              path="/finance"
              element={
                <ProtectedRoute>
                  <FinancePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/automatization"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Automatization" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/ai-agent"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="AI Agent" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/monitoring"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Monitoring" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/notification"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Notification" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/inbox"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Inbox" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/integration"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Integration" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reporting"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Reporting" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/active"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Active" />
                </ProtectedRoute>
              }
            />
            <Route
              path="/past"
              element={
                <ProtectedRoute>
                  <ComingSoonPage title="Past" />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <DealModalProvider>
        <Router>
          <AppContent />
        </Router>
      </DealModalProvider>
    </AuthProvider>
  );
}

export default App;


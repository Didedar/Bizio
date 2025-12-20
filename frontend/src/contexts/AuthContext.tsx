import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../api/client';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  tenantId: number | null;  // Added: current user's tenant ID
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, tenantName: string, tenantCode?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Compute tenantId from user's first tenant
  const tenantId = user?.tenants && user.tenants.length > 0 ? user.tenants[0].id : null;

  useEffect(() => {
    // Check for stored token on mount
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      setToken(storedToken);
      loadUser(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async (authToken: string) => {
    try {
      const userData = await authApi.getMe(authToken);
      setUser(userData);
    } catch (error) {
      console.error('Failed to load user:', error);
      localStorage.removeItem('auth_token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password);
      setToken(response.access_token);
      localStorage.setItem('auth_token', response.access_token);
      await loadUser(response.access_token);
    } catch (error: any) {
      // Clear token on login failure
      setToken(null);
      localStorage.removeItem('auth_token');
      throw error; // Re-throw to let the component handle the error
    }
  };

  const register = async (email: string, password: string, fullName: string, tenantName: string, tenantCode?: string) => {
    try {
      await authApi.register(email, password, fullName, tenantName, tenantCode);
      // After registration, automatically login
      await login(email, password);
    } catch (error: any) {
      // Re-throw to let the component handle the error
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        tenantId,  // Added
        login,
        register,
        logout,
        isAuthenticated: !!user && !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

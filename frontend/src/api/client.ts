import axios from 'axios';
import type { Client, ClientCreate, Deal, DealCreate, Product, ProductCreate, User, DealItemCreate, DealProfitAnalysis, Inventory, InventoryItem, InventoryReceive } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// For development, use tenant_id = 1
// In production, this should come from auth context
const DEFAULT_TENANT_ID = 1;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log error for debugging
    if (error.response) {
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url,
      });
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      // Only redirect if not already on login/register page
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Clients API
export const clientsApi = {
  list: async (tenantId: number = DEFAULT_TENANT_ID): Promise<Client[]> => {
    const response = await api.get<Client[]>('/clients', {
      params: { tenant_id: tenantId },
    });
    return response.data;
  },

  get: async (clientId: number): Promise<Client> => {
    const response = await api.get<Client>(`/clients/${clientId}`);
    return response.data;
  },

  create: async (tenantId: number = DEFAULT_TENANT_ID, data: ClientCreate): Promise<Client> => {
    const response = await api.post<Client>('/clients', data, {
      params: { tenant_id: tenantId },
    });
    return response.data;
  },

  update: async (clientId: number, changes: Partial<ClientCreate>): Promise<Client> => {
    const response = await api.patch<Client>(`/clients/${clientId}`, changes);
    return response.data;
  },

  delete: async (clientId: number): Promise<void> => {
    await api.delete(`/clients/${clientId}`);
  },
};

// Deals API
export const dealsApi = {
  list: async (tenantId: number = DEFAULT_TENANT_ID, skip: number = 0, limit: number = 50): Promise<Deal[]> => {
    const response = await api.get<Deal[]>('/deals', {
      params: { tenant_id: tenantId, skip, limit },
    });
    return response.data;
  },

  get: async (dealId: number): Promise<Deal> => {
    const response = await api.get<Deal>(`/deals/${dealId}`);
    return response.data;
  },

  create: async (tenantId: number = DEFAULT_TENANT_ID, data: DealCreate): Promise<Deal> => {
    const response = await api.post<Deal>('/deals', data, {
      params: { tenant_id: tenantId },
    });
    return response.data;
  },

  update: async (dealId: number, data: Partial<DealCreate>): Promise<Deal> => {
    const response = await api.put<Deal>(`/deals/${dealId}`, data);
    return response.data;
  },

  delete: async (dealId: number): Promise<void> => {
    await api.delete(`/deals/${dealId}`);
  },

  updateStatus: async (dealId: number, status: string): Promise<Deal> => {
    const response = await api.post<Deal>(`/deals/${dealId}/status`, null, {
      params: { status },
    });
    return response.data;
  },
};

// Deal Items API
export const dealItemsApi = {
  add: async (dealId: number, items: DealItemCreate[]): Promise<Deal> => {
    const response = await api.post<Deal>(`/deals/${dealId}/items`, items);
    return response.data;
  },
  remove: async (dealId: number, itemId: number): Promise<void> => {
    await api.delete(`/deals/${dealId}/items/${itemId}`);
  },
};

// Deal Profit API
export const dealProfitApi = {
  get: async (dealId: number): Promise<DealProfitAnalysis> => {
    const response = await api.get<DealProfitAnalysis>(`/deals/${dealId}/profit`);
    return response.data;
  },
};

// Products API
export const productsApi = {
  list: async (tenantId: number = DEFAULT_TENANT_ID, skip: number = 0, limit: number = 50, q?: string): Promise<Product[]> => {
    const response = await api.get<Product[]>('/products', {
      params: { tenant_id: tenantId, skip, limit, q },
    });
    return response.data;
  },

  get: async (productId: number): Promise<Product> => {
    const response = await api.get<Product>(`/products/${productId}`);
    return response.data;
  },

  create: async (tenantId: number = DEFAULT_TENANT_ID, data: ProductCreate): Promise<Product> => {
    const response = await api.post<Product>('/products', data, {
      params: { tenant_id: tenantId },
    });
    return response.data;
  },

  update: async (productId: number, changes: Partial<ProductCreate>): Promise<Product> => {
    const response = await api.patch<Product>(`/products/${productId}`, changes);
    return response.data;
  },

  delete: async (productId: number): Promise<void> => {
    await api.delete(`/products/${productId}`);
  },
};

// Inventory API
export const inventoryApi = {
  receive: async (
    productId: number,
    tenantId: number = DEFAULT_TENANT_ID,
    data: InventoryReceive
  ): Promise<InventoryItem> => {
    const response = await api.post<InventoryItem>(
      `/products/${productId}/inventory/receive`,
      null,
      {
        params: {
          tenant_id: tenantId,
          quantity: data.quantity,
          unit_cost: data.unit_cost,
          received_date: data.received_date,
          currency: data.currency || 'KZT',
          supplier_id: data.supplier_id,
          reference: data.reference,
          location: data.location,
        },
      }
    );
    return response.data;
  },

  getByProduct: async (productId: number, location?: string): Promise<Inventory[]> => {
    const response = await api.get<Inventory[]>(`/products/${productId}/inventory`, {
      params: { location },
    });
    return response.data;
  },

  getReceipts: async (productId: number, skip: number = 0, limit: number = 50): Promise<InventoryItem[]> => {
    const response = await api.get<InventoryItem[]>(`/products/${productId}/inventory/receipts`, {
      params: { skip, limit },
    });
    return response.data;
  },
};

// Users API (for deal owner selection)
export const usersApi = {
  list: async (): Promise<any[]> => {
    // This endpoint might not exist, but we'll try
    try {
      const response = await api.get('/users');
      return response.data;
    } catch {
      // Return mock data if endpoint doesn't exist
      return [
        { id: 1, email: 'admin@example.com', full_name: 'A Administrator' },
      ];
    }
  },
};

// Auth API
export const authApi = {
  login: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (
    email: string,
    password: string,
    fullName: string,
    tenantName: string,
    tenantCode?: string
  ): Promise<User> => {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      tenant_name: tenantName,
      tenant_code: tenantCode,
    });
    return response.data;
  },

  getMe: async (token?: string): Promise<User> => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await api.get('/auth/me', { headers });
    return response.data;
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async (tenantId: number): Promise<import('../types').DashboardStats> => {
    const response = await api.get('/dashboard/stats', {
      params: { tenant_id: tenantId },
    });
    return response.data;
  },
};

export default api;

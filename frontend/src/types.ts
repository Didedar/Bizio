export interface Tenant {
  id: number;
  name: string;
  code?: string;
  timezone?: string;
  currency: string;
  created_at: string;
}

export interface Client {
  id: number;
  tenant_id: number;
  external_id?: string;
  name: string;
  company?: string;
  email?: string;
  phone?: string;
  address?: string;
  deals?: Deal[];
  deals_count?: number;
  extra_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  name: string;
  company?: string;
  email?: string;
  phone?: string;
  address?: string;
  extra_data?: Record<string, any>;
  external_id?: string;
}

// Deal Item interface
export interface DealItem {
  id: number;
  deal_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  unit_cost: number;
  total_price: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
  product?: Product;
}

export interface DealItemCreate {
  product_id: number;
  quantity: number;
  unit_price?: number;
  unit_cost?: number;
}

export interface Deal {
  id: number;
  tenant_id?: number;
  client_id: number;
  title: string;
  status: string;
  total_price: number;
  total_cost: number;
  margin: number; // Changed to required
  currency: string;

  // Additional fields
  completion_date?: string;
  start_date?: string;
  source?: string;
  source_details?: string;
  deal_type?: string;
  is_available_to_all?: boolean;
  responsible_id?: number;
  comments?: string;
  recurring_settings?: Record<string, any>;

  extra_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
  closed_at?: string;

  // Related entities
  client?: Client;
  responsible?: User;
  observers?: User[];
  items?: DealItem[];
}

export interface DealCreate {
  client_id: number;
  title: string;
  total_price?: number; // Optional if items are provided
  total_cost?: number; // Optional if items are provided
  currency?: string;
  status?: string;

  // Additional fields
  completion_date?: string;
  start_date?: string;
  source?: string;
  source_details?: string;
  deal_type?: string;
  is_available_to_all?: boolean;
  responsible_id?: number;
  comments?: string;
  recurring_settings?: Record<string, any>;
  observer_ids?: number[];
  items?: DealItemCreate[]; // Added items support

  extra_data?: Record<string, any>;
}

export interface User {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  tenants?: Tenant[];
}

// ИЗМЕНЕНО: Оставлены только запрашиваемые статусы
export const DEAL_STATUSES = [
  { value: 'new', label: 'New' },
  { value: 'preparing_document', label: 'Document Preparation' },
  { value: 'prepaid_account', label: 'Prepaid Account' },
  { value: 'at_work', label: 'At Work' },
  { value: 'final_account', label: 'Final Account' },
];

export const EMPLOYEE_RANGES = [
  { value: '1-10', label: '1-10' },
  { value: '11-50', label: '11-50' },
  { value: '51-200', label: '51-200' },
  { value: '201-500', label: '201-500' },
  { value: '500+', label: '500+' },
];

export const TERRITORIES = [
  { value: 'Almaty', label: 'Almaty' },
  { value: 'Astana', label: 'Astana' },
  { value: 'Shymkent', label: 'Shymkent' },
  { value: 'Karaganda', label: 'Karaganda' },
  { value: 'Other', label: 'Other' },
];

export const INDUSTRIES = [
  { value: 'Technology', label: 'Technology' },
  { value: 'Retail', label: 'Retail' },
  { value: 'Manufacturing', label: 'Manufacturing' },
  { value: 'Services', label: 'Services' },
  { value: 'Healthcare', label: 'Healthcare' },
  { value: 'Finance', label: 'Finance' },
  { value: 'Other', label: 'Other' },
];

export const SALUTATIONS = [
  { value: 'Mr.', label: 'Mr.' },
  { value: 'Mrs.', label: 'Mrs.' },
  { value: 'Ms.', label: 'Ms.' },
  { value: 'Dr.', label: 'Dr.' },
];

export const GENDERS = [
  { value: 'Male', label: 'Male' },
  { value: 'Female', label: 'Female' },
  { value: 'Other', label: 'Other' },
];

export interface Product {
  id: number;
  tenant_id?: number;
  sku?: string;
  title: string;
  description?: string;
  category?: string;
  default_cost?: number;
  default_price?: number;
  currency: string;
  images?: string[];
  extra_data?: Record<string, any>;
  created_at: string;
}

export interface ProductCreate {
  title: string;
  sku?: string;
  description?: string;
  category?: string;
  default_cost?: number;
  default_price?: number;
  currency?: string;
  images?: string[];
  extra_data?: Record<string, any>;
}

export interface Expense {
  id: number;
  tenant_id?: number;
  user_id?: number;
  category: string;
  amount: number;
  currency: string;
  date: string;
  description?: string;
  days_until_payment?: number;
  is_fixed: boolean;
  created_at: string;
}

export interface ExpenseCreate {
  category: string;
  amount: number;
  currency?: string;
  date: string;
  description?: string;
  days_until_payment?: number;
  is_fixed?: boolean;
}

export interface FinanceDashboardMetrics {
  revenue: number;
  cogs: number;
  gross_profit: number;
  gross_margin_pct: number;
  opex: number;
  ebit: number;
  taxes: number;
  net_profit: number;
  net_margin_pct: number;
  fixed_costs: number;
  variable_costs?: number;
  break_even_revenue?: number;
}

export interface FinancialSettings {
  id: number;
  tenant_id: number;
  tax_rate: number;
  currency: string;
  updated_at: string;
}

export interface FinancialSettingsCreate {
  tax_rate?: number;
  currency?: string;
}

// Deal Profit Analysis
export interface DealProfitAnalysis {
  deal_id: number;
  revenue: number;
  cost: number;
  profit: number;
  profit_margin_pct: number;
  items_count: number;
}

// Inventory types
export interface Inventory {
  id: number;
  product_id: number;
  location?: string;
  quantity: number;
  reserved: number;
  updated_at: string;
}

export interface InventoryItem {
  id: number;
  product_id: number;
  tenant_id: number;
  quantity: number;
  remaining_quantity: number;
  unit_cost: number;
  currency: string;
  received_date: string;
  supplier_id?: number;
  reference?: string;
  location?: string;
  created_at: string;
}

export interface InventoryReceive {
  quantity: number;
  unit_cost: number;
  received_date: string;
  currency?: string;
  supplier_id?: number;
  reference?: string;
  location?: string;
}

// Dashboard Types
export interface DealStatusCount {
  status: string;
  count: number;
  label: string;
}

export interface MonthlyRevenue {
  month: string;
  revenue: number;
  expenses: number;
  profit: number;
}

export interface TopProduct {
  id: number;
  title: string;
  category?: string;
  total_quantity: number;
  total_revenue: number;
}

export interface RecentDeal {
  id: number;
  title: string;
  status: string;
  total_price: number;
  client_name?: string;
  created_at: string;
}

export interface DashboardStats {
  total_revenue: number;
  total_deals: number;
  total_products: number;
  total_clients: number;
  revenue_change_pct: number;
  deals_change_pct: number;
  deals_by_status: DealStatusCount[];
  revenue_by_month: MonthlyRevenue[];
  top_products: TopProduct[];
  recent_deals: RecentDeal[];
}
import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { dashboardApi } from '../api/client';
import { DashboardStats, DEAL_STATUSES } from '../types';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
    Legend,
    Area,
    AreaChart,
} from 'recharts';
import { formatDate } from '../utils/dateUtils';
import './DashboardPage.css';

const DashboardPage: React.FC = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchStats = async () => {
            if (!user?.tenants?.[0]?.id) return;

            try {
                setLoading(true);
                const data = await dashboardApi.getStats(user.tenants[0].id);
                setStats(data);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch dashboard stats:', err);
                setError('Failed to load dashboard data');
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, [user?.tenants]);

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'KZT',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('en-US').format(num);
    };



    const getStatusLabel = (status: string) => {
        const found = DEAL_STATUSES.find(s => s.value === status);
        return found?.label || status;
    };

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            new: '#6366f1',
            preparing_document: '#f59e0b',
            prepaid_account: '#06b6d4',
            at_work: '#8b5cf6',
            final_account: '#10b981',
        };
        return colors[status] || '#6b7280';
    };

    // Chart colors
    const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

    if (loading) {
        return (
            <div className="dashboard-page">
                <div className="dashboard-loading">
                    <div className="loading-spinner" />
                    <p>Loading dashboard...</p>
                </div>
            </div>
        );
    }

    if (error || !stats) {
        return (
            <div className="dashboard-page">
                <div className="dashboard-error">
                    <h2>Unable to load dashboard</h2>
                    <p>{error || 'No data available'}</p>
                </div>
            </div>
        );
    }

    // Prepare chart data
    const barChartData = stats.revenue_by_month.map(item => ({
        name: item.month.split(' ')[0],
        revenue: item.revenue,
        expenses: item.expenses,
    }));

    const pieChartData = stats.deals_by_status.map(item => ({
        name: item.label,
        value: item.count,
        color: getStatusColor(item.status),
    }));

    const lineChartData = stats.revenue_by_month.map(item => ({
        name: item.month.split(' ')[0],
        profit: item.profit,
        revenue: item.revenue,
    }));

    return (
        <div className="dashboard-page">
            {/* Header */}
            <div className="dashboard-header">
                <div className="header-content">
                    <h1>Dashboard</h1>
                    <p className="header-subtitle">Business overview and analytics</p>
                </div>
                <div className="header-actions">
                    <button className="btn-refresh" onClick={() => window.location.reload()}>
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C10.0503 2 11.8687 2.98982 13 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            <path d="M13 1.5V4.5H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Refresh
                    </button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="summary-cards">
                <div className="summary-card">
                    <div className="card-icon revenue-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M12 2V22M17 5H9.5C8.57174 5 7.6815 5.36875 7.02513 6.02513C6.36875 6.6815 6 7.57174 6 8.5C6 9.42826 6.36875 10.3185 7.02513 10.9749C7.6815 11.6313 8.57174 12 9.5 12H14.5C15.4283 12 16.3185 12.3687 16.9749 13.0251C17.6313 13.6815 18 14.5717 18 15.5C18 16.4283 17.6313 17.3185 16.9749 17.9749C16.3185 18.6313 15.4283 19 14.5 19H6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <div className="card-content">
                        <span className="card-label">Total Revenue</span>
                        <span className="card-value">{formatCurrency(stats.total_revenue)}</span>
                        <span className={`card-change ${stats.revenue_change_pct >= 0 ? 'positive' : 'negative'}`}>
                            {stats.revenue_change_pct >= 0 ? '↑' : '↓'} {Math.abs(stats.revenue_change_pct).toFixed(1)}% this month
                        </span>
                    </div>
                </div>

                <div className="summary-card">
                    <div className="card-icon deals-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M16 4H18C18.5304 4 19.0391 4.21071 19.4142 4.58579C19.7893 4.96086 20 5.46957 20 6V20C20 20.5304 19.7893 21.0391 19.4142 21.4142C19.0391 21.7893 18.5304 22 18 22H6C5.46957 22 4.96086 21.7893 4.58579 21.4142C4.21071 21.0391 4 20.5304 4 20V6C4 5.46957 4.21071 4.96086 4.58579 4.58579C4.96086 4.21071 5.46957 4 6 4H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M15 2H9C8.44772 2 8 2.44772 8 3V5C8 5.55228 8.44772 6 9 6H15C15.5523 6 16 5.55228 16 5V3C16 2.44772 15.5523 2 15 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <div className="card-content">
                        <span className="card-label">Total Deals</span>
                        <span className="card-value">{formatNumber(stats.total_deals)}</span>
                        <span className={`card-change ${stats.deals_change_pct >= 0 ? 'positive' : 'negative'}`}>
                            {stats.deals_change_pct >= 0 ? '↑' : '↓'} {Math.abs(stats.deals_change_pct).toFixed(1)}% this month
                        </span>
                    </div>
                </div>

                <div className="summary-card">
                    <div className="card-icon products-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M21 16V8C20.9996 7.6493 20.9071 7.30483 20.7315 7.00017C20.556 6.69552 20.3037 6.44085 20 6.26L13 2.26C12.696 2.08967 12.3511 2 12 2C11.6489 2 11.304 2.08967 11 2.26L4 6.26C3.69626 6.44085 3.44398 6.69552 3.26846 7.00017C3.09294 7.30483 3.00036 7.6493 3 8V16C3.00036 16.3507 3.09294 16.6952 3.26846 16.9998C3.44398 17.3045 3.69626 17.5591 4 17.74L11 21.74C11.304 21.9103 11.6489 22 12 22C12.3511 22 12.696 21.9103 13 21.74L20 17.74C20.3037 17.5591 20.556 17.3045 20.7315 16.9998C20.9071 16.6952 20.9996 16.3507 21 16Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M3.27002 6.96L12 12.01L20.73 6.96" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M12 22.08V12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <div className="card-content">
                        <span className="card-label">Products</span>
                        <span className="card-value">{formatNumber(stats.total_products)}</span>
                        <span className="card-change neutral">In catalog</span>
                    </div>
                </div>

                <div className="summary-card">
                    <div className="card-icon clients-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M9 11C11.2091 11 13 9.20914 13 7C13 4.79086 11.2091 3 9 3C6.79086 3 5 4.79086 5 7C5 9.20914 6.79086 11 9 11Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <div className="card-content">
                        <span className="card-label">Clients</span>
                        <span className="card-value">{formatNumber(stats.total_clients)}</span>
                        <span className="card-change neutral">Active accounts</span>
                    </div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="charts-section">
                {/* Revenue Bar Chart */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h3>Revenue vs Expenses</h3>
                        <span className="chart-subtitle">Last 6 months comparison</span>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={barChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`} />
                                <Tooltip
                                    formatter={(value) => formatCurrency(Number(value))}
                                    contentStyle={{
                                        backgroundColor: '#fff',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '8px',
                                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                    }}
                                />
                                <Legend />
                                <Bar dataKey="revenue" name="Revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="expenses" name="Expenses" fill="#f87171" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Deals Pie Chart */}
                <div className="chart-card">
                    <div className="chart-header">
                        <h3>Deals by Status</h3>
                        <span className="chart-subtitle">Current distribution</span>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={pieChartData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={3}
                                    dataKey="value"
                                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                                    labelLine={false}
                                >
                                    {pieChartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    formatter={(value, name) => [value, name]}
                                    contentStyle={{
                                        backgroundColor: '#fff',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '8px'
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Trend Chart */}
            <div className="trend-section">
                <div className="chart-card full-width">
                    <div className="chart-header">
                        <h3>Revenue & Profit Trend</h3>
                        <span className="chart-subtitle">Monthly performance over time</span>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={280}>
                            <AreaChart data={lineChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <defs>
                                    <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`} />
                                <Tooltip
                                    formatter={(value) => formatCurrency(Number(value))}
                                    contentStyle={{
                                        backgroundColor: '#fff',
                                        border: '1px solid #e5e7eb',
                                        borderRadius: '8px',
                                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                    }}
                                />
                                <Legend />
                                <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#6366f1" fillOpacity={1} fill="url(#colorRevenue)" strokeWidth={2} />
                                <Area type="monotone" dataKey="profit" name="Profit" stroke="#10b981" fillOpacity={1} fill="url(#colorProfit)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Data Tables */}
            <div className="tables-section">
                {/* Recent Deals */}
                <div className="table-card">
                    <div className="table-header">
                        <h3>Recent Deals</h3>
                        <a href="/crm/deals" className="view-all-link">View All →</a>
                    </div>
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Deal</th>
                                    <th>Client</th>
                                    <th>Status</th>
                                    <th>Value</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {stats.recent_deals.length === 0 ? (
                                    <tr>
                                        <td colSpan={5} className="empty-row">No deals yet</td>
                                    </tr>
                                ) : (
                                    stats.recent_deals.map(deal => (
                                        <tr key={deal.id}>
                                            <td className="deal-title">{deal.title}</td>
                                            <td className="client-name">{deal.client_name || '—'}</td>
                                            <td>
                                                <span
                                                    className="status-badge"
                                                    style={{ backgroundColor: `${getStatusColor(deal.status)}15`, color: getStatusColor(deal.status) }}
                                                >
                                                    {getStatusLabel(deal.status)}
                                                </span>
                                            </td>
                                            <td className="deal-value">{formatCurrency(deal.total_price)}</td>
                                            <td className="deal-date">{formatDate(deal.created_at)}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Top Products */}
                <div className="table-card">
                    <div className="table-header">
                        <h3>Top Products</h3>
                        <a href="/crm/products" className="view-all-link">View All →</a>
                    </div>
                    <div className="table-container">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Category</th>
                                    <th>Sold</th>
                                    <th>Revenue</th>
                                </tr>
                            </thead>
                            <tbody>
                                {stats.top_products.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="empty-row">No products sold yet</td>
                                    </tr>
                                ) : (
                                    stats.top_products.map(product => (
                                        <tr key={product.id}>
                                            <td className="product-title">{product.title}</td>
                                            <td className="product-category">{product.category || '—'}</td>
                                            <td className="product-quantity">{formatNumber(product.total_quantity)}</td>
                                            <td className="product-revenue">{formatCurrency(product.total_revenue)}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;

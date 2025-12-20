import React, { useState, useEffect, useMemo } from 'react';
import { productsApi, inventoryApi } from '../api/client';
import type { Product, InventoryItem, InventoryReceive } from '../types';
import { useAuth } from '../contexts/AuthContext';
import './InventoryPage.css';

interface ReceiveModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    product: Product | null;
}

const ReceiveInventoryModal: React.FC<ReceiveModalProps> = ({ isOpen, onClose, onSuccess, product }) => {
    const [formData, setFormData] = useState<InventoryReceive>({
        quantity: 0,
        unit_cost: 0,
        received_date: new Date().toISOString().split('T')[0],
        currency: 'KZT',
        reference: '',
        location: '',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            setFormData({
                quantity: 0,
                unit_cost: product?.default_cost || 0,
                received_date: new Date().toISOString().split('T')[0],
                currency: product?.currency || 'KZT',
                reference: '',
                location: '',
            });
            setError(null);
        }
    }, [isOpen, product]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!product) return;

        setLoading(true);
        setError(null);

        try {
            await inventoryApi.receive(product.id, 1, formData);
            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to receive inventory');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen || !product) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Receive Inventory</h2>
                    <button className="modal-close" onClick={onClose}>
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </button>
                </div>
                <div className="receive-product-info">
                    <strong>{product.title}</strong>
                    {product.sku && <span className="product-sku-badge">{product.sku}</span>}
                </div>
                <form onSubmit={handleSubmit}>
                    {error && <div className="error-message">{error}</div>}
                    <div className="form-row">
                        <div className="form-group">
                            <label>Quantity *</label>
                            <input
                                type="number"
                                step="0.0001"
                                min="0.0001"
                                value={formData.quantity}
                                onChange={(e) => setFormData({ ...formData, quantity: parseFloat(e.target.value) || 0 })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Unit Cost *</label>
                            <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={formData.unit_cost || ''}
                                onChange={(e) => setFormData({ ...formData, unit_cost: parseFloat(e.target.value) || 0 })}
                                required
                            />
                        </div>
                    </div>
                    <div className="form-row">
                        <div className="form-group">
                            <label>Received Date *</label>
                            <input
                                type="date"
                                value={formData.received_date}
                                onChange={(e) => setFormData({ ...formData, received_date: e.target.value })}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Currency</label>
                            <select
                                value={formData.currency}
                                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                            >
                                <option value="KZT">KZT</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="RUB">RUB</option>
                            </select>
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Reference (PO number, invoice)</label>
                        <input
                            type="text"
                            value={formData.reference || ''}
                            onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                            placeholder="e.g., INV-2024-001"
                        />
                    </div>
                    <div className="form-group">
                        <label>Location</label>
                        <input
                            type="text"
                            value={formData.location || ''}
                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                            placeholder="e.g., Warehouse A"
                        />
                    </div>
                    <div className="modal-actions">
                        <button type="button" className="btn-secondary" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? 'Saving...' : 'Receive Inventory'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

interface HistoryModalProps {
    isOpen: boolean;
    onClose: () => void;
    product: Product | null;
}

const HistoryModal: React.FC<HistoryModalProps> = ({ isOpen, onClose, product }) => {
    const [receipts, setReceipts] = useState<InventoryItem[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && product) {
            loadReceipts();
        }
    }, [isOpen, product]);

    const loadReceipts = async () => {
        if (!product) return;
        setLoading(true);
        try {
            const data = await inventoryApi.getReceipts(product.id);
            setReceipts(data);
        } catch (err) {
            console.error('Failed to load receipts:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount: number, currency: string = 'KZT') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
        }).format(amount);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    if (!isOpen || !product) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Inventory History</h2>
                    <button className="modal-close" onClick={onClose}>
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                    </button>
                </div>
                <div className="receive-product-info">
                    <strong>{product.title}</strong>
                    {product.sku && <span className="product-sku-badge">{product.sku}</span>}
                </div>
                <div className="history-content">
                    {loading ? (
                        <div className="loading-state">
                            <div className="loading-spinner"></div>
                            <p>Loading history...</p>
                        </div>
                    ) : receipts.length === 0 ? (
                        <div className="empty-state-small">
                            <p>No inventory receipts found</p>
                        </div>
                    ) : (
                        <table className="history-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Quantity</th>
                                    <th>Remaining</th>
                                    <th>Unit Cost</th>
                                    <th>Total</th>
                                    <th>Reference</th>
                                    <th>Location</th>
                                </tr>
                            </thead>
                            <tbody>
                                {receipts.map((receipt) => (
                                    <tr key={receipt.id}>
                                        <td>{formatDate(receipt.received_date)}</td>
                                        <td>{receipt.quantity}</td>
                                        <td className={receipt.remaining_quantity > 0 ? 'text-green' : 'text-muted'}>
                                            {receipt.remaining_quantity}
                                        </td>
                                        <td>{formatCurrency(receipt.unit_cost, receipt.currency)}</td>
                                        <td>{formatCurrency(receipt.quantity * receipt.unit_cost, receipt.currency)}</td>
                                        <td>{receipt.reference || '—'}</td>
                                        <td>{receipt.location || '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
                <div className="modal-actions">
                    <button type="button" className="btn-secondary" onClick={onClose}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

const InventoryPage: React.FC = () => {
    const { tenantId } = useAuth();
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [isReceiveModalOpen, setIsReceiveModalOpen] = useState(false);
    const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);

    useEffect(() => {
        if (tenantId) {
            loadProducts();
        }
    }, [tenantId]);

    const loadProducts = async () => {
        if (!tenantId) return;
        try {
            setLoading(true);
            const data = await productsApi.list(tenantId, 0, 100);
            setProducts(data);
        } catch (error) {
            console.error('Failed to load products:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredProducts = useMemo(() => {
        if (!searchQuery) return products;
        const query = searchQuery.toLowerCase();
        return products.filter(product =>
            product.title.toLowerCase().includes(query) ||
            product.sku?.toLowerCase().includes(query) ||
            product.category?.toLowerCase().includes(query)
        );
    }, [products, searchQuery]);

    const handleReceive = (product: Product) => {
        setSelectedProduct(product);
        setIsReceiveModalOpen(true);
    };

    const handleViewHistory = (product: Product) => {
        setSelectedProduct(product);
        setIsHistoryModalOpen(true);
    };

    const handleReceiveSuccess = () => {
        loadProducts();
    };

    const formatCurrency = (amount: number | undefined, currency: string = 'KZT') => {
        if (amount === undefined || amount === null) return '—';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
        }).format(amount);
    };

    const getQuantityClass = (quantity: number | undefined) => {
        if (quantity === undefined || quantity === 0) return 'qty-zero';
        if (quantity < 10) return 'qty-low';
        if (quantity < 50) return 'qty-medium';
        return 'qty-high';
    };

    return (
        <div className="inventory-page">
            <div className="inventory-header">
                <div className="inventory-header-content">
                    <div className="inventory-title-section">
                        <h1 className="inventory-title">Inventory</h1>
                        <span className="inventory-count">
                            {filteredProducts.length} {filteredProducts.length === 1 ? 'product' : 'products'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="inventory-toolbar">
                <div className="toolbar-left">
                    <div className="search-wrapper">
                        <svg className="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M7.33333 12.6667C10.2789 12.6667 12.6667 10.2789 12.6667 7.33333C12.6667 4.38781 10.2789 2 7.33333 2C4.38781 2 2 4.38781 2 7.33333C2 10.2789 4.38781 12.6667 7.33333 12.6667Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M14 14L11.1 11.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <input
                            type="text"
                            placeholder="Search products..."
                            className="search-input"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        {searchQuery && (
                            <button className="search-clear" onClick={() => setSearchQuery('')} title="Clear search">
                                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                    <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                </svg>
                            </button>
                        )}
                    </div>
                </div>
                <div className="toolbar-right">
                    <button className="toolbar-btn" onClick={loadProducts} title="Refresh" disabled={loading}>
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={loading ? 'spinning' : ''}>
                            <path d="M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C9.85652 2 11.5076 2.84956 12.5778 4.18919" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            <path d="M14 4V8H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </button>
                </div>
            </div>

            <div className="inventory-content">
                {loading ? (
                    <div className="loading-state">
                        <div className="loading-spinner"></div>
                        <p>Loading inventory...</p>
                    </div>
                ) : filteredProducts.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-content">
                            <div className="empty-state-icon">
                                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                                    <path d="M8 16L32 4L56 16V48L32 60L8 48V16Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M32 28V60" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                    <path d="M8 16L32 28L56 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </div>
                            <h2>No Products Found</h2>
                            <p className="empty-state-description">
                                {searchQuery ? 'Try adjusting your search query.' : 'Create products first to manage inventory.'}
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="inventory-table-container">
                        <table className="inventory-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>SKU</th>
                                    <th>Category</th>
                                    <th>Unit Cost</th>
                                    <th>Quantity</th>
                                    <th className="actions-column">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredProducts.map((product) => (
                                    <tr key={product.id}>
                                        <td>
                                            <div className="product-title">{product.title}</div>
                                        </td>
                                        <td>
                                            <div className="product-sku">{product.sku || '—'}</div>
                                        </td>
                                        <td>
                                            <div className="product-category">{product.category || '—'}</div>
                                        </td>
                                        <td>
                                            <div className="product-cost">{formatCurrency(product.default_cost, product.currency)}</div>
                                        </td>
                                        <td>
                                            <div className={`quantity-badge ${getQuantityClass((product as any).quantity)}`}>
                                                {(product as any).quantity ?? 0}
                                            </div>
                                        </td>
                                        <td className="actions-column">
                                            <div className="table-actions">
                                                <button
                                                    className="action-btn action-btn-receive"
                                                    onClick={() => handleReceive(product)}
                                                    title="Receive Inventory"
                                                >
                                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                                        <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                                    </svg>
                                                    Receive
                                                </button>
                                                <button
                                                    className="action-btn action-btn-history"
                                                    onClick={() => handleViewHistory(product)}
                                                    title="View History"
                                                >
                                                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                                        <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" />
                                                        <path d="M8 5V8L10 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                                                    </svg>
                                                    History
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            <ReceiveInventoryModal
                isOpen={isReceiveModalOpen}
                onClose={() => {
                    setIsReceiveModalOpen(false);
                    setSelectedProduct(null);
                }}
                onSuccess={handleReceiveSuccess}
                product={selectedProduct}
            />

            <HistoryModal
                isOpen={isHistoryModalOpen}
                onClose={() => {
                    setIsHistoryModalOpen(false);
                    setSelectedProduct(null);
                }}
                product={selectedProduct}
            />
        </div>
    );
};

export default InventoryPage;

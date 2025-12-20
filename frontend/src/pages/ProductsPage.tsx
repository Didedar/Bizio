import React, { useState, useEffect, useMemo } from 'react';
import { productsApi } from '../api/client';
import type { Product, ProductCreate } from '../types';
import SortDropdown, { SortOption } from '../components/SortDropdown';
import ColumnsDropdown, { ColumnConfig } from '../components/ColumnsDropdown';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import { useAuth } from '../contexts/AuthContext';
import { formatDate, getSafeTimestamp } from '../utils/dateUtils';
import './ProductsPage.css';

interface CreateProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  product?: Product | null;
  tenantId: number | null;
}

const CreateProductModal: React.FC<CreateProductModalProps> = ({ isOpen, onClose, onSuccess, product, tenantId }) => {
  const [formData, setFormData] = useState<ProductCreate>({
    title: '',
    sku: '',
    description: '',
    category: '',
    default_cost: undefined,
    default_price: undefined,
    currency: 'KZT',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (product) {
      setFormData({
        title: product.title || '',
        sku: product.sku || '',
        description: product.description || '',
        category: product.category || '',
        default_cost: product.default_cost,
        default_price: product.default_price,
        currency: product.currency || 'KZT',
      });
    } else {
      setFormData({
        title: '',
        sku: '',
        description: '',
        category: '',
        default_cost: undefined,
        default_price: undefined,
        currency: 'KZT',
      });
    }
  }, [product, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const submitData: ProductCreate = {
        ...formData,
        default_cost: formData.default_cost ? Number(formData.default_cost) : undefined,
        default_price: formData.default_price ? Number(formData.default_price) : undefined,
      };
      if (product) {
        await productsApi.update(product.id, submitData);
      } else {
        if (!tenantId) throw new Error('Tenant ID is required');
        await productsApi.create(tenantId, submitData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save product');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{product ? 'Edit Product' : 'New Product'}</h2>
          <button className="modal-close" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">{error}</div>
          )}
          <div className="form-group">
            <label>Product Name *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>SKU</label>
            <input
              type="text"
              value={formData.sku || ''}
              onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>
          <div className="form-group">
            <label>Category</label>
            <input
              type="text"
              value={formData.category || ''}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Default Cost</label>
              <input
                type="number"
                step="0.01"
                value={formData.default_cost || ''}
                onChange={(e) => setFormData({ ...formData, default_cost: e.target.value ? parseFloat(e.target.value) : undefined })}
              />
            </div>
            <div className="form-group">
              <label>Default Price</label>
              <input
                type="number"
                step="0.01"
                value={formData.default_price || ''}
                onChange={(e) => setFormData({ ...formData, default_price: e.target.value ? parseFloat(e.target.value) : undefined })}
              />
            </div>
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
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving...' : product ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface ProductFilterOptions {
  dateFrom: string;
  dateTo: string;
  category: string;
  minPrice: string;
  maxPrice: string;
  hasSku: boolean | null;
}

const ProductsPage: React.FC = () => {
  const { tenantId } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [deleteProductId, setDeleteProductId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [filters, setFilters] = useState<ProductFilterOptions>({
    dateFrom: '',
    dateTo: '',
    category: '',
    minPrice: '',
    maxPrice: '',
    hasSku: null,
  });
  const [sortOption, setSortOption] = useState<SortOption>({
    field: 'created_at',
    direction: 'desc',
  });
  const [columns, setColumns] = useState<ColumnConfig[]>([
    { id: 'title', label: 'Product Name', visible: true },
    { id: 'sku', label: 'SKU', visible: true },
    { id: 'category', label: 'Category', visible: true },
    { id: 'cost', label: 'Cost', visible: true },
    { id: 'price', label: 'Price', visible: true },
    { id: 'currency', label: 'Currency', visible: true },
    { id: 'created', label: 'Created', visible: true },
  ]);

  useEffect(() => {
    if (tenantId) {
      loadProducts();
    }
  }, [tenantId]);

  const loadProducts = async () => {
    if (!tenantId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await productsApi.list(tenantId, 0, 50, searchQuery || undefined);
      setProducts(data);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadProducts();
    }, 300);
    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  const handleProductCreated = () => {
    setIsCreateModalOpen(false);
    setSelectedProduct(null);
    loadProducts();
  };

  const handleEditProduct = (product: Product) => {
    setSelectedProduct(product);
    setIsCreateModalOpen(true);
  };

  const handleDeleteProduct = async () => {
    if (deleteProductId === null) return;
    try {
      setDeleting(true);
      await productsApi.delete(deleteProductId);
      setDeleteProductId(null);
      loadProducts();
    } catch (error) {
      console.error('Failed to delete product:', error);
      setError('Failed to delete product');
    } finally {
      setDeleting(false);
    }
  };

  const filteredProducts = useMemo(() => {
    let result = [...products];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(product =>
        product.title.toLowerCase().includes(query) ||
        product.sku?.toLowerCase().includes(query) ||
        product.category?.toLowerCase().includes(query) ||
        product.description?.toLowerCase().includes(query)
      );
    }

    // Date filter
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      result = result.filter(product => {
        const productDate = getSafeTimestamp(product.created_at);
        return productDate > 0 && productDate >= fromDate.getTime();
      });
    }
    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59, 999);
      result = result.filter(product => {
        const productDate = getSafeTimestamp(product.created_at);
        return productDate > 0 && productDate <= toDate.getTime();
      });
    }

    // Category filter
    if (filters.category) {
      result = result.filter(product =>
        product.category?.toLowerCase().includes(filters.category.toLowerCase())
      );
    }

    // Price filter
    if (filters.minPrice) {
      const min = parseFloat(filters.minPrice);
      if (!isNaN(min)) {
        result = result.filter(product =>
          product.default_price !== undefined && product.default_price >= min
        );
      }
    }
    if (filters.maxPrice) {
      const max = parseFloat(filters.maxPrice);
      if (!isNaN(max)) {
        result = result.filter(product =>
          product.default_price !== undefined && product.default_price <= max
        );
      }
    }

    // SKU filter
    if (filters.hasSku !== null) {
      result = result.filter(product =>
        filters.hasSku ? !!product.sku : !product.sku
      );
    }

    return result;
  }, [products, searchQuery, filters]);

  // Apply sorting
  const sortedProducts = useMemo(() => {
    const result = [...filteredProducts];

    result.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortOption.field) {
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'sku':
          aValue = (a.sku || '').toLowerCase();
          bValue = (b.sku || '').toLowerCase();
          break;
        case 'category':
          aValue = (a.category || '').toLowerCase();
          bValue = (b.category || '').toLowerCase();
          break;
        case 'default_price':
          aValue = Number(a.default_price || 0);
          bValue = Number(b.default_price || 0);
          break;
        case 'default_cost':
          aValue = Number(a.default_cost || 0);
          bValue = Number(b.default_cost || 0);
          break;
        case 'created_at':
        default:
          aValue = getSafeTimestamp(a.created_at);
          bValue = getSafeTimestamp(b.created_at);
          break;
      }

      if (aValue < bValue) {
        return sortOption.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortOption.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });

    return result;
  }, [filteredProducts, sortOption]);

  const hasActiveFilters =
    filters.dateFrom !== '' ||
    filters.dateTo !== '' ||
    filters.category !== '' ||
    filters.minPrice !== '' ||
    filters.maxPrice !== '' ||
    filters.hasSku !== null;

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.dateFrom) count++;
    if (filters.dateTo) count++;
    if (filters.category) count++;
    if (filters.minPrice) count++;
    if (filters.maxPrice) count++;
    if (filters.hasSku !== null) count++;
    return count;
  };

  const handleFilterReset = () => {
    const emptyFilters: ProductFilterOptions = {
      dateFrom: '',
      dateTo: '',
      category: '',
      minPrice: '',
      maxPrice: '',
      hasSku: null,
    };
    setFilters(emptyFilters);
  };

  const formatCurrency = (amount: number | undefined, currency: string = 'KZT') => {
    if (amount === undefined || amount === null) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };



  return (
    <div className="products-page">
      <div className="products-header">
        <div className="products-header-content">
          <div className="products-title-section">
            <h1 className="products-title">Products</h1>
            {sortedProducts.length > 0 && (
              <span className="products-count">{sortedProducts.length} {sortedProducts.length === 1 ? 'product' : 'products'}</span>
            )}
          </div>
          <button className="btn-create-product" onClick={() => {
            setSelectedProduct(null);
            setIsCreateModalOpen(true);
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Create Product
          </button>
        </div>
      </div>

      <div className="products-toolbar">
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
              <button
                className="search-clear"
                onClick={() => setSearchQuery('')}
                title="Clear search"
              >
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                  <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            )}
          </div>
        </div>
        <div className="toolbar-right">
          <button
            className="toolbar-btn"
            onClick={loadProducts}
            title="Refresh"
            disabled={loading}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              className={loading ? 'spinning' : ''}
            >
              <path d="M8 1V3M8 13V15M3 8H1M15 8H13M4.34315 4.34315L5.75736 5.75736M10.2426 10.2426L11.6569 11.6569M1 8C1 11.866 4.13401 15 8 15C11.866 15 15 11.866 15 8C15 4.13401 11.866 1 8 1M1 8C1 4.13401 4.13401 1 8 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <button
            className={`toolbar-btn filter-btn ${hasActiveFilters ? 'active' : ''}`}
            onClick={() => setIsFilterOpen(true)}
            title="Filter"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4H14M4 8H12M6 12H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            Filter
            {hasActiveFilters && (
              <span className="filter-badge">{getActiveFilterCount()}</span>
            )}
          </button>
          <SortDropdown
            sortOption={sortOption}
            onSortChange={setSortOption}
            sortFields={[
              { field: 'created_at', label: 'Created Date' },
              { field: 'title', label: 'Product Name' },
              { field: 'sku', label: 'SKU' },
              { field: 'category', label: 'Category' },
              { field: 'default_price', label: 'Price' },
              { field: 'default_cost', label: 'Cost' },
            ]}
          />
          <ColumnsDropdown columns={columns} onColumnsChange={setColumns} />
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 6V10M8 11H8.00667M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span>{error}</span>
          <button className="error-dismiss" onClick={() => setError(null)}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      )}

      <div className="products-content">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading products...</p>
          </div>
        ) : error ? null : sortedProducts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-content">
              <div className="empty-state-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <path d="M32 8C18.745 8 8 18.745 8 32C8 45.255 18.745 56 32 56C45.255 56 56 45.255 56 32C56 18.745 45.255 8 32 8ZM36 24C36 26.2091 34.2091 28 32 28C29.7909 28 28 26.2091 28 24C28 21.7909 29.7909 20 32 20C34.2091 20 36 21.7909 36 24ZM28 36H36V44H28V36ZM36 44V36H44V44H36Z" fill="currentColor" fillOpacity="0.1" />
                  <path d="M32 22C33.1046 22 34 22.8954 34 24C34 25.1046 33.1046 26 32 26C30.8954 26 30 25.1046 30 24C30 22.8954 30.8954 22 32 22ZM28 34H36V42H28V34ZM38 34H46V42H38V34Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <h2>No Products Found</h2>
              <p className="empty-state-description">
                {hasActiveFilters || searchQuery
                  ? 'Try adjusting your filters or search query to see more results.'
                  : 'Get started by creating your first product.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="products-table-container">
            <table className="products-table">
              <thead>
                <tr>
                  {columns.find(col => col.id === 'title')?.visible && <th>Product Name</th>}
                  {columns.find(col => col.id === 'sku')?.visible && <th>SKU</th>}
                  {columns.find(col => col.id === 'category')?.visible && <th>Category</th>}
                  {columns.find(col => col.id === 'cost')?.visible && <th>Cost</th>}
                  {columns.find(col => col.id === 'price')?.visible && <th>Price</th>}
                  {columns.find(col => col.id === 'currency')?.visible && <th>Currency</th>}
                  {columns.find(col => col.id === 'created')?.visible && <th>Created</th>}
                  <th className="actions-column">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedProducts.map((product) => (
                  <tr key={product.id}>
                    {columns.find(col => col.id === 'title')?.visible && (
                      <td>
                        <div className="product-title">{product.title}</div>
                        {product.description && (
                          <div className="product-description">{product.description}</div>
                        )}
                      </td>
                    )}
                    {columns.find(col => col.id === 'sku')?.visible && (
                      <td>
                        <div className="product-sku">{product.sku || '—'}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'category')?.visible && (
                      <td>
                        <div className="product-category">{product.category || '—'}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'cost')?.visible && (
                      <td>
                        <div className="product-cost">{formatCurrency(product.default_cost, product.currency)}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'price')?.visible && (
                      <td>
                        <div className="product-price">{formatCurrency(product.default_price, product.currency)}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'currency')?.visible && (
                      <td>
                        <div className="product-currency">{product.currency}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'created')?.visible && (
                      <td>
                        <div className="product-date">{formatDate(product.created_at)}</div>
                      </td>
                    )}
                    <td className="actions-column">
                      <div className="table-actions">
                        <button
                          className="action-btn action-btn-view"
                          onClick={() => handleEditProduct(product)}
                          title="Edit"
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M11.3333 2.00001C11.5084 1.82491 11.7163 1.686 11.9451 1.59128C12.1739 1.49657 12.4189 1.44775 12.6667 1.44775C12.9144 1.44775 13.1594 1.49657 13.3882 1.59128C13.617 1.686 13.8249 1.82491 14 2.00001C14.1751 2.1751 14.314 2.383 14.4087 2.6118C14.5034 2.8406 14.5522 3.08564 14.5522 3.33334C14.5522 3.58104 14.5034 3.82608 14.4087 4.05486C14.314 4.28364 14.1751 4.49154 14 4.66668L5.00001 13.6667L1.33334 14.6667L2.33334 11L11.3333 2.00001Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>
                        <button
                          className="action-btn action-btn-delete"
                          onClick={() => setDeleteProductId(product.id)}
                          title="Delete"
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M2 4H14M6 4V2C6 1.44772 6.44772 1 7 1H9C9.55228 1 10 1.44772 10 2V4M12.6667 4V13.3333C12.6667 13.687 12.5262 14.0261 12.2761 14.2761C12.0261 14.5262 11.687 14.6667 11.3333 14.6667H4.66667C4.31305 14.6667 3.97391 14.5262 3.72386 14.2761C3.47381 14.0261 3.33333 13.687 3.33333 13.3333V4H12.6667Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
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

      <CreateProductModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setSelectedProduct(null);
        }}
        onSuccess={handleProductCreated}
        product={selectedProduct}
        tenantId={tenantId}
      />

      {isFilterOpen && (
        <div className="filter-modal-overlay" onClick={() => setIsFilterOpen(false)}>
          <div className="filter-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="filter-modal-header">
              <h3>Filter Products</h3>
              <button className="filter-close-btn" onClick={() => setIsFilterOpen(false)}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <div className="filter-modal-body">
              <div className="filter-section">
                <label className="filter-label">Date Range</label>
                <div className="filter-range">
                  <input
                    type="date"
                    value={filters.dateFrom}
                    onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                    className="filter-input"
                  />
                  <span className="filter-range-separator">to</span>
                  <input
                    type="date"
                    value={filters.dateTo}
                    onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                    className="filter-input"
                  />
                </div>
              </div>
              <div className="filter-section">
                <label className="filter-label">Category</label>
                <input
                  type="text"
                  placeholder="Filter by category"
                  value={filters.category}
                  onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                  className="filter-input"
                />
              </div>
              <div className="filter-section">
                <label className="filter-label">Price Range</label>
                <div className="filter-range">
                  <input
                    type="number"
                    placeholder="Min"
                    value={filters.minPrice}
                    onChange={(e) => setFilters({ ...filters, minPrice: e.target.value })}
                    className="filter-input"
                  />
                  <span className="filter-range-separator">to</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={filters.maxPrice}
                    onChange={(e) => setFilters({ ...filters, maxPrice: e.target.value })}
                    className="filter-input"
                  />
                </div>
              </div>
              <div className="filter-section">
                <label className="filter-label">Has SKU</label>
                <div className="filter-radio-group">
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasSku"
                      checked={filters.hasSku === null}
                      onChange={() => setFilters({ ...filters, hasSku: null })}
                    />
                    <span>All</span>
                  </label>
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasSku"
                      checked={filters.hasSku === true}
                      onChange={() => setFilters({ ...filters, hasSku: true })}
                    />
                    <span>Yes</span>
                  </label>
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasSku"
                      checked={filters.hasSku === false}
                      onChange={() => setFilters({ ...filters, hasSku: false })}
                    />
                    <span>No</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="filter-modal-footer">
              <button className="filter-btn-reset" onClick={handleFilterReset}>
                Reset
              </button>
              <div className="filter-footer-right">
                <button className="filter-btn-cancel" onClick={() => setIsFilterOpen(false)}>
                  Cancel
                </button>
                <button className="filter-btn-apply" onClick={() => setIsFilterOpen(false)}>
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <DeleteConfirmModal
        isOpen={deleteProductId !== null}
        onClose={() => setDeleteProductId(null)}
        onConfirm={handleDeleteProduct}
        title="Delete Product"
        message="Are you sure you want to delete this product? This action cannot be undone."
        loading={deleting}
      />
    </div>
  );
};

export default ProductsPage;


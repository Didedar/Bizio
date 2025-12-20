import React, { useState, useEffect } from 'react';
import { productsApi } from '../api/client';
import type { Product, DealItemCreate } from '../types';
import './ProductSelectorModal.css';

interface ProductSelectorModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (item: DealItemCreate & { product?: Product }) => void;
    tenantId: number | null | undefined;
}

const ProductSelectorModal: React.FC<ProductSelectorModalProps> = ({ isOpen, onClose, onSelect, tenantId }) => {
    // 1. Hooks (всегда должны быть наверху)
    const [products, setProducts] = useState<Product[]>([]);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [quantity, setQuantity] = useState<string>('1');
    const [unitPrice, setUnitPrice] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        if (isOpen) {
            loadProducts();
            setSelectedProduct(null);
            setQuantity('1');
            setUnitPrice('');
            setError(null);
            setSearchQuery('');
        }
    }, [isOpen]);

    // 2. РАННИЙ ВЫХОД (Early Return)
    // Если окно закрыто, мы ничего не вычисляем и не рендерим.
    // Это защищает от ошибок в логике ниже.
    if (!isOpen) return null;

    // --- Логика выполняется ТОЛЬКО если окно открыто ---

    const loadProducts = async () => {
        if (!tenantId) {
            setError('Tenant ID missing');
            return;
        }
        try {
            setLoading(true);
            const data = await productsApi.list(tenantId, 0, 100);
            // Защита: убедимся, что пришел массив
            setProducts(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error('Failed to load products:', err);
            setError('Failed to load products');
        } finally {
            setLoading(false);
        }
    };

    const handleProductSelect = (product: Product) => {
        setSelectedProduct(product);
        setUnitPrice(product.default_price?.toString() || '');
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProduct) {
            setError('Please select a product');
            return;
        }

        const qty = parseFloat(quantity);
        const price = parseFloat(unitPrice);

        if (isNaN(qty) || qty <= 0) {
            setError('Please enter a valid quantity');
            return;
        }

        if (isNaN(price) || price < 0) {
            setError('Please enter a valid price');
            return;
        }

        const item: DealItemCreate & { product?: Product } = {
            product_id: selectedProduct.id,
            quantity: qty,
            unit_price: price,
            product: selectedProduct,
        };

        onSelect(item);
        onClose(); // Не вызываем loadDeal здесь, это делает родитель
    };

    // ЗАЩИТА ОТ КРАША: Проверяем p.title перед toLowerCase()
    const filteredProducts = products.filter(p => {
        const titleMatch = p.title ? p.title.toLowerCase().includes(searchQuery.toLowerCase()) : false;
        const skuMatch = p.sku ? p.sku.toLowerCase().includes(searchQuery.toLowerCase()) : false;
        return titleMatch || skuMatch;
    });

    // Безопасная математика
    const qtyNum = parseFloat(quantity) || 0;
    const priceNum = parseFloat(unitPrice) || 0;
    const costNum = selectedProduct?.default_cost ? Number(selectedProduct.default_cost) : 0;

    const totalPrice = (qtyNum * priceNum).toFixed(2);
    const estimatedCost = (qtyNum * costNum).toFixed(2);
    const estimatedProfit = (qtyNum * (priceNum - costNum)).toFixed(2);
    const currency = selectedProduct?.currency || 'KZT';

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content product-selector-modal" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="modal-header-simple">
                    <div className="header-title-row">
                        <div className="header-left">
                            <span className="header-label">ADD PRODUCT</span>
                        </div>
                        <button className="btn-text-cancel" onClick={onClose}>cancel</button>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    {error && <div className="error-message">{error}</div>}

                    <div className="modal-scroll-body">
                        {/* Search Section */}
                        <div className="form-section-group">
                            <div className="form-field-row">
                                <label>Search Product</label>
                                <div className="input-wrapper">
                                    <div className="input-with-icon">
                                        <span className="input-icon">🔍</span>
                                        <input
                                            type="text"
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            placeholder="Search by name or SKU..."
                                            className="simple-input pl-8"
                                        // autoFocus // Удобно для пользователя
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Products List */}
                        <div className="form-section-group">
                            <div className="section-header-row">
                                <span className="section-label">SELECT PRODUCT</span>
                            </div>

                            <div className="products-list">
                                {loading ? (
                                    <div className="loading-state">Loading products...</div>
                                ) : filteredProducts.length === 0 ? (
                                    <div className="empty-state">No products found</div>
                                ) : (
                                    filteredProducts.map(product => (
                                        <div
                                            key={product.id}
                                            className={`product-item ${selectedProduct?.id === product.id ? 'selected' : ''}`}
                                            onClick={() => handleProductSelect(product)}
                                        >
                                            <div className="product-info">
                                                <div className="product-name">{product.title || 'No Name'}</div>
                                                {product.sku && <div className="product-sku">SKU: {product.sku}</div>}
                                            </div>
                                            <div className="product-price">
                                                {product.default_price ? `${product.default_price} ${product.currency}` : 'No price'}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Product Details */}
                        {selectedProduct && (
                            <div className="form-section-group">
                                <div className="section-header-row">
                                    <span className="section-label">PRODUCT DETAILS</span>
                                </div>

                                <div className="form-field-row">
                                    <label>Quantity *</label>
                                    <div className="input-wrapper">
                                        <input
                                            type="number"
                                            step="0.01"
                                            min="0.01"
                                            value={quantity}
                                            onChange={(e) => setQuantity(e.target.value)}
                                            className="simple-input"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-field-row">
                                    <label>Unit Price *</label>
                                    <div className="input-wrapper">
                                        <input
                                            type="number"
                                            step="0.01"
                                            min="0"
                                            value={unitPrice}
                                            onChange={(e) => setUnitPrice(e.target.value)}
                                            className="simple-input"
                                            required
                                        />
                                        <span className="price-currency">{currency}</span>
                                    </div>
                                </div>

                                {/* Preview Calculation */}
                                <div className="calculation-preview">
                                    <div className="preview-row">
                                        <span className="preview-label">Total Price:</span>
                                        <span className="preview-value price">{totalPrice} {currency}</span>
                                    </div>

                                    {costNum > 0 && (
                                        <>
                                            <div className="preview-row">
                                                <span className="preview-label">Estimated Cost:</span>
                                                <span className="preview-value cost">{estimatedCost} {currency}</span>
                                            </div>
                                            <div className="preview-row">
                                                <span className="preview-label">Estimated Profit:</span>
                                                <span className={`preview-value profit ${parseFloat(estimatedProfit) >= 0 ? 'positive' : 'negative'}`}>
                                                    {estimatedProfit} {currency}
                                                </span>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="save-actions-row">
                        <button type="button" className="btn-text-cancel" onClick={onClose}>
                            Cancel
                        </button>
                        <button type="submit" className="btn-save-primary" disabled={!selectedProduct}>
                            Add Product
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ProductSelectorModal;
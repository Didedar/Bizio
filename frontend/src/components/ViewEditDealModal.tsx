import React, { useState, useEffect } from 'react';
import { dealsApi, dealItemsApi } from '../api/client';
import type { Deal, DealItemCreate, Product } from '../types';
import { DEAL_STATUSES } from '../types';
import ProductSelectorModal from './ProductSelectorModal';
import DeleteConfirmModal from './DeleteConfirmModal';
import './ViewEditDealModal.css';

interface ViewEditDealModalProps {
  dealId: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  onDelete?: () => void;
}

const ViewEditDealModal: React.FC<ViewEditDealModalProps> = ({ dealId, isOpen, onClose, onSuccess, onDelete }) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deal, setDeal] = useState<Deal | null>(null);
  const [isProductSelectorOpen, setIsProductSelectorOpen] = useState(false);
  const [showDeleteDealConfirm, setShowDeleteDealConfirm] = useState(false);
  const [deleteItemId, setDeleteItemId] = useState<number | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    status: 'new',
    total_price: '',
    total_cost: '',
    currency: 'KZT',
    completion_date: '',
    client_id: 0,
    contact_name: '',
    company_name: '',
    deal_type: 'Sale',
    source: 'Not selected',
    source_details: '',
    start_date: '',
    is_available_to_all: true,
    responsible_id: 0,
    observer_ids: [] as number[],
    comments: '',
    recurring_settings: {
      frequency: 'Not repeat'
    } as Record<string, any>
  });

  useEffect(() => {
    if (isOpen && dealId) {
      loadDeal();
    } else {
      // Сброс состояния при закрытии или отсутствии ID
      setDeal(null);
      setError(null);
    }
  }, [isOpen, dealId]);

  const loadDeal = async () => {
    if (!dealId) return;
    try {
      setLoading(true);
      setError(null); // Сбрасываем ошибку перед загрузкой
      const data = await dealsApi.get(dealId);
      setDeal(data);

      // БЕЗОПАСНАЯ ОБРАБОТКА ДАТЫ
      let safeCompletionDate = '';
      if (data.completion_date) {
        // Проверяем, строка ли это, перед вызовом split
        safeCompletionDate = typeof data.completion_date === 'string'
          ? data.completion_date.split('T')[0]
          : new Date(data.completion_date).toISOString().split('T')[0];
      }

      let safeStartDate = '';
      if (data.start_date) {
        safeStartDate = typeof data.start_date === 'string'
          ? data.start_date.split('T')[0]
          : new Date(data.start_date).toISOString().split('T')[0];
      }

      setFormData({
        title: data.title || '',
        status: data.status || 'new',
        total_price: (data.total_price ?? 0).toString(),
        total_cost: (data.total_cost ?? 0).toString(),
        currency: data.currency || 'KZT',
        completion_date: safeCompletionDate,
        client_id: data.client_id || 0,
        contact_name: data.client?.name || '',
        company_name: data.client?.extra_data?.company_name || '',
        deal_type: data.deal_type || 'Sale',
        source: data.source || 'Not selected',
        source_details: data.source_details || '',
        start_date: safeStartDate,
        is_available_to_all: data.is_available_to_all ?? true,
        responsible_id: data.responsible_id || 0,
        // БЕЗОПАСНЫЙ MAPPING (фильтруем null)
        observer_ids: Array.isArray(data.observers) ? data.observers.filter(u => u).map(u => u.id) : [],
        comments: data.comments || '',
        recurring_settings: data.recurring_settings || { frequency: 'Not repeat' }
      });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to load deal');
    } finally {
      setLoading(false);
    }
  };



  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // ... (handleDelete и handleSave без изменений, они выглядят нормально) ...
  const handleSave = async () => {
    if (!dealId) return;
    try {
      setSaving(true);
      setError(null);

      const updateData: any = {
        title: formData.title,
        status: formData.status,
        currency: formData.currency,
        completion_date: formData.completion_date ? new Date(formData.completion_date).toISOString() : undefined,
        client_id: formData.client_id,
        deal_type: formData.deal_type,
        source: formData.source,
        source_details: formData.source_details,
        start_date: formData.start_date ? new Date(formData.start_date).toISOString() : undefined,
        is_available_to_all: formData.is_available_to_all,
        responsible_id: formData.responsible_id,
        comments: formData.comments,
        recurring_settings: formData.recurring_settings,
      };

      if (!deal?.items || deal.items.length === 0) {
        updateData.total_price = parseFloat(formData.total_price) || 0;
        updateData.total_cost = parseFloat(formData.total_cost) || 0;
      }

      await dealsApi.update(dealId, updateData);
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to update deal');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!dealId) return;
    try {
      setSaving(true);
      await dealsApi.delete(dealId);
      setShowDeleteDealConfirm(false);
      if (onDelete) onDelete();
      else {
        onSuccess();
        onClose();
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to delete deal');
    } finally {
      setSaving(false);
    }
  };

  const handleAddProduct = async (item: DealItemCreate & { product?: Product }) => {
    if (!dealId) return;

    try {
      setSaving(true);
      setError(null);

      await dealItemsApi.add(dealId, [{
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price,
        unit_cost: item.unit_cost,
      }]);

      await loadDeal();
      setIsProductSelectorOpen(false);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to add product');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveProduct = async () => {
    if (!dealId || deleteItemId === null) return;

    try {
      setSaving(true);
      setError(null);

      await dealItemsApi.remove(dealId, deleteItemId);
      setDeleteItemId(null);
      await loadDeal();
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to remove product');
    } finally {
      setSaving(false);
    }
  };


  if (!isOpen) return null;

  // БЕЗОПАСНАЯ АРИФМЕТИКА
  const hasItems = Array.isArray(deal?.items) && deal.items.length > 0;

  // Calculate display numbers based on mode (items vs manual)
  const displayTotalPrice = hasItems
    ? Number(deal?.total_price ?? 0)
    : parseFloat(formData.total_price || '0');

  const displayTotalCost = hasItems
    ? Number(deal?.total_cost ?? 0)
    : parseFloat(formData.total_cost || '0');

  const displayMargin = hasItems
    ? Number(deal?.margin ?? 0)
    : (displayTotalPrice - displayTotalCost);

  const marginPercent = displayTotalPrice > 0
    ? ((displayMargin / displayTotalPrice) * 100).toFixed(2)
    : '0.00';

  return (
    <>
      <div className="view-edit-modal-overlay" onClick={onClose}>
        <div className="view-edit-modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header-simple">
            <div className="header-title-row">
              <div className="header-left">
                <span className="header-label">ABOUT DEAL</span>
                {/* Кнопка Edit была без действия */}
                <button className="icon-btn-small" title="Edit">
                  <span style={{ fontSize: '16px' }}>✎</span>
                </button>
              </div>
              <button className="btn-text-cancel" onClick={onClose}>cancel</button>
            </div>
          </div>

          {error && (
            <div className="error-banner" style={{ margin: '0 24px 16px', padding: '12px', backgroundColor: '#FEE2E2', color: '#DC2626', borderRadius: '6px', fontSize: '14px' }}>
              {error}
            </div>
          )}

          {loading ? (
            <div style={{ padding: '48px 24px', textAlign: 'center', color: '#6b7280' }}>
              <div>Loading deal...</div>
            </div>
          ) : !deal ? (
            <div style={{ padding: '48px 24px', textAlign: 'center', color: '#6b7280' }}>
              {/* Если ошибка загрузки, показываем сообщение, а не пустой экран */}
              {!error && <div>No deal data available</div>}
            </div>
          ) : (
            <div className="modal-scroll-body">
              {/* Margin Section */}
              <div className="form-section-group margin-section">
                <div className="section-header-row">
                  <span className="section-label">FINANCIALS</span>
                </div>

                <div className="margin-display">
                  <div className="margin-item">
                    <span className="margin-label">Total Price</span>
                    <span className="margin-value price">{displayTotalPrice.toFixed(2)} {deal.currency ?? 'KZT'}</span>
                  </div>
                  <div className="margin-item">
                    <span className="margin-label">Total Cost</span>
                    <span className="margin-value cost">{displayTotalCost.toFixed(2)} {deal.currency ?? 'KZT'}</span>
                  </div>
                  <div className="margin-item highlight">
                    <span className="margin-label">Margin</span>
                    <div className="margin-value-group">
                      <span className={`margin-value margin ${displayMargin >= 0 ? 'positive' : 'negative'}`}>
                        {displayMargin.toFixed(2)} {deal.currency ?? 'KZT'}
                      </span>
                      <span className="margin-percent">{marginPercent}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ... (Остальная часть формы остается прежней) ... */}

              <div className="form-section-group">
                {/* ... About Deal Fields ... */}
                <div className="form-field-row">
                  <label>Name</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      placeholder="Deal #"
                      className="simple-input"
                    />
                  </div>
                </div>
                {/* Остальные поля формы... Вставляю сокращенно для читаемости */}
                <div className="form-field-row">
                  <label>Stage</label>
                  <div className="input-wrapper">
                    <select
                      value={formData.status}
                      onChange={(e) => handleInputChange('status', e.target.value)}
                      className="simple-select"
                    >
                      {DEAL_STATUSES.map(status => (
                        <option key={status.value} value={status.value}>{status.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {!hasItems && (
                  <>
                    <div className="form-field-row">
                      <label>Amount</label>
                      <div className="input-group-row">
                        <input
                          type="number"
                          value={formData.total_price}
                          onChange={(e) => handleInputChange('total_price', e.target.value)}
                          className="simple-input flex-grow"
                          placeholder="0.00"
                        />
                        <select
                          value={formData.currency}
                          onChange={(e) => handleInputChange('currency', e.target.value)}
                          className="simple-select width-auto"
                        >
                          <option value="KZT">Tenge</option>
                          <option value="USD">USD</option>
                          <option value="EUR">EUR</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-field-row">
                      <label>Total Cost</label>
                      <div className="input-wrapper">
                        <input
                          type="number"
                          value={formData.total_cost}
                          onChange={(e) => handleInputChange('total_cost', e.target.value)}
                          className="simple-input"
                          placeholder="0.00"
                        />
                        <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                      </div>
                    </div>
                  </>
                )}

                <div className="form-field-row">
                  <label>Completion Date</label>
                  <div className="input-wrapper">
                    <input
                      type="date"
                      value={formData.completion_date}
                      onChange={(e) => handleInputChange('completion_date', e.target.value)}
                      className="simple-input"
                    />
                  </div>
                </div>
              </div>


              {/* Client Section */}
              <div className="form-section-group">
                <div className="section-header-row"><span className="section-label">CLIENT</span></div>

                <div className="form-field-row">
                  <label>Contact</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      value={formData.contact_name}
                      className="simple-input"
                      disabled
                    />
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                <div className="form-field-row">
                  <label>Company</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      value={formData.company_name}
                      placeholder="Company name"
                      className="simple-input"
                      disabled
                    />
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>
              </div>

              {/* PRODUCTS SECTION */}
              <div className="form-section-group">
                <div className="section-header-row">
                  <span className="section-label">PRODUCTS</span>
                </div>

                {hasItems ? (
                  <div className="products-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>SKU</th>
                          <th>Qty</th>
                          <th>Unit Price</th>
                          <th>Unit Cost</th>
                          <th style={{ width: '60px' }}>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(deal?.items || []).map((item) => (
                          <tr key={item.id}>
                            <td>{item.product?.title || `Product #${item.product_id}`}</td>
                            <td>{item.product?.sku || '-'}</td>
                            <td>{item.quantity}</td>
                            <td>{item.unit_price} {deal?.currency ?? 'KZT'}</td>
                            <td>{item.unit_cost} {deal?.currency ?? 'KZT'}</td>
                            <td>
                              <button
                                type="button"
                                className="btn-remove-item"
                                onClick={() => setDeleteItemId(item.id)}
                                disabled={saving}
                                title="Remove product"
                              >
                                ✕
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-products"><p>No products added yet</p></div>
                )}
                <div className="form-field-row">
                  <button className="btn-add-product" type="button" onClick={() => setIsProductSelectorOpen(true)} disabled={saving}>
                    + add product
                  </button>
                </div>
              </div>

              {/* Additional Section */}
              <div className="form-section-group">
                <div className="section-header-row"><span className="section-label">ADDITIONAL</span></div>

                <div className="form-field-row">
                  <label>Deal Type</label>
                  <div className="input-wrapper">
                    <select
                      value={formData.deal_type}
                      onChange={(e) => handleInputChange('deal_type', e.target.value)}
                      className="simple-select"
                    >
                      <option value="Sale">Sale</option>
                      <option value="Service">Service</option>
                    </select>
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                <div className="form-field-row">
                  <label>Source</label>
                  <div className="input-wrapper">
                    <select
                      value={formData.source}
                      onChange={(e) => handleInputChange('source', e.target.value)}
                      className="simple-select"
                    >
                      <option value="Not selected">Not selected</option>
                      <option value="Website">Website</option>
                      <option value="Referral">Referral</option>
                    </select>
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                <div className="form-field-row">
                  <label>Source Details</label>
                  <div className="input-wrapper">
                    <textarea
                      value={formData.source_details}
                      onChange={(e) => handleInputChange('source_details', e.target.value)}
                      className="simple-textarea"
                      rows={3}
                      placeholder="Additional source information..."
                    />
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                <div className="form-field-row">
                  <label>Start Date</label>
                  <div className="input-wrapper">
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => handleInputChange('start_date', e.target.value)}
                      className="simple-input"
                    />
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                <div className="form-field-row checkbox-row">
                  <input
                    type="checkbox"
                    checked={formData.is_available_to_all}
                    onChange={(e) => handleInputChange('is_available_to_all', e.target.checked)}
                    id="available-all"
                  />
                  <label htmlFor="available-all">Available to all</label>
                  <button type="button" className="icon-btn-input ml-auto"><span className="icon-settings">⚙️</span></button>
                </div>

                <div className="form-field-row">
                  <label>Comment</label>
                  <div className="input-wrapper">
                    <textarea
                      value={formData.comments}
                      onChange={(e) => handleInputChange('comments', e.target.value)}
                      className="simple-textarea"
                      placeholder="Write a comment..."
                      rows={3}
                    />
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="modal-footer-actions">
                <button className="btn-link-danger ml-auto" onClick={() => setShowDeleteDealConfirm(true)} type="button">Delete deal</button>
              </div>
              <div className="save-actions-row">
                <button className="btn-save-primary" onClick={handleSave} disabled={saving} type="button">
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>

            </div>
          )}
        </div>
      </div >

      {/* Product Selector Modal - Убедитесь что он существует и не вызывает ошибок */}
      {
        isProductSelectorOpen && (
          <ProductSelectorModal
            isOpen={isProductSelectorOpen}
            onClose={() => setIsProductSelectorOpen(false)}
            onSelect={handleAddProduct}
            tenantId={deal?.tenant_id}
          />
        )
      }

      <DeleteConfirmModal
        isOpen={showDeleteDealConfirm}
        onClose={() => setShowDeleteDealConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Deal"
        message="Are you sure you want to delete this deal? This action cannot be undone."
        loading={saving}
      />

      <DeleteConfirmModal
        isOpen={deleteItemId !== null}
        onClose={() => setDeleteItemId(null)}
        onConfirm={handleRemoveProduct}
        title="Remove Product"
        message="Are you sure you want to remove this product from the deal?"
        loading={saving}
      />
    </>
  );
};

export default ViewEditDealModal;
import React, { useState, useEffect } from 'react';
import { dealsApi, clientsApi } from '../api/client';
import type { Client, DealItemCreate, Product } from '../types';
import { DEAL_STATUSES } from '../types';
import ProductSelectorModal from './ProductSelectorModal';
import './CreateDealModal.css';

interface CreateDealModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  tenantId: number | null;  // Added
}

interface FormData {
  dealTitle: string;
  clientName: string;
  clientCompany: string;
  clientEmail: string;
  clientPhone: string;
  clientId: number | null;
  totalPrice: string;
  totalCost: string;
  currency: string;
  status: string;
  completion_date: string;
  start_date: string;
  deal_type: string;
  source: string;
  source_details: string;
  is_available_to_all: boolean;
  responsible_id: number;
  comments: string;
  isRecurring: boolean;
  recurringFrequency: string;
  recurringInterval: number;
  recurringEndDate: string;
  observerIds: number[];
}

const initialFormData: FormData = {
  dealTitle: '',
  clientName: '',
  clientCompany: '',
  clientEmail: '',
  clientPhone: '',
  clientId: null,
  totalPrice: '',
  totalCost: '',
  currency: 'KZT',
  status: 'new',
  completion_date: '',
  start_date: '',
  deal_type: 'Sale',
  source: 'Not selected',
  source_details: '',
  is_available_to_all: true,
  responsible_id: 0,
  comments: '',
  isRecurring: false,
  recurringFrequency: 'monthly',
  recurringInterval: 1,
  recurringEndDate: '',
  observerIds: [],
};

const CreateDealModal: React.FC<CreateDealModalProps> = ({ isOpen, onClose, onSuccess, tenantId }) => {
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isNewClient, setIsNewClient] = useState(false);

  // Products state
  const [items, setItems] = useState<(DealItemCreate & { product?: Product })[]>([]);
  const [isProductSelectorOpen, setIsProductSelectorOpen] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadClients();
      setFormData(initialFormData);
      setError(null);
      setIsNewClient(false);
      setItems([]);
    }
  }, [isOpen]);

  const loadClients = async () => {
    if (!tenantId) return;
    try {
      const data = await clientsApi.list(tenantId);
      setClients(data);
    } catch (err) {
      console.error('Failed to load clients:', err);
    }
  };



  const handleInputChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAddProduct = (item: DealItemCreate & { product?: Product }) => {
    setItems(prev => [...prev, item]);
    recalculateTotals([...items, item]);
  };

  const handleRemoveProduct = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
    recalculateTotals(newItems);
  };

  const recalculateTotals = (currentItems: (DealItemCreate & { product?: Product })[]) => {
    if (currentItems.length > 0) {
      const totalPrice = currentItems.reduce((sum, item) =>
        sum + (item.quantity * (item.unit_price || 0)), 0
      );
      const totalCost = currentItems.reduce((sum, item) => {
        const cost = item.unit_cost || item.product?.default_cost || 0;
        return sum + (item.quantity * cost);
      }, 0);

      setFormData(prev => ({
        ...prev,
        totalPrice: totalPrice.toFixed(2),
        totalCost: totalCost.toFixed(2),
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let finalClientId = formData.clientId;

      if (isNewClient && !finalClientId) {
        if (!tenantId) throw new Error('Tenant ID is required');
        const newClient = await clientsApi.create(tenantId, {
          name: formData.clientName,
          company: formData.clientCompany,
          email: formData.clientEmail,
          phone: formData.clientPhone,
        });
        finalClientId = newClient.id;
      }

      if (!finalClientId) {
        throw new Error('Please select or create a client');
      }

      const dealData: any = {
        client_id: finalClientId,
        title: formData.dealTitle,
        status: formData.status,
        currency: formData.currency,
        completion_date: formData.completion_date ? new Date(formData.completion_date).toISOString() : undefined,
        start_date: formData.start_date ? new Date(formData.start_date).toISOString() : undefined,
        source: formData.source,
        source_details: formData.source_details,
        deal_type: formData.deal_type,
        is_available_to_all: formData.is_available_to_all,
        responsible_id: formData.responsible_id || undefined,
        comments: formData.comments,
        recurring_settings: formData.isRecurring ? {
          frequency: formData.recurringFrequency,
          interval: formData.recurringInterval,
          end_date: formData.recurringEndDate,
        } : undefined,
        observer_ids: formData.observerIds,
      };

      // Add items or manual totals
      if (items.length > 0) {
        dealData.items = items.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          unit_cost: item.unit_cost,
        }));
      } else {
        dealData.total_price = parseFloat(formData.totalPrice) || 0;
        dealData.total_cost = parseFloat(formData.totalCost) || 0;
      }

      if (!tenantId) throw new Error('Tenant ID is required');
      await dealsApi.create(tenantId, dealData);

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create deal');
    } finally {
      setLoading(false);
    }
  };

  const hasItems = items.length > 0;
  const calculatedMargin = hasItems
    ? (parseFloat(formData.totalPrice) - parseFloat(formData.totalCost)).toFixed(2)
    : '0.00';

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content create-deal-modal" onClick={e => e.stopPropagation()}>
          {/* Header */}
          <div className="modal-header-simple">
            <div className="header-title-row">
              <div className="header-left">
                <span className="header-label">CREATE NEW DEAL</span>
                <button className="icon-btn-small" title="Info">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M10 2L2 10M2 10H4M2 10V8" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
              <button className="btn-text-cancel" onClick={onClose}>cancel</button>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}

            <div className="modal-scroll-body">
              {/* About Deal Section */}
              <div className="form-section-group">
                <div className="form-field-row">
                  <label>Name</label>
                  <div className="input-wrapper">
                    <input
                      type="text"
                      value={formData.dealTitle}
                      onChange={(e) => handleInputChange('dealTitle', e.target.value)}
                      placeholder="Deal #"
                      className="simple-input"
                      required
                    />
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                <div className="form-field-row">
                  <label>Stage</label>
                  <div className="input-wrapper">
                    <select
                      value={formData.status}
                      onChange={(e) => handleInputChange('status', e.target.value)}
                      className="simple-select"
                      required
                    >
                      {DEAL_STATUSES.map(status => (
                        <option key={status.value} value={status.value}>{status.label}</option>
                      ))}
                    </select>
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                {!hasItems && (
                  <>
                    <div className="form-field-row">
                      <label>Amount and Currency</label>
                      <div className="input-group-row">
                        <input
                          type="number"
                          step="0.01"
                          value={formData.totalPrice}
                          onChange={(e) => handleInputChange('totalPrice', e.target.value)}
                          className="simple-input flex-grow"
                          placeholder="0.00"
                          required={!hasItems}
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
                        <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                      </div>
                    </div>

                    <div className="form-field-row">
                      <label>Total Cost</label>
                      <div className="input-wrapper">
                        <input
                          type="number"
                          step="0.01"
                          value={formData.totalCost}
                          onChange={(e) => handleInputChange('totalCost', e.target.value)}
                          placeholder="0.00"
                          className="simple-input"
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
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>
              </div>

              {/* Products Section */}
              <div className="form-section-group">
                <div className="section-header-row">
                  <span className="section-label">PRODUCTS</span>
                </div>

                {items.length > 0 ? (
                  <div className="products-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>Qty</th>
                          <th>Price</th>
                          <th>Total</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item, index) => (
                          <tr key={index}>
                            <td>{item.product?.title || `Product #${item.product_id}`}</td>
                            <td>{item.quantity}</td>
                            <td>{item.unit_price} {formData.currency}</td>
                            <td>{(item.quantity * (item.unit_price || 0)).toFixed(2)} {formData.currency}</td>
                            <td>
                              <button
                                type="button"
                                className="btn-remove-item"
                                onClick={() => handleRemoveProduct(index)}
                              >
                                ✕
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    <div className="totals-summary">
                      <div className="total-row">
                        <span>Total Price:</span>
                        <span className="total-value price">{formData.totalPrice} {formData.currency}</span>
                      </div>
                      <div className="total-row">
                        <span>Total Cost:</span>
                        <span className="total-value cost">{formData.totalCost} {formData.currency}</span>
                      </div>
                      <div className="total-row">
                        <span>Margin:</span>
                        <span className={`total-value margin ${parseFloat(calculatedMargin) >= 0 ? 'positive' : 'negative'}`}>
                          {calculatedMargin} {formData.currency}
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="empty-products">
                    <p>No products added yet</p>
                  </div>
                )}

                <button
                  type="button"
                  className="btn-add-product"
                  onClick={() => setIsProductSelectorOpen(true)}
                >
                  + add product
                </button>
              </div>

              {/* Client Section */}
              <div className="form-section-group">
                <div className="section-header-row">
                  <span className="section-label">CLIENT</span>
                </div>

                <div className="form-field-row">
                  <label>Contact</label>
                  <div className="input-wrapper">
                    {isNewClient ? (
                      <div className="input-with-icon">
                        <span className="input-icon">👤</span>
                        <input
                          type="text"
                          value={formData.clientName}
                          onChange={(e) => handleInputChange('clientName', e.target.value)}
                          placeholder="New Client Name"
                          className="simple-input pl-8"
                          required
                        />
                      </div>
                    ) : (
                      <div className="input-with-icon">
                        <span className="input-icon">👤</span>
                        <select
                          value={formData.clientId || ''}
                          onChange={(e) => handleInputChange('clientId', parseInt(e.target.value))}
                          className="simple-input pl-8"
                          required
                        >
                          <option value="">Select Client</option>
                          {clients.map(client => (
                            <option key={client.id} value={client.id}>{client.name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    <button
                      type="button"
                      className="btn-text-small"
                      onClick={() => {
                        setIsNewClient(!isNewClient);
                        handleInputChange('clientId', null);
                        handleInputChange('clientName', '');
                        handleInputChange('clientCompany', '');
                      }}
                    >
                      {isNewClient ? 'select existing' : 'create new'}
                    </button>
                    <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                  </div>
                </div>

                {isNewClient && (
                  <>
                    <div className="form-field-row">
                      <label>Company</label>
                      <div className="input-wrapper">
                        <input
                          type="text"
                          value={formData.clientCompany}
                          onChange={(e) => handleInputChange('clientCompany', e.target.value)}
                          placeholder="Company name"
                          className="simple-input"
                        />
                        <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                      </div>
                    </div>

                    <div className="form-field-row">
                      <label>Email</label>
                      <div className="input-wrapper">
                        <input
                          type="email"
                          value={formData.clientEmail}
                          onChange={(e) => handleInputChange('clientEmail', e.target.value)}
                          placeholder="client@example.com"
                          className="simple-input"
                        />
                        <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                      </div>
                    </div>

                    <div className="form-field-row">
                      <label>Phone</label>
                      <div className="input-wrapper">
                        <input
                          type="tel"
                          value={formData.clientPhone}
                          onChange={(e) => handleInputChange('clientPhone', e.target.value)}
                          placeholder="+7 (___) ___-__-__"
                          className="simple-input"
                        />
                        <button type="button" className="icon-btn-input"><span className="icon-settings">⚙️</span></button>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Additional Section */}
              <div className="form-section-group">
                <div className="section-header-row">
                  <span className="section-label">ADDITIONAL</span>
                </div>

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
            </div>

            {/* Footer */}
            <div className="save-actions-row">
              <button type="button" className="btn-text-cancel" onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button type="submit" className="btn-save-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Deal'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Product Selector Modal */}
      <ProductSelectorModal
        isOpen={isProductSelectorOpen}
        onClose={() => setIsProductSelectorOpen(false)}
        onSelect={handleAddProduct}
        tenantId={tenantId}
      />
    </>
  );
};

export default CreateDealModal;

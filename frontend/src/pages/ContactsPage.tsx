import React, { useState, useEffect, useMemo } from 'react';
import { clientsApi } from '../api/client';
import type { Client, ClientCreate } from '../types';
import SortDropdown, { SortOption } from '../components/SortDropdown';
import ColumnsDropdown, { ColumnConfig } from '../components/ColumnsDropdown';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import { useAuth } from '../contexts/AuthContext';
import './ContactsPage.css';

interface CreateContactModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  contact?: Client | null;
  tenantId: number | null;
}

const CreateContactModal: React.FC<CreateContactModalProps> = ({ isOpen, onClose, onSuccess, contact, tenantId }) => {
  const [formData, setFormData] = useState<ClientCreate>({
    name: '',
    email: '',
    phone: '',
    address: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (contact) {
      setFormData({
        name: contact.name || '',
        email: contact.email || '',
        phone: contact.phone || '',
        address: contact.address || '',
      });
    } else {
      setFormData({
        name: '',
        email: '',
        phone: '',
        address: '',
      });
    }
  }, [contact, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (contact) {
        await clientsApi.update(contact.id, formData);
      } else {
        if (!tenantId) throw new Error('Tenant ID is required');
        await clientsApi.create(tenantId, formData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save contact');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{contact ? 'Edit Contact' : 'New Contact'}</h2>
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
            <label>Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={formData.email || ''}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Phone</label>
            <input
              type="tel"
              value={formData.phone || ''}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Address</label>
            <textarea
              value={formData.address || ''}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              rows={3}
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving...' : contact ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface ContactFilterOptions {
  dateFrom: string;
  dateTo: string;
  hasEmail: boolean | null;
  hasPhone: boolean | null;
}

const ContactsPage: React.FC = () => {
  const { tenantId } = useAuth();
  const [contacts, setContacts] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedContact, setSelectedContact] = useState<Client | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [deleteContactId, setDeleteContactId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [filters, setFilters] = useState<ContactFilterOptions>({
    dateFrom: '',
    dateTo: '',
    hasEmail: null,
    hasPhone: null,
  });
  const [sortOption, setSortOption] = useState<SortOption>({
    field: 'created_at',
    direction: 'desc',
  });
  const [columns, setColumns] = useState<ColumnConfig[]>([
    { id: 'name', label: 'Name', visible: true },
    { id: 'email', label: 'Email', visible: true },
    { id: 'phone', label: 'Phone', visible: true },
    { id: 'address', label: 'Address', visible: true },
    { id: 'created', label: 'Created', visible: true },
  ]);

  useEffect(() => {
    if (tenantId) {
      loadContacts();
    }
  }, [tenantId]);

  const loadContacts = async () => {
    if (!tenantId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await clientsApi.list(tenantId);
      setContacts(data);
    } catch (error) {
      console.error('Failed to load contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleContactCreated = () => {
    setIsCreateModalOpen(false);
    setSelectedContact(null);
    loadContacts();
  };

  const handleEditContact = (contact: Client) => {
    setSelectedContact(contact);
    setIsCreateModalOpen(true);
  };

  const handleDeleteContact = async () => {
    if (deleteContactId === null) return;
    try {
      setDeleting(true);
      await clientsApi.delete(deleteContactId);
      setDeleteContactId(null);
      loadContacts();
    } catch (error) {
      console.error('Failed to delete contact:', error);
      setError('Failed to delete contact');
    } finally {
      setDeleting(false);
    }
  };

  const filteredContacts = useMemo(() => {
    let result = [...contacts];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(contact =>
        contact.name.toLowerCase().includes(query) ||
        contact.email?.toLowerCase().includes(query) ||
        contact.phone?.toLowerCase().includes(query)
      );
    }

    // Date filter
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      result = result.filter(contact => new Date(contact.created_at) >= fromDate);
    }
    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59, 999);
      result = result.filter(contact => new Date(contact.created_at) <= toDate);
    }

    // Email filter
    if (filters.hasEmail !== null) {
      result = result.filter(contact =>
        filters.hasEmail ? !!contact.email : !contact.email
      );
    }

    // Phone filter
    if (filters.hasPhone !== null) {
      result = result.filter(contact =>
        filters.hasPhone ? !!contact.phone : !contact.phone
      );
    }

    return result;
  }, [contacts, searchQuery, filters]);

  // Apply sorting
  const sortedContacts = useMemo(() => {
    const result = [...filteredContacts];

    result.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortOption.field) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'email':
          aValue = (a.email || '').toLowerCase();
          bValue = (b.email || '').toLowerCase();
          break;
        case 'phone':
          aValue = (a.phone || '').toLowerCase();
          bValue = (b.phone || '').toLowerCase();
          break;
        case 'created_at':
        default:
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
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
  }, [filteredContacts, sortOption]);

  const hasActiveFilters =
    filters.dateFrom !== '' ||
    filters.dateTo !== '' ||
    filters.hasEmail !== null ||
    filters.hasPhone !== null;

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.dateFrom) count++;
    if (filters.dateTo) count++;
    if (filters.hasEmail !== null) count++;
    if (filters.hasPhone !== null) count++;
    return count;
  };



  const handleFilterReset = () => {
    const emptyFilters: ContactFilterOptions = {
      dateFrom: '',
      dateTo: '',
      hasEmail: null,
      hasPhone: null,
    };
    setFilters(emptyFilters);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="contacts-page">
      <div className="contacts-header">
        <div className="contacts-header-content">
          <div className="contacts-title-section">
            <h1 className="contacts-title">Contacts</h1>
            {sortedContacts.length > 0 && (
              <span className="contacts-count">{sortedContacts.length} {sortedContacts.length === 1 ? 'contact' : 'contacts'}</span>
            )}
          </div>
          <button className="btn-create-contact" onClick={() => {
            setSelectedContact(null);
            setIsCreateModalOpen(true);
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            Create Contact
          </button>
        </div>
      </div>

      <div className="contacts-toolbar">
        <div className="toolbar-left">
          <div className="search-wrapper">
            <svg className="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M7.33333 12.6667C10.2789 12.6667 12.6667 10.2789 12.6667 7.33333C12.6667 4.38781 10.2789 2 7.33333 2C4.38781 2 2 4.38781 2 7.33333C2 10.2789 4.38781 12.6667 7.33333 12.6667Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M14 14L11.1 11.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <input
              type="text"
              placeholder="Search contacts..."
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
            onClick={loadContacts}
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
              { field: 'name', label: 'Name' },
              { field: 'email', label: 'Email' },
              { field: 'phone', label: 'Phone' },
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

      <div className="contacts-content">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading contacts...</p>
          </div>
        ) : error ? null : sortedContacts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-content">
              <div className="empty-state-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <path d="M32 8C18.745 8 8 18.745 8 32C8 45.255 18.745 56 32 56C45.255 56 56 45.255 56 32C56 18.745 45.255 8 32 8ZM36 24C36 26.2091 34.2091 28 32 28C29.7909 28 28 26.2091 28 24C28 21.7909 29.7909 20 32 20C34.2091 20 36 21.7909 36 24ZM28 36H36V44H28V36ZM36 44V36H44V44H36Z" fill="currentColor" fillOpacity="0.1" />
                  <path d="M32 22C33.1046 22 34 22.8954 34 24C34 25.1046 33.1046 26 32 26C30.8954 26 30 25.1046 30 24C30 22.8954 30.8954 22 32 22ZM28 34H36V42H28V34ZM38 34H46V42H38V34Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <h2>No Contacts Found</h2>
              <p className="empty-state-description">
                {hasActiveFilters || searchQuery
                  ? 'Try adjusting your filters or search query to see more results.'
                  : 'Get started by creating your first contact.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="contacts-table-container">
            <table className="contacts-table">
              <thead>
                <tr>
                  {columns.find(col => col.id === 'name')?.visible && <th>Name</th>}
                  {columns.find(col => col.id === 'email')?.visible && <th>Email</th>}
                  {columns.find(col => col.id === 'phone')?.visible && <th>Phone</th>}
                  {columns.find(col => col.id === 'address')?.visible && <th>Address</th>}
                  {columns.find(col => col.id === 'created')?.visible && <th>Created</th>}
                  <th className="actions-column">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedContacts.map((contact) => (
                  <tr key={contact.id}>
                    {columns.find(col => col.id === 'name')?.visible && (
                      <td>
                        <div className="contact-name">{contact.name}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'email')?.visible && (
                      <td>
                        <div className="contact-email">{contact.email || '—'}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'phone')?.visible && (
                      <td>
                        <div className="contact-phone">{contact.phone || '—'}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'address')?.visible && (
                      <td>
                        <div className="contact-address">{contact.address || '—'}</div>
                      </td>
                    )}
                    {columns.find(col => col.id === 'created')?.visible && (
                      <td>
                        <div className="contact-date">{formatDate(contact.created_at)}</div>
                      </td>
                    )}
                    <td className="actions-column">
                      <div className="table-actions">
                        <button
                          className="action-btn action-btn-view"
                          onClick={() => handleEditContact(contact)}
                          title="Edit"
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M11.3333 2.00001C11.5084 1.82491 11.7163 1.686 11.9451 1.59128C12.1739 1.49657 12.4189 1.44775 12.6667 1.44775C12.9144 1.44775 13.1594 1.49657 13.3882 1.59128C13.617 1.686 13.8249 1.82491 14 2.00001C14.1751 2.1751 14.314 2.383 14.4087 2.6118C14.5034 2.8406 14.5522 3.08564 14.5522 3.33334C14.5522 3.58104 14.5034 3.82608 14.4087 4.05486C14.314 4.28364 14.1751 4.49154 14 4.66668L5.00001 13.6667L1.33334 14.6667L2.33334 11L11.3333 2.00001Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>
                        <button
                          className="action-btn action-btn-delete"
                          onClick={() => setDeleteContactId(contact.id)}
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

      <CreateContactModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setSelectedContact(null);
        }}
        onSuccess={handleContactCreated}
        contact={selectedContact}
        tenantId={tenantId}
      />

      {isFilterOpen && (
        <div className="filter-modal-overlay" onClick={() => setIsFilterOpen(false)}>
          <div className="filter-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="filter-modal-header">
              <h3>Filter Contacts</h3>
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
                <label className="filter-label">Has Email</label>
                <div className="filter-radio-group">
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasEmail"
                      checked={filters.hasEmail === null}
                      onChange={() => setFilters({ ...filters, hasEmail: null })}
                    />
                    <span>All</span>
                  </label>
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasEmail"
                      checked={filters.hasEmail === true}
                      onChange={() => setFilters({ ...filters, hasEmail: true })}
                    />
                    <span>Yes</span>
                  </label>
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasEmail"
                      checked={filters.hasEmail === false}
                      onChange={() => setFilters({ ...filters, hasEmail: false })}
                    />
                    <span>No</span>
                  </label>
                </div>
              </div>
              <div className="filter-section">
                <label className="filter-label">Has Phone</label>
                <div className="filter-radio-group">
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasPhone"
                      checked={filters.hasPhone === null}
                      onChange={() => setFilters({ ...filters, hasPhone: null })}
                    />
                    <span>All</span>
                  </label>
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasPhone"
                      checked={filters.hasPhone === true}
                      onChange={() => setFilters({ ...filters, hasPhone: true })}
                    />
                    <span>Yes</span>
                  </label>
                  <label className="filter-radio-label">
                    <input
                      type="radio"
                      name="hasPhone"
                      checked={filters.hasPhone === false}
                      onChange={() => setFilters({ ...filters, hasPhone: false })}
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
        isOpen={deleteContactId !== null}
        onClose={() => setDeleteContactId(null)}
        onConfirm={handleDeleteContact}
        title="Delete Contact"
        message="Are you sure you want to delete this contact? This action cannot be undone."
        loading={deleting}
      />
    </div>
  );
};

export default ContactsPage;


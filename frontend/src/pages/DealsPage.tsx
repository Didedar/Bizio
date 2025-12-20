import React, { useState, useEffect, useMemo } from 'react';
import { dealsApi } from '../api/client';
import type { Deal } from '../types';
import { DEAL_STATUSES } from '../types';
import CreateDealModal from '../components/CreateDealModal';
import ViewEditDealModal from '../components/ViewEditDealModal';
import DealsKanban from '../components/DealsKanban';
import FilterModal, { FilterOptions } from '../components/FilterModal';
import SortDropdown, { SortOption } from '../components/SortDropdown';
import ColumnsDropdown, { ColumnConfig } from '../components/ColumnsDropdown';
import { useDealModal } from '../contexts/DealModalContext';
import { useAuth } from '../contexts/AuthContext';
import './DealsPage.css';

const DealsPage: React.FC = () => {
  const { tenantId } = useAuth();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const { isCreateModalOpen, openCreateModal, closeCreateModal } = useDealModal();
  const [isViewEditModalOpen, setIsViewEditModalOpen] = useState(false);
  const [selectedDealId, setSelectedDealId] = useState<number | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({
    statuses: [],
    minAmount: '',
    maxAmount: '',
    dateFrom: '',
    dateTo: '',
    clientName: '',
  });
  const [sortOption, setSortOption] = useState<SortOption>({
    field: 'created_at',
    direction: 'desc',
  });
  const [columns, setColumns] = useState<ColumnConfig[]>([
    { id: 'title', label: 'Deal Name', visible: true },
    { id: 'client', label: 'Client', visible: true },
    { id: 'status', label: 'Status', visible: true },
    { id: 'amount', label: 'Amount', visible: true },
    { id: 'created', label: 'Created', visible: true },
  ]);
  const [viewMode] = useState<'table' | 'kanban'>('kanban');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tenantId) {
      loadDeals();
    }
  }, [tenantId]);

  const loadDeals = async () => {
    if (!tenantId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await dealsApi.list(tenantId);
      setDeals(data);
    } catch (error) {
      console.error('Failed to load deals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDealCreated = () => {
    closeCreateModal();
    loadDeals();
  };

  const handleViewDeal = (dealId: number) => {
    setSelectedDealId(dealId);
    setIsViewEditModalOpen(true);
  };

  const handleDealUpdated = () => {
    loadDeals();
  };

  const handleDealDeleted = () => {
    setIsViewEditModalOpen(false);
    setSelectedDealId(null);
    loadDeals();
  };

  const handleStatusChange = (dealId: number, newStatus: string) => {
    setDeals(prevDeals =>
      prevDeals.map(deal =>
        deal.id === dealId ? { ...deal, status: newStatus } : deal
      )
    );
  };

  const handleFilterApply = (newFilters: FilterOptions) => {
    setFilters(newFilters);
  };

  const handleFilterReset = () => {
    const emptyFilters: FilterOptions = {
      statuses: [],
      minAmount: '',
      maxAmount: '',
      dateFrom: '',
      dateTo: '',
      clientName: '',
    };
    setFilters(emptyFilters);
  };

  const hasActiveFilters =
    filters.statuses.length > 0 ||
    filters.minAmount !== '' ||
    filters.maxAmount !== '' ||
    filters.dateFrom !== '' ||
    filters.dateTo !== '' ||
    filters.clientName !== '';

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.statuses.length > 0) count += filters.statuses.length;
    if (filters.minAmount !== '') count++;
    if (filters.maxAmount !== '') count++;
    if (filters.dateFrom !== '') count++;
    if (filters.dateTo !== '') count++;
    if (filters.clientName !== '') count++;
    return count;
  };

  // Apply filters and search
  const filteredDeals = useMemo(() => {
    let result = [...deals];

    // Search filter
    if (searchQuery) {
      result = result.filter(deal =>
        deal.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        deal.client?.name.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Status filter
    if (filters.statuses.length > 0) {
      result = result.filter(deal => filters.statuses.includes(deal.status));
    }

    // Amount filter
    if (filters.minAmount) {
      const min = parseFloat(filters.minAmount);
      if (!isNaN(min)) {
        result = result.filter(deal => deal.total_price >= min);
      }
    }
    if (filters.maxAmount) {
      const max = parseFloat(filters.maxAmount);
      if (!isNaN(max)) {
        result = result.filter(deal => deal.total_price <= max);
      }
    }

    // Date filter
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      result = result.filter(deal => new Date(deal.created_at) >= fromDate);
    }
    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59, 999); // End of day
      result = result.filter(deal => new Date(deal.created_at) <= toDate);
    }

    // Client name filter
    if (filters.clientName) {
      result = result.filter(deal =>
        deal.client?.name.toLowerCase().includes(filters.clientName.toLowerCase())
      );
    }

    return result;
  }, [deals, searchQuery, filters]);

  // Apply sorting
  const sortedDeals = useMemo(() => {
    const result = [...filteredDeals];

    result.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortOption.field) {
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'total_price':
          aValue = a.total_price;
          bValue = b.total_price;
          break;
        case 'status':
          aValue = a.status.toLowerCase();
          bValue = b.status.toLowerCase();
          break;
        case 'client':
          aValue = a.client?.name.toLowerCase() || '';
          bValue = b.client?.name.toLowerCase() || '';
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
  }, [filteredDeals, sortOption]);

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

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      // ИСПРАВЛЕНО: Оставлены только запрашиваемые статусы
      new: '#6B7280',
      preparing_document: '#3B82F6',
      prepaid_account: '#8B5CF6',
      at_work: '#F59E0B',
      final_account: '#10B981',
    };
    return colors[status] || '#6B7280';
  };

  const getStatusLabel = (status: string) => {
    const statusObj = DEAL_STATUSES.find(s => s.value === status);
    return statusObj ? statusObj.label : status;
  };

  return (
    <div className="deals-page">
      <div className="sticky-header-container">
        {/* Header Section */}
        <div className="deals-header">
          <div className="page-container">
            <div className="deals-header-content">
              <div className="deals-title-section">
                <h1 className="deals-title">Deals</h1>
                {sortedDeals.length > 0 && (
                  <span className="deals-count">{sortedDeals.length} {sortedDeals.length === 1 ? 'deal' : 'deals'}</span>
                )}
              </div>
              <button className="btn-create-deal" onClick={openCreateModal}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Create Deal
              </button>
            </div>
          </div>
        </div>

        {/* Toolbar Section */}
        <div className="deals-toolbar">
          <div className="page-container">
            <div className="deals-toolbar-content">
              <div className="toolbar-left">
                <div className="search-wrapper">
                  <svg className="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M7.33333 12.6667C10.2789 12.6667 12.6667 10.2789 12.6667 7.33333C12.6667 4.38781 10.2789 2 7.33333 2C4.38781 2 2 4.38781 2 7.33333C2 10.2789 4.38781 12.6667 7.33333 12.6667Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M14 14L11.1 11.1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <input
                    type="text"
                    placeholder="Search deals, clients..."
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
                  onClick={loadDeals}
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
                <SortDropdown sortOption={sortOption} onSortChange={setSortOption} />
                <ColumnsDropdown columns={columns} onColumnsChange={setColumns} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="page-container">
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
        </div>
      )}

      {/* Main Content */}
      <div className={`deals-content ${viewMode === 'kanban' ? 'kanban-view' : ''}`}>
        <div className="page-container content-container">
          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading deals...</p>
            </div>
          ) : error ? null : sortedDeals.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-content">
                <div className="empty-state-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <path d="M32 8C18.745 8 8 18.745 8 32C8 45.255 18.745 56 32 56C45.255 56 56 45.255 56 32C56 18.745 45.255 8 32 8ZM36 24C36 26.2091 34.2091 28 32 28C29.7909 28 28 26.2091 28 24C28 21.7909 29.7909 20 32 20C34.2091 20 36 21.7909 36 24ZM28 36H36V44H28V36ZM36 44V36H44V44H36Z" fill="currentColor" fillOpacity="0.1" />
                    <path d="M32 22C33.1046 22 34 22.8954 34 24C34 25.1046 33.1046 26 32 26C30.8954 26 30 25.1046 30 24C30 22.8954 30.8954 22 32 22ZM28 34H36V42H28V34ZM38 34H46V42H38V34Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </div>
                <h2>No Deals Found</h2>
                <p className="empty-state-description">
                  {hasActiveFilters || searchQuery
                    ? 'Try adjusting your filters or search query to see more results.'
                    : 'Get started by creating your first deal.'}
                </p>
              </div>
            </div>
          ) : viewMode === 'kanban' ? (
            <DealsKanban
              deals={sortedDeals}
              onDealClick={handleViewDeal}
              onStatusChange={handleStatusChange}
              onAddDeal={() => {
                openCreateModal();
              }}
            />
          ) : (
            <div className="deals-table-container">
              <table className="deals-table">
                <thead>
                  <tr>
                    {columns.find(col => col.id === 'title')?.visible && <th>Deal Name</th>}
                    {columns.find(col => col.id === 'client')?.visible && <th>Client</th>}
                    {columns.find(col => col.id === 'status')?.visible && <th>Status</th>}
                    {columns.find(col => col.id === 'amount')?.visible && <th>Amount</th>}
                    {columns.find(col => col.id === 'created')?.visible && <th>Created</th>}
                    <th className="actions-column">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedDeals.map((deal) => (
                    <tr key={deal.id}>
                      {columns.find(col => col.id === 'title')?.visible && (
                        <td>
                          <div className="deal-title">{deal.title}</div>
                        </td>
                      )}
                      {columns.find(col => col.id === 'client')?.visible && (
                        <td>
                          <div className="deal-client">{deal.client?.name || 'N/A'}</div>
                        </td>
                      )}
                      {columns.find(col => col.id === 'status')?.visible && (
                        <td>
                          <span
                            className="status-badge"
                            style={{ backgroundColor: getStatusColor(deal.status) + '20', color: getStatusColor(deal.status) }}
                          >
                            {getStatusLabel(deal.status)}
                          </span>
                        </td>
                      )}
                      {columns.find(col => col.id === 'amount')?.visible && (
                        <td>
                          <div className="deal-amount">{formatCurrency(deal.total_price, deal.currency)}</div>
                        </td>
                      )}
                      {columns.find(col => col.id === 'created')?.visible && (
                        <td>
                          <div className="deal-date">{formatDate(deal.created_at)}</div>
                        </td>
                      )}
                      <td className="actions-column">
                        <div className="table-actions">
                          <button
                            className="action-btn action-btn-view"
                            onClick={() => handleViewDeal(deal.id)}
                            title="View/Edit"
                          >
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                              <path d="M8 2.66667C4.66667 2.66667 2 5.33333 2 8.66667C2 12 4.66667 14.6667 8 14.6667C11.3333 14.6667 14 12 14 8.66667C14 5.33333 11.3333 2.66667 8 2.66667ZM8 12.6667C6.16 12.6667 4.66667 11.1733 4.66667 9.33333C4.66667 7.49333 6.16 6 8 6C9.84 6 11.3333 7.49333 11.3333 9.33333C11.3333 11.1733 9.84 12.6667 8 12.6667ZM8 7.33333C7.26667 7.33333 6.66667 7.93333 6.66667 8.66667C6.66667 9.4 7.26667 10 8 10C8.73333 10 9.33333 9.4 9.33333 8.66667C9.33333 7.93333 8.73333 7.33333 8 7.33333Z" fill="currentColor" />
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
      </div>

      <CreateDealModal
        isOpen={isCreateModalOpen}
        onClose={closeCreateModal}
        onSuccess={handleDealCreated}
        tenantId={tenantId}
      />

      <FilterModal
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        filters={filters}
        onApply={handleFilterApply}
        onReset={handleFilterReset}
      />

      <ViewEditDealModal
        dealId={selectedDealId}
        isOpen={isViewEditModalOpen}
        onClose={() => {
          setIsViewEditModalOpen(false);
          setSelectedDealId(null);
        }}
        onSuccess={handleDealUpdated}
        onDelete={handleDealDeleted}
      />
    </div>
  );
};

export default DealsPage;
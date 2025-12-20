import React, { useState } from 'react';
import { DEAL_STATUSES } from '../types';
import './FilterModal.css';

export interface FilterOptions {
  statuses: string[];
  minAmount: string;
  maxAmount: string;
  dateFrom: string;
  dateTo: string;
  clientName: string;
}

interface FilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  filters: FilterOptions;
  onApply: (filters: FilterOptions) => void;
  onReset: () => void;
}

const FilterModal: React.FC<FilterModalProps> = ({ isOpen, onClose, filters, onApply, onReset }) => {
  const [localFilters, setLocalFilters] = useState<FilterOptions>(filters);

  if (!isOpen) return null;

  const handleStatusToggle = (status: string) => {
    setLocalFilters(prev => ({
      ...prev,
      statuses: prev.statuses.includes(status)
        ? prev.statuses.filter(s => s !== status)
        : [...prev.statuses, status]
    }));
  };

  const handleApply = () => {
    onApply(localFilters);
    onClose();
  };

  const handleReset = () => {
    const emptyFilters: FilterOptions = {
      statuses: [],
      minAmount: '',
      maxAmount: '',
      dateFrom: '',
      dateTo: '',
      clientName: '',
    };
    setLocalFilters(emptyFilters);
    onReset();
    onClose();
  };

  const hasActiveFilters = 
    localFilters.statuses.length > 0 ||
    localFilters.minAmount !== '' ||
    localFilters.maxAmount !== '' ||
    localFilters.dateFrom !== '' ||
    localFilters.dateTo !== '' ||
    localFilters.clientName !== '';

  return (
    <div className="filter-modal-overlay" onClick={onClose}>
      <div className="filter-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="filter-modal-header">
          <h3>Filter Deals</h3>
          <button className="filter-close-btn" onClick={onClose}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </button>
        </div>

        <div className="filter-modal-body">
          {/* Status Filter */}
          <div className="filter-section">
            <label className="filter-label">Status</label>
            <div className="filter-status-grid">
              {DEAL_STATUSES.map((status) => (
                <label key={status.value} className="filter-checkbox-label">
                  <input
                    type="checkbox"
                    checked={localFilters.statuses.includes(status.value)}
                    onChange={() => handleStatusToggle(status.value)}
                  />
                  <span>{status.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Amount Range */}
          <div className="filter-section">
            <label className="filter-label">Amount Range (KZT)</label>
            <div className="filter-range">
              <input
                type="number"
                placeholder="Min"
                value={localFilters.minAmount}
                onChange={(e) => setLocalFilters(prev => ({ ...prev, minAmount: e.target.value }))}
                className="filter-input"
              />
              <span className="filter-range-separator">to</span>
              <input
                type="number"
                placeholder="Max"
                value={localFilters.maxAmount}
                onChange={(e) => setLocalFilters(prev => ({ ...prev, maxAmount: e.target.value }))}
                className="filter-input"
              />
            </div>
          </div>

          {/* Date Range */}
          <div className="filter-section">
            <label className="filter-label">Date Range</label>
            <div className="filter-range">
              <input
                type="date"
                value={localFilters.dateFrom}
                onChange={(e) => setLocalFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                className="filter-input"
              />
              <span className="filter-range-separator">to</span>
              <input
                type="date"
                value={localFilters.dateTo}
                onChange={(e) => setLocalFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                className="filter-input"
              />
            </div>
          </div>

          {/* Client Name */}
          <div className="filter-section">
            <label className="filter-label">Client Name</label>
            <input
              type="text"
              placeholder="Filter by client name"
              value={localFilters.clientName}
              onChange={(e) => setLocalFilters(prev => ({ ...prev, clientName: e.target.value }))}
              className="filter-input"
            />
          </div>
        </div>

        <div className="filter-modal-footer">
          <button className="filter-btn-reset" onClick={handleReset}>
            Reset
          </button>
          <div className="filter-footer-right">
            <button className="filter-btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button 
              className="filter-btn-apply" 
              onClick={handleApply}
              disabled={!hasActiveFilters}
            >
              Apply {hasActiveFilters && `(${localFilters.statuses.length + 
                (localFilters.minAmount ? 1 : 0) + 
                (localFilters.maxAmount ? 1 : 0) + 
                (localFilters.dateFrom ? 1 : 0) + 
                (localFilters.dateTo ? 1 : 0) + 
                (localFilters.clientName ? 1 : 0)})`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterModal;



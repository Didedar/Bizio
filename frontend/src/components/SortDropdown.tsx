import React, { useState, useRef, useEffect } from 'react';
import './SortDropdown.css';

export type SortField = 'created_at' | 'title' | 'total_price' | 'status' | 'client' | 'name' | 'company' | 'email' | 'phone' | 'sku' | 'category' | 'default_price' | 'default_cost';
export type SortDirection = 'asc' | 'desc';

export interface SortOption {
  field: SortField;
  direction: SortDirection;
}

export interface SortFieldOption {
  field: SortField;
  label: string;
}

interface SortDropdownProps {
  sortOption: SortOption;
  onSortChange: (sort: SortOption) => void;
  sortFields?: SortFieldOption[];
}

const DEFAULT_SORT_OPTIONS: SortFieldOption[] = [
  { field: 'created_at', label: 'Created Date' },
  { field: 'title', label: 'Deal Name' },
  { field: 'total_price', label: 'Amount' },
  { field: 'status', label: 'Status' },
  { field: 'client', label: 'Client' },
];

const SortDropdown: React.FC<SortDropdownProps> = ({ sortOption, onSortChange, sortFields = DEFAULT_SORT_OPTIONS }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleFieldSelect = (field: SortField) => {
    // Numeric fields should default to descending (highest first), others to ascending
    const numericFields: SortField[] = ['default_cost', 'default_price', 'total_price'];
    const isNumericField = numericFields.includes(field);

    let newDirection: SortDirection;
    if (sortOption.field === field) {
      // Toggle direction if same field is selected
      newDirection = sortOption.direction === 'asc' ? 'desc' : 'asc';
    } else {
      // Set default direction based on field type
      newDirection = isNumericField ? 'desc' : 'asc';
    }

    onSortChange({ field, direction: newDirection });
    setIsOpen(false);
  };

  const currentLabel = sortFields.find(opt => opt.field === sortOption.field)?.label || 'Sort';

  return (
    <div className="sort-dropdown" ref={dropdownRef}>
      <button
        className="sort-dropdown-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d={sortOption.direction === 'asc'
              ? "M4 6L8 2L12 6M4 10L8 14L12 10"
              : "M4 10L8 14L12 10M4 6L8 2L12 6"
            }
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {currentLabel}
        {sortOption.direction === 'asc' ? ' ↑' : ' ↓'}
      </button>

      {isOpen && (
        <div className="sort-dropdown-menu">
          {sortFields.map((option) => (
            <button
              key={option.field}
              className={`sort-dropdown-item ${sortOption.field === option.field ? 'active' : ''
                }`}
              onClick={() => handleFieldSelect(option.field)}
            >
              <span>{option.label}</span>
              {sortOption.field === option.field && (
                <span className="sort-indicator">
                  {sortOption.direction === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default SortDropdown;



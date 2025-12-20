import React, { useState, useRef, useEffect } from 'react';
import './ColumnsDropdown.css';

export interface ColumnConfig {
  id: string;
  label: string;
  visible: boolean;
}

interface ColumnsDropdownProps {
  columns: ColumnConfig[];
  onColumnsChange: (columns: ColumnConfig[]) => void;
}

const ColumnsDropdown: React.FC<ColumnsDropdownProps> = ({ columns, onColumnsChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localColumns, setLocalColumns] = useState<ColumnConfig[]>(columns);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLocalColumns(columns);
  }, [columns]);

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

  const handleToggleColumn = (columnId: string) => {
    const updated = localColumns.map(col =>
      col.id === columnId ? { ...col, visible: !col.visible } : col
    );
    setLocalColumns(updated);
    onColumnsChange(updated);
  };

  const handleSelectAll = () => {
    const allVisible = localColumns.every(col => col.visible);
    const updated = localColumns.map(col => ({ ...col, visible: !allVisible }));
    setLocalColumns(updated);
    onColumnsChange(updated);
  };

  const visibleCount = localColumns.filter(col => col.visible).length;

  return (
    <div className="columns-dropdown" ref={dropdownRef}>
      <button
        className="columns-dropdown-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 2H6V14H2V2ZM6 2H10V14H6V2ZM10 2H14V14H10V2Z" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
        Columns {visibleCount > 0 && `(${visibleCount})`}
      </button>

      {isOpen && (
        <div className="columns-dropdown-menu">
          <div className="columns-dropdown-header">
            <button className="columns-select-all" onClick={handleSelectAll}>
              {localColumns.every(col => col.visible) ? 'Deselect All' : 'Select All'}
            </button>
          </div>
          <div className="columns-dropdown-list">
            {localColumns.map((column) => (
              <label
                key={column.id}
                className="columns-dropdown-item"
              >
                <input
                  type="checkbox"
                  checked={column.visible}
                  onChange={() => handleToggleColumn(column.id)}
                />
                <span>{column.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ColumnsDropdown;



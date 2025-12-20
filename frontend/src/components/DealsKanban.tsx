import React, { useState, useEffect } from 'react';
import type { Deal, User } from '../types';
import { DEAL_STATUSES } from '../types';
import { dealsApi, usersApi } from '../api/client';
import './DealsKanban.css';

interface DealsKanbanProps {
  deals: Deal[];
  onDealClick: (dealId: number) => void;
  onStatusChange: (dealId: number, newStatus: string) => void;
  onAddDeal?: (status: string) => void;
}

const DealsKanban: React.FC<DealsKanbanProps> = ({ deals, onDealClick, onStatusChange, onAddDeal }) => {
  const [draggedDeal, setDraggedDeal] = useState<Deal | null>(null);
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await usersApi.list();
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  };

  const handleDragStart = (deal: Deal) => {
    setDraggedDeal(deal);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (status: string) => {
    if (draggedDeal && draggedDeal.status !== status) {
      try {
        await dealsApi.updateStatus(draggedDeal.id, status);
        onStatusChange(draggedDeal.id, status);
      } catch (error) {
        console.error('Failed to update deal status:', error);
      }
    }
    setDraggedDeal(null);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: '#6B7280',
      preparing_document: '#3B82F6',
      prepaid_account: '#8B5CF6',
      at_work: '#F59E0B',
      final_account: '#10B981',
    };
    return colors[status] || '#6B7280';
  };

  const formatCurrency = (amount: number, currency: string = 'KZT') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 30) return `${diffDays} days ago`;
    if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    }
    const years = Math.floor(diffDays / 365);
    return `${years} year${years > 1 ? 's' : ''} ago`;
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  // Group deals by status
  const dealsByStatus = DEAL_STATUSES.reduce((acc, status) => {
    acc[status.value] = deals.filter(deal => deal.status === status.value);
    return acc;
  }, {} as Record<string, Deal[]>);

  // Get all unique statuses from deals (to show all statuses that have deals)
  const dealStatuses = new Set(deals.map(deal => deal.status));
  
  // Also include main statuses even if they have no deals (for empty columns)
  const mainStatuses = ['new', 'in_progress', 'preparing_document', 'prepaid_account', 'at_work', 'final_account', 'won', 'lost', 'cancelled'];
  const allStatusesToShow = new Set([...mainStatuses, ...Array.from(dealStatuses)]);

  // Status labels mapping - use DEAL_STATUSES for consistent labeling
  const statusLabels: Record<string, string> = DEAL_STATUSES.reduce((acc, status) => {
    acc[status.value] = status.label;
    return acc;
  }, {} as Record<string, string>);

  return (
    <div className="kanban-board">
      {DEAL_STATUSES.filter(s => allStatusesToShow.has(s.value)).map((status) => {
        const statusDeals = dealsByStatus[status.value] || [];
        const statusColor = getStatusColor(status.value);

        return (
          <div
            key={status.value}
            className="kanban-column"
            onDragOver={handleDragOver}
            onDrop={() => handleDrop(status.value)}
          >
            <div className="kanban-column-header" style={{ borderTopColor: statusColor }}>
              <div className="column-title-wrapper">
                <span className="column-dot" style={{ backgroundColor: statusColor }}></span>
                <h3 className="column-title">{statusLabels[status.value] || status.label}</h3>
                <span className="column-count">{statusDeals.length}</span>
              </div>
              <button
                className="column-add-btn"
                title="Add deal"
                onClick={(e) => {
                  e.stopPropagation();
                  if (onAddDeal) {
                    onAddDeal(status.value);
                  }
                }}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </button>
            </div>

            <div className="kanban-column-content">
              {statusDeals.map((deal) => (
                <div
                  key={deal.id}
                  className="kanban-card"
                  draggable
                  onDragStart={() => handleDragStart(deal)}
                  onClick={() => onDealClick(deal.id)}
                >
                  <div className="card-header">
                    <div className="company-info">
                      {deal.client?.name ? (
                        <div className="company-avatar">
                          {getInitials(deal.client.name)}
                        </div>
                      ) : (
                        <div className="company-avatar default">
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M8 2C9.1 2 10 2.9 10 4C10 5.1 9.1 6 8 6C6.9 6 6 5.1 6 4C6 2.9 6.9 2 8 2ZM8 7C9.7 7 11 8.3 11 10V11H5V10C5 8.3 6.3 7 8 7Z" fill="currentColor" />
                          </svg>
                        </div>
                      )}
                      <div className="company-details">
                        <div className="company-name">{deal.title}</div>
                        {deal.client?.name && (
                          <div className="company-subtitle">{deal.client.name}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {deal.total_price > 0 && (
                    <div className="card-amount">
                      {formatCurrency(deal.total_price, deal.currency)}
                    </div>
                  )}

                  <div className="card-info">
                    {deal.client?.email && (
                      <div className="info-row">
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                          <path d="M2 4H14M3 4V12C3 12.5523 3.44772 13 4 13H12C12.5523 13 13 12.5523 13 12V4M3 4L8 8L13 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span>{deal.client.email}</span>
                      </div>
                    )}
                    {deal.client?.phone && (
                      <div className="info-row">
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                          <path d="M3.33333 2.66667C2.59695 2.66667 2 3.26362 2 4V12C2 12.7364 2.59695 13.3333 3.33333 13.3333H12.6667C13.403 13.3333 14 12.7364 14 12V4C14 3.26362 13.403 2.66667 12.6667 2.66667H3.33333Z" stroke="currentColor" strokeWidth="1.5" />
                          <path d="M6 10H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                        <span>{deal.client.phone}</span>
                      </div>
                    )}
                  </div>

                  <div className="card-footer">
                    <div className="card-assigned">
                      {deal.extra_data?.deal_owner && users.length > 0 && (
                        <div className="assigned-user">
                          <div className="user-avatar-small">
                            {(() => {
                              const user = users.find(u => u.id === deal.extra_data?.deal_owner);
                              return user?.full_name ? getInitials(user.full_name) : 'U';
                            })()}
                          </div>
                          <span className="user-name">
                            {(() => {
                              const user = users.find(u => u.id === deal.extra_data?.deal_owner);
                              return user?.full_name || user?.email || 'Unassigned';
                            })()}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="card-meta">
                      <span className="last-updated">{formatDate(deal.created_at)}</span>
                    </div>
                  </div>

                  <div className="card-actions">
                    <button className="action-icon" title="Email">
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M2 4H14M3 4V12C3 12.5523 3.44772 13 4 13H12C12.5523 13 13 12.5523 13 12V4M3 4L8 8L13 4" stroke="currentColor" strokeWidth="1.5" />
                      </svg>
                    </button>
                    <button className="action-icon" title="Documents">
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M4 2H10L13 5V13C13 13.5523 12.5523 14 12 14H4C3.44772 14 3 13.5523 3 13V3C3 2.44772 3.44772 2 4 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>
                    <button className="action-icon" title="Tasks">
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M4 8L6 10L12 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>
                    <button className="action-icon" title="Comments">
                      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <path d="M3 3H13C13.5523 3 14 3.44772 14 4V10C14 10.5523 13.5523 11 13 11H6L3 14V4C3 3.44772 3.44772 3 3 3Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default DealsKanban;


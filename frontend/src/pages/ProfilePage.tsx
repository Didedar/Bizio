import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './ProfilePage.css';

const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    fullName: user?.full_name || '',
    email: user?.email || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // TODO: Implement update user API
      // await usersApi.update(user.id, formData);
      setSuccess('Profile updated successfully');
      setIsEditing(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>Profile</h1>
      </div>

      <div className="profile-content">
        <div className="profile-card">
          <div className="profile-card-header">
            <div className="profile-avatar">
              <span>{user?.full_name?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U'}</span>
            </div>
            <div className="profile-info">
              <h2>{user?.full_name || 'User'}</h2>
              <p className="profile-email">{user?.email}</p>
              <p className="profile-role">Role: {user?.role}</p>
            </div>
            {!isEditing && (
              <button className="btn-edit" onClick={() => setIsEditing(true)}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M11.3333 2.00001C11.5084 1.82491 11.7163 1.686 11.9451 1.59128C12.1739 1.49657 12.4189 1.44775 12.6667 1.44775C12.9144 1.44775 13.1594 1.49657 13.3882 1.59128C13.617 1.686 13.8249 1.82491 14 2.00001C14.1751 2.1751 14.314 2.383 14.4087 2.6118C14.5034 2.8406 14.5522 3.08564 14.5522 3.33334C14.5522 3.58104 14.5034 3.82608 14.4087 4.05486C14.314 4.28364 14.1751 4.49154 14 4.66668L5.00001 13.6667L1.33334 14.6667L2.33334 11L11.3333 2.00001Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Edit Profile
              </button>
            )}
          </div>

          {error && (
            <div className="profile-error">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 6V10M8 11H8.00667M14 8C14 11.3137 11.3137 14 8 14C4.68629 14 2 11.3137 2 8C2 4.68629 4.68629 2 8 2C11.3137 2 14 4.68629 14 8Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="profile-success">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M13.3333 4L6 11.3333L2.66667 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>{success}</span>
            </div>
          )}

          {isEditing ? (
            <form onSubmit={handleSubmit} className="profile-form">
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  placeholder="Enter your full name"
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled
                  className="disabled-input"
                />
                <small className="form-hint">Email cannot be changed</small>
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => {
                  setIsEditing(false);
                  setFormData({
                    fullName: user?.full_name || '',
                    email: user?.email || '',
                  });
                  setError(null);
                  setSuccess(null);
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          ) : (
            <div className="profile-details">
              <div className="detail-item">
                <span className="detail-label">Full Name</span>
                <span className="detail-value">{user?.full_name || 'Not set'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Email</span>
                <span className="detail-value">{user?.email}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Role</span>
                <span className="detail-value">{user?.role}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <span className="detail-value">
                  <span className={`status-badge ${user?.is_active ? 'active' : 'inactive'}`}>
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </span>
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Member Since</span>
                <span className="detail-value">{user?.created_at ? formatDate(user.created_at) : 'N/A'}</span>
              </div>
              {user?.tenants && user.tenants.length > 0 && (
                <>
                  <div className="detail-item">
                    <span className="detail-label">Company</span>
                    <span className="detail-value">{user.tenants[0].name}</span>
                  </div>
                  {user.tenants[0].code && (
                    <div className="detail-item">
                      <span className="detail-label">Company Code</span>
                      <span className="detail-value">
                        <code className="tenant-code">{user.tenants[0].code}</code>
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        <div className="profile-actions">
          <button className="btn-logout" onClick={logout}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V3.33333C2 2.97971 2.14048 2.64057 2.39052 2.39052C2.64057 2.14048 2.97971 2 3.33333 2H6M10.6667 11.3333L14 8M14 8L10.6667 4.66667M14 8H6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;


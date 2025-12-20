import React from 'react';
import './ComingSoonPage.css';

interface ComingSoonPageProps {
  title?: string;
}

const ComingSoonPage: React.FC<ComingSoonPageProps> = ({ title = 'Coming Soon' }) => {
  return (
    <div className="coming-soon-page">
      <div className="coming-soon-container">
        <div className="coming-soon-icon">
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
            <circle cx="40" cy="40" r="38" stroke="#e5e7eb" strokeWidth="2" strokeDasharray="4 4"/>
            <path d="M40 20V40L55 50" stroke="#9ca3af" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1 className="coming-soon-title">{title}</h1>
        <p className="coming-soon-description">
          This feature is under development and will be available soon.
        </p>
      </div>
    </div>
  );
};

export default ComingSoonPage;



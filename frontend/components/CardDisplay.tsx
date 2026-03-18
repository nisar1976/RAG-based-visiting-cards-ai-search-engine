'use client';

import { Card, getImageUrl } from '@/lib/api';

interface CardDisplayProps {
  card: Card | null;
  loading?: boolean;
}

export default function CardDisplay({ card, loading = false }: CardDisplayProps) {
  if (loading) {
    return (
      <div className="card-display">
        <div className="card-container">
          <div className="card-image-section">
            <div className="skeleton skeleton-title" style={{ width: '100%', height: '250px' }} />
          </div>

          <div className="card-metadata">
            <div className="skeleton skeleton-title" />
            <div className="skeleton skeleton-text" />
            <div className="skeleton skeleton-text" />
            <div className="skeleton skeleton-text" />
            <div className="skeleton skeleton-text" />
          </div>
        </div>
      </div>
    );
  }

  if (!card) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔍</div>
        <h2 className="empty-title">No card selected</h2>
        <p className="empty-description">Search for a visiting card to get started</p>
      </div>
    );
  }

  return (
    <div id="card-display" className="card-display">
      <div className="card-container">
        <div className="card-image-section">
          <img
            src={getImageUrl(card.id)}
            alt={`Card for ${card.name}`}
            className="card-image"
          />
        </div>

        <div className="card-metadata">
          <div className="card-person-header">
            <h2 className="card-name">{card.name}</h2>
            <p className="card-designation">{card.designation}</p>
          </div>

          <div className="metadata-field">
            <div className="metadata-icon">🏢</div>
            <div className="metadata-content">
              <label className="metadata-label">Company</label>
              <p className="metadata-value">
                {card.company}
                {card.company !== 'Not Available' && (
                  <span className="badge badge-company">{card.company}</span>
                )}
              </p>
            </div>
          </div>

          <div className="metadata-field">
            <div className="metadata-icon">🌍</div>
            <div className="metadata-content">
              <label className="metadata-label">Country</label>
              <p className="metadata-value">
                {card.country}
                {card.country !== 'Not Available' && (
                  <span className="badge badge-country">{card.country}</span>
                )}
              </p>
            </div>
          </div>

          <div className="metadata-field">
            <div className="metadata-icon">📞</div>
            <div className="metadata-content">
              <label className="metadata-label">Phone</label>
              <p className="metadata-value">{card.phone}</p>
            </div>
          </div>

          <div className="metadata-field">
            <div className="metadata-icon">📧</div>
            <div className="metadata-content">
              <label className="metadata-label">Email</label>
              <p className="metadata-value">{card.email}</p>
            </div>
          </div>

          <div className="metadata-field">
            <div className="metadata-icon">📍</div>
            <div className="metadata-content">
              <label className="metadata-label">Address</label>
              <p className="metadata-value">{card.address}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

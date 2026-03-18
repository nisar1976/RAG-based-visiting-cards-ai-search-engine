'use client';

import { useState, useEffect } from 'react';
import { Card, getAllCards } from '@/lib/api';

interface CardsTableProps {
  onCardSelect?: (card: Card) => void;
}

export default function CardsTable({ onCardSelect }: CardsTableProps) {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCards = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAllCards();
        setCards(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch cards');
      } finally {
        setLoading(false);
      }
    };

    fetchCards();
  }, []);

  if (loading) {
    return (
      <div className="cards-table-container">
        <div className="skeleton-table">
          <div className="skeleton-row">
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
          </div>
          <div className="skeleton-row">
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
          </div>
          <div className="skeleton-row">
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
            <div className="skeleton-cell skeleton-text"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-banner">
        Failed to load cards: {error}
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📇</div>
        <div className="empty-title">No cards indexed yet</div>
        <div className="empty-description">Cards will appear here once indexing is complete.</div>
      </div>
    );
  }

  return (
    <div className="cards-table-container">
      <div className="table-header">
        <h3>All Indexed Cards ({cards.length})</h3>
      </div>
      <div className="table-wrapper">
        <table className="cards-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Designation</th>
              <th>Company</th>
              <th>Country</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Address</th>
            </tr>
          </thead>
          <tbody>
            {cards.map((card) => (
              <tr
                key={card.id}
                className="table-row"
                onClick={() => onCardSelect?.(card)}
              >
                <td className="table-id">{card.id}</td>
                <td className="table-cell">{card.name}</td>
                <td className="table-cell">{card.designation}</td>
                <td className="table-cell">{card.company}</td>
                <td className="table-cell">{card.country}</td>
                <td className="table-cell table-phone">{card.phone}</td>
                <td className="table-cell table-email">{card.email}</td>
                <td className="table-cell">{card.address}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

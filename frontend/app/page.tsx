'use client';

import { useState, useEffect, useRef } from 'react';
import SearchBar from '@/components/SearchBar';
import CardDisplay from '@/components/CardDisplay';
import ActionButtons from '@/components/ActionButtons';
import CardsTable from '@/components/CardsTable';
import { searchCard, Card, getHealth, HealthStatus } from '@/lib/api';

export default function Home() {
  const [query, setQuery] = useState('');
  const [card, setCard] = useState<Card | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Fetch health on mount and set up polling
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const health = await getHealth();
        setHealthData(health);
      } catch (err) {
        console.error('Health check failed:', err);
      }
    };

    fetchHealth();

    // Poll health every 3 seconds if indexing is running
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  // Debounced search handler
  const handleSearchChange = (q: string) => {
    setQuery(q);

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      handleSearch(q);
    }, 300);
  };

  const handleSearch = async (q: string) => {
    if (!q.trim()) {
      setCard(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await searchCard(q);
      setCard(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setCard(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">Visiting Card Search</h1>
          <p className="header-subtitle">Offline semantic search across 348+ visiting cards</p>
        </div>
      </header>

      {healthData && (
        <div className="stats-bar">
          <div className="stats-bar-content">
            <div className="stat-item">
              <span className="stat-label">Cards Indexed</span>
              <span className="stat-value">{healthData.cards_indexed}</span>
            </div>
          </div>
        </div>
      )}

      <main className="main-content">
        <div className="search-container">
          <SearchBar
            onSearch={handleSearch}
            loading={loading}
            onChangeDebounced={handleSearchChange}
          />
        </div>

        {healthData?.indexing_status === 'running' && (
          <div className="indexing-banner">
            <div className="spinner"></div>
            <div style={{ flex: 1 }}>
              <div className="banner-text">
                Indexing cards ({healthData.cards_indexed} / {healthData.total_cards})
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${healthData.total_cards > 0 ? (healthData.cards_indexed / healthData.total_cards) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          </div>
        )}

        {healthData?.indexing_status === 'error' && healthData?.indexing_error && (
          <div className="error-banner">
            ⚠️ Indexing failed: {healthData.indexing_error}
          </div>
        )}

        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        <CardDisplay card={card} loading={loading} />

        {card && <ActionButtons card={card} />}

        <CardsTable onCardSelect={setCard} />
      </main>
    </>
  );
}

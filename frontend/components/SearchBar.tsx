'use client';

import { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
  onChangeDebounced?: (query: string) => void;
}

export default function SearchBar({ onSearch, loading = false, onChangeDebounced }: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleChange = (value: string) => {
    setQuery(value);
    onChangeDebounced?.(value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <input
        type="text"
        value={query}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="Search for a card (name, company, location, etc.)"
        disabled={loading}
        className="search-input"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="search-button"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}

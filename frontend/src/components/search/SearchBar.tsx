import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

interface SearchBarProps {
  className?: string;
}

export default function SearchBar({ className = '' }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // URL에서 초기 검색어 가져오기
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
    }
  }, [location.search]);

  // Debounced search with 300ms delay
  const handleSearch = useCallback((searchQuery: string) => {
    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout
    timeoutRef.current = setTimeout(() => {
      if (searchQuery.trim().length > 0) {
        navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      }
    }, 300);
  }, [navigate]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    handleSearch(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      // Clear timeout and search immediately on Enter
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (query.trim().length > 0) {
        navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (query.trim().length > 0) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <form onSubmit={handleSubmit} className={`flex items-center ${className}`}>
      <div className="relative flex items-center w-full max-w-md">
        <input
          type="text"
          placeholder="검색"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className="w-full bg-gray-700 text-white placeholder-gray-400 rounded-full px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
        />
        <button
          type="submit"
          className="absolute right-2 text-gray-400 hover:text-white transition-colors"
          aria-label="검색"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </button>
      </div>
    </form>
  );
}

import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import FilterPanel from '../components/FilterPanel';
import PatentCard from '../components/PatentCard';
import SearchBar from '../components/SearchBar';
import { api } from '../services/api';
import { Search as SearchIcon, SlidersHorizontal, Sparkles, RotateCcw } from 'lucide-react';

function getPageNumbers(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  const pages = [];
  pages.push(1);
  if (current > 3) {
    pages.push('...');
  }
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  if (current < total - 2) {
    pages.push('...');
  }
  pages.push(total);
  return pages;
}

export default function Search({ isDarkTheme }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialTech = searchParams.get('tech') || '';
  const initialOffice = searchParams.get('office') || '';
  const initialPage = parseInt(searchParams.get('page') || '1', 10);
  const initialPageSize = parseInt(searchParams.get('pageSize') || '25', 10);

  const [query, setQuery] = useState(initialQuery);
  const [filters, setFilters] = useState({
    dateType: '',
    priorityDate: '',
    exactDate: '',
    dateFrom: '',
    dateTo: '',
    inventor: '',
    organization: '',
    selectedTechnologies: initialTech ? [initialTech] : [],
    patentOffice: initialOffice || '',
    status: 'All'
  });

  const [page, setPage] = useState(Math.max(1, initialPage));
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [totalMatching, setTotalMatching] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(true);
  const [sortBy, setSortBy] = useState('relevance');
  const [backendError, setBackendError] = useState(false);
  const resultsTopRef = useRef(null);

  // Sync state when URL parameters change (e.g. from Technology Explorer navigation)
  useEffect(() => {
    const urlTech = searchParams.get('tech');
    const urlOffice = searchParams.get('office');
    const urlPage = parseInt(searchParams.get('page') || '1', 10);
    const urlQ = searchParams.get('q') || '';

    setFilters(prev => {
      const updatedTechs = urlTech ? [urlTech] : prev.selectedTechnologies;
      const updatedOffice = urlOffice !== null ? urlOffice : prev.patentOffice;
      return {
        ...prev,
        selectedTechnologies: updatedTechs,
        patentOffice: updatedOffice
      };
    });

    if (urlQ !== query) {
      setQuery(urlQ);
    }
    if (urlPage !== page && urlPage > 0) {
      setPage(urlPage);
    }
  }, [searchParams]);

  // Execute Search & Filter logic against real FastAPI backend
  const executeFetch = useCallback(async (isManualTrigger = false) => {
    setIsSearching(true);
    setBackendError(false);

    try {
      const response = await api.search(query, filters, page, pageSize, sortBy, 'hybrid');
      if (response !== null && response.results !== undefined) {
        setResults(response.results);
        setTotalMatching(response.totalMatching ?? response.total ?? response.results.length);
        setTotalPages(Math.max(1, response.totalPages ?? Math.ceil((response.total ?? 0) / pageSize)));
        setIsSearching(false);
      } else {
        setBackendError(true);
        setResults([]);
        setTotalMatching(0);
        setTotalPages(1);
        setIsSearching(false);
      }
    } catch (e) {
      console.warn('Backend search error:', e);
      setBackendError(true);
      setResults([]);
      setTotalMatching(0);
      setTotalPages(1);
      setIsSearching(false);
    }
  }, [query, filters, page, pageSize, sortBy]);

  // Debounced auto-search when filters, query, page, or sort change
  useEffect(() => {
    const timer = setTimeout(() => {
      executeFetch();
    }, 250);

    return () => clearTimeout(timer);
  }, [executeFetch]);

  // Search input submit
  const handleSearchSubmit = (searchQuery) => {
    setQuery(searchQuery);
    setPage(1);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      if (searchQuery) p.set('q', searchQuery);
      else p.delete('q');
      p.set('page', '1');
      return p;
    });
  };

  // Page change
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages || newPage === page) return;
    setPage(newPage);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      p.set('page', String(newPage));
      return p;
    });
    if (resultsTopRef.current) {
      resultsTopRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Page size change
  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize);
    setPage(1);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      p.set('pageSize', String(newSize));
      p.set('page', '1');
      return p;
    });
  };

  // Reset all filters
  const handleResetFilters = () => {
    setQuery('');
    setPage(1);
    setFilters({
      dateType: '',
      priorityDate: '',
      exactDate: '',
      dateFrom: '',
      dateTo: '',
      inventor: '',
      organization: '',
      selectedTechnologies: [],
      patentOffice: '',
      status: 'All'
    });
    setSearchParams({});
  };

  // Explicit Apply button click
  const handleApplyFilters = () => {
    setPage(1);
    setSearchParams(prev => {
      const p = new URLSearchParams();
      if (query.trim()) p.set('q', query.trim());
      if (filters.selectedTechnologies.length > 0) p.set('tech', filters.selectedTechnologies[0]);
      if (filters.patentOffice && filters.patentOffice !== 'All') p.set('office', filters.patentOffice);
      p.set('page', '1');
      return p;
    });
    executeFetch(true);
  };

  return (
    <div className={`min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 transition-colors duration-300 ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Search Header Banner */}
        <div className={`rounded-3xl p-6 sm:p-8 border shadow-lg space-y-4 ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold flex items-center gap-3">
                <SearchIcon className="w-6 h-6 text-[#6b46c1]" />
                Patent Search & Discovery
              </h1>
              <p className={`text-xs sm:text-sm mt-1 ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
                Search Indian patent database across 2016–2018 by technical keywords, inventors, patent offices, or dates.
              </p>
            </div>
            <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#6b46c1]/10 text-[#6b46c1] border border-[#6b46c1]/20 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              AI Hybrid Search
            </div>
          </div>

          <SearchBar
            placeholder="e.g. pharmaceutical container, solar battery, wind turbine generator..."
            value={query}
            onChange={(q) => {
              setQuery(q);
              setPage(1);
            }}
            onSearch={handleSearchSubmit}
            large={true}
            isDarkTheme={isDarkTheme}
          />
        </div>

        {/* Layout Grid: Left Filter Panel + Right Results List */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start" ref={resultsTopRef}>
          
          {/* Left Column: Filter Panel */}
          <div className="lg:col-span-4 xl:col-span-3">
            <FilterPanel
              filters={filters}
              setFilters={(updater) => {
                setPage(1);
                setFilters(updater);
              }}
              onReset={handleResetFilters}
              onApply={handleApplyFilters}
              isDarkTheme={isDarkTheme}
            />
          </div>

          {/* Right Column: Search Results */}
          <div className="lg:col-span-8 xl:col-span-9 space-y-4">
            
            {/* Results Top Info Bar */}
            <div className={`rounded-2xl p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border shadow-xs ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <div className="text-xs sm:text-sm font-medium">
                {isSearching ? (
                  <span className="animate-pulse text-[#6b46c1]">Evaluating Indian patent database...</span>
                ) : (
                  <>
                    Found <strong className="text-[#6b46c1] font-extrabold">{totalMatching.toLocaleString()}</strong> patents
                    {query && <span> for "<span className="font-semibold">{query}</span>"</span>}
                    {filters.selectedTechnologies.length > 0 && (
                      <span> in <span className="font-semibold text-[#6b46c1]">{filters.selectedTechnologies.join(', ')}</span></span>
                    )}
                    {filters.patentOffice && (
                      <span> (IPO <span className="font-semibold text-[#6b46c1]">{filters.patentOffice}</span>)</span>
                    )}
                    <span className="text-slate-400 text-xs ml-2">
                      — Showing page {page} of {totalPages} ({results.length} on this page)
                    </span>
                  </>
                )}
              </div>

              {/* Sort By Dropdown */}
              <div className="flex items-center gap-2 text-xs">
                <SlidersHorizontal className="w-3.5 h-3.5 text-[#6b46c1]" />
                <span className="font-semibold">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value);
                    setPage(1);
                  }}
                  className={`rounded-xl px-3 py-1 text-xs font-semibold focus:outline-none border cursor-pointer ${
                    isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-[#f4effc] border-[#e2d5f8] text-[#2d1f56]'
                  }`}
                >
                  <option value="relevance">Relevance</option>
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                </select>
              </div>
            </div>

            {/* Results Cards List */}
            {isSearching ? (
              <div className={`flex flex-col items-center justify-center py-16 rounded-3xl border ${
                isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
              }`}>
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#6b46c1] mb-3" />
                <p className="text-xs font-semibold text-[#6b46c1]">Evaluating Indian patent database...</p>
              </div>
            ) : backendError ? (
              <div className={`rounded-3xl p-12 text-center space-y-3 border ${
                isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
              }`}>
                <div className="w-14 h-14 bg-rose-500/10 text-rose-500 rounded-2xl flex items-center justify-center mx-auto">
                  <SearchIcon className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold text-rose-500">Backend Server Offline</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Could not connect to the local PatentGraph FastAPI backend at http://localhost:8000. Please ensure the backend service is running.
                </p>
                <button
                  onClick={() => executeFetch(true)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white rounded-xl text-xs font-semibold transition-all shadow-sm cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Retry Connection
                </button>
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  {results.map(patent => (
                    <PatentCard key={patent.id} patent={patent} isDarkTheme={isDarkTheme} />
                  ))}
                </div>

                {/* Server-Side Pagination Bar */}
                {totalPages > 1 && (
                  <div className={`mt-6 p-4 rounded-2xl border flex flex-col sm:flex-row items-center justify-between gap-4 ${
                    isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
                  }`}>
                    {/* Summary */}
                    <div className="text-xs text-slate-400">
                      Page <span className="font-bold text-[#6b46c1]">{page}</span> of <span className="font-bold">{totalPages}</span> ({totalMatching.toLocaleString()} total patents)
                    </div>

                    {/* Pagination buttons */}
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handlePageChange(1)}
                        disabled={page <= 1}
                        className="px-2.5 py-1.5 rounded-xl border text-xs font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#6b46c1] hover:text-white transition-all cursor-pointer"
                        title="First Page"
                      >
                        &laquo;
                      </button>
                      <button
                        onClick={() => handlePageChange(page - 1)}
                        disabled={page <= 1}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-xl border text-xs font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#6b46c1] hover:text-white transition-all cursor-pointer"
                      >
                        &lsaquo; Prev
                      </button>

                      {getPageNumbers(page, totalPages).map((p, idx) => (
                        p === '...' ? (
                          <span key={`ellipsis-${idx}`} className="px-2 text-xs text-slate-400">...</span>
                        ) : (
                          <button
                            key={`page-${p}`}
                            onClick={() => handlePageChange(p)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                              p === page
                                ? 'bg-[#6b46c1] text-white shadow-xs'
                                : isDarkTheme
                                  ? 'border border-[#2b1f4c] hover:bg-[#231845]'
                                  : 'border border-[#e9e1fa] hover:bg-[#f3eefc]'
                            }`}
                          >
                            {p}
                          </button>
                        )
                      ))}

                      <button
                        onClick={() => handlePageChange(page + 1)}
                        disabled={page >= totalPages}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-xl border text-xs font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#6b46c1] hover:text-white transition-all cursor-pointer"
                      >
                        Next &rsaquo;
                      </button>
                      <button
                        onClick={() => handlePageChange(totalPages)}
                        disabled={page >= totalPages}
                        className="px-2.5 py-1.5 rounded-xl border text-xs font-semibold disabled:opacity-30 disabled:cursor-not-allowed hover:bg-[#6b46c1] hover:text-white transition-all cursor-pointer"
                        title="Last Page"
                      >
                        &raquo;
                      </button>
                    </div>

                    {/* Page size dropdown */}
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-400">Per page:</span>
                      <select
                        value={pageSize}
                        onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                        className={`rounded-xl px-2.5 py-1 text-xs font-semibold focus:outline-none border cursor-pointer ${
                          isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-[#f4effc] border-[#e2d5f8] text-[#2d1f56]'
                        }`}
                      >
                        <option value={10}>10</option>
                        <option value={25}>25</option>
                        <option value={50}>50</option>
                        <option value={100}>100</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className={`rounded-3xl p-12 text-center space-y-3 border ${
                isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
              }`}>
                <div className="w-14 h-14 bg-[#f3eefc] text-[#6b46c1] rounded-2xl flex items-center justify-center mx-auto">
                  <SearchIcon className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold">No Matching Patents Found</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  No granted Indian patent records from 2016–2018 matched your search query and filters. Try adjusting your query or resetting filters.
                </p>
                <button
                  onClick={handleResetFilters}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white rounded-xl text-xs font-semibold transition-all shadow-sm cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Reset All Filters
                </button>
              </div>
            )}

          </div>

        </div>

      </div>
    </div>
  );
}

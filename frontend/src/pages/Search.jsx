import { useState, useEffect, useCallback, useRef, useLayoutEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import FilterPanel from '../components/FilterPanel';
import PatentCard from '../components/PatentCard';
import SearchBar from '../components/SearchBar';
import { api } from '../services/api';
import {
  saveSearchState,
  loadSearchState,
  clearSearchState,
  buildStateKey
} from '../hooks/useSearchState';
import { Search as SearchIcon, SlidersHorizontal, Sparkles, RotateCcw } from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

function getPageNumbers(current, total) {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }
  const pages = [];
  pages.push(1);
  if (current > 3) pages.push('...');
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  for (let i = start; i <= end; i++) pages.push(i);
  if (current < total - 2) pages.push('...');
  pages.push(total);
  return pages;
}

const DEFAULT_FILTERS = {
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
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function Search({ isDarkTheme }) {
  const [searchParams, setSearchParams] = useSearchParams();

  // Read URL params (used for direct links / Technology Explorer navigation)
  const urlQuery       = searchParams.get('q') || '';
  const urlTech        = searchParams.get('tech') || '';
  const urlOffice      = searchParams.get('office') || '';
  const urlPriorityYear = searchParams.get('priorityDate') || '';
  const urlPage        = parseInt(searchParams.get('page') || '1', 10);
  const urlPageSize    = parseInt(searchParams.get('pageSize') || '25', 10);
  const urlSortBy      = searchParams.get('sort') || 'relevance';

  const hasUrlParams = Boolean(
    urlQuery.trim() || urlTech || urlOffice || urlPriorityYear ||
    searchParams.get('exactDate') || searchParams.get('dateFrom') ||
    searchParams.get('dateTo') || searchParams.get('inventor') ||
    searchParams.get('org')
  );

  // ── Decide initial state: prefer URL params → then session cache → then blank ─
  const cachedState = loadSearchState();

  // Build filters from URL params (only when URL has something)
  const filtersFromUrl = hasUrlParams ? {
    ...DEFAULT_FILTERS,
    dateType: urlPriorityYear ? 'Priority' : '',
    priorityDate: urlPriorityYear,
    selectedTechnologies: urlTech ? [urlTech] : [],
    patentOffice: urlOffice || ''
  } : null;

  // If URL params match cached state key exactly, we can restore from cache without re-fetching
  const cachedKey = cachedState ? cachedState.stateKey : null;
  const urlStateKey = hasUrlParams ? buildStateKey({
    query: urlQuery,
    filters: filtersFromUrl,
    page: urlPage,
    pageSize: urlPageSize,
    sortBy: urlSortBy
  }) : null;

  const canRestoreCache = !hasUrlParams && cachedState && Array.isArray(cachedState.results) && cachedState.results.length > 0;
  const urlMatchesCache = hasUrlParams && urlStateKey && cachedKey && urlStateKey === cachedKey;

  // Derive initial component state
  const initialQuery   = canRestoreCache ? cachedState.query   : (hasUrlParams ? urlQuery  : '');
  const initialFilters = canRestoreCache ? cachedState.filters : (filtersFromUrl || DEFAULT_FILTERS);
  const initialPage    = canRestoreCache ? cachedState.page    : Math.max(1, urlPage);
  const initialPageSize= canRestoreCache ? cachedState.pageSize: urlPageSize;
  const initialSortBy  = canRestoreCache ? cachedState.sortBy  : urlSortBy;
  const initialResults = (canRestoreCache || urlMatchesCache) ? (cachedState.results || []) : [];
  const initialTotal   = (canRestoreCache || urlMatchesCache) ? (cachedState.totalMatching || 0) : 0;
  const initialTotalPages = (canRestoreCache || urlMatchesCache) ? (cachedState.totalPages || 1) : 1;
  const initialHasSearched = canRestoreCache || urlMatchesCache ? true : hasUrlParams;

  const [query, setQuery]             = useState(initialQuery);
  const [filters, setFilters]         = useState(initialFilters);
  const [page, setPage]               = useState(initialPage);
  const [pageSize, setPageSize]       = useState(initialPageSize);
  const [sortBy, setSortBy]           = useState(initialSortBy);
  const [results, setResults]         = useState(initialResults);
  const [totalMatching, setTotalMatching] = useState(initialTotal);
  const [totalPages, setTotalPages]   = useState(initialTotalPages);
  const [hasSearched, setHasSearched] = useState(initialHasSearched);
  const [isSearching, setIsSearching] = useState(hasUrlParams && !canRestoreCache && !urlMatchesCache);
  const [backendError, setBackendError] = useState(false);

  // Track whether the initial render is using cached results (to skip auto-fetch)
  const isRestoredFromCache = useRef(canRestoreCache || urlMatchesCache);

  const resultsTopRef = useRef(null);
  const scrollRestoredRef = useRef(false);

  // ── Restore scroll position after cached results render ───────────────────
  useLayoutEffect(() => {
    if (isRestoredFromCache.current && !scrollRestoredRef.current && cachedState?.scrollY != null) {
      scrollRestoredRef.current = true;
      // Defer to after paint so the result list has fully rendered
      requestAnimationFrame(() => {
        window.scrollTo({ top: cachedState.scrollY, behavior: 'instant' });
      });
    }
  }, [results]);

  // ── Persist state to session storage whenever key search data changes ─────
  useEffect(() => {
    if (!hasSearched || results.length === 0) return;
    const key = buildStateKey({ query, filters, page, pageSize, sortBy });
    saveSearchState({
      stateKey: key,
      query,
      filters,
      page,
      pageSize,
      sortBy,
      results,
      totalMatching,
      totalPages,
      scrollY: window.scrollY
    });
  }, [results, query, filters, page, pageSize, sortBy, totalMatching, totalPages, hasSearched]);

  // ── Sync URL when Technology Explorer sets URL params externally ──────────
  useEffect(() => {
    const uTech     = searchParams.get('tech');
    const uOffice   = searchParams.get('office');
    const uPage     = parseInt(searchParams.get('page') || '1', 10);
    const uQ        = searchParams.get('q') || '';
    const uPriority = searchParams.get('priorityDate') || '';

    const hasParams = Boolean(uTech || uOffice || uQ || uPriority);
    if (!hasParams) return;

    // External navigation changed URL — flush cache and re-fetch
    isRestoredFromCache.current = false;
    setHasSearched(true);

    setFilters(prev => ({
      ...prev,
      selectedTechnologies: uTech ? [uTech] : prev.selectedTechnologies,
      patentOffice: uOffice !== null ? uOffice : prev.patentOffice,
      priorityDate: uPriority || prev.priorityDate,
      dateType: uPriority ? 'Priority' : prev.dateType
    }));

    if (uQ !== query) setQuery(uQ);
    if (uPage !== page && uPage > 0) setPage(uPage);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // ── Core fetch function ───────────────────────────────────────────────────
  const executeFetch = useCallback(async () => {
    setIsSearching(true);
    setBackendError(false);
    try {
      const response = await api.search(query, filters, page, pageSize, sortBy, 'hybrid');
      if (response !== null && response.results !== undefined) {
        setResults(response.results);
        setTotalMatching(response.totalMatching ?? response.total ?? response.results.length);
        setTotalPages(Math.max(1, response.totalPages ?? Math.ceil((response.total ?? 0) / pageSize)));
      } else {
        setBackendError(true);
        setResults([]);
        setTotalMatching(0);
        setTotalPages(1);
      }
    } catch (e) {
      console.warn('Backend search error:', e);
      setBackendError(true);
      setResults([]);
      setTotalMatching(0);
      setTotalPages(1);
    } finally {
      setIsSearching(false);
    }
  }, [query, filters, page, pageSize, sortBy]);

  // ── Auto-trigger search (debounced) when criteria change ─────────────────
  useEffect(() => {
    const hasCriteria = Boolean(
      query.trim() ||
      filters.selectedTechnologies.length > 0 ||
      (filters.patentOffice && filters.patentOffice !== 'All') ||
      filters.priorityDate || filters.exactDate ||
      filters.dateFrom || filters.dateTo ||
      filters.inventor.trim() || filters.organization.trim()
    );

    // If we just restored from cache, skip the fetch for this render cycle only
    if (isRestoredFromCache.current) {
      isRestoredFromCache.current = false;
      return;
    }

    if (!hasSearched && !hasCriteria) {
      setIsSearching(false);
      return;
    }

    const timer = setTimeout(() => {
      setHasSearched(true);
      executeFetch();
    }, 250);

    return () => clearTimeout(timer);
  // executeFetch is stable (useCallback) — include it.
  }, [executeFetch, hasSearched, query, filters]);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSearchSubmit = (searchQuery) => {
    isRestoredFromCache.current = false;
    setQuery(searchQuery);
    setPage(1);
    setHasSearched(true);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      if (searchQuery) p.set('q', searchQuery);
      else p.delete('q');
      p.set('page', '1');
      p.set('sort', sortBy);
      return p;
    });
  };

  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages || newPage === page) return;
    isRestoredFromCache.current = false;
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

  const handlePageSizeChange = (newSize) => {
    isRestoredFromCache.current = false;
    setPageSize(newSize);
    setPage(1);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      p.set('pageSize', String(newSize));
      p.set('page', '1');
      return p;
    });
  };

  const handleSortChange = (newSort) => {
    isRestoredFromCache.current = false;
    setSortBy(newSort);
    setPage(1);
    setSearchParams(prev => {
      const p = new URLSearchParams(prev);
      p.set('sort', newSort);
      p.set('page', '1');
      return p;
    });
  };

  const handleResetFilters = () => {
    clearSearchState();
    isRestoredFromCache.current = false;
    setQuery('');
    setPage(1);
    setPageSize(25);
    setSortBy('relevance');
    setFilters({ ...DEFAULT_FILTERS });
    setResults([]);
    setTotalMatching(0);
    setTotalPages(1);
    setHasSearched(false);
    setIsSearching(false);
    setBackendError(false);
    setSearchParams({});
  };

  const handleApplyFilters = () => {
    isRestoredFromCache.current = false;
    setPage(1);
    setHasSearched(true);
    setSearchParams(prev => {
      const p = new URLSearchParams();
      if (query.trim()) p.set('q', query.trim());
      if (filters.selectedTechnologies.length > 0) p.set('tech', filters.selectedTechnologies[0]);
      if (filters.patentOffice && filters.patentOffice !== 'All') p.set('office', filters.patentOffice);
      if (filters.priorityDate) p.set('priorityDate', filters.priorityDate);
      p.set('page', '1');
      p.set('sort', sortBy);
      return p;
    });
    executeFetch();
  };

  // ── Render ────────────────────────────────────────────────────────────────

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
                Patent Search &amp; Discovery
              </h1>
              <p className={`text-xs sm:text-sm mt-1 ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
                Search Indian patent database across 2016–2023 by technical keywords, inventors, patent offices, or priority year.
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
                isRestoredFromCache.current = false;
                setFilters(updater);
              }}
              onReset={handleResetFilters}
              onApply={handleApplyFilters}
              isDarkTheme={isDarkTheme}
            />
          </div>

          {/* Right Column: Search Results */}
          <div className="lg:col-span-8 xl:col-span-9 space-y-4">

            {/* 1. INITIAL EMPTY STATE BEFORE SEARCH */}
            {!hasSearched && !isSearching ? (
              <div className={`rounded-3xl p-10 sm:p-14 border text-center shadow-sm space-y-5 ${
                isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
              }`}>
                <div className="w-16 h-16 rounded-2xl bg-[#6b46c1]/10 text-[#6b46c1] border border-[#6b46c1]/20 flex items-center justify-center mx-auto shadow-inner">
                  <SearchIcon className="w-8 h-8" />
                </div>
                <div className="max-w-md mx-auto space-y-2">
                  <h3 className="text-xl font-extrabold">Search Indian Patent Database</h3>
                  <p className={`text-xs sm:text-sm ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
                    Search patents by keyword, technology domain, or priority year.
                  </p>
                </div>
                <div className="pt-3 max-w-lg mx-auto">
                  <p className="text-[11px] font-semibold text-slate-400 mb-2.5 uppercase tracking-wider">
                    Explore Official Technology Domains
                  </p>
                  <div className="flex flex-wrap items-center justify-center gap-2">
                    {['Chemistry', 'Mechanical', 'Electronics', 'Computer', 'Biotechnology', 'Biomedical'].map((tech) => (
                      <button
                        key={tech}
                        onClick={() => {
                          isRestoredFromCache.current = false;
                          setFilters(prev => ({ ...prev, selectedTechnologies: [tech] }));
                          setHasSearched(true);
                        }}
                        className={`text-xs font-semibold px-3.5 py-1.5 rounded-xl border transition-all cursor-pointer ${
                          isDarkTheme
                            ? 'bg-[#231845] border-[#382969] text-purple-200 hover:border-[#6b46c1]'
                            : 'bg-[#f4effc] border-[#e2d5f8] text-[#553c9a] hover:border-[#6b46c1]'
                        }`}
                      >
                        {tech}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <>
                {/* Results Top Info Bar */}
                <div className={`rounded-2xl p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border shadow-xs ${
                  isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
                }`}>
                  <div className="text-xs sm:text-sm font-medium">
                    {isSearching ? (
                      <span className="animate-pulse text-[#6b46c1] font-semibold">Evaluating Indian patent database...</span>
                    ) : (
                      <>
                        Found <strong className="text-[#6b46c1] font-extrabold">{totalMatching.toLocaleString()}</strong> patents
                        {query && <span> for &quot;<span className="font-semibold">{query}</span>&quot;</span>}
                        {filters.selectedTechnologies.length > 0 && (
                          <span> in <span className="font-semibold text-[#6b46c1]">{filters.selectedTechnologies.join(', ')}</span></span>
                        )}
                        {filters.patentOffice && (
                          <span> (IPO <span className="font-semibold text-[#6b46c1]">{filters.patentOffice}</span>)</span>
                        )}
                        {filters.priorityDate && (
                          <span> (Priority Year: <span className="font-semibold text-[#6b46c1]">{filters.priorityDate}</span>)</span>
                        )}
                        <span className="text-slate-400 text-xs ml-2">
                          — Showing page {page} of {totalPages} ({results.length} on this page)
                        </span>
                        {/* Session restore badge */}
                        {(canRestoreCache || urlMatchesCache) && !isSearching && (
                          <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 text-[10px] font-semibold">
                            ✓ Session restored
                          </span>
                        )}
                      </>
                    )}
                  </div>

                  {/* Sort By Dropdown */}
                  <div className="flex items-center gap-2 text-xs">
                    <SlidersHorizontal className="w-3.5 h-3.5 text-[#6b46c1]" />
                    <span className="font-semibold">Sort:</span>
                    <select
                      value={sortBy}
                      onChange={(e) => handleSortChange(e.target.value)}
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

                {/* Results List / Loading / Error / Empty Results */}
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
                      onClick={() => executeFetch()}
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
                      No granted Indian patent records matched your search query and filters. Try adjusting your query or resetting filters.
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
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

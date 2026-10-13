import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import FilterPanel from '../components/FilterPanel';
import PatentCard from '../components/PatentCard';
import SearchBar from '../components/SearchBar';
import { patents } from '../data/patents';
import { api } from '../services/api';
import { Search as SearchIcon, SlidersHorizontal, Sparkles, RotateCcw } from 'lucide-react';

export default function Search({ isDarkTheme }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialTech = searchParams.get('tech') || '';

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
    patentOffice: '',
    status: 'All'
  });

  const [results, setResults] = useState(patents);
  const [isSearching, setIsSearching] = useState(false);
  const [sortBy, setSortBy] = useState('relevance');

  // Handle URL tech parameter
  useEffect(() => {
    if (initialTech && !filters.selectedTechnologies.includes(initialTech)) {
      setFilters(prev => ({
        ...prev,
        selectedTechnologies: [initialTech]
      }));
    }
  }, [initialTech]);

  // Execute Search & Filter logic against real FastAPI backend
  useEffect(() => {
    setIsSearching(true);

    const timer = setTimeout(async () => {
      try {
        const backendResults = await api.search(query, filters, 40, 'hybrid');
        if (backendResults && backendResults.length > 0) {
          let sorted = [...backendResults];
          if (sortBy === 'newest') {
            sorted.sort((a, b) => new Date(b.filingDate || 0) - new Date(a.filingDate || 0));
          } else if (sortBy === 'oldest') {
            sorted.sort((a, b) => new Date(a.filingDate || 0) - new Date(b.filingDate || 0));
          } else {
            sorted.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));
          }
          setResults(sorted);
          setIsSearching(false);
          return;
        }
      } catch (e) {
        console.warn('Backend search error, falling back to local dataset:', e);
      }

      // Fallback local filtering
      let filtered = [...patents];

      // 1. Natural Query
      if (query.trim()) {
        const lowerQ = query.toLowerCase();
        filtered = filtered.filter(p =>
          p.title.toLowerCase().includes(lowerQ) ||
          p.abstract.toLowerCase().includes(lowerQ) ||
          p.patentNumber.toLowerCase().includes(lowerQ) ||
          p.inventor.toLowerCase().includes(lowerQ) ||
          p.organization.toLowerCase().includes(lowerQ) ||
          p.technology.some(t => t.toLowerCase().includes(lowerQ))
        );
      }

      // 2. Dynamic Date Filtering
      if (filters.dateType === 'Priority' && filters.priorityDate) {
        filtered = filtered.filter(p => p.filingDate <= filters.priorityDate);
      } else if (filters.dateType === 'Exact Date' && filters.exactDate) {
        filtered = filtered.filter(p => p.filingDate === filters.exactDate);
      } else if (filters.dateType === 'Range') {
        if (filters.dateFrom) filtered = filtered.filter(p => p.filingDate >= filters.dateFrom);
        if (filters.dateTo) filtered = filtered.filter(p => p.filingDate <= filters.dateTo);
      }

      // 3. Inventor Search
      if (filters.inventor.trim()) {
        const invQ = filters.inventor.toLowerCase();
        filtered = filtered.filter(p => p.inventor.toLowerCase().includes(invQ));
      }

      // 4. Organisation Search
      if (filters.organization.trim()) {
        const orgQ = filters.organization.toLowerCase();
        filtered = filtered.filter(p => p.organization.toLowerCase().includes(orgQ));
      }

      // 5. Technology Multi-Select
      if (filters.selectedTechnologies.length > 0) {
        filtered = filtered.filter(p =>
          filters.selectedTechnologies.every(selectedTech =>
            p.technology.some(t => t.toLowerCase() === selectedTech.toLowerCase())
          )
        );
      }

      // 6. Patent Office (Country)
      if (filters.patentOffice) {
        filtered = filtered.filter(p => 
          p.patentOffice.toLowerCase() === filters.patentOffice.toLowerCase()
        );
      }

      // 7. Status Radio
      if (filters.status && filters.status !== 'All') {
        filtered = filtered.filter(p => 
          p.status.toLowerCase() === filters.status.toLowerCase()
        );
      }

      // Sort
      if (sortBy === 'newest') {
        filtered.sort((a, b) => new Date(b.filingDate) - new Date(a.filingDate));
      } else if (sortBy === 'oldest') {
        filtered.sort((a, b) => new Date(a.filingDate) - new Date(b.filingDate));
      } else {
        filtered.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));
      }

      setResults(filtered);
      setIsSearching(false);
    }, 250);

    return () => clearTimeout(timer);
  }, [query, filters, sortBy]);

  const handleSearchSubmit = (searchQuery) => {
    setQuery(searchQuery);
    setSearchParams(searchQuery ? { q: searchQuery } : {});
  };

  const handleResetFilters = () => {
    setQuery('');
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
                Search natural language queries, keywords, patent numbers, inventors, or patent offices.
              </p>
            </div>
            <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#6b46c1]/10 text-[#6b46c1] border border-[#6b46c1]/20 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              AI Natural Language Search
            </div>
          </div>

          <SearchBar
            placeholder="e.g. AI based crop disease detection using drones..."
            value={query}
            onChange={setQuery}
            onSearch={handleSearchSubmit}
            large={true}
            isDarkTheme={isDarkTheme}
          />
        </div>

        {/* Layout Grid: Left Filter Panel + Right Results List */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Filter Panel */}
          <div className="lg:col-span-4 xl:col-span-3">
            <FilterPanel
              filters={filters}
              setFilters={setFilters}
              onReset={handleResetFilters}
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
                  <span className="animate-pulse text-[#6b46c1]">Evaluating patent database...</span>
                ) : (
                  <>
                    Found <strong className="text-[#6b46c1] font-extrabold">{results.length}</strong> patents
                    {query && <span> for "<span className="font-semibold">{query}</span>"</span>}
                  </>
                )}
              </div>

              {/* Sort By Dropdown */}
              <div className="flex items-center gap-2 text-xs">
                <SlidersHorizontal className="w-3.5 h-3.5 text-[#6b46c1]" />
                <span className="font-semibold">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
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
                <p className="text-xs font-semibold text-[#6b46c1]">Processing search filters...</p>
              </div>
            ) : results.length > 0 ? (
              <div className="grid grid-cols-1 gap-4">
                {results.map(patent => (
                  <PatentCard key={patent.id} patent={patent} isDarkTheme={isDarkTheme} />
                ))}
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
                  Try adjusting your search query or choosing different date and technology filters.
                </p>
                <button
                  onClick={handleResetFilters}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white rounded-xl text-xs font-semibold transition-all shadow-sm"
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

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import PatentCard from '../components/PatentCard';
import FilterPanel from '../components/FilterPanel';
import { patents } from '../data/patents';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState(patents);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery);
    }
  }, [initialQuery]);

  const handleSearch = (searchQuery) => {
    setIsSearching(true);
    setQuery(searchQuery);
    setSearchParams(searchQuery ? { q: searchQuery } : {});
    
    // Simulate network delay and simple filtering
    setTimeout(() => {
      if (!searchQuery.trim()) {
        setResults(patents);
      } else {
        const lowerQuery = searchQuery.toLowerCase();
        const filtered = patents.filter(p => 
          p.title.toLowerCase().includes(lowerQuery) || 
          p.abstract.toLowerCase().includes(lowerQuery) ||
          p.technology.some(t => t.toLowerCase().includes(lowerQuery))
        );
        setResults(filtered);
      }
      setIsSearching(false);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header Search Area */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 mb-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-6">Search Indian Patents</h1>
          <SearchBar 
            placeholder="Search by patent, technology, inventor or ask a question..." 
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
          />
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="w-full lg:w-1/4">
            <FilterPanel />
          </div>
          
          {/* Results Area */}
          <div className="w-full lg:w-3/4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-medium text-slate-700">
                {isSearching ? 'Searching...' : (
                  <>
                    <span className="font-bold text-slate-900">{results.length}</span> patents found
                    {query && <span> for "<span className="text-indigo-600">{query}</span>"</span>}
                  </>
                )}
              </h2>
              
              <div className="flex items-center text-sm text-slate-500">
                <span>Sort by:</span>
                <select className="ml-2 bg-transparent border-none font-medium text-slate-900 focus:ring-0 cursor-pointer">
                  <option>Relevance</option>
                  <option>Newest First</option>
                  <option>Oldest First</option>
                </select>
              </div>
            </div>

            {isSearching ? (
              <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
              </div>
            ) : results.length > 0 ? (
              <div className="grid grid-cols-1 gap-6">
                {results.map(patent => (
                  <PatentCard key={patent.id} patent={patent} />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-1">No patents found</h3>
                <p className="text-slate-500">Try adjusting your search terms or filters.</p>
                <button 
                  onClick={() => handleSearch('')}
                  className="mt-4 text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  Clear search
                </button>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

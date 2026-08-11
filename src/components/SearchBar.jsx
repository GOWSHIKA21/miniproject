import { Search, ArrowRight } from 'lucide-react';

export default function SearchBar({ placeholder, onSearch, value, onChange, large = false }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(value);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto relative group">
      <div className={`absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none ${large ? 'pl-6' : 'pl-4'}`}>
        <Search className={`text-slate-400 group-focus-within:text-indigo-500 transition-colors ${large ? 'w-6 h-6' : 'w-5 h-5'}`} />
      </div>
      <input
        type="text"
        className={`block w-full bg-white border border-slate-300 rounded-full text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all shadow-sm group-hover:shadow-md ${
          large ? 'py-4 pl-14 pr-32 text-lg' : 'py-3 pl-12 pr-24 text-base'
        }`}
        placeholder={placeholder || 'Search...'}
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
      />
      <div className="absolute inset-y-0 right-2 flex items-center">
        <button
          type="submit"
          className={`inline-flex items-center justify-center border border-transparent rounded-full shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all ${
            large ? 'px-6 py-2.5 text-base font-medium' : 'px-4 py-1.5 text-sm font-medium'
          }`}
        >
          Search
          {large && <ArrowRight className="ml-2 -mr-1 w-5 h-5" />}
        </button>
      </div>
    </form>
  );
}

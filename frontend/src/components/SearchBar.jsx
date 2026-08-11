import { Search, ArrowRight } from 'lucide-react';

export default function SearchBar({ placeholder, onSearch, value, onChange, large = false, isDarkTheme }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSearch) onSearch(value || '');
  };

  return (
    <form onSubmit={handleSubmit} className="w-full relative group">
      <div className={`absolute inset-y-0 left-0 flex items-center pointer-events-none ${large ? 'pl-5' : 'pl-4'}`}>
        <Search className={`text-[#6b46c1] transition-colors ${large ? 'w-5 h-5' : 'w-4 h-4'}`} />
      </div>

      <input
        type="text"
        className={`block w-full rounded-2xl border transition-all focus:outline-none focus:ring-2 focus:ring-[#6b46c1] shadow-xs ${
          large ? 'py-3.5 pl-12 pr-32 text-xs sm:text-sm' : 'py-2.5 pl-10 pr-24 text-xs'
        } ${
          isDarkTheme 
            ? 'bg-[#231845] border-[#382969] text-white placeholder-slate-400' 
            : 'bg-[#f4effc] border-[#e2d5f8] text-[#2d1f56] placeholder-slate-400'
        }`}
        placeholder={placeholder || 'Search by keywords, natural query, inventor, or patent office...'}
        value={value || ''}
        onChange={(e) => onChange && onChange(e.target.value)}
      />

      <div className="absolute inset-y-0 right-1.5 flex items-center">
        <button
          type="submit"
          className={`inline-flex items-center justify-center border border-transparent rounded-xl font-bold text-white bg-[#6b46c1] hover:bg-[#553c9a] focus:outline-none transition-all shadow-xs ${
            large ? 'px-5 py-2 text-xs sm:text-sm' : 'px-3.5 py-1.5 text-xs'
          }`}
        >
          Search
          {large && <ArrowRight className="ml-1.5 w-3.5 h-3.5" />}
        </button>
      </div>
    </form>
  );
}

import { useState, useRef, useEffect } from 'react';
import { ALL_TECHNOLOGIES, PATENT_OFFICES, STATUS_OPTIONS } from '../data/patents';
import { Filter, Calendar, User, Building2, Cpu, Globe, CheckCircle2, X, Search, RotateCcw, ChevronDown } from 'lucide-react';

export default function FilterPanel({ filters, setFilters, onReset, isDarkTheme }) {
  // Local state for technology search inside multi-select dropdown
  const [techQuery, setTechQuery] = useState('');
  const [techDropdownOpen, setTechDropdownOpen] = useState(false);
  
  // Local state for country office search inside dropdown
  const [officeQuery, setOfficeQuery] = useState('');
  const [officeDropdownOpen, setOfficeDropdownOpen] = useState(false);

  const techDropdownRef = useRef(null);
  const officeDropdownRef = useRef(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (techDropdownRef.current && !techDropdownRef.current.contains(event.target)) {
        setTechDropdownOpen(false);
      }
      if (officeDropdownRef.current && !officeDropdownRef.current.contains(event.target)) {
        setOfficeDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filtered technology list for search input
  const filteredTechs = ALL_TECHNOLOGIES.filter(t =>
    t.toLowerCase().includes(techQuery.toLowerCase()) &&
    !filters.selectedTechnologies.includes(t)
  );

  // Filtered patent offices for country dropdown
  const filteredOffices = PATENT_OFFICES.filter(country =>
    country.toLowerCase().includes(officeQuery.toLowerCase())
  );

  const handleAddTechnology = (tech) => {
    setFilters(prev => ({
      ...prev,
      selectedTechnologies: [...prev.selectedTechnologies, tech]
    }));
    setTechQuery('');
  };

  const handleRemoveTechnology = (techToRemove) => {
    setFilters(prev => ({
      ...prev,
      selectedTechnologies: prev.selectedTechnologies.filter(t => t !== techToRemove)
    }));
  };

  // Date Type change handler
  const handleDateTypeChange = (newType) => {
    setFilters(prev => ({
      ...prev,
      dateType: newType,
      priorityDate: '',
      exactDate: '',
      dateFrom: '',
      dateTo: ''
    }));
  };

  return (
    <div className={`rounded-3xl p-5 sm:p-6 border shadow-lg space-y-5 ${
      isDarkTheme 
        ? 'bg-[#18112e] border-[#2b1f4c] text-white' 
        : 'bg-white border-[#e9e1fa] text-[#2d1f56]'
    }`}>
      
      {/* Filter Panel Header */}
      <div className="flex items-center justify-between pb-3.5 border-b border-[#e9e1fa]/40">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-xl bg-[#f3eefc] text-[#6b46c1] border border-[#e2d5f8]">
            <Filter className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-extrabold">Filter Patents</h2>
          </div>
        </div>

        <button
          onClick={onReset}
          className="flex items-center gap-1 text-xs font-semibold text-[#6b46c1] hover:underline p-1"
          title="Reset all filters"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset
        </button>
      </div>

      {/* 1. DYNAMIC DATE FILTER WITH DROPDOWN (Requirement 4 & 5) */}
      <div className="space-y-3">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#6b46c1] flex items-center gap-1.5">
          <Calendar className="w-4 h-4" />
          Date Filter
        </label>
        
        {/* Date Type Select Dropdown */}
        <div className="relative">
          <select
            value={filters.dateType || ''}
            onChange={(e) => handleDateTypeChange(e.target.value)}
            className={`w-full rounded-xl px-3.5 py-2.5 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-[#6b46c1] border cursor-pointer ${
              isDarkTheme
                ? 'bg-[#231845] border-[#382969] text-white'
                : 'bg-[#f4effc] border-[#e2d5f8] text-[#2d1f56]'
            }`}
          >
            <option value="">Select Date Type ▼</option>
            <option value="Priority">Priority</option>
            <option value="Exact Date">Exact Date</option>
            <option value="Range">Range</option>
          </select>
        </div>

        {/* CONDITIONALLY RENDERED DATE PICKERS BASED ON SELECTION */}
        {filters.dateType === 'Priority' && (
          <div className="space-y-1 animate-fade-in pt-1">
            <span className="text-[11px] font-bold text-[#6b46c1]">Priority Date</span>
            <div className="relative">
              <input
                type="date"
                value={filters.priorityDate || ''}
                onChange={(e) => setFilters({ ...filters, priorityDate: e.target.value })}
                className={`w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
                  isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56]'
                }`}
              />
            </div>
          </div>
        )}

        {filters.dateType === 'Exact Date' && (
          <div className="space-y-1 animate-fade-in pt-1">
            <span className="text-[11px] font-bold text-[#6b46c1]">Exact Date</span>
            <div className="relative">
              <input
                type="date"
                value={filters.exactDate || ''}
                onChange={(e) => setFilters({ ...filters, exactDate: e.target.value })}
                className={`w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
                  isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56]'
                }`}
              />
            </div>
          </div>
        )}

        {filters.dateType === 'Range' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 animate-fade-in pt-1">
            <div className="space-y-1">
              <span className="text-[11px] font-bold text-[#6b46c1]">From</span>
              <input
                type="date"
                value={filters.dateFrom || ''}
                onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
                className={`w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
                  isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56]'
                }`}
              />
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-bold text-[#6b46c1]">To</span>
              <input
                type="date"
                value={filters.dateTo || ''}
                onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
                className={`w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
                  isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56]'
                }`}
              />
            </div>
          </div>
        )}
      </div>

      {/* 2. Inventor Search Input */}
      <div className="space-y-1.5">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#6b46c1] flex items-center gap-1.5">
          <User className="w-4 h-4" />
          Inventor
        </label>
        <input
          type="text"
          placeholder="Search inventor..."
          value={filters.inventor || ''}
          onChange={(e) => setFilters({ ...filters, inventor: e.target.value })}
          className={`w-full rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
            isDarkTheme ? 'bg-[#231845] border-[#382969] text-white placeholder-slate-400' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56] placeholder-slate-400'
          }`}
        />
      </div>

      {/* 3. Organisation / Applicant Search Input */}
      <div className="space-y-1.5">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#6b46c1] flex items-center gap-1.5">
          <Building2 className="w-4 h-4" />
          Organisation
        </label>
        <input
          type="text"
          placeholder="Search organisation..."
          value={filters.organization || ''}
          onChange={(e) => setFilters({ ...filters, organization: e.target.value })}
          className={`w-full rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
            isDarkTheme ? 'bg-[#231845] border-[#382969] text-white placeholder-slate-400' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56] placeholder-slate-400'
          }`}
        />
      </div>

      {/* 4. Technology Searchable Multi-Select Input */}
      <div className="space-y-1.5" ref={techDropdownRef}>
        <label className="block text-xs font-bold uppercase tracking-wider text-[#6b46c1] flex items-center gap-1.5">
          <Cpu className="w-4 h-4" />
          Technology Domain
        </label>

        {/* Selected Technology Chips */}
        {filters.selectedTechnologies.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-1.5">
            {filters.selectedTechnologies.map((tech) => (
              <span
                key={tech}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#6b46c1] text-white shadow-xs"
              >
                {tech}
                <button
                  type="button"
                  onClick={() => handleRemoveTechnology(tech)}
                  className="hover:text-purple-200 p-0.5 rounded-full hover:bg-purple-800 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Technology Search Input Box */}
        <div className="relative">
          <div className="relative flex items-center">
            <Search className="absolute left-3 w-3.5 h-3.5 text-[#6b46c1]" />
            <input
              type="text"
              placeholder="🔎 Search technology..."
              value={techQuery}
              onFocus={() => setTechDropdownOpen(true)}
              onChange={(e) => {
                setTechQuery(e.target.value);
                setTechDropdownOpen(true);
              }}
              className={`w-full rounded-xl pl-9 pr-8 py-2 text-xs focus:outline-none focus:border-[#6b46c1] border ${
                isDarkTheme ? 'bg-[#231845] border-[#382969] text-white placeholder-slate-400' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56] placeholder-slate-400'
              }`}
            />
            <ChevronDown className="absolute right-3 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
          </div>

          {/* Technology Dropdown Menu */}
          {techDropdownOpen && (
            <div className={`absolute z-30 left-0 right-0 mt-1 max-h-48 overflow-y-auto border rounded-2xl shadow-2xl p-1.5 space-y-0.5 ${
              isDarkTheme ? 'bg-[#1e153b] border-[#382969]' : 'bg-white border-[#e2d5f8]'
            }`}>
              {filteredTechs.length > 0 ? (
                filteredTechs.map((tech) => (
                  <button
                    key={tech}
                    type="button"
                    onClick={() => handleAddTechnology(tech)}
                    className={`w-full text-left px-3 py-1.5 text-xs font-medium rounded-xl transition-colors flex items-center justify-between ${
                      isDarkTheme ? 'text-slate-200 hover:bg-[#2e2057]' : 'text-[#2d1f56] hover:bg-[#f4effc]'
                    }`}
                  >
                    <span>{tech}</span>
                    <span className="text-[10px] text-[#6b46c1] font-bold">+ Add</span>
                  </button>
                ))
              ) : (
                <div className="px-3 py-2 text-xs text-slate-400 text-center">
                  No matching technologies
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 5. Patent Office Searchable Country Dropdown */}
      <div className="space-y-1.5" ref={officeDropdownRef}>
        <label className="block text-xs font-bold uppercase tracking-wider text-[#6b46c1] flex items-center gap-1.5">
          <Globe className="w-4 h-4" />
          Patent Office
        </label>

        <div className="relative">
          <div 
            onClick={() => setOfficeDropdownOpen(!officeDropdownOpen)}
            className={`w-full rounded-xl px-3.5 py-2 text-xs font-medium cursor-pointer flex items-center justify-between border ${
              isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56]'
            }`}
          >
            <span className={filters.patentOffice ? "font-bold text-[#6b46c1]" : "text-slate-400"}>
              {filters.patentOffice || "All Patent Offices"}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </div>

          {officeDropdownOpen && (
            <div className={`absolute z-30 left-0 right-0 mt-1 border rounded-2xl shadow-2xl p-2 space-y-2 ${
              isDarkTheme ? 'bg-[#1e153b] border-[#382969]' : 'bg-white border-[#e2d5f8]'
            }`}>
              <input
                type="text"
                placeholder="Search country..."
                value={officeQuery}
                onChange={(e) => setOfficeQuery(e.target.value)}
                className={`w-full rounded-xl px-3 py-1.5 text-xs focus:outline-none border ${
                  isDarkTheme ? 'bg-[#120c24] border-[#382969] text-white' : 'bg-slate-50 border-[#e2d5f8] text-[#2d1f56]'
                }`}
              />

              <div className="max-h-40 overflow-y-auto space-y-0.5">
                <button
                  type="button"
                  onClick={() => {
                    setFilters({ ...filters, patentOffice: '' });
                    setOfficeDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 text-xs rounded-xl ${
                    !filters.patentOffice ? 'bg-[#6b46c1] text-white font-bold' : 'hover:bg-[#f4effc]'
                  }`}
                >
                  All Patent Offices
                </button>

                {filteredOffices.map((country) => (
                  <button
                    key={country}
                    type="button"
                    onClick={() => {
                      setFilters({ ...filters, patentOffice: country });
                      setOfficeDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 text-xs rounded-xl ${
                      filters.patentOffice === country
                        ? 'bg-[#6b46c1] text-white font-bold'
                        : 'hover:bg-[#f4effc]'
                    }`}
                  >
                    {country}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 6. Patent Status Radio Buttons */}
      <div className="space-y-2 pt-2 border-t border-[#e9e1fa]/40">
        <label className="block text-xs font-bold uppercase tracking-wider text-[#6b46c1] flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4" />
          Patent Status
        </label>
        <div className="space-y-1.5">
          {STATUS_OPTIONS.map((status) => {
            const isChecked = 
              (status === 'All' && (!filters.status || filters.status === 'All')) ||
              filters.status === status;

            return (
              <label 
                key={status}
                className={`flex items-center px-3 py-1.5 rounded-xl text-xs cursor-pointer border transition-all ${
                  isChecked
                    ? 'bg-[#6b46c1] text-white font-bold border-[#6b46c1]'
                    : isDarkTheme
                      ? 'bg-[#231845]/50 border-[#382969] text-slate-300 hover:bg-[#281c4e]'
                      : 'bg-slate-50 border-[#e2d5f8] text-[#4a367c] hover:bg-[#f4effc]'
                }`}
              >
                <input
                  type="radio"
                  name="status"
                  value={status}
                  checked={isChecked}
                  onChange={() => setFilters({ ...filters, status })}
                  className="w-3.5 h-3.5 text-[#6b46c1] focus:ring-[#6b46c1]"
                />
                <span className="ml-2.5">{status}</span>
              </label>
            );
          })}
        </div>
      </div>

    </div>
  );
}

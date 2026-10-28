import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ALL_TECHNOLOGIES } from '../data/patents';
import { api } from '../services/api';
import { Cpu, Search, ArrowUpRight, Layers, Sparkles } from 'lucide-react';

export default function Explorer({ isDarkTheme }) {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [backendStats, setBackendStats] = useState(null);

  useEffect(() => {
    async function loadStats() {
      const data = await api.getStats();
      if (data && data.field_counts) {
        setBackendStats(data);
      }
    }
    loadStats();
  }, []);

  // Show only domains genuinely represented in the dataset with valid matching patents (> 0)
  const techStats = ALL_TECHNOLOGIES.map(tech => {
    const upperTech = tech.toUpperCase();
    const realCount = backendStats?.field_counts?.[upperTech];

    return {
      name: tech,
      count: realCount !== undefined ? realCount : 0,
      isReal: realCount !== undefined && realCount > 0
    };
  }).filter(t => !backendStats || t.count > 0);

  const filteredTechnologies = techStats.filter(t => 
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleTechClick = (techName) => {
    navigate(`/search?tech=${encodeURIComponent(techName)}`);
  };

  return (
    <div className={`min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 space-y-6 ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className={`rounded-3xl p-6 sm:p-8 border shadow-lg ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#6b46c1]/10 text-[#6b46c1] border border-[#6b46c1]/20 text-xs font-semibold mb-3">
            <Cpu className="w-3.5 h-3.5" />
            Technology Explorer & Taxonomy
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold mb-2">
            Explore {filteredTechnologies.length} Official Technology Domains
          </h1>
          <p className={`text-xs sm:text-sm max-w-2xl ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
            Browse verified Indian Patent Office technology fields with matching granted records and filter searches directly.
          </p>

          <div className="mt-6 relative max-w-lg">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6b46c1]" />
            <input
              type="text"
              placeholder="Filter domains e.g. Chemistry, Computer, Electronics, Biotechnology..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 pr-4 py-2.5 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-[#6b46c1] border ${
                isDarkTheme ? 'bg-[#231845] border-[#382969] text-white' : 'bg-[#f4effc] border-[#e2d5f8] text-[#2d1f56]'
              }`}
            />
          </div>
        </div>

        {/* Tech Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#6b46c1]" />
              Available Domains ({filteredTechnologies.length})
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredTechnologies.map((tech) => (
              <div
                key={tech.name}
                onClick={() => handleTechClick(tech.name)}
                className={`rounded-2xl p-4 border cursor-pointer transition-all duration-200 hover:-translate-y-1 shadow-xs hover:shadow-md flex flex-col justify-between ${
                  isDarkTheme
                    ? 'bg-[#18112e] border-[#2b1f4c] hover:border-[#6b46c1]'
                    : 'bg-white border-[#e9e1fa] hover:border-[#6b46c1]'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-bold text-sm line-clamp-1">
                      {tech.name}
                    </h3>
                    <ArrowUpRight className="w-3.5 h-3.5 text-[#6b46c1] flex-shrink-0" />
                  </div>

                  <div className="flex items-baseline gap-1.5 mb-3">
                    <span className="text-xl font-extrabold text-[#6b46c1]">{tech.count.toLocaleString()}</span>
                    <span className="text-[11px] text-slate-400">verified patents</span>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#e9e1fa]/30 flex items-center justify-between text-[11px]">
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-[#6b46c1]" />
                    Official IPO Domain
                  </span>
                  <span className="text-[#6b46c1] font-bold">Filter Search &rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

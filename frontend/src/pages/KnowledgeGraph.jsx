import { useSearchParams, useNavigate } from 'react-router-dom';
import GraphViewer from '../components/GraphViewer';
import { Network, Info, Sparkles, X } from 'lucide-react';

export default function KnowledgeGraph({ isDarkTheme }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const patentId = searchParams.get('patentId');

  return (
    <div className={`min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 space-y-6 ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        <div className={`rounded-3xl p-6 border shadow-lg ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#6b46c1]/10 text-[#6b46c1] border border-[#6b46c1]/20 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              Interactive Knowledge Graph Engine
            </div>

            {patentId && (
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#6b46c1] text-white text-xs font-bold shadow-xs">
                <span>Inspecting Patent: {patentId}</span>
                <button
                  onClick={() => navigate('/graph')}
                  className="p-0.5 hover:bg-purple-800 rounded-full transition-colors"
                  title="View Global Graph Cluster"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold flex items-center gap-3">
            <div className="p-2 rounded-2xl bg-[#f3eefc] text-[#6b46c1] border border-[#e2d5f8]">
              <Network className="w-5 h-5" />
            </div>
            Patent Graph Explorer
          </h1>
          <p className={`mt-2 text-xs sm:text-sm max-w-2xl ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
            {patentId 
              ? `Exploring 1-hop and 2-hop graph neighborhood for patent ${patentId}.` 
              : 'Visualize relationship connections between patents, technologies, classifications, and technical concepts.'}
          </p>
        </div>

        <div className={`rounded-3xl p-5 border shadow-md space-y-3 ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          <div className="flex items-center gap-2 text-xs bg-[#f4effc] dark:bg-[#231845] p-3 rounded-2xl border border-[#e2d5f8] dark:border-[#382969]">
            <Info className="w-4 h-4 text-[#6b46c1] flex-shrink-0" />
            <p><strong>Interactive Controls:</strong> Drag nodes to re-layout, scroll wheel to zoom, and examine patent connections.</p>
          </div>
          
          <GraphViewer patentId={patentId} />
        </div>

        {/* Legend */}
        <div className={`rounded-3xl p-5 border shadow-sm ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3 text-[#6b46c1]">Node Type Legend</h3>
          <div className="flex flex-wrap gap-5 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-md bg-[#6b46c1]"></div>
              <span>Patent Node</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-md bg-teal-500"></div>
              <span>Technology Domain</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-md bg-amber-500"></div>
              <span>Inventor</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-md bg-emerald-500"></div>
              <span>Organisation</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

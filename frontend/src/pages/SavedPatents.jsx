import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { patents } from '../data/patents';
import PatentCard from '../components/PatentCard';
import { Bookmark, Download, Trash2, Search, Filter } from 'lucide-react';

export default function SavedPatents() {
  const navigate = useNavigate();
  // Filter patents that have isSaved true, or initialize with mock saved list
  const [savedList, setSavedList] = useState(
    patents.filter(p => p.isSaved)
  );

  const handleToggleSave = (patentId) => {
    setSavedList(prev => prev.filter(p => p.id !== patentId));
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 lg:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Top Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
              <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl text-teal-400">
                <Bookmark className="w-6 h-6" />
              </div>
              Saved Patents Library
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Manage your saved intellectual property research, organize portfolios, and export citations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => alert('Exporting saved patents list as CSV...')}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-sm font-semibold text-slate-200 transition-colors shadow-sm"
            >
              <Download className="w-4 h-4 text-indigo-400" />
              Export Portfolio (CSV)
            </button>
          </div>
        </div>

        {/* Content list */}
        {savedList.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {savedList.map(patent => (
              <PatentCard 
                key={patent.id} 
                patent={{ ...patent, isSaved: true }} 
                onToggleSave={() => handleToggleSave(patent.id)}
              />
            ))}
          </div>
        ) : (
          <div className="bg-slate-800/40 border border-slate-800 rounded-3xl p-16 text-center max-w-xl mx-auto">
            <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4 text-slate-500">
              <Bookmark className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">No Saved Patents Yet</h3>
            <p className="text-slate-400 text-sm mb-6">
              When searching for patents, click the "Save" button on any patent card to bookmark it for later review.
            </p>
            <button
              onClick={() => navigate('/search')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-semibold rounded-xl text-sm transition-all shadow-lg shadow-indigo-950/50"
            >
              <Search className="w-4 h-4" />
              Go to Patent Search
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

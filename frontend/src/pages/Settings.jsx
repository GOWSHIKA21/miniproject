import { useState } from 'react';
import { Settings, Globe, Shield, Bell, Database, Sliders, Check } from 'lucide-react';
import { PATENT_OFFICES } from '../data/patents';

export default function SettingsPage() {
  const [defaultOffice, setDefaultOffice] = useState('All Offices');
  const [semanticSearch, setSemanticSearch] = useState(true);
  const [autoSummarize, setAutoSummarize] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 lg:p-10">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="pb-6 border-b border-slate-800">
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl text-teal-400">
              <Settings className="w-6 h-6" />
            </div>
            Platform Settings
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Configure your PatentGraph AI discovery engine, default search filters, and display preferences.
          </p>
        </div>

        <div className="space-y-6">
          
          {/* Default Search Preferences */}
          <div className="bg-slate-800/60 border border-slate-700/60 rounded-3xl p-6 lg:p-8 space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Globe className="w-5 h-5 text-indigo-400" />
              Default Patent Office Preference
            </h2>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-300">
                Primary Patent Office for New Searches
              </label>
              <select
                value={defaultOffice}
                onChange={(e) => setDefaultOffice(e.target.value)}
                className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="All Offices">All Patent Offices (Global)</option>
                {PATENT_OFFICES.map((office) => (
                  <option key={office} value={office}>{office}</option>
                ))}
              </select>
            </div>
          </div>

          {/* AI Search Settings */}
          <div className="bg-slate-800/60 border border-slate-700/60 rounded-3xl p-6 lg:p-8 space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-teal-400" />
              AI & Semantic Search Configuration
            </h2>

            <div className="space-y-4">
              <label className="flex items-center justify-between cursor-pointer p-4 bg-slate-900/60 rounded-2xl border border-slate-700/50 hover:border-slate-600 transition-colors">
                <div>
                  <div className="font-semibold text-white text-sm">Semantic Neural Matching</div>
                  <div className="text-slate-400 text-xs mt-0.5">Use AI embedding models to match patent meaning beyond strict keywords.</div>
                </div>
                <input
                  type="checkbox"
                  checked={semanticSearch}
                  onChange={(e) => setSemanticSearch(e.target.checked)}
                  className="w-5 h-5 text-indigo-600 rounded bg-slate-800 border-slate-600 focus:ring-indigo-500 cursor-pointer"
                />
              </label>

              <label className="flex items-center justify-between cursor-pointer p-4 bg-slate-900/60 rounded-2xl border border-slate-700/50 hover:border-slate-600 transition-colors">
                <div>
                  <div className="font-semibold text-white text-sm">Auto AI Patent Summaries</div>
                  <div className="text-slate-400 text-xs mt-0.5">Generate concise key claim summaries when viewing patent detail views.</div>
                </div>
                <input
                  type="checkbox"
                  checked={autoSummarize}
                  onChange={(e) => setAutoSummarize(e.target.checked)}
                  className="w-5 h-5 text-indigo-600 rounded bg-slate-800 border-slate-600 focus:ring-indigo-500 cursor-pointer"
                />
              </label>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleSave}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-bold rounded-xl text-sm transition-all shadow-lg shadow-indigo-950/50 flex items-center gap-2"
            >
              <Check className="w-4 h-4" />
              Save Preferences
            </button>

            {savedSuccess && (
              <span className="text-teal-400 text-sm font-semibold animate-fade-in">
                ✓ Preferences updated successfully!
              </span>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}

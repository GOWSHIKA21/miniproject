import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, BrainCircuit, Share2, Check, FileText, User, Building2, Calendar, Tag, ShieldCheck, Zap, Globe, Network, ArrowRight } from 'lucide-react';
import { patents } from '../data/patents';
import { api } from '../services/api';
import GraphViewer from '../components/GraphViewer';

export default function PatentDetails({ isDarkTheme }) {
  const params = useParams();
  const rawId = params['*'] || params.id || '';
  const id = decodeURIComponent(rawId);
  const navigate = useNavigate();
  
  const [patent, setPatent] = useState(() => patents.find(p => p.id === id) || null);
  const [relatedPatents, setRelatedPatents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      if (!id) return;
      setLoading(true);
      try {
        const fetched = await api.getPatentById(id);
        if (isMounted && fetched) {
          setPatent(fetched);
        }
        const related = await api.getRelatedPatents(id);
        if (isMounted && related) {
          setRelatedPatents(related);
        }
      } catch (err) {
        console.warn('Failed to load patent from backend:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, [id]);

  const handleShare = () => {
    try {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.warn('Clipboard write error:', e);
    }
  };

  if (loading && !patent) {
    return (
      <div className={`min-h-[70vh] flex flex-col items-center justify-center p-6 ${
        isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
      }`}>
        <div className="w-8 h-8 border-4 border-[#6b46c1] border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-base font-semibold">Retrieving Patent Record...</h2>
      </div>
    );
  }

  if (!patent) {
    return (
      <div className={`min-h-[70vh] flex flex-col items-center justify-center p-6 ${
        isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
      }`}>
        <h2 className="text-xl font-bold mb-2">Patent Record Not Found</h2>
        <button 
          onClick={() => navigate('/search')} 
          className="px-4 py-2 bg-[#6b46c1] text-white font-semibold rounded-xl text-xs"
        >
          Return to Search
        </button>
      </div>
    );
  }

  return (
    <div className={`min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 space-y-6 ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Top Action Bar */}
        <div className="flex items-center justify-between">
          <button 
            onClick={() => navigate(-1)}
            className={`flex items-center text-xs font-semibold px-3 py-2 rounded-xl border transition-colors ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c] text-white' : 'bg-white border-[#e9e1fa] text-[#2d1f56]'
            }`}
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Back to Search Results
          </button>
          
          <button 
            onClick={handleShare}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold transition-colors ${
              copied
                ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30 font-bold'
                : isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c] text-white hover:border-[#6b46c1]' : 'bg-white border-[#e9e1fa] text-[#2d1f56] hover:border-[#6b46c1]'
            }`}
            title="Copy patent link to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Link Copied!</span>
              </>
            ) : (
              <>
                <Share2 className="w-3.5 h-3.5" />
                <span>Share</span>
              </>
            )}
          </button>
        </div>

        {/* Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Main Patent Content */}
          <div className="lg:col-span-8 space-y-6">
            
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-lg space-y-4 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs font-bold text-[#6b46c1] bg-[#f3eefc] dark:bg-[#231845] px-3 py-1 rounded-lg border border-[#e2d5f8] dark:border-[#382969]">
                  {patent.patentNumber}
                </span>

                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 border border-emerald-500/30">
                  <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                  {patent.status}
                </span>

                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800">
                  <Globe className="w-3.5 h-3.5 mr-1 text-[#6b46c1]" />
                  {patent.patentOffice}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold leading-snug">
                {patent.title}
              </h1>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {patent.technology.map((tech, idx) => (
                  <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-xl text-xs font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#553c9a] dark:text-purple-200 border border-[#e2d5f8] dark:border-[#382969]">
                    <Tag className="w-3.5 h-3.5 mr-1 text-[#6b46c1]" />
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Abstract */}
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-3 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <h2 className="text-base font-bold flex items-center gap-2">
                <FileText className="w-4 h-4 text-[#6b46c1]" />
                Detailed Abstract & Specification
              </h2>
              <p className={`leading-relaxed text-xs sm:text-sm ${isDarkTheme ? 'text-slate-300' : 'text-[#4a367c]'}`}>
                {patent.abstract}
              </p>
            </div>

            {/* Knowledge Graph Neighborhood */}
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-4 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <h2 className="text-base font-bold flex items-center gap-2">
                <Network className="w-4 h-4 text-[#6b46c1]" />
                Knowledge Graph Neighborhood
              </h2>
              <p className={`text-xs ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
                Interactive visual subnetwork representing this patent's classification, location, and shared technical concepts.
              </p>
              <GraphViewer patentId={patent.id} />
            </div>

            {/* Related Patents from Knowledge Graph */}
            {relatedPatents && relatedPatents.length > 0 && (
              <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-4 ${
                isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
              }`}>
                <h2 className="text-base font-bold flex items-center gap-2">
                  <Network className="w-4 h-4 text-[#6b46c1]" />
                  Related Inventions via Concept Overlap ({relatedPatents.length})
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {relatedPatents.map((rel, idx) => (
                    <div
                      key={idx}
                      onClick={() => navigate(`/patent/${encodeURIComponent(rel.patent_id)}`)}
                      className={`p-3.5 rounded-2xl border cursor-pointer transition-all hover:scale-[1.01] ${
                        isDarkTheme ? 'bg-[#231845] border-[#382969] hover:border-[#6b46c1]' : 'bg-[#f4effc] border-[#e2d5f8] hover:border-[#6b46c1]'
                      }`}
                    >
                      <div className="font-mono text-[11px] font-bold text-[#6b46c1] mb-1">
                        {rel.patent_id}
                      </div>
                      <div className="text-xs font-semibold line-clamp-2 mb-2">
                        {rel.title}
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-purple-200/20">
                        <span>{rel.field}</span>
                        <span className="text-[#6b46c1] font-bold flex items-center gap-1">
                          {rel.shared_concepts_count} shared concepts <ArrowRight className="w-2.5 h-2.5" />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar Metadata */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Quick Actions */}
            <div className={`rounded-3xl p-6 border shadow-md space-y-3 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <h3 className="text-sm font-bold flex items-center gap-2 text-[#6b46c1]">
                <Zap className="w-4 h-4" />
                AI Actions
              </h3>
              
              <button 
                onClick={() => navigate(`/assistant?q=${encodeURIComponent(`Tell me about granted patent ${patent.patentNumber}: ${patent.title}`)}`)}
                className="w-full flex items-center justify-center gap-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white px-4 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer"
              >
                <BrainCircuit className="w-4 h-4" />
                Ask AI Assistant About Patent
              </button>
            </div>

            {/* Metadata */}
            <div className={`rounded-3xl p-6 border shadow-sm space-y-4 text-xs ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <h3 className="text-sm font-bold">Bibliographic Details</h3>
              
              <div className="space-y-3">
                <div>
                  <div className="flex items-center text-slate-400 mb-0.5">
                    <User className="w-3.5 h-3.5 mr-1 text-[#6b46c1]" /> Inventor
                  </div>
                  <div className="font-semibold">{patent.inventor}</div>
                </div>

                <div>
                  <div className="flex items-center text-slate-400 mb-0.5">
                    <Building2 className="w-3.5 h-3.5 mr-1 text-[#6b46c1]" /> Assignee Org
                  </div>
                  <div className="font-semibold">{patent.organization}</div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-400">Filing Date</div>
                    <div className="font-semibold">{patent.filingDate}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Publication</div>
                    <div className="font-semibold">{patent.publicationDate}</div>
                  </div>
                </div>
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}

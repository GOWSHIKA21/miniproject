import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  BrainCircuit, 
  Share2, 
  Check, 
  FileText, 
  Calendar, 
  Tag, 
  Zap, 
  Globe, 
  Network, 
  ArrowRight,
  ExternalLink,
  Hash,
  Clock,
  Layers,
  FileCode,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Building2,
  BookOpen
} from 'lucide-react';
import { api } from '../services/api';

export default function PatentDetails({ isDarkTheme }) {
  const params = useParams();
  const rawId = params['*'] || params.id || '';
  const id = decodeURIComponent(rawId).trim();
  const navigate = useNavigate();
  
  const [patent, setPatent] = useState(null);
  const [relatedPatents, setRelatedPatents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showSearchText, setShowSearchText] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setPatent(null);
    setRelatedPatents([]);
    setError(null);
    setLoading(true);
    setShowSearchText(false);

    if (!id) {
      setLoading(false);
      setError("No patent application number provided in URL.");
      return;
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });

    async function loadData() {
      try {
        const fetched = await api.getPatentById(id);
        if (!isMounted) return;

        if (fetched) {
          setPatent(fetched);
          try {
            const related = await api.getRelatedPatents(id);
            if (isMounted && related) {
              setRelatedPatents(related);
            }
          } catch (rErr) {
            console.warn('Failed to load related patents:', rErr);
          }
        } else {
          setError(`Patent record '${id}' was not found in the database.`);
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Failed to load patent from backend:', err);
          setError(`Failed to retrieve patent '${id}'. Please verify the application number.`);
        }
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

  const handleNavigateToRelated = (relatedId) => {
    if (!relatedId) return;
    navigate(`/patent/${encodeURIComponent(relatedId)}`);
  };

  if (loading) {
    return (
      <div className={`min-h-[70vh] flex flex-col items-center justify-center p-6 ${
        isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
      }`}>
        <div className="w-10 h-10 border-4 border-[#6b46c1] border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-base font-bold">Retrieving Patent Record...</h2>
        <p className="text-xs text-slate-400 mt-1 font-mono">{id}</p>
      </div>
    );
  }

  if (error || !patent) {
    return (
      <div className={`min-h-[70vh] flex flex-col items-center justify-center p-6 text-center space-y-4 ${
        isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
      }`}>
        <div className="w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/30 flex items-center justify-center mx-auto">
          <FileText className="w-7 h-7" />
        </div>
        <div className="space-y-1 max-w-md">
          <h2 className="text-xl font-bold">Patent Record Not Found</h2>
          <p className="text-xs text-slate-400">{error || `Patent '${id}' does not exist in the database.`}</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate(-1)} 
            className={`px-4 py-2 border rounded-xl text-xs font-semibold cursor-pointer transition-colors ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c] text-white hover:border-[#6b46c1]' : 'bg-white border-[#e9e1fa] text-[#2d1f56] hover:border-[#6b46c1]'
            }`}
          >
            &larr; Go Back
          </button>
          <button 
            onClick={() => navigate('/search')} 
            className="px-4 py-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white font-semibold rounded-xl text-xs cursor-pointer transition-colors"
          >
            Return to Search
          </button>
        </div>
      </div>
    );
  }

  // Safe field resolution across snake_case and camelCase
  const patentId = patent.patent_id || patent.patentId || patent.id || 'Not available';
  const pubNumber = patent.publication_number || patent.publicationNumber || 'Not available';
  const title = patent.title || 'Untitled Patent Record';
  const titleNormalized = patent.title_normalized || patent.titleNormalized || 'Not available';
  
  const filingDate = patent.filing_date || patent.filingDate || 'Not available';
  const pubDate = patent.publication_date || patent.publicationDate || 'Not available';
  const dateUpdated = patent.date_updated || patent.dateUpdated || 'Not available';
  const filingYear = patent.filing_year || patent.filingYear || 'Not available';
  const pubYear = patent.publication_year || patent.publicationYear || 'Not available';
  const pendencyDays = (patent.pendency_days !== undefined && patent.pendency_days !== null)
    ? `${patent.pendency_days} days`
    : (patent.pendencyDays !== undefined && patent.pendencyDays !== null)
      ? `${patent.pendencyDays} days`
      : 'Not available';

  const domain = patent.field_of_invention || patent.fieldOfInvention || patent.ipc || 'Not available';
  const isFieldImputed = patent.field_imputed !== undefined ? patent.field_imputed : patent.fieldImputed;
  
  const jurisdiction = patent.jurisdiction || patent.patentOffice || 'India';
  const ipoLocation = patent.ipo_location || patent.ipoLocation || 'Not available';
  const ipoCode = patent.ipo_code || patent.ipoCode || 'Not available';
  const appType = patent.application_type || patent.applicationType || 'Not available';
  const appCategory = patent.application_category || patent.applicationCategory || 'Not available';

  const noOfPages = (patent.no_of_pages !== undefined && patent.no_of_pages !== null)
    ? patent.no_of_pages
    : (patent.noOfPages !== undefined && patent.noOfPages !== null)
      ? patent.noOfPages
      : (patent.no_of_pages_imputed ? `${patent.no_of_pages_imputed} (imputed)` : 'Not available');

  const noOfClaims = (patent.no_of_claims !== undefined && patent.no_of_claims !== null)
    ? patent.no_of_claims
    : (patent.noOfClaims !== undefined && patent.noOfClaims !== null)
      ? patent.noOfClaims
      : (patent.no_of_claims_imputed ? `${patent.no_of_claims_imputed} (imputed)` : 'Not available');

  const claimsRange = patent.claims_range || patent.claimsRange || 'Not available';
  const sourceFile = patent.source_file || patent.sourceFile || 'Not available';
  const sourceUrl = patent.source_url || patent.sourceUrl || '';
  const searchText = patent.search_text || patent.searchText || '';

  return (
    <div className={`min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-8 space-y-6 ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Top Action Bar */}
        <div className="flex items-center justify-between">
          <button 
            onClick={() => navigate(-1)}
            className={`flex items-center text-xs font-semibold px-3 py-2 rounded-xl border transition-colors cursor-pointer ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c] text-white hover:border-[#6b46c1]' : 'bg-white border-[#e9e1fa] text-[#2d1f56] hover:border-[#6b46c1]'
            }`}
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Back to Search Results
          </button>
          
          <button 
            onClick={handleShare}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold transition-colors cursor-pointer ${
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
            
            {/* Header Hero Card */}
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-lg space-y-4 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs font-bold text-[#6b46c1] bg-[#f3eefc] dark:bg-[#231845] px-3 py-1 rounded-lg border border-[#e2d5f8] dark:border-[#382969]" title="Official Application Number">
                  Application: {patentId}
                </span>

                {pubNumber && pubNumber !== 'Not available' && (
                  <span className="font-mono text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-lg border border-slate-200 dark:border-slate-700" title="Publication Number">
                    Pub No: {pubNumber}
                  </span>
                )}

                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] border border-[#e2d5f8] dark:border-[#382969]">
                  <Globe className="w-3.5 h-3.5 mr-1" />
                  {jurisdiction} • IPO {ipoLocation} ({ipoCode})
                </span>

                {isFieldImputed !== null && isFieldImputed !== undefined && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                    isFieldImputed 
                      ? 'bg-amber-500/10 text-amber-600 border-amber-500/30' 
                      : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30'
                  }`}>
                    {isFieldImputed ? 'Domain Imputed' : 'Direct Domain Record'}
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold leading-snug">
                {title}
              </h1>

              {/* Badges Bar */}
              <div className="flex flex-wrap gap-2 pt-1">
                {domain && domain !== 'Not available' && (
                  <span className="inline-flex items-center px-3 py-1 rounded-xl text-xs font-semibold bg-[#6b46c1] text-white shadow-xs">
                    <Tag className="w-3.5 h-3.5 mr-1" />
                    {domain}
                  </span>
                )}
                {appType && appType !== 'Not available' && (
                  <span className="inline-flex items-center px-3 py-1 rounded-xl text-xs font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#553c9a] dark:text-purple-200 border border-[#e2d5f8] dark:border-[#382969]">
                    <Layers className="w-3.5 h-3.5 mr-1 text-[#6b46c1]" />
                    {appType}
                  </span>
                )}
                {claimsRange && claimsRange !== 'Not available' && (
                  <span className="inline-flex items-center px-3 py-1 rounded-xl text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    <Hash className="w-3.5 h-3.5 mr-1 text-[#6b46c1]" />
                    {claimsRange}
                  </span>
                )}
              </div>
            </div>

            {/* SECTION A: Patent Overview & Bibliographic Metadata */}
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-4 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <div className="flex items-center justify-between pb-3 border-b border-[#e9e1fa]/40 dark:border-[#2b1f4c]">
                <h2 className="text-base font-bold flex items-center gap-2 text-[#6b46c1]">
                  <FileText className="w-4 h-4" />
                  A. Patent Overview & Metadata
                </h2>
                <span className="text-[11px] text-slate-400 font-medium">Dataset Records</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                
                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Application Number</div>
                  <div className="font-mono font-bold text-sm text-[#6b46c1] break-all">{patentId}</div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Publication Number</div>
                  <div className="font-mono font-bold text-sm break-all">{pubNumber}</div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Filing Date & Year</div>
                  <div className="font-semibold text-sm">{filingDate} <span className="text-xs text-slate-400 font-normal">({filingYear})</span></div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Publication Date & Year</div>
                  <div className="font-semibold text-sm">{pubDate} <span className="text-xs text-slate-400 font-normal">({pubYear})</span></div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Date Last Updated</div>
                  <div className="font-semibold text-sm">{dateUpdated}</div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Pendency Duration</div>
                  <div className="font-semibold text-sm flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-[#6b46c1]" />
                    {pendencyDays}
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Technology Domain</div>
                  <div className="font-bold text-sm text-[#6b46c1]">{domain}</div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Domain Imputed</div>
                  <div className="font-semibold text-sm">
                    {isFieldImputed !== null && isFieldImputed !== undefined 
                      ? (isFieldImputed ? 'Yes (Derived classification)' : 'No (Original classification)') 
                      : 'Not available'}
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Jurisdiction & Office</div>
                  <div className="font-semibold text-sm">{jurisdiction} • IPO {ipoLocation} ({ipoCode})</div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Application Type</div>
                  <div className="font-semibold text-sm">{appType}</div>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Application Category</div>
                  <div className="font-semibold text-sm">{appCategory}</div>
                </div>

              </div>
            </div>

            {/* SECTION B: Patent Specification and Claims */}
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-4 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <div className="flex items-center justify-between pb-3 border-b border-[#e9e1fa]/40 dark:border-[#2b1f4c]">
                <h2 className="text-base font-bold flex items-center gap-2 text-[#6b46c1]">
                  <Layers className="w-4 h-4" />
                  B. Patent Specification & Claims
                </h2>
                <span className="text-[11px] text-slate-400 font-medium">Structure & Boundaries</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                
                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Number of Pages</div>
                  <div className="font-extrabold text-lg text-[#6b46c1]">
                    {noOfPages}
                  </div>
                  <p className="text-[11px] text-slate-400">Total specification length</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Number of Claims</div>
                  <div className="font-extrabold text-lg text-[#6b46c1]">
                    {noOfClaims}
                  </div>
                  <p className="text-[11px] text-slate-400">Legal claim scope count</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Claims Range Bin</div>
                  <div className="font-extrabold text-lg text-[#6b46c1]">
                    {claimsRange}
                  </div>
                  <p className="text-[11px] text-slate-400">Categorical grouping</p>
                </div>

              </div>

              {/* Normalized Title Inspection */}
              <div className="p-4 rounded-2xl bg-slate-50/50 dark:bg-[#231845]/30 border border-[#e9e1fa]/40 dark:border-[#382969]/40 space-y-1.5 text-xs">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-[#6b46c1]" /> Normalized Title in Index
                </div>
                <div className="font-mono text-xs text-slate-600 dark:text-slate-300 break-words leading-relaxed">
                  {titleNormalized}
                </div>
              </div>
            </div>

            {/* SECTION C: Source & Provenance */}
            <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-4 ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <div className="flex items-center justify-between pb-3 border-b border-[#e9e1fa]/40 dark:border-[#2b1f4c]">
                <h2 className="text-base font-bold flex items-center gap-2 text-[#6b46c1]">
                  <FileCode className="w-4 h-4" />
                  C. Source & Provenance
                </h2>
                <span className="text-[11px] text-slate-400 font-medium">Official Verification</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                
                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1.5">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Original Source Gazette File</div>
                  <div className="font-mono font-semibold text-xs text-[#6b46c1] break-all">{sourceFile}</div>
                  <p className="text-[11px] text-slate-400">Official IPO tabular publication extract</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50/70 dark:bg-[#231845]/50 border border-[#e9e1fa]/50 dark:border-[#382969]/50 space-y-1.5">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Official Portal Verification URL</div>
                  {sourceUrl ? (
                    <div>
                      <a 
                        href={sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-[#6b46c1] hover:underline break-all"
                      >
                        {sourceUrl}
                        <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                      </a>
                      <p className="text-[11px] text-slate-400 mt-1">Direct link to IP India Public Search Services</p>
                    </div>
                  ) : (
                    <div className="text-slate-400 italic">Not available</div>
                  )}
                </div>

              </div>

              {/* Collapsible Searchable Text Accordion */}
              {searchText && (
                <div className="rounded-2xl border border-[#e9e1fa]/60 dark:border-[#382969]/60 overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setShowSearchText(!showSearchText)}
                    className={`w-full p-4 flex items-center justify-between text-xs font-bold transition-colors cursor-pointer text-left ${
                      isDarkTheme ? 'bg-[#231845] hover:bg-[#2a1d52]' : 'bg-[#f4effc] hover:bg-[#ebe1fa]'
                    }`}
                  >
                    <span className="flex items-center gap-2 text-[#6b46c1]">
                      <FileText className="w-4 h-4" />
                      {showSearchText ? 'Hide Searchable Indexed Text' : 'Inspect Searchable Indexed Text'}
                    </span>
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500">
                      {showSearchText ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </span>
                  </button>

                  {showSearchText && (
                    <div className={`p-4 text-xs font-mono leading-relaxed border-t border-[#e9e1fa]/40 dark:border-[#382969]/40 ${
                      isDarkTheme ? 'bg-[#18112e] text-slate-300' : 'bg-white text-slate-700'
                    }`}>
                      <div className="text-[11px] text-slate-400 mb-2 font-sans font-medium">
                        Indexed textual representation used by Hybrid Search & BM25 retrieval:
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-black/30 border border-slate-200/50 dark:border-slate-800 break-words whitespace-pre-wrap">
                        {searchText}
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>

            {/* Related Patents from Knowledge Graph via Concept Overlap */}
            {relatedPatents && relatedPatents.length > 0 && (
              <div className={`rounded-3xl p-6 sm:p-8 border shadow-md space-y-4 ${
                isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
              }`}>
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-bold flex items-center gap-2">
                    <Network className="w-4 h-4 text-[#6b46c1]" />
                    Related Inventions via Concept Overlap ({relatedPatents.length})
                  </h2>
                  <span className="text-[11px] text-slate-400">Click any card to inspect patent</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  {relatedPatents.map((rel, idx) => (
                    <div
                      key={idx}
                      onClick={() => handleNavigateToRelated(rel.patent_id)}
                      className={`group p-4 rounded-2xl border cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md flex flex-col justify-between ${
                        isDarkTheme 
                          ? 'bg-[#231845] border-[#382969] hover:border-[#6b46c1]' 
                          : 'bg-[#f4effc] border-[#e2d5f8] hover:border-[#6b46c1]'
                      }`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1.5">
                          <span className="font-mono text-[11px] font-bold text-[#6b46c1] group-hover:underline">
                            {rel.patent_id}
                          </span>
                          {rel.location && (
                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/40 dark:bg-black/20 text-slate-500">
                              {rel.location}
                            </span>
                          )}
                        </div>

                        <h4 className="text-xs font-bold line-clamp-2 mb-3 group-hover:text-[#6b46c1] transition-colors">
                          {rel.title}
                        </h4>
                      </div>

                      <div className="pt-2.5 border-t border-purple-200/30 flex items-center justify-between text-[11px]">
                        <span className="text-slate-400 text-[10px] uppercase font-semibold">
                          {rel.field || 'Invention'}
                        </span>
                        <span className="text-[#6b46c1] font-bold flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                          {rel.shared_concepts_count ? `${rel.shared_concepts_count} shared concepts` : 'View Patent'} <ArrowRight className="w-3 h-3" />
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
                AI Assistant Actions
              </h3>
              
              <button 
                onClick={() => navigate(`/assistant?q=${encodeURIComponent(`Explain the technical concepts and claims scope for patent ${patentId}: ${title}`)}`)}
                className="w-full flex items-center justify-center gap-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white px-4 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer shadow-xs"
              >
                <BrainCircuit className="w-4 h-4" />
                Ask AI About Patent
              </button>

              <button 
                onClick={() => navigate(`/graph?patentId=${encodeURIComponent(patentId)}`)}
                className="w-full flex items-center justify-center gap-2 bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] dark:text-purple-200 hover:bg-[#6b46c1] hover:text-white px-4 py-2.5 rounded-xl font-bold text-xs transition-all cursor-pointer border border-[#e2d5f8] dark:border-[#382969]"
              >
                <Network className="w-4 h-4" />
                Explore Knowledge Graph
              </button>
            </div>

            {/* At-a-glance Record Card */}
            <div className={`rounded-3xl p-6 border shadow-sm space-y-4 text-xs ${
              isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
            }`}>
              <h3 className="text-sm font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                Record Summary
              </h3>
              
              <div className="space-y-3">
                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-0.5">Application ID</div>
                  <div className="font-mono font-bold text-[#6b46c1] break-all">{patentId}</div>
                </div>

                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-0.5">Publication Number</div>
                  <div className="font-mono font-semibold break-all">{pubNumber}</div>
                </div>

                <div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-0.5">Patent Office</div>
                  <div className="font-semibold">{jurisdiction} • IPO {ipoLocation} ({ipoCode})</div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-purple-200/20">
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Filing Date</div>
                    <div className="font-semibold">{filingDate}</div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Published</div>
                    <div className="font-semibold">{pubDate}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-purple-200/20">
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Claims</div>
                    <div className="font-semibold">{noOfClaims}</div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Pages</div>
                    <div className="font-semibold">{noOfPages}</div>
                  </div>
                </div>

                <div className="pt-2 border-t border-purple-200/20">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Technical Domain</div>
                  <div className="font-bold text-[#6b46c1]">{domain}</div>
                </div>

                {sourceUrl && (
                  <div className="pt-2 border-t border-purple-200/20">
                    <a
                      href={sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[#6b46c1] hover:underline font-bold text-xs"
                    >
                      Verify on IP India Portal <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}

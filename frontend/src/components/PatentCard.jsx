import { useNavigate } from 'react-router-dom';
import { Calendar, Tag, Globe, ExternalLink, Network, FileText, Layers, Hash } from 'lucide-react';
import { saveScrollPosition } from '../hooks/useSearchState';

export default function PatentCard({ patent, isDarkTheme }) {
  const navigate = useNavigate();

  // Safe field resolution
  const patentId = patent.patent_id || patent.patentId || patent.id || 'N/A';
  const pubNumber = patent.publication_number || patent.publicationNumber || null;
  const title = patent.title || 'Untitled Patent Record';
  
  const filingDate = patent.filing_date || patent.filingDate || 'N/A';
  const pubDate = patent.publication_date || patent.publicationDate || 'N/A';
  
  const domain = patent.field_of_invention || patent.fieldOfInvention || patent.ipc || 'GENERAL';
  const jurisdiction = patent.jurisdiction || patent.patentOffice || 'India';
  const ipoLocation = patent.ipo_location || patent.ipoLocation || 'Delhi';
  const ipoCode = patent.ipo_code || patent.ipoCode || 'DEL';
  
  const appType = patent.application_type || patent.applicationType || 'Patent Application';
  const appCategory = patent.application_category || patent.applicationCategory || null;
  
  const pages = (patent.no_of_pages !== undefined && patent.no_of_pages !== null)
    ? patent.no_of_pages
    : (patent.noOfPages !== undefined && patent.noOfPages !== null)
      ? patent.noOfPages
      : (patent.no_of_pages_imputed || '—');
      
  const claims = (patent.no_of_claims !== undefined && patent.no_of_claims !== null)
    ? patent.no_of_claims
    : (patent.noOfClaims !== undefined && patent.noOfClaims !== null)
      ? patent.noOfClaims
      : (patent.no_of_claims_imputed || '—');
      
  const claimsRange = patent.claims_range || patent.claimsRange || null;
  const relevance = patent.relevance || patent.relevanceScore || 90;

  return (
    <div className={`rounded-3xl p-5 sm:p-6 border shadow-sm hover:shadow-md transition-all duration-200 group flex flex-col justify-between ${
      isDarkTheme 
        ? 'bg-[#18112e] border-[#2b1f4c] hover:border-[#6b46c1]' 
        : 'bg-white border-[#e9e1fa] hover:border-[#6b46c1]'
    }`}>
      <div>
        {/* Top Header Badges */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2.5 mb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-[#6b46c1] bg-[#f3eefc] dark:bg-[#231845] px-2.5 py-0.5 rounded-lg border border-[#e2d5f8] dark:border-[#382969]" title="Patent Application Number">
                {patentId}
              </span>

              {pubNumber && pubNumber !== patentId && (
                <span className="font-mono text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700" title="Publication Number">
                  Pub: {pubNumber}
                </span>
              )}

              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] border border-[#e2d5f8] dark:border-[#382969]">
                <Globe className="w-3 h-3 mr-1 text-[#6b46c1]" />
                {jurisdiction} • IPO {ipoLocation} ({ipoCode})
              </span>
            </div>

            {/* Patent Title */}
            <h3 
              onClick={() => { saveScrollPosition(); navigate(`/patent/${encodeURIComponent(patentId)}`); }}
              className={`text-lg font-bold group-hover:text-[#6b46c1] transition-colors cursor-pointer leading-snug mt-1.5 ${
                isDarkTheme ? 'text-white' : 'text-[#2d1f56]'
              }`}
            >
              {title}
            </h3>
          </div>

          <span className="inline-flex items-center px-2.5 py-1 rounded-xl text-xs font-extrabold bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] border border-[#e2d5f8] dark:border-[#382969] flex-shrink-0 self-start">
            {relevance}% Match
          </span>
        </div>

        {/* Category & Tech Tags */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-[#6b46c1] text-white">
            <Tag className="w-3 h-3 mr-1" />
            {domain}
          </span>

          <span className="inline-flex items-center px-2.5 py-0.5 rounded-lg text-[11px] font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#553c9a] dark:text-purple-200 border border-[#e2d5f8] dark:border-[#382969]">
            <Layers className="w-3 h-3 mr-1 text-[#6b46c1]" />
            {appType} {appCategory ? `(${appCategory})` : ''}
          </span>

          {claimsRange && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-lg text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              <Hash className="w-3 h-3 mr-1 text-[#6b46c1]" />
              {claimsRange}
            </span>
          )}
        </div>

        {/* Metadata Details Bar */}
        <div className={`grid grid-cols-2 sm:grid-cols-4 gap-2.5 py-2.5 px-3.5 rounded-2xl text-xs mb-3.5 border ${
          isDarkTheme ? 'bg-[#120c24] border-[#2b1f4c]' : 'bg-[#f4effc]/60 border-[#e2d5f8]/60'
        }`}>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Filed</div>
            <div className="font-semibold flex items-center gap-1 mt-0.5 truncate">
              <Calendar className="w-3 h-3 text-[#6b46c1] flex-shrink-0" />
              <span className="truncate">{filingDate}</span>
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Published</div>
            <div className="font-semibold flex items-center gap-1 mt-0.5 truncate">
              <Calendar className="w-3 h-3 text-[#6b46c1] flex-shrink-0" />
              <span className="truncate">{pubDate}</span>
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Specification</div>
            <div className="font-semibold flex items-center gap-1 mt-0.5 truncate">
              <FileText className="w-3 h-3 text-[#6b46c1] flex-shrink-0" />
              <span className="truncate">{pages} pages • {claims} claims</span>
            </div>
          </div>

          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Office Location</div>
            <div className="font-semibold flex items-center gap-1 mt-0.5 truncate">
              <Globe className="w-3 h-3 text-[#6b46c1] flex-shrink-0" />
              <span className="truncate">IPO {ipoLocation}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="pt-3 border-t border-[#e9e1fa]/40 flex items-center justify-between gap-2">
        <button
          onClick={() => { saveScrollPosition(); navigate(`/patent/${encodeURIComponent(patentId)}`); }}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          View Patent
          <ExternalLink className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => navigate(`/graph?patentId=${encodeURIComponent(patentId)}`)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] dark:text-purple-200 hover:bg-[#6b46c1] hover:text-white rounded-xl text-xs font-semibold border border-[#e2d5f8] dark:border-[#382969] transition-colors cursor-pointer"
        >
          <Network className="w-3.5 h-3.5" />
          Explore Graph
        </button>
      </div>

    </div>
  );
}

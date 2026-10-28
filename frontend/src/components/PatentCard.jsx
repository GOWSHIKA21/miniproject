import { useNavigate } from 'react-router-dom';
import { Calendar, Tag, Globe, ExternalLink, FileText, Layers, Hash } from 'lucide-react';
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

  // Scale relevance percentage
  const relevance = patent.relevance ? Math.round(patent.relevance) : null;

  return (
    <div className={`p-5 rounded-2xl border transition-all duration-200 hover:shadow-lg flex flex-col justify-between ${
      isDarkTheme 
        ? 'bg-[#18112e] border-[#2b1f4c] hover:border-[#6b46c1]' 
        : 'bg-white border-[#e9e1fa] hover:border-[#6b46c1]'
    }`}>
      
      {/* Top Header Row */}
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs font-bold text-[#6b46c1] bg-[#f3eefc] dark:bg-[#231845] px-2.5 py-0.5 rounded-md border border-[#e2d5f8] dark:border-[#382969]">
              {patentId}
            </span>
            {pubNumber && pubNumber !== 'Not available' && (
              <span className="font-mono text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700">
                Pub: {pubNumber}
              </span>
            )}
            <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
              <Globe className="w-3 h-3 text-[#6b46c1]" />
              {jurisdiction} • {ipoCode}
            </span>
          </div>

          {relevance !== null && (
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-[#6b46c1]/10 text-[#6b46c1] border border-[#6b46c1]/20">
              {relevance}% Match
            </span>
          )}
        </div>

        {/* Title */}
        <h3 
          onClick={() => { saveScrollPosition(); navigate(`/patent/${encodeURIComponent(patentId)}`); }}
          className="text-base font-bold line-clamp-2 hover:text-[#6b46c1] cursor-pointer transition-colors"
          title={title}
        >
          {title}
        </h3>

        {/* Domain and Application Badges */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {domain && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#6b46c1] text-white">
              <Tag className="w-3 h-3 mr-1" />
              {domain}
            </span>
          )}
          {appType && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#553c9a] dark:text-purple-200 border border-[#e2d5f8] dark:border-[#382969]">
              <Layers className="w-3 h-3 mr-1 text-[#6b46c1]" />
              {appType}
            </span>
          )}
        </div>

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-3 pb-1 border-t border-[#e9e1fa]/60 text-xs">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Filing & Publication</div>
            <div className="font-semibold flex items-center gap-1 mt-0.5 truncate">
              <Calendar className="w-3 h-3 text-[#6b46c1] flex-shrink-0" />
              <span className="truncate">{filingDate} &bull; {pubDate}</span>
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
      </div>

    </div>
  );
}

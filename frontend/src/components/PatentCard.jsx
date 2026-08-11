import { useNavigate } from 'react-router-dom';
import { Building2, User, Calendar, Tag, Globe, ShieldCheck, ExternalLink, Network } from 'lucide-react';

export default function PatentCard({ patent, isDarkTheme }) {
  const navigate = useNavigate();

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Active':
      case 'Granted':
        return 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30';
      case 'Pending':
        return 'bg-amber-500/10 text-amber-600 border-amber-500/30';
      case 'Expired':
        return 'bg-slate-500/10 text-slate-500 border-slate-500/30';
      case 'Abandoned':
        return 'bg-rose-500/10 text-rose-600 border-rose-500/30';
      default:
        return 'bg-[#6b46c1]/10 text-[#6b46c1] border-[#6b46c1]/30';
    }
  };

  return (
    <div className={`rounded-3xl p-5 sm:p-6 border shadow-sm hover:shadow-md transition-all duration-200 group flex flex-col justify-between ${
      isDarkTheme 
        ? 'bg-[#18112e] border-[#2b1f4c] hover:border-[#6b46c1]' 
        : 'bg-white border-[#e9e1fa] hover:border-[#6b46c1]'
    }`}>
      <div>
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2.5 mb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-[#6b46c1] bg-[#f3eefc] dark:bg-[#231845] px-2.5 py-0.5 rounded-lg border border-[#e2d5f8] dark:border-[#382969]">
                {patent.patentNumber}
              </span>

              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${getStatusBadge(patent.status)}`}>
                <ShieldCheck className="w-3 h-3 mr-1" />
                {patent.status}
              </span>

              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                <Globe className="w-3 h-3 mr-1 text-[#6b46c1]" />
                {patent.patentOffice}
              </span>
            </div>

            <h3 
              onClick={() => navigate(`/patent/${patent.id}`)}
              className={`text-lg font-bold group-hover:text-[#6b46c1] transition-colors cursor-pointer leading-snug mt-1 ${
                isDarkTheme ? 'text-white' : 'text-[#2d1f56]'
              }`}
            >
              {patent.title}
            </h3>
          </div>

          <span className="inline-flex items-center px-2.5 py-1 rounded-xl text-xs font-extrabold bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] border border-[#e2d5f8] dark:border-[#382969] flex-shrink-0 self-start">
            {patent.relevance || 92}% Match
          </span>
        </div>

        {/* Abstract */}
        <p className={`text-xs sm:text-sm leading-relaxed line-clamp-2 mb-4 ${
          isDarkTheme ? 'text-slate-300' : 'text-[#4a367c]'
        }`}>
          {patent.abstract}
        </p>

        {/* Metadata Bar */}
        <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 py-3 px-3.5 rounded-2xl text-xs mb-4 border ${
          isDarkTheme ? 'bg-[#120c24] border-[#2b1f4c]' : 'bg-[#f4effc]/60 border-[#e2d5f8]/60'
        }`}>
          <div className="flex items-center gap-1.5 truncate">
            <User className="w-3.5 h-3.5 text-[#6b46c1] flex-shrink-0" />
            <span className="truncate"><strong>Inventor:</strong> {patent.inventor}</span>
          </div>

          <div className="flex items-center gap-1.5 truncate">
            <Building2 className="w-3.5 h-3.5 text-[#6b46c1] flex-shrink-0" />
            <span className="truncate"><strong>Org:</strong> {patent.organization}</span>
          </div>

          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#6b46c1] flex-shrink-0" />
            <span><strong>Filed:</strong> {patent.filingDate}</span>
          </div>

          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[#6b46c1] flex-shrink-0" />
            <span><strong>Published:</strong> {patent.publicationDate}</span>
          </div>
        </div>

        {/* Tech Tags */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {patent.technology.map((tech, idx) => (
            <span 
              key={idx} 
              className="inline-flex items-center px-2.5 py-0.5 rounded-lg text-[11px] font-medium bg-[#f3eefc] dark:bg-[#231845] text-[#553c9a] dark:text-purple-200 border border-[#e2d5f8] dark:border-[#382969]"
            >
              <Tag className="w-3 h-3 mr-1 text-[#6b46c1]" />
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="pt-3 border-t border-[#e9e1fa]/40 flex items-center justify-between gap-2">
        <button
          onClick={() => navigate(`/patent/${patent.id}`)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#6b46c1] hover:bg-[#553c9a] text-white rounded-xl text-xs font-bold transition-all shadow-xs"
        >
          View Patent
          <ExternalLink className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => navigate(`/graph?patentId=${patent.id}`)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#f3eefc] dark:bg-[#231845] text-[#6b46c1] dark:text-purple-200 hover:bg-[#6b46c1] hover:text-white rounded-xl text-xs font-semibold border border-[#e2d5f8] dark:border-[#382969] transition-colors"
        >
          <Network className="w-3.5 h-3.5" />
          Explore Graph
        </button>
      </div>

    </div>
  );
}

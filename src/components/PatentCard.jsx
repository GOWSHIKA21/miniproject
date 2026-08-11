import { useNavigate } from 'react-router-dom';
import { FileText, Building2, User, Calendar, Tag, ChevronRight } from 'lucide-react';

export default function PatentCard({ patent }) {
  const navigate = useNavigate();

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-2">
              {patent.title}
            </h3>
            <p className="text-sm font-medium text-indigo-600 mt-1">{patent.patentNumber}</p>
          </div>
          <div className="flex flex-col items-end">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              {patent.relevance}% Match
            </span>
          </div>
        </div>
        
        <p className="text-slate-600 text-sm mb-5 line-clamp-3">
          {patent.abstract}
        </p>
        
        <div className="grid grid-cols-2 gap-y-3 gap-x-4 mb-6">
          <div className="flex items-center text-sm text-slate-500">
            <User className="flex-shrink-0 mr-1.5 h-4 w-4 text-slate-400" />
            <span className="truncate">{patent.inventor}</span>
          </div>
          <div className="flex items-center text-sm text-slate-500">
            <Building2 className="flex-shrink-0 mr-1.5 h-4 w-4 text-slate-400" />
            <span className="truncate">{patent.organization}</span>
          </div>
          <div className="flex items-center text-sm text-slate-500">
            <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4 text-slate-400" />
            <span>{patent.filingDate}</span>
          </div>
          <div className="flex items-center text-sm text-slate-500">
            <Tag className="flex-shrink-0 mr-1.5 h-4 w-4 text-slate-400" />
            <span className="truncate">{patent.technology[0]}</span>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="flex gap-2 overflow-hidden">
            {patent.technology.slice(0, 2).map((tech, idx) => (
              <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 whitespace-nowrap">
                {tech}
              </span>
            ))}
            {patent.technology.length > 2 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 whitespace-nowrap">
                +{patent.technology.length - 2}
              </span>
            )}
          </div>
          <button
            onClick={() => navigate(`/patent/${patent.id}`)}
            className="inline-flex items-center text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            View Patent
            <ChevronRight className="ml-1 w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

import { useParams, useNavigate } from 'react-router-dom';
import { Bookmark, ArrowLeft, BrainCircuit, Share2, FileText, User, Building2, Calendar, Tag, ShieldCheck, Zap } from 'lucide-react';
import { patents } from '../data/patents';

export default function PatentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const patent = patents.find(p => p.id === id);

  if (!patent) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center">
        <h2 className="text-2xl font-bold text-slate-800">Patent not found</h2>
        <button onClick={() => navigate('/search')} className="mt-4 text-indigo-600 font-medium hover:underline">
          Return to search
        </button>
      </div>
    );
  }

  return (
    <div className="bg-slate-50 min-h-screen pb-12">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-slate-200 py-3 sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <button 
            onClick={() => navigate(-1)}
            className="flex items-center text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Results
          </button>
          <div className="flex gap-2">
            <button className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors">
              <Share2 className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors">
              <Bookmark className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* Main Content Area */}
          <div className="w-full lg:w-2/3 space-y-6">
            
            {/* Header Section */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200">
                  {patent.patentNumber}
                </span>
                <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${
                  patent.status === 'Granted' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-blue-50 text-blue-700 border-blue-200'
                }`}>
                  <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                  {patent.status}
                </span>
              </div>
              
              <h1 className="text-3xl font-bold text-slate-900 mb-6 leading-tight">
                {patent.title}
              </h1>

              <div className="flex flex-wrap gap-2 mb-6">
                {patent.technology.map((tech, idx) => (
                  <span key={idx} className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                    <Tag className="w-3.5 h-3.5 mr-1.5" />
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Abstract Section */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center">
                <FileText className="w-5 h-5 mr-2 text-indigo-600" />
                Abstract
              </h2>
              <p className="text-slate-700 leading-relaxed text-lg">
                {patent.abstract}
              </p>
            </div>
            
            {/* Mock Claims Section */}
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <h2 className="text-xl font-bold text-slate-900 mb-4">Claims</h2>
              <div className="space-y-4 text-slate-700">
                <p><strong>1.</strong> A method comprising: receiving data from a plurality of sensors; processing the data using a machine learning model; and generating an output based on the processed data.</p>
                <p><strong>2.</strong> The method of claim 1, wherein the machine learning model comprises a convolutional neural network.</p>
                <p className="italic text-slate-400 text-sm">... additional claims available in full document.</p>
              </div>
            </div>
          </div>

          {/* Sidebar Area */}
          <div className="w-full lg:w-1/3 space-y-6">
            
            {/* AI Actions */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-2xl p-6 border border-indigo-100 shadow-sm">
              <h3 className="text-lg font-bold text-indigo-900 mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-indigo-600" />
                AI Actions
              </h3>
              <div className="space-y-3">
                <button className="w-full flex items-center justify-center gap-2 bg-white border border-indigo-200 hover:border-indigo-400 text-indigo-700 px-4 py-3 rounded-xl font-medium transition-colors shadow-sm hover:shadow">
                  <BrainCircuit className="w-5 h-5" />
                  Summarize with AI
                </button>
                <button 
                  onClick={() => navigate('/assistant')}
                  className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-3 rounded-xl font-medium transition-colors shadow-sm hover:shadow"
                >
                  Ask AI About This Patent
                </button>
                <button 
                  onClick={() => navigate('/graph')}
                  className="w-full flex items-center justify-center gap-2 bg-white border border-slate-200 hover:border-indigo-400 text-slate-700 hover:text-indigo-700 px-4 py-3 rounded-xl font-medium transition-colors shadow-sm hover:shadow"
                >
                  View in Knowledge Graph
                </button>
              </div>
            </div>

            {/* Metadata Card */}
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-5">Key Information</h3>
              
              <div className="space-y-5">
                <div>
                  <div className="flex items-center text-sm font-medium text-slate-500 mb-1">
                    <User className="w-4 h-4 mr-1.5" /> Inventor(s)
                  </div>
                  <div className="text-slate-900 font-medium">{patent.inventor}</div>
                </div>
                
                <div>
                  <div className="flex items-center text-sm font-medium text-slate-500 mb-1">
                    <Building2 className="w-4 h-4 mr-1.5" /> Organization
                  </div>
                  <div className="text-slate-900 font-medium">{patent.organization}</div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center text-sm font-medium text-slate-500 mb-1">
                      <Calendar className="w-4 h-4 mr-1.5" /> Filing Date
                    </div>
                    <div className="text-slate-900 font-medium">{patent.filingDate}</div>
                  </div>
                  <div>
                    <div className="flex items-center text-sm font-medium text-slate-500 mb-1">
                      <Calendar className="w-4 h-4 mr-1.5" /> Published
                    </div>
                    <div className="text-slate-900 font-medium">{patent.publicationDate}</div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100">
                  <div className="text-sm font-medium text-slate-500 mb-1">IPC Classification</div>
                  <div className="inline-flex items-center px-2 py-1 bg-slate-100 text-slate-700 rounded text-sm font-medium">
                    {patent.ipc}
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

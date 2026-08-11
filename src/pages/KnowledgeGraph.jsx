import GraphViewer from '../components/GraphViewer';
import { Network, Info } from 'lucide-react';

export default function KnowledgeGraph() {
  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
              <Network className="w-6 h-6" />
            </div>
            Patent Relationship Explorer
          </h1>
          <p className="mt-3 text-lg text-slate-600 max-w-3xl">
            Visualize connections between patents, technologies, inventors, and organizations. 
            This graph helps identify innovation clusters and white spaces in the technology landscape.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-8">
          <div className="flex items-center gap-2 mb-4 text-sm text-slate-500 bg-slate-50 p-3 rounded-lg border border-slate-100">
            <Info className="w-4 h-4 text-indigo-500 flex-shrink-0" />
            <p><strong>Interactive Graph:</strong> You can drag nodes to rearrange them, scroll to zoom, and click on nodes (future) to explore related entities. (Currently showing mock data)</p>
          </div>
          
          {/* Graph Visualization Component */}
          <GraphViewer />
        </div>

        {/* Legend */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wider">Node Legend</h3>
          <div className="flex flex-wrap gap-6">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm bg-indigo-600"></div>
              <span className="text-sm text-slate-600">Patent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm bg-indigo-100 border border-indigo-200"></div>
              <span className="text-sm text-slate-600">Technology</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm bg-amber-100 border border-amber-200"></div>
              <span className="text-sm text-slate-600">Inventor</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm bg-green-100 border border-green-200"></div>
              <span className="text-sm text-slate-600">Organization</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-sm bg-slate-100 border border-slate-200"></div>
              <span className="text-sm text-slate-600">IPC Class</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

import { BrainCircuit, MessageSquare, Database, Network, Search, BarChart3 } from 'lucide-react';
import FeatureCard from '../components/FeatureCard';

export default function About() {
  return (
    <div className="bg-slate-50 min-h-screen py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h1 className="text-4xl font-bold text-slate-900 mb-4">About PatentIQ</h1>
          <h2 className="text-xl text-indigo-600 font-medium mb-6">
            Knowledge-Graph-Enhanced RAG System for Intelligent Querying of Indian Patent Databases
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            This project aims to make Indian patent information easier to search, analyze, and understand by combining advanced semantic search, Retrieval-Augmented Generation (RAG), and Knowledge Graph technologies.
          </p>
        </div>

        {/* Architecture Visual */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 mb-16 overflow-x-auto">
          <h3 className="text-xl font-bold text-slate-900 mb-8 text-center">System Architecture</h3>
          <div className="flex items-center justify-center min-w-[700px] py-4">
            <div className="flex items-center gap-2">
              
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center border-2 border-slate-300 text-slate-600 z-10 relative shadow-sm">
                  User
                </div>
              </div>
              <div className="w-12 h-1 bg-indigo-200"></div>
              
              <div className="flex flex-col items-center">
                <div className="w-24 h-16 rounded-lg bg-blue-50 flex items-center justify-center border-2 border-blue-200 text-blue-700 font-medium z-10 relative shadow-sm">
                  Search
                </div>
              </div>
              <div className="w-12 h-1 bg-indigo-200"></div>

              <div className="flex flex-col items-center">
                <div className="w-24 h-16 rounded-lg bg-indigo-50 flex items-center justify-center border-2 border-indigo-200 text-indigo-700 font-medium z-10 relative shadow-sm">
                  Retrieval
                </div>
              </div>
              <div className="w-12 h-1 bg-indigo-200"></div>

              <div className="flex flex-col items-center">
                <div className="w-32 h-16 rounded-lg bg-purple-50 flex items-center justify-center border-2 border-purple-200 text-purple-700 font-medium z-10 relative shadow-sm text-center px-2">
                  Knowledge Graph
                </div>
              </div>
              <div className="w-12 h-1 bg-indigo-200"></div>

              <div className="flex flex-col items-center">
                <div className="w-24 h-16 rounded-lg bg-pink-50 flex items-center justify-center border-2 border-pink-200 text-pink-700 font-medium z-10 relative shadow-sm">
                  AI / LLM
                </div>
              </div>
              <div className="w-12 h-1 bg-indigo-200"></div>

              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center border-2 border-green-300 text-green-700 font-medium z-10 relative shadow-sm">
                  Answer
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Technologies */}
        <div className="mb-12">
          <h3 className="text-2xl font-bold text-slate-900 mb-8 text-center">Core Technology Areas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard 
              icon={BrainCircuit}
              title="Artificial Intelligence"
              description="Powering the core intelligence to understand complex technical queries and generate human-like summaries."
            />
            <FeatureCard 
              icon={MessageSquare}
              title="Natural Language Processing"
              description="Enabling the system to parse, understand, and extract meaning from dense patent documents."
            />
            <FeatureCard 
              icon={Database}
              title="RAG Pipeline"
              description="Retrieval-Augmented Generation grounds the AI's answers in actual patent data to prevent hallucinations."
            />
            <FeatureCard 
              icon={Network}
              title="Knowledge Graphs"
              description="Structuring data into nodes and edges (Neo4j) to map relationships between inventors, companies, and technologies."
            />
            <FeatureCard 
              icon={Search}
              title="Semantic Search"
              description="Vector embeddings allow users to search by concept and meaning, overcoming the limitations of exact keyword matching."
            />
            <FeatureCard 
              icon={BarChart3}
              title="Patent Analytics"
              description="Extracting trends and insights from large volumes of intellectual property data to aid research and development."
            />
          </div>
        </div>

      </div>
    </div>
  );
}

import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import FeatureCard from '../components/FeatureCard';
import { Search, BrainCircuit, Lightbulb, Network } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();

  const handleSearch = (query) => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
    } else {
      navigate('/search');
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        {/* Background Decorative Elements */}
        <div className="absolute inset-0 bg-slate-50 z-0"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[50%] rounded-full bg-indigo-100/50 blur-3xl mix-blend-multiply"></div>
          <div className="absolute top-[20%] right-[-5%] w-[35%] h-[45%] rounded-full bg-blue-100/50 blur-3xl mix-blend-multiply"></div>
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center mt-12">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-sm font-medium mb-8 animate-fade-in-up">
            <span className="flex h-2 w-2 rounded-full bg-indigo-600 mr-2"></span>
            Next-Gen Patent Intelligence
          </div>
          
          <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight mb-6 leading-tight">
            Intelligent Search for <br className="hidden md:block" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-blue-500">
              Indian Patents
            </span>
          </h1>
          
          <p className="mt-4 text-xl text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed">
            Explore, understand, and discover relationships across Indian patent information using AI-powered semantic search.
          </p>
          
          <div className="max-w-3xl mx-auto mb-12 relative z-20">
            <SearchBar 
              placeholder="Ask a question about Indian patents..." 
              onSearch={handleSearch}
              large={true}
            />
          </div>

          <div className="flex flex-wrap justify-center gap-4 text-sm text-slate-500">
            <span className="font-medium text-slate-700 mr-2">Try asking:</span>
            <button onClick={() => handleSearch("Find patents related to AI in agriculture")} className="hover:text-indigo-600 transition-colors bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm hover:border-indigo-200">
              "Find patents related to AI in agriculture"
            </button>
            <button onClick={() => handleSearch("Show patents for electric vehicle batteries")} className="hover:text-indigo-600 transition-colors bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm hover:border-indigo-200">
              "Show patents for electric vehicle batteries"
            </button>
            <button onClick={() => handleSearch("Blockchain in healthcare")} className="hover:text-indigo-600 transition-colors bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm hover:border-indigo-200 hidden sm:block">
              "Blockchain in healthcare"
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">Platform Capabilities</h2>
            <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
              Leverage advanced AI and Knowledge Graphs to transform how you research intellectual property.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <FeatureCard
              icon={Search}
              title="Semantic Search"
              description="Find relevant patents based on meaning and context, not just exact keyword matches."
            />
            <FeatureCard
              icon={BrainCircuit}
              title="AI-Powered Answers"
              description="Get concise, accurate answers to natural-language patent queries instantly."
            />
            <FeatureCard
              icon={Lightbulb}
              title="Patent Insights"
              description="Explore detailed patent information, key inventors, organizations, and technologies."
            />
            <FeatureCard
              icon={Network}
              title="Knowledge Graph"
              description="Discover hidden relationships between patents, technologies, and related entities."
            />
          </div>
        </div>
      </section>
    </div>
  );
}

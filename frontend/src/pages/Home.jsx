import { useNavigate } from 'react-router-dom';
import { Search, Cpu, ArrowRight, Sparkles, ShieldCheck, Zap, Layers, Network } from 'lucide-react';
import FeatureCard from '../components/FeatureCard';

export default function Home({ isDarkTheme }) {
  const navigate = useNavigate();

  // Floating keywords from the reference image
  const patentKeywords = [
    { text: "Infringement Analysis", top: "12%", right: "35%", size: "text-lg font-bold opacity-60" },
    { text: "Patentability", top: "28%", right: "52%", size: "text-[#553c9a] text-xl font-bold opacity-80" },
    { text: "Proofreading", top: "18%", right: "12%", size: "text-sm font-semibold opacity-50" },
    { text: "Technology", top: "27%", right: "8%", size: "text-base font-semibold opacity-60" },
    { text: "Prior Art", top: "37%", right: "10%", size: "text-[#6b46c1] text-lg font-extrabold opacity-85" },
    { text: "Freedom to Operate", top: "48%", right: "8%", size: "text-[#553c9a] text-base font-bold opacity-75" },
    { text: "Patent Watch", top: "63%", right: "12%", size: "text-sm font-medium opacity-60" },
    { text: "Chemical", top: "72%", right: "15%", size: "text-base font-semibold opacity-65" },
    { text: "Examination", top: "80%", right: "9%", size: "text-lg font-bold opacity-70" },
    { text: "Accelerated Examination", top: "88%", right: "18%", size: "text-[#6b46c1] text-xl font-black opacity-90" },
    { text: "Novelty", top: "58%", right: "50%", size: "text-xl font-extrabold text-[#553c9a] opacity-80" },
    { text: "Claims", top: "42%", right: "55%", size: "text-2xl font-black opacity-40" },
  ];

  return (
    <div className={`min-h-[calc(100vh-4rem)] flex flex-col justify-between p-4 sm:p-6 lg:p-10 transition-colors duration-300 ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      
      {/* Hero Container: Grid matching the reference screenshot */}
      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center py-6 my-auto">
        
        {/* Left Column: Quotation + Headline + Subtitle + CTA */}
        <div className="lg:col-span-6 space-y-6">
          
          {/* Large Decorative Quote Icon */}
          <div className="text-5xl sm:text-6xl text-[#6b46c1] font-serif leading-none font-black select-none">
            “
          </div>

          {/* Main Headline */}
          <h1 className={`text-3xl sm:text-4xl lg:text-5xl font-serif font-semibold tracking-tight leading-snug ${
            isDarkTheme ? 'text-white' : 'text-[#2d1f56]'
          }`}>
            Find the ideas <br />
            that protect <br />
            innovation and <br />
            shape the future.”
          </h1>

          {/* Underline Accent */}
          <div className="w-16 h-1 bg-[#6b46c1] rounded-full" />

          {/* Subtitle */}
          <p className={`text-base sm:text-lg max-w-md leading-relaxed ${
            isDarkTheme ? 'text-slate-300' : 'text-[#4a367c]'
          }`}>
            PatentGraph helps you search, explore, and analyze patents intelligently.
          </p>

          {/* CTA Action Buttons */}
          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={() => navigate('/search')}
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-[#6b46c1] hover:bg-[#553c9a] text-white font-bold rounded-2xl text-sm sm:text-base transition-all shadow-lg shadow-purple-900/30 hover:scale-105"
            >
              <Search className="w-4 h-4" />
              Start Patent Search
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>

            <button
              onClick={() => navigate('/explorer')}
              className={`inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl font-bold text-sm sm:text-base border transition-all hover:scale-105 ${
                isDarkTheme 
                  ? 'bg-[#231845] hover:bg-[#2e2057] text-purple-200 border-[#3d2b70]' 
                  : 'bg-white hover:bg-slate-50 text-[#6b46c1] border-[#e2d5f8] shadow-sm'
              }`}
            >
              <Cpu className="w-4 h-4" />
              Explore Technologies
            </button>
          </div>

        </div>

        {/* Right Column: Magnifying Glass Focus Lens over PatentGraph Word Cloud */}
        <div className="lg:col-span-6 relative flex items-center justify-center min-h-[380px] sm:min-h-[460px] overflow-hidden rounded-3xl p-4">
          
          {/* Subtle Constellation Glow Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-indigo-500/5 to-transparent rounded-3xl blur-2xl" />

          {/* Floating Keyword Cloud (CSS Layer) */}
          <div className="absolute inset-0 pointer-events-none select-none hidden sm:block">
            {patentKeywords.map((item, idx) => (
              <span
                key={idx}
                style={{ top: item.top, right: item.right }}
                className={`absolute ${item.size} ${isDarkTheme ? 'text-purple-300' : 'text-[#4a367c]'} transition-all`}
              >
                {item.text}
              </span>
            ))}
          </div>

          {/* High Resolution Rendered Lens Graphic matching reference image */}
          <div className="relative z-10 w-full max-w-lg aspect-4/3 rounded-3xl overflow-hidden shadow-2xl border border-purple-300/20 group">
            <img 
              src="/home-hero.jpg" 
              alt="PatentGraph Magnifying Glass Hero Illustration" 
              className="w-full h-full object-cover rounded-3xl transform group-hover:scale-105 transition-transform duration-700"
            />
          </div>

        </div>

      </div>

      {/* Feature Capabilities Grid */}
      <div className="max-w-7xl mx-auto w-full pt-12 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <FeatureCard
            icon={Search}
            title="Semantic Discovery"
            description="Find relevant prior art using natural-language questions and patent concepts."
            isDarkTheme={isDarkTheme}
          />
          <FeatureCard
            icon={Layers}
            title="Dynamic Date Filters"
            description="Filter by Priority, Exact Date, or Date Ranges with interactive calendar selectors."
            isDarkTheme={isDarkTheme}
          />
          <FeatureCard
            icon={Network}
            title="Knowledge Graph"
            description="Explore connected networks of patents, inventors, assignees, and technology IPCs."
            isDarkTheme={isDarkTheme}
          />
          <FeatureCard
            icon={Sparkles}
            title="AI Assistance"
            description="Chat with an intelligent assistant to summarize claims, explain technical jargon, and refine queries."
            isDarkTheme={isDarkTheme}
          />
        </div>
      </div>

    </div>
  );
}

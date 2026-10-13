import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Cpu, ArrowRight, Sparkles, ZoomIn, ZoomOut, Play, Pause, RefreshCw } from 'lucide-react';

export default function Home({ isDarkTheme }) {
  const navigate = useNavigate();
  const [isZooming, setIsZooming] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const [isClickZoomed, setIsClickZoomed] = useState(false);

  // Smooth mouse move parallax for 3D depth effect
  const handleMouseMove = (e) => {
    const { clientX, clientY } = e;
    const { innerWidth, innerHeight } = window;
    const x = (clientX / innerWidth - 0.5) * 20; // -10px to +10px
    const y = (clientY / innerHeight - 0.5) * 20; // -10px to +10px
    setMousePos({ x, y });
  };

  // Background blurred floating patent keywords matching reference image layout
  const bgKeywords = [
    { text: "Infringement", top: "8%", left: "55%", size: "text-2xl font-bold opacity-35" },
    { text: "Analysis", top: "12%", left: "75%", size: "text-3xl font-extrabold opacity-40" },
    { text: "Proofreading", top: "15%", left: "38%", size: "text-lg font-semibold opacity-30" },
    { text: "Mapping", top: "20%", left: "52%", size: "text-base font-bold opacity-35" },
    { text: "Innovation", top: "24%", left: "63%", size: "text-3xl font-black text-[#6b46c1] opacity-75" },
    { text: "Intellectual Property", top: "28%", left: "32%", size: "text-xl font-bold opacity-45" },
    { text: "Patentability", top: "36%", left: "42%", size: "text-2xl font-bold text-[#553c9a] opacity-65" },
    { text: "Technology", top: "32%", left: "85%", size: "text-lg font-bold opacity-40" },
    { text: "Prior Art", top: "42%", left: "84%", size: "text-xl font-extrabold opacity-50" },
    { text: "Claims", top: "48%", left: "44%", size: "text-2xl font-black opacity-35" },
    { text: "Freedom to Operate", top: "54%", left: "82%", size: "text-lg font-bold opacity-45" },
    { text: "Novelty", top: "62%", left: "45%", size: "text-2xl font-bold opacity-50" },
    { text: "Patent Watch", top: "68%", left: "80%", size: "text-lg font-medium opacity-40" },
    { text: "Chemical", top: "76%", left: "78%", size: "text-xl font-bold opacity-45" },
    { text: "Examination", top: "84%", left: "77%", size: "text-2xl font-black opacity-55" },
    { text: "Accelerated Examination", top: "92%", left: "58%", size: "text-2xl font-black text-[#6b46c1] opacity-70" },
    { text: "Patent Search", top: "80%", left: "55%", size: "text-3xl font-black text-[#553c9a] opacity-80" },
  ];

  return (
    <div 
      onMouseMove={handleMouseMove}
      className={`relative min-h-[calc(100vh-4rem)] lg:h-[calc(100vh)] w-full flex flex-col justify-between p-6 lg:p-12 overflow-hidden transition-colors duration-500 select-none ${
        isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-gradient-to-br from-[#f5efff] via-[#ede6fd] to-[#f3eefc] text-[#2d1f56]'
      }`}
    >

      {/* Background Glowing Constellation & Ambient Sparkles */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/3 right-1/4 w-[400px] h-[400px] bg-indigo-500/10 rounded-full blur-3xl" />
        
        {/* Constellation Network Grid SVG */}
        <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
          <line x1="10%" y1="20%" x2="30%" y2="40%" stroke={isDarkTheme ? "#a78bfa" : "#6b46c1"} strokeWidth="1" strokeDasharray="4 4" />
          <line x1="30%" y1="40%" x2="60%" y2="25%" stroke={isDarkTheme ? "#a78bfa" : "#6b46c1"} strokeWidth="1" strokeDasharray="4 4" />
          <line x1="60%" y1="25%" x2="85%" y2="50%" stroke={isDarkTheme ? "#a78bfa" : "#6b46c1"} strokeWidth="1" strokeDasharray="4 4" />
          <line x1="45%" y1="70%" x2="75%" y2="85%" stroke={isDarkTheme ? "#a78bfa" : "#6b46c1"} strokeWidth="1" strokeDasharray="4 4" />
          
          <circle cx="10%" cy="20%" r="3" fill="#6b46c1" className="animate-node-pulse" />
          <circle cx="30%" cy="40%" r="4" fill="#8b5cf6" className="animate-node-pulse" />
          <circle cx="60%" cy="25%" r="3.5" fill="#a78bfa" className="animate-node-pulse" />
          <circle cx="85%" cy="50%" r="4" fill="#6b46c1" className="animate-node-pulse" />
          <circle cx="75%" cy="85%" r="3" fill="#8b5cf6" className="animate-node-pulse" />
        </svg>

        {/* Faded Background Words floating across canvas matching reference image */}
        {bgKeywords.map((kw, idx) => (
          <span
            key={idx}
            style={{ 
              top: kw.top, 
              left: kw.left,
              transform: `translate(${mousePos.x * 0.3}px, ${mousePos.y * 0.3}px)`
            }}
            className={`absolute ${kw.size} ${
              isDarkTheme ? 'text-purple-300/40' : 'text-[#4a367c]/40'
            } transition-transform duration-300 font-sans tracking-wide blur-[0.3px] animate-float-keyword`}
          >
            {kw.text}
          </span>
        ))}
      </div>

      {/* Main Workspace Grid (Left Text Content + Right Magnifying Glass Lens) */}
      <div className="relative z-10 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center my-auto">
        
        {/* Left Column: Quotation, Headline, Subtitle, CTA buttons, Zoom Toggle */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Decorative Purple Quotation Mark */}
          <div className="text-6xl sm:text-7xl text-[#6b46c1] font-serif leading-none font-black select-none drop-shadow-sm">
            “
          </div>

          {/* Headline Text matching the reference image */}
          <h1 className={`text-3xl sm:text-4xl lg:text-5xl font-serif font-medium tracking-tight leading-[1.25] ${
            isDarkTheme ? 'text-white' : 'text-[#2d1f56]'
          }`}>
            Empowering <br />
            innovation today, <br />
            protecting <br />
            ideas tomorrow.”
          </h1>

          {/* Underline Indicator Accent */}
          <div className="w-16 h-1 bg-[#6b46c1] rounded-full shadow-xs" />

          {/* Subtitle */}
          <p className={`text-base sm:text-lg max-w-md leading-relaxed font-normal ${
            isDarkTheme ? 'text-slate-300' : 'text-[#4a367c]'
          }`}>
            PatentGraph helps you discover, explore, and analyze patents with intelligence.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={() => navigate('/search')}
              className="inline-flex items-center gap-2 px-7 py-3.5 bg-[#6b46c1] hover:bg-[#553c9a] text-white font-bold rounded-2xl text-sm sm:text-base transition-all shadow-lg shadow-purple-900/25 hover:scale-105 active:scale-95"
            >
              <Search className="w-4 h-4" />
              Start Patent Search
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>

            <button
              onClick={() => navigate('/explorer')}
              className={`inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl font-bold text-sm sm:text-base border transition-all hover:scale-105 active:scale-95 ${
                isDarkTheme 
                  ? 'bg-[#231845] hover:bg-[#2e2057] text-purple-200 border-[#3d2b70]' 
                  : 'bg-white/90 hover:bg-white text-[#6b46c1] border-[#e2d5f8] shadow-xs'
              }`}
            >
              <Cpu className="w-4 h-4" />
              Explore Technologies
            </button>
          </div>

          {/* Interactive Magnifying Glass Zoom Controls */}
          <div className="pt-4 flex items-center gap-3">
            <button
              onClick={() => setIsZooming(!isZooming)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${
                isZooming 
                  ? 'bg-[#efe6fd] text-[#5c3ea1] border-[#d8c5fa]' 
                  : isDarkTheme ? 'bg-[#1e1538] text-slate-300 border-[#382863]' : 'bg-white text-slate-600 border-slate-200'
              }`}
            >
              {isZooming ? <Pause className="w-3.5 h-3.5 text-[#6b46c1]" /> : <Play className="w-3.5 h-3.5 text-[#6b46c1]" />}
              <span>{isZooming ? "Pause Zooming Effect" : "Enable Auto-Zoom"}</span>
            </button>

            <button
              onClick={() => setIsClickZoomed(!isClickZoomed)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold border transition-all ${
                isClickZoomed 
                  ? 'bg-[#6b46c1] text-white border-[#6b46c1]' 
                  : isDarkTheme ? 'bg-[#1e1538] text-slate-300 border-[#382863]' : 'bg-white text-slate-600 border-slate-200'
              }`}
            >
              {isClickZoomed ? <ZoomOut className="w-3.5 h-3.5" /> : <ZoomIn className="w-3.5 h-3.5" />}
              <span>{isClickZoomed ? "Reset Lens Zoom" : "Deep Inspect Zoom"}</span>
            </button>
          </div>

        </div>

        {/* Right Column: Handheld Magnifying Glass with Handle attached cleanly at bottom-left outer rim */}
        <div className="lg:col-span-7 relative flex items-center justify-center min-h-[440px] sm:min-h-[560px]">
          
          {/* Glass Specular Ambient Blur Glow */}
          <div className="absolute w-[480px] h-[480px] bg-gradient-to-tr from-purple-400/20 via-indigo-400/10 to-transparent rounded-full blur-3xl animate-pulse" />

          {/* Interactive Native Magnifying Glass Frame */}
          <div 
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onClick={() => setIsClickZoomed(!isClickZoomed)}
            style={{
              transform: `translate(${mousePos.x * 0.7}px, ${mousePos.y * 0.7}px) ${
                isClickZoomed ? 'scale(1.16)' : isHovered ? 'scale(1.06)' : 'scale(1)'
              }`
            }}
            className={`relative w-full max-w-[580px] aspect-square flex items-center justify-center cursor-pointer transition-transform duration-500 ease-out select-none ${
              isZooming && !isHovered && !isClickZoomed ? 'animate-zoom-in-out' : ''
            }`}
          >

            {/* Magnifying Glass Assembly Container (Circle + Handle) */}
            <div className="relative w-[350px] sm:w-[440px] h-[350px] sm:h-[440px] flex items-center justify-center">

              {/* Ferrule & Handle Stick on Right Side (z-10 so circle sits on top; never above circle) */}
              <div className="absolute top-[82%] left-[82%] -translate-y-1/2 w-[380px] sm:w-[500px] h-[36px] sm:h-[44px] rotate-[44deg] origin-left z-10 pointer-events-none">
                
                {/* Silver Ribbed Ferrule Joint (4 rings) tucked under outer rim */}
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-20 sm:w-24 h-full bg-gradient-to-b from-slate-200 via-slate-100 to-slate-400 rounded-md border border-slate-300 shadow-xl flex items-center justify-between px-1.5 z-10">
                  <div className="w-2.5 h-full bg-gradient-to-r from-slate-400 via-white to-slate-400 rounded-xs border-x border-slate-400 shadow-inner" />
                  <div className="w-2.5 h-full bg-gradient-to-r from-slate-400 via-white to-slate-400 rounded-xs border-x border-slate-400 shadow-inner" />
                  <div className="w-2.5 h-full bg-gradient-to-r from-slate-400 via-white to-slate-400 rounded-xs border-x border-slate-400 shadow-inner" />
                  <div className="w-2.5 h-full bg-gradient-to-r from-slate-400 via-white to-slate-400 rounded-xs border-x border-slate-400 shadow-inner" />
                </div>

                {/* Cylindrical Dark Glossy Black Handle Rod extending down-right */}
                <div className="ml-[72px] sm:ml-[88px] w-full h-full bg-gradient-to-b from-slate-800 via-slate-950 to-slate-900 rounded-full shadow-2xl border-t border-slate-700/60 relative overflow-hidden">
                  <div className="w-full h-1.5 bg-gradient-to-r from-slate-700/30 via-white/40 to-slate-700/30 rounded-full" />
                </div>

              </div>

              {/* Circular Chrome Metal Frame Rim (z-20 so it sits ABOVE the stick) */}
              <div className="relative w-full h-full rounded-full p-3 bg-gradient-to-tr from-slate-400 via-slate-100 to-slate-600 shadow-[0_25px_60px_-10px_rgba(85,60,154,0.4)] border-4 border-slate-300 z-20 flex items-center justify-center group">
                
                {/* Inner Metallic Bevel Groove Rim */}
                <div className="w-full h-full rounded-full p-2 bg-gradient-to-br from-slate-700 via-slate-300 to-slate-800 shadow-2xl flex items-center justify-center">
                  
                  {/* Round Concave Lens - Background matches page background */}
                  <div className={`w-full h-full rounded-full relative overflow-hidden flex items-center justify-center p-6 transition-colors duration-500 shadow-[inset_0_0_35px_rgba(107,70,193,0.18),_inset_0_0_15px_rgba(0,0,0,0.15)] border-2 border-slate-300/40 ${
                    isDarkTheme ? 'bg-[#120c24]' : 'bg-[#ede6fd]'
                  }`}>
                    
                    {/* Real Glass Specular Glare Highlights */}
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_35%_20%,_rgba(255,255,255,0.45)_0%,_rgba(255,255,255,0.08)_45%,_transparent_70%)] pointer-events-none z-30" />
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_70%_80%,_rgba(255,255,255,0.2)_0%,_transparent_60%)] pointer-events-none z-30" />
                    <div className="absolute inset-0 rounded-full border-[10px] border-purple-500/10 pointer-events-none z-30 blur-xs" />

                    {/* Optical Lens Content - Deep Dark Purple Text in light theme (#1c0e3d), Light Purple in dark theme */}
                    <div className={`relative z-10 text-center w-full h-full flex flex-col items-center justify-center transition-transform duration-700 ease-in-out transform [perspective:600px] ${
                      isZooming ? 'animate-lens-text' : ''
                    }`}>
                      
                      {/* Top lens keywords */}
                      <div className={`flex items-center justify-center gap-3 text-xs sm:text-sm font-extrabold mb-1 tracking-wide transition-colors duration-300 ${
                        isDarkTheme ? 'text-purple-200' : 'text-[#1c0e3d]'
                      }`}>
                        <span>Patent Search</span>
                        <span className={isDarkTheme ? 'text-purple-400' : 'text-[#361e68]'}>•</span>
                        <span>Infringement Search</span>
                      </div>

                      <div className={`flex items-center justify-center gap-4 text-xs font-bold mb-3 transition-colors duration-300 ${
                        isDarkTheme ? 'text-purple-300' : 'text-[#2d1754]'
                      }`}>
                        <span>Patentability</span>
                        <span>Prior Art</span>
                        <span>Novelty</span>
                      </div>

                      {/* Centered Main Brand Title inside Lens */}
                      <div className="my-2 transform scale-105">
                        <h2 className={`text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight font-sans drop-shadow-md transition-colors duration-300 ${
                          isDarkTheme ? 'text-purple-100 drop-shadow-[0_2px_12px_rgba(192,132,252,0.35)]' : 'text-[#1c0e3d]'
                        }`}>
                          PatentGraph
                        </h2>
                      </div>

                      {/* Lower lens keywords */}
                      <div className={`flex items-center justify-center gap-3 text-xs font-bold mt-3 transition-colors duration-300 ${
                        isDarkTheme ? 'text-purple-200' : 'text-[#2d1754]'
                      }`}>
                        <span>Validity Search</span>
                        <span className={isDarkTheme ? 'text-purple-400' : 'text-[#361e68]'}>•</span>
                        <span>Patent Watch</span>
                      </div>

                      <div className={`flex items-center justify-center gap-2 text-[11px] font-extrabold mt-1 transition-colors duration-300 ${
                        isDarkTheme ? 'text-purple-300' : 'text-[#361e68]'
                      }`}>
                        <span>Licensing</span>
                        <span className={isDarkTheme ? 'text-purple-400' : 'text-[#361e68]'}>•</span>
                        <span>FTO Search</span>
                        <span className={isDarkTheme ? 'text-purple-400' : 'text-[#361e68]'}>•</span>
                        <span>Prior Art Search</span>
                      </div>

                      <div className={`text-[10px] font-black mt-1.5 uppercase tracking-wider transition-colors duration-300 ${
                        isDarkTheme ? 'text-purple-300/80' : 'text-[#1c0e3d]'
                      }`}>
                        Accelerated Examination & Mapping
                      </div>

                    </div>

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

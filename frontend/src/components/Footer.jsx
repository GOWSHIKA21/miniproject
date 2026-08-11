import { Link } from 'react-router-dom';

export default function Footer({ isDarkTheme }) {
  return (
    <footer className={`border-t text-xs py-6 px-4 sm:px-6 lg:px-8 mt-auto transition-colors ${
      isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c] text-slate-400' : 'bg-white border-[#e9e1fa] text-[#4a367c]'
    }`}>
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
        <Link to="/" className="flex items-center gap-2">
          <img 
            src="/logo.jpg" 
            alt="PatentGraph Logo" 
            className="w-6 h-6 rounded-md object-contain bg-white/20 p-0.5"
          />
          <span className="font-extrabold text-sm text-[#6b46c1]">
            PatentGraph
          </span>
        </Link>
        
        <p className="text-[11px] text-center sm:text-right">
          &copy; {new Date().getFullYear()} PatentGraph — Intelligent AI Patent Discovery & Relationship Platform.
        </p>
      </div>
    </footer>
  );
}

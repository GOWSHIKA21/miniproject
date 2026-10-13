import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Search, 
  Cpu, 
  Bot, 
  Sun, 
  Moon, 
  Menu, 
  X, 
  ChevronLeft, 
  ChevronRight 
} from 'lucide-react';

export default function Sidebar({ isDarkTheme, setIsDarkTheme, isCollapsed, setIsCollapsed }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { name: 'Home', path: '/', icon: Home },
    { name: 'Patent Search', path: '/search', icon: Search },
    { name: 'Technology Explorer', path: '/explorer', icon: Cpu },
    { name: 'AI Assistance', path: '/assistant', icon: Bot },
  ];

  return (
    <>
      {/* Mobile Top Navigation Header */}
      <div className={`lg:hidden fixed top-0 left-0 right-0 h-16 z-50 px-4 flex items-center justify-between border-b shadow-xs ${
        isDarkTheme ? 'bg-[#18112e] text-white border-[#2b1f4c]' : 'bg-white text-[#2d1f56] border-[#e9e1fa]'
      }`}>
        <Link to="/" className="flex items-center gap-3">
          <img 
            src="/logo.jpg" 
            alt="PatentGraph Logo" 
            className="w-8 h-8 rounded-lg object-contain bg-white/20 p-0.5"
          />
          <span className="font-extrabold text-lg tracking-tight text-[#5c3ea1]">
            PatentGraph
          </span>
        </Link>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className={`p-2 rounded-xl border ${
            isDarkTheme 
              ? 'bg-[#231845] text-slate-200 border-[#382969]' 
              : 'bg-[#f4effc] text-[#5c3ea1] border-[#e2d5f8]'
          }`}
          aria-label="Toggle Navigation Menu"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div 
          onClick={() => setMobileOpen(false)}
          className="lg:hidden fixed inset-0 bg-slate-950/60 backdrop-blur-xs z-40"
        />
      )}

      {/* Main Vertical Sidebar Container matching the reference image layout */}
      <aside
        className={`fixed top-0 left-0 bottom-0 z-50 flex flex-col justify-between transition-all duration-300 ease-in-out ${
          isCollapsed ? 'w-20' : 'w-64'
        } ${
          mobileOpen ? 'translate-x-0 w-64' : '-translate-x-full lg:translate-x-0'
        } ${
          isDarkTheme 
            ? 'bg-[#18112e] border-r border-[#2b1f4c] text-slate-200' 
            : 'bg-white border-r border-[#e9e1fa] text-[#2d1f56] shadow-lg shadow-purple-900/5'
        }`}
      >
        {/* Top Header: Logo + Brand Name */}
        <div>
          <div className="pt-7 pb-6 px-6 flex items-center justify-between">
            <Link 
              to="/" 
              onClick={() => setMobileOpen(false)}
              className="flex flex-col items-center text-center w-full"
            >
              <div className="w-14 h-14 rounded-2xl bg-[#f3eefc] border border-[#e2d5f8] flex items-center justify-center p-2 mb-2 shadow-xs group hover:scale-105 transition-transform">
                <img 
                  src="/logo.jpg" 
                  alt="PatentGraph Logo" 
                  className="w-full h-full object-contain"
                />
              </div>
              
              {(!isCollapsed || mobileOpen) && (
                <span className={`font-extrabold text-xl tracking-tight ${
                  isDarkTheme ? 'text-white' : 'text-[#2d1f56]'
                }`}>
                  PatentGraph
                </span>
              )}
            </Link>

            {/* Desktop Collapse Toggle */}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="hidden lg:flex items-center justify-center w-6 h-6 rounded-full bg-[#f3eefc] text-[#5c3ea1] hover:bg-[#6b46c1] hover:text-white transition-colors absolute right-2 top-6 border border-[#e2d5f8]"
              title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            >
              {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 space-y-1.5 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = 
                location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path));

              return (
                <Link
                  key={item.name}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center px-4 py-3 rounded-2xl font-semibold text-sm transition-all duration-200 group ${
                    isActive
                      ? isDarkTheme
                        ? 'bg-[#6b46c1] text-white shadow-md shadow-purple-900/30'
                        : 'bg-[#efe6fd] text-[#5c3ea1] font-bold shadow-xs'
                      : isDarkTheme
                        ? 'text-slate-300 hover:bg-[#251947] hover:text-white'
                        : 'text-[#4a367c] hover:bg-[#f4effc] hover:text-[#6b46c1]'
                  }`}
                  title={isCollapsed ? item.name : undefined}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 ${
                    isActive 
                      ? isDarkTheme ? 'text-white scale-110' : 'text-[#5c3ea1] scale-110' 
                      : 'text-[#6b46c1] group-hover:scale-105'
                  }`} />

                  {(!isCollapsed || mobileOpen) && (
                    <span className="ml-3.5 truncate tracking-wide text-xs sm:text-sm">
                      {item.name}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom Section: Theme Toggle Control (Sun ☀️ / Moon 🌙) */}
        <div className="p-4 border-t border-[#e9e1fa]/30 mb-2">
          {(!isCollapsed || mobileOpen) ? (
            <div className="flex items-center justify-between px-3 py-2.5 rounded-2xl bg-[#f4effc]/70 dark:bg-[#231845] border border-[#e2d5f8]/50 dark:border-[#382969]">
              <Sun className={`w-4 h-4 transition-colors ${!isDarkTheme ? 'text-amber-500 font-bold' : 'text-slate-400'}`} />
              
              {/* Interactive Smooth Toggle Control */}
              <button
                type="button"
                onClick={() => setIsDarkTheme(!isDarkTheme)}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out focus:outline-none ${
                  isDarkTheme ? 'bg-[#6b46c1]' : 'bg-slate-300'
                }`}
                role="switch"
                aria-checked={isDarkTheme}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-300 ease-in-out ${
                    isDarkTheme ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>

              <Moon className={`w-4 h-4 transition-colors ${isDarkTheme ? 'text-indigo-400 font-bold' : 'text-slate-400'}`} />
            </div>
          ) : (
            <button
              onClick={() => setIsDarkTheme(!isDarkTheme)}
              className="w-full flex items-center justify-center p-2.5 rounded-2xl bg-[#f4effc] text-[#6b46c1] hover:bg-[#6b46c1] hover:text-white transition-colors"
              title="Toggle Theme"
            >
              {isDarkTheme ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
          )}
        </div>

      </aside>
    </>
  );
}

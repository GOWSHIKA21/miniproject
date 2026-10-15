import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Search from './pages/Search';
import Explorer from './pages/Explorer';
import KnowledgeGraph from './pages/KnowledgeGraph';
import AIAssistant from './pages/AIAssistant';
import PatentDetails from './pages/PatentDetails';

function App() {
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Apply theme class to html and body
  useEffect(() => {
    if (isDarkTheme) {
      document.documentElement.classList.add('dark');
      document.body.classList.add('theme-dark', 'dark');
      document.body.classList.remove('theme-light');
    } else {
      document.documentElement.classList.remove('dark');
      document.body.classList.add('theme-light');
      document.body.classList.remove('theme-dark', 'dark');
    }
  }, [isDarkTheme]);

  return (
    <Router>
      <div className={`min-h-screen flex flex-col font-sans antialiased transition-colors duration-300 ${
        isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
      }`}>
        
        {/* Left Vertical Sidebar */}
        <Sidebar 
          isDarkTheme={isDarkTheme}
          setIsDarkTheme={setIsDarkTheme}
          isCollapsed={isCollapsed} 
          setIsCollapsed={setIsCollapsed} 
        />

        {/* Main Workspace (Direct alignment with sidebar, zero unwanted side gaps) */}
        <div className={`flex-1 flex flex-col transition-all duration-300 ${
          isCollapsed ? 'lg:ml-20' : 'lg:ml-64'
        }`}>
          {/* Mobile top spacer */}
          <div className="h-16 lg:h-0 flex-shrink-0" />

          {/* Main Content Area */}
          <main className="flex-1 w-full">
            <Routes>
              <Route path="/" element={<Home isDarkTheme={isDarkTheme} />} />
              <Route path="/search" element={<Search isDarkTheme={isDarkTheme} />} />
              <Route path="/explorer" element={<Explorer isDarkTheme={isDarkTheme} />} />
              <Route path="/graph" element={<KnowledgeGraph isDarkTheme={isDarkTheme} />} />
              <Route path="/assistant" element={<AIAssistant isDarkTheme={isDarkTheme} />} />
              <Route path="/patent/*" element={<PatentDetails isDarkTheme={isDarkTheme} />} />
            </Routes>
          </main>

          {/* Footer */}
          <Footer isDarkTheme={isDarkTheme} />
        </div>

      </div>
    </Router>
  );
}

export default App;

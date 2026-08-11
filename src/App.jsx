import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Search from './pages/Search';
import PatentDetails from './pages/PatentDetails';
import AIAssistant from './pages/AIAssistant';
import KnowledgeGraph from './pages/KnowledgeGraph';
import About from './pages/About';

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/patent/:id" element={<PatentDetails />} />
            <Route path="/assistant" element={<AIAssistant />} />
            <Route path="/graph" element={<KnowledgeGraph />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;

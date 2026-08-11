import { useState, useRef, useEffect } from 'react';
import { Send, Bot, FileText, ChevronRight } from 'lucide-react';
import ChatMessage from '../components/ChatMessage';
import { Link } from 'react-router-dom';

export default function AIAssistant() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      isAi: true,
      text: "Hello! I am the PatentIQ AI Assistant. You can ask me questions about Indian patents, technology trends, or ask me to summarize specific patent documents.",
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { id: Date.now(), isAi: false, text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Mock AI Response
    setTimeout(() => {
      let aiResponseText = "";
      let aiResponseComponent = null;

      if (userMsg.text.toLowerCase().includes("crop disease") || userMsg.text.toLowerCase().includes("agriculture")) {
        aiResponseComponent = (
          <div>
            <p className="mb-4">
              I found several relevant patent records related to AI-based crop disease detection. The most relevant results involve computer vision, machine learning, image-based crop monitoring, and disease classification.
            </p>
            <p className="font-semibold mb-2">Relevant Patents:</p>
            <div className="space-y-2">
              <Link to="/patent/P001" className="flex items-center p-3 bg-indigo-50 border border-indigo-100 rounded-lg hover:bg-indigo-100 transition-colors">
                <FileText className="w-4 h-4 text-indigo-600 mr-2 flex-shrink-0" />
                <span className="text-indigo-900 font-medium text-sm line-clamp-1">AI-Based Crop Disease Detection System</span>
                <ChevronRight className="w-4 h-4 text-indigo-400 ml-auto" />
              </Link>
              <Link to="/patent/P003" className="flex items-center p-3 bg-indigo-50 border border-indigo-100 rounded-lg hover:bg-indigo-100 transition-colors">
                <FileText className="w-4 h-4 text-indigo-600 mr-2 flex-shrink-0" />
                <span className="text-indigo-900 font-medium text-sm line-clamp-1">Intelligent Agricultural Monitoring Platform</span>
                <ChevronRight className="w-4 h-4 text-indigo-400 ml-auto" />
              </Link>
              <Link to="/patent/P002" className="flex items-center p-3 bg-indigo-50 border border-indigo-100 rounded-lg hover:bg-indigo-100 transition-colors">
                <FileText className="w-4 h-4 text-indigo-600 mr-2 flex-shrink-0" />
                <span className="text-indigo-900 font-medium text-sm line-clamp-1">Machine Learning Based Smart Irrigation</span>
                <ChevronRight className="w-4 h-4 text-indigo-400 ml-auto" />
              </Link>
            </div>
          </div>
        );
      } else {
        aiResponseText = "Based on my analysis of the Indian Patent Database, this area shows significant growth. However, since I am currently a prototype, I can only provide detailed mock answers for queries related to 'crop disease' or 'agriculture'.";
      }

      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        isAi: true, 
        text: aiResponseComponent || aiResponseText 
      }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)] bg-slate-50">
      
      {/* Header */}
      <div className="bg-white border-b border-slate-200 py-6 px-4 sm:px-6 lg:px-8 text-center sticky top-16 z-30 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center justify-center gap-2">
          <Bot className="w-7 h-7 text-indigo-600" />
          Patent AI Assistant
        </h1>
        <p className="text-slate-500 mt-2">Ask questions about Indian patents using natural language.</p>
      </div>

      {/* Chat Area */}
      <div className="flex-1 w-full max-w-4xl mx-auto px-4 py-8 overflow-y-auto">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg.text} isAi={msg.isAi} />
        ))}
        
        {isTyping && (
          <div className="flex w-full justify-start mb-6">
            <div className="flex max-w-[80%] flex-row">
              <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 mr-3">
                <Bot className="w-5 h-5" />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-5 py-4 shadow-sm flex space-x-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-slate-200 p-4 sticky bottom-0">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSend} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask another patent-related question..."
              className="w-full bg-slate-50 border border-slate-300 rounded-full py-4 pl-6 pr-16 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all shadow-inner"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={!input.trim() || isTyping}
              className="absolute right-2 p-2.5 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-3 text-xs text-slate-400">
            AI-generated answers may be inaccurate. This is a prototype interface.
          </div>
        </div>
      </div>
    </div>
  );
}

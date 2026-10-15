import { useState, useEffect, useRef } from 'react';
import { Bot, Send, Sparkles, FileText, HelpCircle, Layers, ArrowRight, User, CheckCircle2, ExternalLink, RotateCcw } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';

const DEFAULT_WELCOME_MESSAGE = {
  id: 'welcome',
  sender: 'ai',
  text: 'Hello! I am your PatentGraph AI Assistant. I can help you query granted Indian patents from 2016-2018, summarize patent specifications, explore technical domains, and retrieve official InPASS gazette evidence. How can I assist your patent research today?'
};

const STORAGE_KEY = 'patentgraph_ai_chat_history';

export default function AIAssistant({ isDarkTheme }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialPrompt = searchParams.get('q');
  const hasTriggeredInitial = useRef(false);
  const messagesEndRef = useRef(null);

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Failed to parse chat history from localStorage', e);
    }
    return [DEFAULT_WELCOME_MESSAGE];
  });
  const [inputQuery, setInputQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  // Sync messages to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save chat history to localStorage', e);
    }
  }, [messages]);

  // Smooth auto-scroll on new messages or thinking state
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleClearChat = () => {
    const freshWelcome = [{ ...DEFAULT_WELCOME_MESSAGE, id: Date.now() }];
    setMessages(freshWelcome);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Failed to remove chat history from localStorage', e);
    }
  };

  const quickPrompts = [
    "Patents related to lithium ion battery anodes",
    "Surgical cutting and fastening devices",
    "Pharmaceutical compositions for melt containers",
    "Wind turbine electric power generation"
  ];

  const handleSend = async (textToSend) => {
    if (isThinking) return;
    const query = (textToSend || inputQuery).trim();
    if (!query) return;

    // Add user message
    const userMsg = { id: Date.now(), sender: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsThinking(true);

    // Extract recent history for multi-turn RAG context
    const historyForBackend = messages
      .filter(m => m.id !== 'welcome' && (m.sender === 'user' || m.sender === 'ai'))
      .slice(-6)
      .map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

    try {
      const ragRes = await api.askQuestion(query, historyForBackend);
      if (ragRes && ragRes.answer) {
        const aiMsg = {
          id: Date.now() + 1,
          sender: 'ai',
          text: ragRes.answer,
          citations: ragRes.citations || [],
          verification: ragRes.verification,
          provider: ragRes.llm_provider
        };
        setMessages(prev => [...prev, aiMsg]);
        setIsThinking(false);
        return;
      }
    } catch (err) {
      console.warn('RAG backend error:', err);
    }

    // Honest fallback when backend service is unreachable
    setMessages(prev => [
      ...prev,
      {
        id: Date.now() + 1,
        sender: 'ai',
        text: 'The PatentGraph backend RAG service is currently unavailable or returned no grounded evidence for this query. Please ensure the FastAPI backend is running locally on port 8000.'
      }
    ]);
    setIsThinking(false);
  };

  useEffect(() => {
    if (initialPrompt && !hasTriggeredInitial.current) {
      hasTriggeredInitial.current = true;
      handleSend(initialPrompt);
    }
  }, [initialPrompt]);

  return (
    <div className={`min-h-[calc(100vh-4rem)] p-4 sm:p-6 lg:p-10 flex flex-col justify-between ${
      isDarkTheme ? 'bg-[#120c24] text-white' : 'bg-[#f3eefc] text-[#2d1f56]'
    }`}>
      <div className="max-w-5xl mx-auto w-full flex-1 flex flex-col space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#e9e1fa]/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-[#6b46c1] text-white shadow-md">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold flex items-center gap-2">
                AI Patent Assistant
                <span className="text-xs px-2 py-0.5 rounded-full bg-[#6b46c1]/20 text-[#6b46c1] border border-[#6b46c1]/30 font-semibold">
                  v3.6 Active
                </span>
              </h1>
              <p className={`text-xs ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
                Intelligent assistant to summarize claims, explain terms, compare patents, and refine searches.
              </p>
            </div>
          </div>

          <button
            onClick={handleClearChat}
            title="Clear chat conversation"
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${
              isDarkTheme
                ? 'bg-[#1e153a] hover:bg-[#2b1f4c] text-purple-300 border-[#382969]'
                : 'bg-white hover:bg-slate-100 text-[#6b46c1] border-[#e2d5f8] shadow-xs'
            }`}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear Chat</span>
          </button>
        </div>

        {/* Chat Messages Container */}
        <div className={`flex-1 min-h-[420px] max-h-[550px] overflow-y-auto rounded-3xl p-6 border shadow-inner space-y-4 ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-3xl ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                msg.sender === 'user' ? 'bg-[#6b46c1] text-white' : 'bg-[#f3eefc] text-[#6b46c1] border border-[#e2d5f8]'
              }`}>
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap ${
                msg.sender === 'user'
                  ? 'bg-[#6b46c1] text-white font-medium rounded-tr-none'
                  : isDarkTheme
                    ? 'bg-[#231845] border border-[#382969] text-slate-100 rounded-tl-none'
                    : 'bg-[#f4effc] border border-[#e2d5f8] text-[#2d1f56] rounded-tl-none'
              }`}>
                {msg.text}

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-purple-300/30">
                    <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 mb-2">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Retrieved & Verified Patent Citations:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((c, i) => (
                        <button
                          key={i}
                          onClick={() => navigate(`/patent/${encodeURIComponent(c.patent_id)}`)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono font-medium bg-[#6b46c1]/10 hover:bg-[#6b46c1]/20 text-[#6b46c1] dark:text-purple-300 border border-[#6b46c1]/30 transition-all cursor-pointer"
                        >
                          <FileText className="w-3 h-3" />
                          <span>{c.patent_id}</span>
                          <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {msg.provider && (
                  <div className="mt-2.5 pt-2 border-t border-purple-300/20 text-[10px] text-purple-400 font-mono opacity-80 flex items-center gap-1">
                    <span>Engine:</span>
                    <span className="font-semibold">{msg.provider}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isThinking && (
            <div className="flex gap-3 items-center text-xs text-[#6b46c1] font-semibold animate-pulse">
              <Sparkles className="w-4 h-4" />
              Analyzing patent repository embeddings...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap gap-2">
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className={`text-xs font-medium px-3 py-2 rounded-xl border transition-all hover:scale-102 ${
                isDarkTheme
                  ? 'bg-[#1f163b] hover:bg-[#2e2057] text-purple-200 border-[#382969]'
                  : 'bg-white hover:bg-slate-50 text-[#553c9a] border-[#e2d5f8] shadow-xs'
              }`}
            >
              💡 {prompt}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="relative flex items-center"
        >
          <input
            type="text"
            placeholder={isThinking ? "Analyzing patent evidence, please wait..." : "Ask AI anything about patents, technical terms, or claim comparisons..."}
            value={inputQuery}
            disabled={isThinking}
            onChange={(e) => setInputQuery(e.target.value)}
            className={`w-full rounded-2xl pl-4 pr-14 py-3.5 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#6b46c1] border shadow-md disabled:opacity-60 ${
              isDarkTheme
                ? 'bg-[#18112e] border-[#2b1f4c] text-white placeholder-slate-400'
                : 'bg-white border-[#e9e1fa] text-[#2d1f56] placeholder-slate-400'
            }`}
          />
          <button
            type="submit"
            disabled={isThinking || !inputQuery.trim()}
            className="absolute right-2 p-2.5 rounded-xl bg-[#6b46c1] hover:bg-[#553c9a] disabled:opacity-50 disabled:cursor-not-allowed text-white transition-all cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

      </div>
    </div>
  );
}

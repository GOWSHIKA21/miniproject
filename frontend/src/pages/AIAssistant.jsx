import { useState } from 'react';
import { Bot, Send, Sparkles, FileText, HelpCircle, Layers, ArrowRight, User } from 'lucide-react';
import { patents } from '../data/patents';

export default function AIAssistant({ isDarkTheme }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      text: 'Hello! I am your PatentGraph AI Assistant. I can help you summarize patent claims, explain complex technical terms, compare patents, or refine your natural language search queries. How can I assist your IP research today?'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  const quickPrompts = [
    "Summarize AI Drone Crop Disease Detection patent",
    "Explain technical term 'Solid-State Battery Anode'",
    "Compare Patent IN202411009401 with US11849201B2",
    "Help refine my search query for Quantum Encryption"
  ];

  const handleSend = (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    // Add user message
    const userMsg = { id: Date.now(), sender: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsThinking(true);

    // Simulate AI intelligent response
    setTimeout(() => {
      let aiResponseText = '';
      const lower = query.toLowerCase();

      if (lower.includes('crop') || lower.includes('drone') || lower.includes('in202411009401')) {
        aiResponseText = "### Patent Summary: IN202411009401 (AI Crop Disease Detection)\n\n**Core Invention:** Autonomous drone multi-spectral imaging integrated with deep neural networks for early fungal detection.\n\n**Key Novelty:** Real-time edge classification before crop stress is visible to human operators.\n\n**IPC Code:** A01G 7/00 (Agriculture & Crop Health).";
      } else if (lower.includes('battery') || lower.includes('solid-state')) {
        aiResponseText = "### Technical Concept: Solid-State Anode Architecture\n\nSolid-state batteries replace traditional liquid electrolytes with solid ceramics or polymers. This matrix doubles volumetric energy density while mitigating thermal runaway risks during fast-charging cycles.";
      } else if (lower.includes('compare')) {
        aiResponseText = "### Comparative Analysis:\n\n- **IN202411009401 (India):** Focuses on aerial image telemetry & computer vision models for plant pathology.\n- **US11849201B2 (United States):** Focuses on underground IoT soil sensors & automated irrigation valve actuation.\n\n*Synergy:* Both systems target agricultural resource optimization using machine learning.";
      } else {
        aiResponseText = `Based on your request "${query}", I analyzed the active PatentGraph index. This topic relates primarily to IPC classifications G06F and H04L. Would you like me to generate a prior-art claim matrix or list top assignees in this domain?`;
      }

      setMessages(prev => [...prev, { id: Date.now() + 1, sender: 'ai', text: aiResponseText }]);
      setIsThinking(false);
    }, 650);
  };

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
              </div>
            </div>
          ))}

          {isThinking && (
            <div className="flex gap-3 items-center text-xs text-[#6b46c1] font-semibold animate-pulse">
              <Sparkles className="w-4 h-4" />
              Analyzing patent repository embeddings...
            </div>
          )}
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
            placeholder="Ask AI anything about patents, technical terms, or claim comparisons..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            className={`w-full rounded-2xl pl-4 pr-14 py-3.5 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-[#6b46c1] border shadow-md ${
              isDarkTheme
                ? 'bg-[#18112e] border-[#2b1f4c] text-white placeholder-slate-400'
                : 'bg-white border-[#e9e1fa] text-[#2d1f56] placeholder-slate-400'
            }`}
          />
          <button
            type="submit"
            className="absolute right-2 p-2.5 rounded-xl bg-[#6b46c1] hover:bg-[#553c9a] text-white transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

      </div>
    </div>
  );
}

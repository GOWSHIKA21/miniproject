import { useState, useEffect, useRef } from 'react';
import { Bot, Send, Sparkles, FileText, RotateCcw, User, CheckCircle2, ExternalLink, AlertCircle, Info } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';

// ─── Constants ───────────────────────────────────────────────────────────────

const DEFAULT_WELCOME_MESSAGE = {
  id: 'welcome',
  sender: 'ai',
  text: 'Hello! I am your **PatentGraph AI Assistant**.\n\nI can help you:\n- **Query** granted Indian patents from 2016–2023\n- **Summarize** patent specifications and claims\n- **Explore** technical domains and inventor networks\n- **Retrieve** official InPASS gazette evidence\n\nEvery answer I provide is grounded in retrieved patent records — I will clearly tell you when evidence is insufficient rather than guess. How can I assist your patent research today?'
};

const STORAGE_KEY = 'patentgraph_ai_chat_history';

const QUICK_PROMPTS = [
  "Patents related to lithium ion battery anodes",
  "Surgical cutting and fastening devices",
  "Pharmaceutical compositions for melt containers",
  "Wind turbine electric power generation"
];

// ─── Minimal Markdown Renderer ───────────────────────────────────────────────
// Renders a safe subset of markdown without any external dependency.
// Handles: **bold**, *italic*, headings (#, ##, ###), bullet lists (-, *),
// numbered lists, horizontal rules (---), and code spans (`code`).

function renderMarkdown(text) {
  if (!text) return null;

  const lines = text.split('\n');
  const elements = [];
  let i = 0;
  let listBuffer = [];
  let listType = null;

  const flushList = () => {
    if (listBuffer.length === 0) return;
    const items = listBuffer.map((item, idx) => (
      <li key={idx} className="ml-1">{inlineMarkdown(item)}</li>
    ));
    if (listType === 'ol') {
      elements.push(<ol key={`ol-${i}`} className="list-decimal list-outside ml-4 space-y-0.5 my-1">{items}</ol>);
    } else {
      elements.push(<ul key={`ul-${i}`} className="list-disc list-outside ml-4 space-y-0.5 my-1">{items}</ul>);
    }
    listBuffer = [];
    listType = null;
  };

  while (i < lines.length) {
    const line = lines[i];

    // Heading 1
    if (/^# /.test(line)) {
      flushList();
      elements.push(<h2 key={i} className="text-base font-extrabold mt-3 mb-1">{inlineMarkdown(line.slice(2))}</h2>);
    }
    // Heading 2
    else if (/^## /.test(line)) {
      flushList();
      elements.push(<h3 key={i} className="text-sm font-bold mt-2 mb-1">{inlineMarkdown(line.slice(3))}</h3>);
    }
    // Heading 3
    else if (/^### /.test(line)) {
      flushList();
      elements.push(<h4 key={i} className="text-xs font-bold mt-2 mb-0.5">{inlineMarkdown(line.slice(4))}</h4>);
    }
    // Horizontal rule
    else if (/^---+$/.test(line.trim())) {
      flushList();
      elements.push(<hr key={i} className="border-purple-300/20 my-2" />);
    }
    // Unordered list item
    else if (/^[\-\*] /.test(line)) {
      if (listType !== 'ul') { flushList(); listType = 'ul'; }
      listBuffer.push(line.slice(2));
    }
    // Ordered list item
    else if (/^\d+\. /.test(line)) {
      if (listType !== 'ol') { flushList(); listType = 'ol'; }
      listBuffer.push(line.replace(/^\d+\. /, ''));
    }
    // Empty line
    else if (line.trim() === '') {
      flushList();
      elements.push(<br key={`br-${i}`} />);
    }
    // Normal paragraph
    else {
      flushList();
      elements.push(<p key={i} className="my-0.5">{inlineMarkdown(line)}</p>);
    }
    i++;
  }
  flushList();
  return elements;
}

function inlineMarkdown(text) {
  // Process inline: **bold**, *italic*, `code`
  const parts = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let match;
  let keyIdx = 0;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(text.slice(last, match.index));
    }
    const token = match[0];
    if (token.startsWith('`')) {
      parts.push(<code key={keyIdx++} className="font-mono text-[10px] bg-purple-500/10 px-1 py-0.5 rounded">{token.slice(1, -1)}</code>);
    } else if (token.startsWith('**')) {
      parts.push(<strong key={keyIdx++} className="font-bold">{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('*')) {
      parts.push(<em key={keyIdx++} className="italic">{token.slice(1, -1)}</em>);
    }
    last = match.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length === 1 && typeof parts[0] === 'string' ? parts[0] : parts;
}

// ─── Message Bubble ──────────────────────────────────────────────────────────

function MessageBubble({ msg, isDarkTheme, onPatentClick }) {
  const isUser = msg.sender === 'user';

  const verifiedCitations = (msg.citations || []).filter(c => c.verified !== false);
  const unverifiedCitations = (msg.citations || []).filter(c => c.verified === false);

  return (
    <div className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold ${
        isUser ? 'bg-[#6b46c1] text-white' : 'bg-[#f3eefc] text-[#6b46c1] border border-[#e2d5f8]'
      }`}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble */}
      <div className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed flex-1 min-w-0 ${
        isUser
          ? 'bg-[#6b46c1] text-white font-medium rounded-tr-none'
          : isDarkTheme
            ? 'bg-[#231845] border border-[#382969] text-slate-100 rounded-tl-none'
            : 'bg-[#f4effc] border border-[#e2d5f8] text-[#2d1f56] rounded-tl-none'
      }`}>

        {/* Message content */}
        {isUser ? (
          <span className="whitespace-pre-wrap">{msg.text}</span>
        ) : (
          <div className="space-y-1">
            {renderMarkdown(msg.text)}
          </div>
        )}

        {/* Verified citations that the LLM actually cited */}
        {verifiedCitations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-purple-300/30">
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 mb-2">
              <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Retrieved &amp; Cited Patent Evidence ({verifiedCitations.length}):</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {verifiedCitations.map((c, i) => (
                <button
                  key={i}
                  onClick={() => onPatentClick(c.patent_id)}
                  title={c.title || c.patent_id}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-mono font-medium bg-[#6b46c1]/10 hover:bg-[#6b46c1]/25 text-[#6b46c1] dark:text-purple-300 border border-[#6b46c1]/30 transition-all cursor-pointer"
                >
                  <FileText className="w-3 h-3 flex-shrink-0" />
                  <span>{c.patent_id}</span>
                  {c.field_of_invention && (
                    <span className="opacity-60 text-[10px]">· {c.field_of_invention}</span>
                  )}
                  <ExternalLink className="w-2.5 h-2.5 opacity-50 flex-shrink-0" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Retrieved but not explicitly cited — shown as supporting context */}
        {unverifiedCitations.length > 0 && (
          <div className="mt-3 pt-2 border-t border-purple-300/20">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-400 mb-1.5">
              <Info className="w-3 h-3 flex-shrink-0" />
              <span>Additional retrieved records (supporting context, not directly cited):</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {unverifiedCitations.map((c, i) => (
                <button
                  key={i}
                  onClick={() => onPatentClick(c.patent_id)}
                  title={c.title || c.patent_id}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-mono text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-[#6b46c1]/40 transition-all cursor-pointer"
                >
                  <FileText className="w-2.5 h-2.5 flex-shrink-0" />
                  <span>{c.patent_id}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* LLM engine badge */}
        {msg.provider && (
          <div className="mt-2.5 pt-2 border-t border-purple-300/20 text-[10px] text-purple-400 font-mono opacity-70 flex items-center gap-1">
            <span>Engine:</span>
            <span className="font-semibold">{msg.provider}</span>
            {msg.verification && (
              <span className="ml-2 opacity-70">
                | Grounding: {Math.round(msg.verification.grounding_ratio * 100)}%
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

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
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Failed to parse chat history from localStorage', e);
    }
    return [DEFAULT_WELCOME_MESSAGE];
  });

  const [inputQuery, setInputQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  // Persist messages to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (e) {
      console.warn('Failed to save chat history to localStorage', e);
    }
  }, [messages]);

  // Smooth auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleClearChat = () => {
    const freshWelcome = [{ ...DEFAULT_WELCOME_MESSAGE, id: Date.now() }];
    setMessages(freshWelcome);
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* noop */ }
  };

  const handlePatentClick = (patentId) => {
    if (!patentId) return;
    navigate(`/patent/${encodeURIComponent(patentId)}`);
  };

  const handleSend = async (textToSend) => {
    if (isThinking) return;
    const query = (textToSend || inputQuery).trim();
    if (!query) return;

    const userMsg = { id: Date.now(), sender: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsThinking(true);

    // Build recent history for multi-turn context (fresh evidence is always retrieved)
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

    // Honest error message — never substitutes a generic LLM answer
    setMessages(prev => [
      ...prev,
      {
        id: Date.now() + 1,
        sender: 'ai',
        text: '⚠️ **Backend Unavailable**\n\nThe PatentGraph RAG service is currently unreachable or returned no grounded evidence for this query.\n\nPlease ensure the FastAPI backend is running:\n```\nuvicorn backend.app.main:app --reload --port 8000\n```'
      }
    ]);
    setIsThinking(false);
  };

  // Fire initial prompt from URL params (e.g. from PatentDetails "Ask AI" button)
  useEffect(() => {
    if (initialPrompt && !hasTriggeredInitial.current) {
      hasTriggeredInitial.current = true;
      handleSend(initialPrompt);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
                  RAG-Grounded
                </span>
              </h1>
              <p className={`text-xs ${isDarkTheme ? 'text-slate-400' : 'text-[#5a478c]'}`}>
                Every answer is grounded in retrieved InPASS patent evidence. Unsupported claims are explicitly flagged.
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

        {/* Evidence notice */}
        <div className={`flex items-start gap-2 px-4 py-3 rounded-2xl border text-xs ${
          isDarkTheme ? 'bg-[#1a1235] border-[#2b1f4c] text-slate-400' : 'bg-amber-50 border-amber-200 text-amber-700'
        }`}>
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <p>
            <strong>Evidence-grounded responses only.</strong> Answers are limited to retrieved InPASS patent records.
            The AI will explicitly state when evidence is insufficient — it will never fabricate patent IDs, claims, or specifications.
          </p>
        </div>

        {/* Chat Messages Container */}
        <div className={`flex-1 min-h-[420px] max-h-[580px] overflow-y-auto rounded-3xl p-6 border shadow-inner space-y-4 ${
          isDarkTheme ? 'bg-[#18112e] border-[#2b1f4c]' : 'bg-white border-[#e9e1fa]'
        }`}>
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              isDarkTheme={isDarkTheme}
              onPatentClick={handlePatentClick}
            />
          ))}

          {isThinking && (
            <div className="flex gap-3 items-center">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 bg-[#f3eefc] text-[#6b46c1] border border-[#e2d5f8]">
                <Bot className="w-4 h-4" />
              </div>
              <div className={`px-4 py-3 rounded-2xl rounded-tl-none border text-xs ${
                isDarkTheme ? 'bg-[#231845] border-[#382969]' : 'bg-[#f4effc] border-[#e2d5f8]'
              }`}>
                <span className="flex items-center gap-1.5 text-[#6b46c1] font-semibold animate-pulse">
                  <Sparkles className="w-3.5 h-3.5" />
                  Searching patent records and generating grounded evidence...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              disabled={isThinking}
              className={`text-xs font-medium px-3 py-2 rounded-xl border transition-all hover:scale-102 disabled:opacity-50 disabled:cursor-not-allowed ${
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
            placeholder={isThinking ? "Retrieving patent evidence, please wait..." : "Ask about patents, technical terms, inventors, or claim comparisons..."}
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

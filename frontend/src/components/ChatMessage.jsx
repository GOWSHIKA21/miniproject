import { User, BrainCircuit } from 'lucide-react';

export default function ChatMessage({ message, isAi }) {
  return (
    <div className={`flex w-full ${isAi ? 'justify-start' : 'justify-end'} mb-6`}>
      <div className={`flex max-w-[80%] ${isAi ? 'flex-row' : 'flex-row-reverse'}`}>
        <div className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full ${
          isAi ? 'bg-indigo-100 text-indigo-600 mr-3' : 'bg-slate-100 text-slate-600 ml-3'
        }`}>
          {isAi ? <BrainCircuit className="w-5 h-5" /> : <User className="w-5 h-5" />}
        </div>
        
        <div className={`rounded-2xl px-5 py-3.5 shadow-sm ${
          isAi 
            ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-none' 
            : 'bg-indigo-600 text-white rounded-tr-none'
        }`}>
          <div className="prose prose-sm max-w-none">
            {typeof message === 'string' ? (
              <p className="whitespace-pre-wrap">{message}</p>
            ) : (
              message
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

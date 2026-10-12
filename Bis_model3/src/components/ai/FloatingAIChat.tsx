import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Bot, X, MessageSquare, Sparkles } from 'lucide-react';
import { AIChat } from './AIChat';

export const FloatingAIChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Hide the floating widget if user is already on the dedicated full-page AI Assistant route
  if (location.pathname === '/ai-assistant') {
    return null;
  }

  return (
    <div className="fixed bottom-5 right-5 z-40">
      {isOpen ? (
        <div className="w-[360px] sm:w-[420px] h-[550px] max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-slate-200/90 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200">
          <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold leading-none">ISense AI Assistant</h4>
                <span className="text-[10px] text-slate-400">RAG Regulatory Guidance</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              title="Close assistant"
              aria-label="Close assistant"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 min-h-0">
            <AIChat className="h-full border-0 rounded-none shadow-none" />
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="group flex items-center gap-2.5 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5 cursor-pointer font-medium text-xs sm:text-sm border border-blue-500/50"
          aria-label="Open ISense AI Assistant"
        >
          <div className="relative flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <span>Ask ISense AI</span>
          <Sparkles className="w-3.5 h-3.5 text-amber-300 opacity-90 group-hover:rotate-12 transition-transform" />
        </button>
      )}
    </div>
  );
};

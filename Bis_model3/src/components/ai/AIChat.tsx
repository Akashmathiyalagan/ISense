import React, { useRef, useEffect } from 'react';
import { Bot, Sparkles, RefreshCw, MessageSquare } from 'lucide-react';
import { useAIChat } from '../../hooks/useAIChat';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';

interface AIChatProps {
  applicationId?: string;
  className?: string;
  onAttachDocument?: () => void;
}

export const AIChat: React.FC<AIChatProps> = ({
  applicationId,
  className = '',
  onAttachDocument,
}) => {
  const { messages, isSending, sendMessage, clearChat } = useAIChat(applicationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedQuestions = [
    'What is my next step?',
    'Which documents are pending?',
    'Show my application status',
    'Explain this requirement',
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  return (
    <div className={`flex flex-col h-full bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs ${className}`}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-900 text-base">ISense AI Assistant</h3>
              <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                RAG Grounded
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Ask questions about your BIS application and available BIS information.
            </p>
          </div>
        </div>

        <button
          onClick={clearChat}
          title="Reset conversation"
          className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors text-xs flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Reset</span>
        </button>
      </div>

      {/* Suggested prompts strip */}
      <div className="px-5 py-2.5 bg-slate-50 border-b border-slate-100 flex items-center gap-2 overflow-x-auto text-xs">
        <span className="text-slate-400 shrink-0 flex items-center gap-1 font-medium text-[11px]">
          <Sparkles className="w-3 h-3 text-amber-500" /> Suggestions:
        </span>
        {suggestedQuestions.map((q) => (
          <button
            key={q}
            onClick={() => sendMessage(q)}
            disabled={isSending}
            className="shrink-0 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-700 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-colors text-[11px] font-medium"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages scroll area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-2 bg-slate-50/40">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isSending && (
          <div className="flex gap-3 items-center text-xs text-slate-500 py-2">
            <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center">
              <Bot className="w-4 h-4 animate-pulse" />
            </div>
            <span className="animate-pulse">Retrieving grounded clauses from BIS knowledge base...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <ChatInput
          onSendMessage={sendMessage}
          onAttachClick={onAttachDocument}
          isLoading={isSending}
          placeholder="Ask ISense anything about your BIS application..."
        />
        <p className="text-[10px] text-slate-400 text-center mt-2">
          Responses cite relevant Indian Standards and regulatory documents from configured knowledge repositories.
        </p>
      </div>
    </div>
  );
};

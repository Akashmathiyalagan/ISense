import React from 'react';
import { Bot, User as UserIcon } from 'lucide-react';
import { ChatMessageItem } from '../../types/ai';
import { SourceReference } from './SourceReference';

interface ChatMessageProps {
  message: ChatMessageItem;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`flex gap-3.5 ${isAssistant ? 'justify-start' : 'justify-end'} mb-4`}>
      {isAssistant && (
        <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 text-sm shadow-xs ${
          isAssistant
            ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-xs'
            : 'bg-blue-600 text-white rounded-tr-xs'
        }`}
      >
        <div className="whitespace-pre-line leading-relaxed">{message.content}</div>

        {isAssistant && message.confidence !== undefined && message.confidence > 0 && (
          <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span className="text-slate-500">Grounding Confidence:</span>
            <span className={`px-1.5 py-0.2 rounded font-mono font-semibold text-[10px] ${
              message.confidence >= 0.7 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
              message.confidence >= 0.4 ? 'bg-amber-50 text-amber-700 border border-amber-200' :
              'bg-rose-50 text-rose-700 border border-rose-200'
            }`}>
              {Math.round(message.confidence * 100)}%
            </span>
          </div>
        )}

        {isAssistant && message.sources && message.sources.length > 0 && (
          <SourceReference sources={message.sources} />
        )}

        <div
          className={`text-[10px] mt-1.5 flex justify-end font-medium ${
            isAssistant ? 'text-slate-400' : 'text-blue-200'
          }`}
        >
          {message.timestamp}
        </div>
      </div>

      {!isAssistant && (
        <div className="w-8 h-8 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0 shadow-xs">
          <UserIcon className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};

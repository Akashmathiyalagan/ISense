import React from 'react';
import { Bot, User as UserIcon } from 'lucide-react';
import { ChatMessageItem } from '../../types/ai';
import { SourceReference } from './SourceReference';

interface ChatMessageProps {
  message: ChatMessageItem;
}

const formatInline = (str: string): React.ReactNode => {
  const parts: React.ReactNode[] = [];
  let remaining = str;
  let keyIndex = 0;

  while (remaining.length > 0) {
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
    const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
    const italicMatch = remaining.match(/(?<!\*)\*([^*]+)\*(?!\*)/);

    let earliestMatch: { index: number; length: number; node: React.ReactNode } | null = null;

    if (linkMatch && linkMatch.index !== undefined) {
      earliestMatch = {
        index: linkMatch.index,
        length: linkMatch[0].length,
        node: (
          <a
            key={`lnk-${keyIndex++}`}
            href={linkMatch[2]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline font-medium hover:text-blue-800"
          >
            {linkMatch[1]}
          </a>
        ),
      };
    }

    if (boldMatch && boldMatch.index !== undefined) {
      if (!earliestMatch || boldMatch.index < earliestMatch.index) {
        earliestMatch = {
          index: boldMatch.index,
          length: boldMatch[0].length,
          node: (
            <strong key={`bld-${keyIndex++}`} className="font-semibold text-slate-900">
              {boldMatch[1]}
            </strong>
          ),
        };
      }
    }

    if (italicMatch && italicMatch.index !== undefined) {
      if (!earliestMatch || italicMatch.index < earliestMatch.index) {
        earliestMatch = {
          index: italicMatch.index,
          length: italicMatch[0].length,
          node: (
            <em key={`itc-${keyIndex++}`} className="italic text-slate-600">
              {italicMatch[1]}
            </em>
          ),
        };
      }
    }

    if (earliestMatch) {
      if (earliestMatch.index > 0) {
        parts.push(remaining.substring(0, earliestMatch.index));
      }
      parts.push(earliestMatch.node);
      remaining = remaining.substring(earliestMatch.index + earliestMatch.length);
    } else {
      parts.push(remaining);
      break;
    }
  }

  return parts.length === 1 ? parts[0] : <>{parts}</>;
};

const renderFormattedText = (text: string) => {
  const lines = text.split('\n');
  return lines.map((line, idx) => {
    if (line.startsWith('### ')) {
      return (
        <h4 key={idx} className="font-bold text-slate-900 mt-2 mb-1 text-sm">
          {formatInline(line.replace(/^###\s+/, ''))}
        </h4>
      );
    }
    if (line.startsWith('## ')) {
      return (
        <h3 key={idx} className="font-bold text-slate-900 mt-2.5 mb-1.5 text-base">
          {formatInline(line.replace(/^##\s+/, ''))}
        </h3>
      );
    }
    const bulletMatch = line.match(/^(\s*)([•\-\*]|\d+\.)\s+(.+)$/);
    if (bulletMatch) {
      return (
        <div key={idx} className="flex items-start gap-1.5 my-0.5 pl-1 text-slate-800">
          <span className="font-bold text-blue-600 shrink-0">{bulletMatch[2]}</span>
          <span className="leading-relaxed">{formatInline(bulletMatch[3])}</span>
        </div>
      );
    }
    if (!line.trim()) {
      return <div key={idx} className="h-1.5" />;
    }
    return (
      <p key={idx} className="my-0.5 leading-relaxed">
        {formatInline(line)}
      </p>
    );
  });
};

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
        <div className="leading-relaxed">
          {isAssistant ? renderFormattedText(message.content) : message.content}
        </div>

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

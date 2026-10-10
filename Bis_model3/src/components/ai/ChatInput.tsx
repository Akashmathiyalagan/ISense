import React, { useState, FormEvent, KeyboardEvent } from 'react';
import { Send, Paperclip, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  onAttachClick?: () => void;
  isLoading?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onAttachClick,
  isLoading = false,
  placeholder = 'Ask ISense anything...',
}) => {
  const [text, setText] = useState('');

  const handleSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (text.trim() && !isLoading) {
      onSendMessage(text);
      setText('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
      <div className="relative flex-1 flex items-center">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder={placeholder}
          className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-4 pr-10 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white focus:border-transparent transition-all shadow-xs"
        />
        {onAttachClick && (
          <button
            type="button"
            onClick={onAttachClick}
            title="Attach Document for Context"
            className="absolute right-3 p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50 transition-colors"
          >
            <Paperclip className="w-4 h-4" />
          </button>
        )}
      </div>

      <button
        type="submit"
        disabled={!text.trim() || isLoading}
        className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl flex items-center justify-center gap-2 transition-colors shadow-xs shrink-0 cursor-pointer"
        aria-label="Send Message"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <>
            <span>Send</span>
            <Send className="w-4 h-4" />
          </>
        )}
      </button>
    </form>
  );
};

import React from 'react';
import { PageHeader } from '../components/layout/PageHeader';
import { AIChat } from '../components/ai/AIChat';
import { MessageCircle, Database, ShieldCheck } from 'lucide-react';

export const AIAssistant: React.FC = () => {
  return (
    <div className="space-y-4 h-[calc(100vh-7rem)] flex flex-col">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">ISense AI Assistant</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ask questions about your BIS application and available BIS information.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 text-emerald-800 rounded-full border border-emerald-200 text-xs font-semibold">
            <MessageCircle className="w-3.5 h-3.5 text-emerald-600" />
            <span>Synced with WhatsApp Assistant</span>
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <AIChat className="h-full" />
      </div>
    </div>
  );
};

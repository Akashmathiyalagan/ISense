import React from 'react';
import { BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';
import { SourceReferenceItem } from '../../types/ai';

interface SourceReferenceProps {
  sources: SourceReferenceItem[];
}

export const SourceReference: React.FC<SourceReferenceProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-2.5 border-t border-slate-200/80">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 mb-2">
        <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
        <span>Grounded BIS Regulatory Evidence:</span>
      </div>
      <div className="space-y-2">
        {sources.map((src) => (
          <div
            key={src.id}
            className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/90 text-xs text-slate-700 hover:bg-slate-100/70 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5 font-medium text-slate-900">
                <BookOpen className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                <span>{src.title}</span>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {src.page && (
                  <span className="text-[11px] font-mono bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-600">
                    Page {src.page}
                  </span>
                )}
                {src.sourceUrl && (
                  <a
                    href={src.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-slate-400 hover:text-blue-600 rounded transition-colors"
                    title="View official document reference"
                  >
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
            {src.section && (
              <p className="text-[11px] text-blue-700 font-medium mt-1">{src.section}</p>
            )}
            {src.excerpt && (
              <p className="text-[11px] text-slate-600 mt-1 italic leading-relaxed border-l-2 border-blue-300 pl-2 bg-white/60 py-0.5 rounded-r">
                "{src.excerpt}"
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

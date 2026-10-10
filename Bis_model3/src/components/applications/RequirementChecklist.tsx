import React from 'react';
import { CheckCircle2, Circle, Clock, ArrowRight, ExternalLink } from 'lucide-react';
import { ApplicationRequirement } from '../../types/application';
import { Badge } from '../common/Badge';

interface RequirementChecklistProps {
  requirements: ApplicationRequirement[];
  onActionClick?: (req: ApplicationRequirement) => void;
}

export const RequirementChecklist: React.FC<RequirementChecklistProps> = ({
  requirements,
  onActionClick,
}) => {
  const completedCount = requirements.filter((r) => r.status === 'completed').length;
  const totalCount = requirements.length;

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      {/* Header with progress summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100 mb-4">
        <div>
          <h3 className="font-semibold text-slate-900 text-base">Requirement Checklist</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Compiled from configured BIS knowledge base standard schedule
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
            {completedCount} / {totalCount} Completed
          </span>
        </div>
      </div>

      {/* Checklist items */}
      <div className="divide-y divide-slate-100">
        {requirements.map((req) => {
          const isDone = req.status === 'completed';
          const isPending = req.status === 'pending';

          return (
            <div
              key={req.id}
              className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/60 p-2 rounded-lg transition-colors"
            >
              <div className="flex items-start gap-3 min-w-0">
                <div className="mt-0.5 shrink-0">
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 fill-emerald-50" />
                  ) : (
                    <Circle className="w-5 h-5 text-amber-500 stroke-[1.5]" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-sm font-semibold ${
                        isDone ? 'text-slate-900' : 'text-slate-800'
                      }`}
                    >
                      {req.title}
                    </span>
                    {isDone ? (
                      <Badge variant="success" size="sm">
                        Verified
                      </Badge>
                    ) : (
                      <Badge variant="warning" size="sm">
                        Pending
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{req.description}</p>
                  <div className="mt-1.5 flex items-center gap-2 text-[11px] text-slate-400 flex-wrap">
                    <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600 font-mono text-[10px]">
                      {req.source}
                    </span>
                    {req.sectionRef && <span>• {req.sectionRef}</span>}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="sm:shrink-0 ml-8 sm:ml-0">
                <button
                  onClick={() => onActionClick && onActionClick(req)}
                  className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors ${
                    isDone
                      ? 'border-slate-200 text-slate-600 hover:bg-slate-100 bg-white'
                      : 'border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 font-semibold'
                  }`}
                >
                  <span>{req.actionLabel || (isDone ? 'View Record' : 'Upload Artifact')}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

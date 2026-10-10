import React from 'react';
import { Check, Clock, CircleDot, AlertCircle } from 'lucide-react';

interface TimelineStep {
  number: number;
  title: string;
  subtitle?: string;
  status: 'completed' | 'current' | 'upcoming';
  detail?: string;
}

interface ApplicationTimelineProps {
  currentStageIndex?: number;
  totalDocuments?: number;
  completedDocuments?: number;
}

export const ApplicationTimeline: React.FC<ApplicationTimelineProps> = ({
  currentStageIndex = 4, // 0-indexed: step 5 (Documents) is active
  totalDocuments = 9,
  completedDocuments = 7,
}) => {
  const steps: TimelineStep[] = [
    {
      number: 1,
      title: 'Application Created',
      subtitle: 'System ID generated & synced',
      status: currentStageIndex > 0 ? 'completed' : currentStageIndex === 0 ? 'current' : 'upcoming',
      detail: 'Registered via Web/WhatsApp interface',
    },
    {
      number: 2,
      title: 'Product Information',
      subtitle: 'Parameters & categorization',
      status: currentStageIndex > 1 ? 'completed' : currentStageIndex === 1 ? 'current' : 'upcoming',
      detail: 'Product specs, wattage & ratings verified',
    },
    {
      number: 3,
      title: 'BIS Information Reviewed',
      subtitle: 'Standard mapped from KB',
      status: currentStageIndex > 2 ? 'completed' : currentStageIndex === 2 ? 'current' : 'upcoming',
      detail: 'Matched against configured BIS knowledge base',
    },
    {
      number: 4,
      title: 'Requirements Identified',
      subtitle: 'Mandatory checklist populated',
      status: currentStageIndex > 3 ? 'completed' : currentStageIndex === 3 ? 'current' : 'upcoming',
      detail: 'Standard clauses & documentation roadmap loaded',
    },
    {
      number: 5,
      title: `Documents (${completedDocuments}/${totalDocuments})`,
      subtitle: 'Dossier upload & consistency check',
      status: currentStageIndex > 4 ? 'completed' : currentStageIndex === 4 ? 'current' : 'upcoming',
      detail: 'Under review: 2 files pending upload/check',
    },
    {
      number: 6,
      title: 'Application Readiness',
      subtitle: 'Pre-submission validation audit',
      status: currentStageIndex > 5 ? 'completed' : currentStageIndex === 5 ? 'current' : 'upcoming',
      detail: 'Automated completeness report generation',
    },
    {
      number: 7,
      title: 'Official BIS Process',
      subtitle: 'Manak Online submission assistance',
      status: currentStageIndex > 6 ? 'completed' : currentStageIndex === 6 ? 'current' : 'upcoming',
      detail: 'External portal filing and test sample tracking',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="mb-4">
        <h3 className="font-semibold text-slate-900 text-base">Certification Journey Timeline</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Step-by-step progression from initial product identification to official BIS portal readiness
        </p>
      </div>

      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {steps.map((step) => {
          const isCompleted = step.status === 'completed';
          const isCurrent = step.status === 'current';

          return (
            <div key={step.number} className="relative flex items-start group">
              {/* Step indicator node */}
              <div
                className={`absolute -left-6 sm:-left-8 w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  isCompleted
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : isCurrent
                    ? 'bg-blue-600 text-white ring-4 ring-blue-100 shadow-xs'
                    : 'bg-slate-100 text-slate-400 border border-slate-300'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
                ) : (
                  <span>{step.number}</span>
                )}
              </div>

              {/* Step content */}
              <div className="flex-1 ml-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4
                    className={`text-sm font-semibold ${
                      isCurrent
                        ? 'text-blue-700'
                        : isCompleted
                        ? 'text-slate-900'
                        : 'text-slate-400'
                    }`}
                  >
                    {step.title}
                  </h4>
                  {isCurrent && (
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      In Progress
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      Verified
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{step.subtitle}</p>
                {step.detail && (
                  <p className="text-[11px] text-slate-400 mt-1 font-mono bg-slate-50 p-1.5 rounded border border-slate-100 inline-block">
                    {step.detail}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 p-3 bg-blue-50/50 rounded-lg border border-blue-100 text-xs text-slate-600">
        <p className="leading-snug">
          <strong className="text-blue-900 font-semibold">Important Notice:</strong> ISense provides guidance and document readiness checks. Official grant of BIS certification or CRS registration is issued solely by the Bureau of Indian Standards through authorized statutory procedures.
        </p>
      </div>
    </div>
  );
};

import React from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  FileSearch, 
  ArrowRight,
  ShieldCheck 
} from 'lucide-react';
import { ApplicationStatusType } from '../../types/application';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';

interface ApplicationStatusProps {
  status: ApplicationStatusType;
  progress: number;
  currentStage: string;
  totalDocuments: number;
  completedDocuments: number;
  onContinueAction?: () => void;
}

export const ApplicationStatus: React.FC<ApplicationStatusProps> = ({
  status,
  progress,
  currentStage,
  totalDocuments,
  completedDocuments,
  onContinueAction,
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'Completed':
        return {
          badge: <Badge variant="success">Completed</Badge>,
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
          color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
          recommendation: 'All prerequisites assembled. You can now download the complete dossier for official portal filing.',
          buttonText: 'Export Dossier',
        };
      case 'Documents Pending':
        return {
          badge: <Badge variant="warning">Documents Pending</Badge>,
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
          color: 'bg-amber-50 text-amber-700 border-amber-200',
          recommendation: 'Missing premise address proof and quality manual. Upload documents to proceed.',
          buttonText: 'Upload Missing Documents',
        };
      case 'Under Review':
        return {
          badge: <Badge variant="info">Under Review</Badge>,
          icon: <FileSearch className="w-5 h-5 text-sky-600" />,
          color: 'bg-sky-50 text-sky-700 border-sky-200',
          recommendation: 'Document information check in progress against applicable standard clauses.',
          buttonText: 'Check Audit Trail',
        };
      case 'In Progress':
      default:
        return {
          badge: <Badge variant="blue">In Progress</Badge>,
          icon: <Clock className="w-5 h-5 text-blue-600" />,
          color: 'bg-blue-50 text-blue-700 border-blue-200',
          recommendation: 'Complete outstanding laboratory test report verification and sign-off.',
          buttonText: 'Review Next Step',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${config.color}`}>
            {config.icon}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Status</span>
              {config.badge}
            </div>
            <h4 className="text-sm font-semibold text-slate-900 mt-0.5">{currentStage}</h4>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-600">
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200/60">
            <span className="text-slate-400">Documents:</span>{' '}
            <span className="font-semibold text-slate-800">
              {completedDocuments} of {totalDocuments} complete
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <ProgressBar progress={progress} showLabel size="md" />
      </div>

      <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <p className="text-slate-700 leading-relaxed">
            <strong className="font-semibold text-slate-900">Next Action:</strong> {config.recommendation}
          </p>
        </div>
        {onContinueAction && (
          <button
            onClick={onContinueAction}
            className="inline-flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-700 shrink-0 self-start sm:self-auto cursor-pointer"
          >
            <span>{config.buttonText}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};

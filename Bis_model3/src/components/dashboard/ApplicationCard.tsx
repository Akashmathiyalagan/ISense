import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, FileCheck, Clock, Shield } from 'lucide-react';
import { Application } from '../../types/application';
import { Badge } from '../common/Badge';
import { ProgressBar } from '../common/ProgressBar';

interface ApplicationCardProps {
  application: Application;
}

export const ApplicationCard: React.FC<ApplicationCardProps> = ({ application }) => {
  const getStatusBadge = () => {
    switch (application.status) {
      case 'Completed':
        return <Badge variant="success">Completed</Badge>;
      case 'Documents Pending':
        return <Badge variant="warning">Documents Pending</Badge>;
      case 'In Progress':
        return <Badge variant="blue">In Progress</Badge>;
      case 'Under Review':
        return <Badge variant="info">Under Review</Badge>;
      default:
        return <Badge variant="neutral">{application.status}</Badge>;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-blue-300 hover:shadow-sm transition-all flex flex-col justify-between group">
      <div>
        {/* Top: ID & Status */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-xs font-mono font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            {application.id}
          </span>
          {getStatusBadge()}
        </div>

        {/* Product Title & Category */}
        <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors text-base line-clamp-1">
          {application.productName}
        </h3>
        <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
          {application.productCategory} • {application.manufacturer}
        </p>

        {/* Standard reference if available */}
        {application.standardCode && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs text-slate-600 bg-slate-50 p-2 rounded-md border border-slate-100">
            <Shield className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <span className="truncate font-medium">{application.standardCode}</span>
          </div>
        )}

        {/* Progress bar */}
        <div className="mt-4">
          <ProgressBar progress={application.progress} showLabel size="sm" />
        </div>
      </div>

      {/* Footer metadata & Link */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <FileCheck className="w-3.5 h-3.5 text-slate-400" />
          <span>
            {application.completedDocuments}/{application.totalDocuments} Docs
          </span>
        </div>
        <Link
          to={`/applications/${application.id}`}
          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 font-medium group-hover:translate-x-0.5 transition-transform"
        >
          <span>View Application</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};

import React from 'react';
import { 
  FileUp, 
  CheckCircle2, 
  MessageSquare, 
  Layers, 
  Clock, 
  ArrowRight 
} from 'lucide-react';
import { ApplicationActivity } from '../../types/application';
import { Link } from 'react-router-dom';

interface RecentActivityProps {
  activities: ApplicationActivity[];
  limit?: number;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({ activities, limit = 5 }) => {
  const displayList = activities.slice(0, limit);

  const getActivityIcon = (type: ApplicationActivity['type']) => {
    switch (type) {
      case 'document_upload':
        return <FileUp className="w-4 h-4 text-blue-600" />;
      case 'status_change':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case 'ai_query':
        return <MessageSquare className="w-4 h-4 text-purple-600" />;
      case 'system':
      default:
        return <Layers className="w-4 h-4 text-amber-600" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-slate-900 text-base">Recent Activity</h3>
          <p className="text-xs text-slate-500 mt-0.5">Live events across Web &amp; WhatsApp</p>
        </div>
        <Link
          to="/applications"
          className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
        >
          <span>View all</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="space-y-3.5">
        {displayList.map((item) => (
          <div
            key={item.id}
            className="flex items-start gap-3 p-2.5 rounded-lg hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100"
          >
            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 mt-0.5">
              {getActivityIcon(item.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-semibold text-slate-800 truncate">{item.title}</p>
                <span className="text-[11px] text-slate-400 shrink-0 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.timestamp}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5 line-clamp-1">{item.description}</p>
              <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                <span className="font-mono text-slate-500">{item.applicationId}</span>
                <span>•</span>
                <span>{item.actor}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

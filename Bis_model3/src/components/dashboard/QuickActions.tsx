import React from 'react';
import { Link } from 'react-router-dom';
import { PlusCircle, Search, UploadCloud, MessageSquare, ExternalLink } from 'lucide-react';

interface QuickActionsProps {
  onOpenUpload?: () => void;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onOpenUpload }) => {
  const actions = [
    {
      to: '/new-application',
      label: 'New Application',
      description: 'Start a multi-step BIS product wizard',
      icon: PlusCircle,
      iconColor: 'text-blue-600 bg-blue-50 border-blue-100',
    },
    {
      to: '/standards',
      label: 'Search BIS Standards',
      description: 'Query official knowledge base specifications',
      icon: Search,
      iconColor: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    },
    {
      to: '/documents',
      label: 'Upload Document',
      description: 'Submit lab reports & compliance dossiers',
      icon: UploadCloud,
      iconColor: 'text-amber-600 bg-amber-50 border-amber-100',
      onClick: onOpenUpload,
    },
    {
      to: '/ai-assistant',
      label: 'Ask ISense AI',
      description: 'RAG-grounded answers with citations',
      icon: MessageSquare,
      iconColor: 'text-purple-600 bg-purple-50 border-purple-100',
    },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs">
      <h3 className="font-semibold text-slate-900 text-base mb-1">Quick Actions</h3>
      <p className="text-xs text-slate-500 mb-4">Fast shortcuts to common BIS certification workflows</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {actions.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              to={item.to}
              onClick={item.onClick}
              className="flex items-start gap-3 p-3 rounded-lg border border-slate-200/80 hover:border-blue-300 hover:bg-blue-50/30 transition-all group text-left"
            >
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border ${item.iconColor}`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                  {item.label}
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-snug line-clamp-1">
                  {item.description}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

import React, { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center bg-white rounded-xl border border-dashed border-slate-300 ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 mb-3">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-base font-medium text-slate-900 mb-1">{title}</h4>
      <p className="text-sm text-slate-500 max-w-sm mb-5">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

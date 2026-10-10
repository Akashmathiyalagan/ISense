import React, { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  actions,
  className = '',
}) => {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200/80 mb-6 ${className}`}>
      <div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{title}</h1>
          {badge}
        </div>
        {description && (
          <p className="text-sm text-slate-500 mt-1 max-w-3xl leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2.5 shrink-0 flex-wrap">{actions}</div>}
    </div>
  );
};

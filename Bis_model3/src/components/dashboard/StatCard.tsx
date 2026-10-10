import React, { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: ReactNode;
  iconBg?: string;
  subtitle?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  iconBg = 'bg-blue-50 text-blue-600 border-blue-100',
  subtitle,
}) => {
  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${iconBg}`}>
          {icon}
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">{value}</span>
        {change && (
          <span
            className={`text-xs font-medium ${
              changeType === 'positive'
                ? 'text-emerald-600'
                : changeType === 'negative'
                ? 'text-rose-600'
                : 'text-slate-500'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
};

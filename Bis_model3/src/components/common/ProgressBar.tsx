import React from 'react';

interface ProgressBarProps {
  progress: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
  colorScheme?: 'blue' | 'green' | 'amber';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  size = 'md',
  showLabel = false,
  className = '',
  colorScheme = 'blue',
}) => {
  const clampedProgress = Math.min(Math.max(Math.round(progress), 0), 100);

  const heightStyles = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  const colorStyles = {
    blue: 'bg-blue-600',
    green: 'bg-emerald-600',
    amber: 'bg-amber-500',
  };

  const activeColor = colorScheme === 'blue' 
    ? (clampedProgress === 100 ? colorStyles.green : colorStyles.blue)
    : colorStyles[colorScheme];

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between items-center text-xs font-medium text-slate-600 mb-1.5">
          <span>Completion</span>
          <span className="text-slate-900 font-semibold">{clampedProgress}%</span>
        </div>
      )}
      <div className={`w-full bg-slate-200/80 rounded-full overflow-hidden ${heightStyles[size]}`}>
        <div
          className={`${activeColor} h-full rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${clampedProgress}%` }}
          role="progressbar"
          aria-valuenow={clampedProgress}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};

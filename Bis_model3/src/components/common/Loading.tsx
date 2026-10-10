import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  fullPage?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({
  message = 'Loading BIS assistance data...',
  size = 'md',
  fullPage = false,
}) => {
  const sizeStyles = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const content = (
    <div className="flex flex-col items-center justify-center p-8 gap-3">
      <Loader2 className={`${sizeStyles[size]} text-blue-600 animate-spin`} />
      {message && <p className="text-sm font-medium text-slate-600 animate-pulse">{message}</p>}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-xs flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return content;
};

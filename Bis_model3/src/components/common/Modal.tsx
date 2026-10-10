import React, { useEffect, ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth = 'md',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthStyles = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs transition-opacity" 
        onClick={onClose} 
      />

      {/* Modal Dialog */}
      <div className="flex min-h-full items-center justify-center p-4 text-center">
        <div
          className={`w-full ${maxWidthStyles[maxWidth]} transform overflow-hidden rounded-xl bg-white p-6 text-left align-middle shadow-xl transition-all border border-slate-200`}
        >
          {/* Header */}
          <div className="flex items-start justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
              {description && <p className="text-xs text-slate-500 mt-1">{description}</p>}
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 rounded-lg p-1 hover:bg-slate-100 transition-colors focus:outline-none"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="mt-4">{children}</div>

          {/* Optional Footer */}
          {footer && (
            <div className="mt-6 flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error in ISense platform:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-slate-900">
          <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
            <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-7 h-7" />
            </div>

            <h2 className="text-xl font-bold text-slate-900 mb-2">Something went wrong</h2>
            <p className="text-xs text-slate-500 mb-6 leading-relaxed">
              An unexpected interface error occurred. Your live application data and BIS dossiers remain safely persisted on the server.
            </p>

            {this.state.error && (
              <div className="p-3 mb-6 bg-slate-50 rounded-lg border border-slate-200 text-left font-mono text-[11px] text-slate-600 max-h-24 overflow-y-auto">
                {this.state.error.message}
              </div>
            )}

            <div className="flex items-center justify-center gap-3">
              <Button
                variant="outline"
                size="sm"
                icon={<Home className="w-4 h-4" />}
                onClick={() => window.location.href = '/'}
              >
                Go Home
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<RefreshCw className="w-4 h-4" />}
                onClick={this.handleReset}
              >
                Reload Dashboard
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[Samvedna ErrorBoundary] Uncaught error:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[60vh] flex items-center justify-center p-4 font-sans">
          <div className="w-full max-w-lg bg-[#FAF9F3] border-2 border-[#8E2F2B] rounded-3xl p-6 sm:p-8 shadow-2xl text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/30 text-[#8E2F2B] flex items-center justify-center mx-auto">
              <AlertTriangle className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <span className="text-xs font-mono font-bold text-[#8E2F2B] uppercase tracking-widest block">
                APPLICATION RECOVERY LAYER
              </span>
              <h2 className="text-xl font-heading font-black text-[#202622]">
                Unexpected View Error
              </h2>
            </div>

            <p className="text-xs text-[#536A72] leading-relaxed max-w-sm mx-auto">
              A temporary display error occurred in this view. Your emergency status, offline queue, and device telemetry remain safe in local storage.
            </p>

            {this.state.error?.message && (
              <div className="p-3 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/50 text-[11px] font-mono text-[#8E2F2B] text-left break-words max-h-24 overflow-y-auto">
                {this.state.error.message}
              </div>
            )}

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-2">
              <button
                onClick={this.handleReload}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#1b382d] transition-colors flex items-center justify-center space-x-2 cursor-pointer shadow-md"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Reload View</span>
              </button>
              <button
                onClick={this.handleReset}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B] text-[#202622] font-heading font-bold text-xs hover:bg-[#E8E6DC] transition-colors flex items-center justify-center space-x-1.5 cursor-pointer"
              >
                <Home className="w-4 h-4" />
                <span>Return to Home</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

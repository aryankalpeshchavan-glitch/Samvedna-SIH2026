import React, { createContext, useContext, useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';
import { ModalPortal } from '../components/ui/ModalPortal';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

interface ToastContextType {
  toast: (message: Omit<ToastMessage, 'id'>) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  warning: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    ({ type, title, description, duration = 4000 }: Omit<ToastMessage, 'id'>) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      const newToast: ToastMessage = { id, type, title, description, duration };

      setToasts((prev) => [...prev.slice(-4), newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback((title: string, description?: string) => {
    toast({ type: 'success', title, description });
  }, [toast]);

  const error = useCallback((title: string, description?: string) => {
    toast({ type: 'error', title, description, duration: 6000 });
  }, [toast]);

  const warning = useCallback((title: string, description?: string) => {
    toast({ type: 'warning', title, description, duration: 5000 });
  }, [toast]);

  const info = useCallback((title: string, description?: string) => {
    toast({ type: 'info', title, description });
  }, [toast]);

  const getIcon = (type: ToastType) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-[#23483A]" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-[#8E2F2B]" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-[#D88A32]" />;
      case 'info':
      default:
        return <Info className="w-4 h-4 text-[#536A72]" />;
    }
  };

  const getBorderColor = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'border-[#23483A]/40 bg-[#FAF9F3] text-[#202622]';
      case 'error':
        return 'border-[#8E2F2B]/40 bg-[#FAF9F3] text-[#8E2F2B]';
      case 'warning':
        return 'border-[#D88A32]/40 bg-[#FAF9F3] text-[#202622]';
      case 'info':
      default:
        return 'border-[#C7B89B]/50 bg-[#FAF9F3] text-[#202622]';
    }
  };

  return (
    <ToastContext.Provider value={{ toast, success, error, warning, info }}>
      {children}
      <ModalPortal lockScroll={false}>
        <div
          aria-live="polite"
          aria-atomic="true"
          className="fixed top-4 right-4 z-[9999] flex flex-col space-y-2 pointer-events-none max-w-sm w-full px-3 sm:px-0"
        >
          <AnimatePresence>
            {toasts.map((item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: -16, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
                className={`pointer-events-auto p-3.5 rounded-2xl border shadow-xl flex items-start space-x-3 font-sans ${getBorderColor(item.type)}`}
              >
                <div className="shrink-0 mt-0.5">{getIcon(item.type)}</div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-heading font-bold uppercase tracking-wider text-[#202622]">
                    {item.title}
                  </h4>
                  {item.description && (
                    <p className="text-[11px] text-[#536A72] font-mono mt-0.5 leading-snug">
                      {item.description}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => removeToast(item.id)}
                  className="shrink-0 text-[#536A72] hover:text-[#202622] p-1 rounded-md cursor-pointer transition-colors"
                  aria-label="Close notification"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </ModalPortal>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

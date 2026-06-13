import { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export type ToastMessage = {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
};

// Global event emitter for toasts
let addToastFn: (toast: Omit<ToastMessage, 'id'>) => void = () => {};

export const toast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
  addToastFn({ type, message });
};

export const Toaster = () => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    addToastFn = (newToast) => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { ...newToast, id }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    };
  }, []);

  return (
    <div className="fixed bottom-20 md:bottom-4 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 w-[90vw] max-w-sm pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm font-medium animate-in slide-in-from-bottom-2 fade-in pointer-events-auto border",
            t.type === 'success' && "bg-[#1c1c1e] text-[var(--accent-green)] border-[var(--accent-green)]/30",
            t.type === 'error' && "bg-[#1c1c1e] text-[var(--accent-red)] border-[var(--accent-red)]/30",
            t.type === 'info' && "bg-[#1c1c1e] text-white border-white/10"
          )}
        >
          {t.type === 'success' && <CheckCircle size={18} />}
          {t.type === 'error' && <AlertCircle size={18} />}
          <div className="flex-1 text-white">{t.message}</div>
          <button onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))} className="opacity-50 hover:opacity-100 text-white">
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
};

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import ReactDOM from 'react-dom';
import './Toast.css';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContextType {
    showToast: (type: ToastType, message: string, duration?: number) => void;
    showSuccess: (message: string, duration?: number) => void;
    showError: (message: string, duration?: number) => void;
    showInfo: (message: string, duration?: number) => void;
    showWarning: (message: string, duration?: number) => void;
    dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
};

interface ToastProviderProps {
    children: ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = useCallback((type: ToastType, message: string, duration: number = 5000) => {
        const id = Math.random().toString(36).substr(2, 9);
        const newToast: Toast = { id, type, message, duration };

        setToasts(prev => [...prev, newToast]);

        if (duration > 0) {
            setTimeout(() => {
                setToasts(prev => prev.filter(t => t.id !== id));
            }, duration);
        }
    }, []);

    const showSuccess = useCallback((message: string, duration?: number) => {
        showToast('success', message, duration);
    }, [showToast]);

    const showError = useCallback((message: string, duration?: number) => {
        showToast('error', message, duration);
    }, [showToast]);

    const showInfo = useCallback((message: string, duration?: number) => {
        showToast('info', message, duration);
    }, [showToast]);

    const showWarning = useCallback((message: string, duration?: number) => {
        showToast('warning', message, duration);
    }, [showToast]);

    const dismissToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ showToast, showSuccess, showError, showInfo, showWarning, dismissToast }}>
            {children}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
        </ToastContext.Provider>
    );
};

interface ToastContainerProps {
    toasts: Toast[];
    onDismiss: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
    if (toasts.length === 0) return null;

    return ReactDOM.createPortal(
        <div className="toast-container">
            {toasts.map((toast, index) => (
                <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} index={index} />
            ))}
        </div>,
        document.body
    );
};

interface ToastItemProps {
    toast: Toast;
    onDismiss: (id: string) => void;
    index: number;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onDismiss, index }) => {
    const icons: Record<ToastType, string> = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠',
    };

    const icon = icons[toast.type];

    return (
        <div
            className={`toast toast-${toast.type}`}
            style={{
                animationDelay: `${index * 0.1}s`,
                transform: `translateY(${index * -10}px)`,
            }}
            role="alert"
            aria-live="polite"
        >
            <div className="toast-icon">{icon}</div>
            <div className="toast-content">
                <p className="toast-message">{toast.message}</p>
            </div>
            <button
                className="toast-dismiss"
                onClick={() => onDismiss(toast.id)}
                aria-label="Dismiss notification"
            >
                ×
            </button>
            <div className={`toast-progress toast-progress-${toast.type}`} />
        </div>
    );
};

export default ToastProvider;

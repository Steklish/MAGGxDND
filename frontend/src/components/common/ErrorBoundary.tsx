import React, { Component, ErrorInfo, ReactNode } from 'react';
import './ErrorBoundary.css';

// Preload the error background image so it's ready instantly
const preloadErrorBackground = () => {
    const img = new Image();
    img.src = '/arts/backgrounds/bg-error.png';
};
preloadErrorBackground();

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: ErrorInfo) => void;
    onRetry?: () => void;
    errorType?: 'general' | 'no-session' | 'connection';
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

// Error code mappings
const ERROR_CODE_MAP: Record<string, string> = {
    'Network Error': 'CONNECTION_LOST',
    'Failed to fetch': 'SERVER_UNREACHABLE',
    'timeout': 'REQUEST_TIMEOUT',
    '404': 'NOT_FOUND',
    '403': 'ACCESS_DENIED',
    '401': 'UNAUTHORIZED',
    '500': 'SERVER_ERROR',
    '503': 'SERVICE_UNAVAILABLE',
};

const ERROR_DESCRIPTIONS: Record<string, string> = {
    'CONNECTION_LOST': 'The connection to the server was lost. Check your internet connection.',
    'SERVER_UNREACHABLE': 'Unable to reach the server. The server may be down or unreachable.',
    'REQUEST_TIMEOUT': 'The request took too long to complete. Please try again.',
    'NOT_FOUND': 'The requested resource could not be found.',
    'ACCESS_DENIED': 'You do not have permission to access this resource.',
    'UNAUTHORIZED': 'Authentication required. Please log in to continue.',
    'SERVER_ERROR': 'An internal server error occurred. Please try again later.',
    'SERVICE_UNAVAILABLE': 'The service is temporarily unavailable. Please try again later.',
    'DEFAULT': 'An unexpected error occurred. Please try refreshing the page.',
};

const getErrorCode = (error: Error | null): string => {
    if (!error) return 'UNKNOWN_ERROR';

    const errorMessage = error.message;

    for (const [key, code] of Object.entries(ERROR_CODE_MAP)) {
        if (errorMessage.toLowerCase().includes(key.toLowerCase())) {
            return code;
        }
    }

    // Check for HTTP status codes in message
    const statusMatch = errorMessage.match(/\b([0-9]{3})\b/);
    if (statusMatch && ERROR_CODE_MAP[statusMatch[1]]) {
        return ERROR_CODE_MAP[statusMatch[1]];
    }

    return 'UNKNOWN_ERROR';
};

const getErrorDescription = (errorCode: string): string => {
    return ERROR_DESCRIPTIONS[errorCode] || ERROR_DESCRIPTIONS['DEFAULT'];
};

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null,
    };

    private retryTimeoutRef: ReturnType<typeof setTimeout> | null = null;

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error, errorInfo: null };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        this.setState({ errorInfo });
        if (this.props.onError) {
            this.props.onError(error, errorInfo);
        }
    }

    public componentDidUpdate(_prevProps: Props, prevState: State) {
        // Toggle body scroll lock when error state changes
        if (this.state.hasError !== prevState.hasError) {
            if (this.state.hasError) {
                document.documentElement.style.overflow = 'hidden';
                document.body.style.overflow = 'hidden';
                document.documentElement.style.touchAction = 'none';
            } else {
                document.documentElement.style.overflow = '';
                document.body.style.overflow = '';
                document.documentElement.style.touchAction = '';
            }
        }
    }

    public componentWillUnmount() {
        // Restore scroll on unmount
        document.documentElement.style.overflow = '';
        document.body.style.overflow = '';
        document.documentElement.style.touchAction = '';
        if (this.retryTimeoutRef) {
            clearTimeout(this.retryTimeoutRef);
        }
    }

    private handleRetry = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
        if (this.props.onRetry) {
            this.props.onRetry();
        } else {
            window.location.reload();
        }
    };

    public render() {
        const { hasError, error, errorInfo } = this.state;
        const { fallback, errorType = 'general', children } = this.props;

        if (hasError) {
            if (fallback) {
                return fallback;
            }

            const errorCode = getErrorCode(error);
            const errorDescription = getErrorDescription(errorCode);

            // Determine CSS class based on error type
            const boundaryClass = `error-boundary ${errorType === 'no-session' ? 'no-session' : errorType === 'connection' ? 'connection-error' : ''}`;

            return (
                <div className={boundaryClass}>
                    <div className="error-content">
                        <div className="error-code">{errorCode}</div>
                        <div className="error-description">{errorDescription}</div>
                        {import.meta.env.DEV && error && (
                            <details className="error-details">
                                <summary>Technical Details</summary>
                                <pre className="error-stack">
                                    {error.stack}
                                </pre>
                                {errorInfo && (
                                    <pre className="error-info">
                                        {errorInfo.componentStack}
                                    </pre>
                                )}
                            </details>
                        )}
                        <div className="error-actions">
                            <button className="error-retry-btn" onClick={this.handleRetry}>
                                🔄 Retry
                            </button>
                            <button
                                className="error-home-btn"
                                onClick={() => window.location.href = '/'}
                            >
                                🏠 Go to Login
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return children;
    }
}

export default ErrorBoundary;

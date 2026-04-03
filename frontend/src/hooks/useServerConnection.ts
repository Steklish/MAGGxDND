import { useState, useEffect, useCallback } from 'react';

interface UseServerConnectionOptions {
    /** Health check endpoint */
    endpoint?: string;
    /** Check interval in milliseconds */
    interval?: number;
    /** Number of failed checks before showing error */
    failureThreshold?: number;
}

interface UseServerConnectionResult {
    isConnected: boolean;
    isChecking: boolean;
    error: string | null;
    forceShowError: () => void;
    hideError: () => void;
}

/**
 * Hook that monitors server connection via periodic health checks.
 * Shows error page when server becomes unreachable.
 */
export function useServerConnection(
    options: UseServerConnectionOptions = {}
): UseServerConnectionResult {
    const {
        endpoint = '/health',
        interval = 5000,
        failureThreshold = 3,
    } = options;

    const [isConnected, setIsConnected] = useState(true);
    const [isChecking, setIsChecking] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [failureCount, setFailureCount] = useState(0);

    const checkConnection = useCallback(async () => {
        if (isChecking) return;

        setIsChecking(true);
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);

            const response = await fetch(endpoint, {
                method: 'GET',
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (response.ok) {
                setIsConnected(true);
                setFailureCount(0);
                setError(null);
            } else {
                throw new Error(`Server returned ${response.status}`);
            }
        } catch (err) {
            const newFailureCount = failureCount + 1;
            setFailureCount(newFailureCount);

            if (newFailureCount >= failureThreshold) {
                setIsConnected(false);
                setError(
                    err instanceof DOMException && err.name === 'AbortError'
                        ? 'Server is not responding'
                        : 'Connection to server lost'
                );
            }
        } finally {
            setIsChecking(false);
        }
    }, [endpoint, failureThreshold, failureCount, isChecking]);

    const forceShowError = useCallback(() => {
        setIsConnected(false);
        setError('Server connection lost');
        setFailureCount(failureThreshold);
    }, [failureThreshold]);

    const hideError = useCallback(() => {
        setIsConnected(true);
        setError(null);
        setFailureCount(0);
    }, []);

    useEffect(() => {
        // Initial check
        checkConnection();

        // Periodic checks
        const checkInterval = setInterval(checkConnection, interval);

        // Also listen for online/offline events
        const handleOnline = () => {
            setFailureCount(0);
            checkConnection();
        };

        const handleOffline = () => {
            setIsConnected(false);
            setError('Network connection lost');
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            clearInterval(checkInterval);
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, [checkConnection, interval]);

    return {
        isConnected,
        isChecking,
        error,
        forceShowError,
        hideError,
    };
}

import { useState, useEffect, useRef } from 'react';

interface UseServerConnectionOptions {
    endpoint?: string;
    interval?: number;
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
 * Monitors server connection via health checks.
 * Runs EXACTLY one check per interval. No duplicates.
 */
export function useServerConnection(
    options: UseServerConnectionOptions = {}
): UseServerConnectionResult {
    const endpoint = options.endpoint ?? '/health';
    const intervalMs = options.interval ?? 5000;
    const threshold = options.failureThreshold ?? 3;

    const [isConnected, setIsConnected] = useState(true);
    const [isChecking, setIsChecking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // All mutable state in a single ref
    const state = useRef({
        intervalId: 0 as number,
        checking: false,
        failures: 0,
    });

    useEffect(() => {
        // If already running, don't create a new one
        if (state.current.intervalId) return;

        const tick = () => {
            if (state.current.checking) return;
            state.current.checking = true;
            setIsChecking(true);

            const ctrl = new AbortController();
            const tid = setTimeout(() => ctrl.abort(), 3000);

            fetch(endpoint, { signal: ctrl.signal })
                .then((res) => {
                    clearTimeout(tid);
                    if (!res.ok) throw new Error(`${res.status}`);
                    state.current.failures = 0;
                    setIsConnected(true);
                    setError(null);
                })
                .catch((err) => {
                    clearTimeout(tid);
                    state.current.failures += 1;
                    if (state.current.failures >= threshold) {
                        setIsConnected(false);
                        setError(
                            err.name === 'AbortError'
                                ? 'Server not responding'
                                : 'Connection lost'
                        );
                    }
                })
                .finally(() => {
                    state.current.checking = false;
                    setIsChecking(false);
                });
        };

        // Initial check
        tick();

        // Single interval
        state.current.intervalId = window.setInterval(tick, intervalMs);

        // Cleanup: runs ONCE when component unmounts
        return () => {
            if (state.current.intervalId) {
                window.clearInterval(state.current.intervalId);
                state.current.intervalId = 0;
            }
        };
    }, []); // Empty deps = runs ONCE on mount

    const forceShowError = () => {
        setIsConnected(false);
        setError('Server connection lost');
        state.current.failures = threshold;
    };

    const hideError = () => {
        setIsConnected(true);
        setError(null);
        state.current.failures = 0;
    };

    return { isConnected, isChecking, error, forceShowError, hideError };
}

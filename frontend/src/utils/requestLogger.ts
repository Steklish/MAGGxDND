/**
 * Frontend Request/Response Logging Utility
 * Provides comprehensive console logging for all frontend-backend communication
 * with trace ID support for end-to-end request tracking
 * 
 * JOURNEY TRACKING:
 * Frontend → Backend API → Core Engine → Event Pool → WebSocket → Frontend
 */

// Trace colors for console (using ANSI-like styling via console %c)
export const TRACE_STYLES = {
    // Outbound (Frontend → Backend)
    request: 'background: #3498db; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',
    wsOut: 'background: #3498db; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',

    // Inbound (Backend → Frontend)
    response: 'background: #27ae60; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',
    wsIn: 'background: #27ae60; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',

    // Errors
    error: 'background: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',

    // Core/Engine flow
    core: 'background: #9b59b6; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',
    engine: 'background: #8e44ad; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;',

    // Data payloads
    data: 'background: #f39c12; color: white; padding: 2px 8px; border-radius: 3px;',

    // Info/metadata
    info: 'background: #1abc9c; color: white; padding: 2px 8px; border-radius: 3px;',

    // Timing
    timing: 'background: #34495e; color: white; padding: 2px 8px; border-radius: 3px;',

    // Trace ID
    trace: 'color: #f1c40f; font-weight: bold;',

    // Journey stages
    journeyStart: 'background: #16a085; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 14px;',
    journeyStage: 'background: #2ecc71; color: white; padding: 2px 8px; border-radius: 3px;',
    journeyComplete: 'background: #27ae60; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;',
};

/**
 * Generate a unique trace ID for request tracking
 */
export const generateTraceId = (): string => {
    const timestamp = Date.now().toString(36);
    const randomPart = Math.random().toString(36).substring(2, 8);
    return `trace_${timestamp}_${randomPart}`;
};

/**
 * Get or create a trace ID for the current request chain
 */
export const getTraceId = (): string => {
    let traceId = sessionStorage.getItem('current_trace_id');
    if (!traceId) {
        traceId = generateTraceId();
        sessionStorage.setItem('current_trace_id', traceId);
    }
    return traceId;
};

/**
 * Set trace ID for the current request chain
 */
export const setTraceId = (traceId: string): void => {
    sessionStorage.setItem('current_trace_id', traceId);
};

/**
 * Request timing map for tracking request duration
 */
const requestTimings = new Map<string, number>();

/**
 * Log an outbound API request
 */
export const logRequest = (
    method: string,
    url: string,
    data?: any,
    headers?: Record<string, string>
): string => {
    const traceId = getTraceId();
    const startTime = Date.now();
    const timestamp = new Date().toLocaleTimeString();
    const requestKey = `${method}:${url}`;
    
    // Store timing
    requestTimings.set(requestKey, startTime);
    
    // Log request
    console.groupCollapsed(`%c 📤 [${timestamp}] REQUEST → ${method} ${url}`, TRACE_STYLES.request);
    console.log(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    console.log(`%c Method: ${method}`, TRACE_STYLES.info);
    console.log(`%c URL: ${url}`, TRACE_STYLES.info);
    
    if (data) {
        console.log(`%c Request Body:`, TRACE_STYLES.data, data);
    }
    
    if (headers) {
        console.log(`%c Headers:`, TRACE_STYLES.info, {
            ...headers,
            Authorization: headers.Authorization ? 'Bearer ***' : undefined,
            'X-Trace-ID': traceId
        });
    }
    
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #3498db;');
    
    return traceId;
};

/**
 * Log an API response
 */
export const logResponse = (
    method: string,
    url: string,
    status: number,
    data?: any,
    headers?: Record<string, string>
): void => {
    const requestKey = `${method}:${url}`;
    const startTime = requestTimings.get(requestKey);
    const duration = startTime ? Date.now() - startTime : 0;
    const traceId = headers?.['x-trace-id'] || getTraceId();
    const timestamp = new Date().toLocaleTimeString();
    
    console.groupCollapsed(`%c 📥 [${timestamp}] RESPONSE ← ${status} ${method} ${url}`, TRACE_STYLES.response);
    console.log(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
    console.log(`%c Status: ${status}`, TRACE_STYLES.info);
    console.log(`%c Duration: ${duration}ms`, TRACE_STYLES.timing);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    
    if (data) {
        console.log(`%c Response Data:`, TRACE_STYLES.data, data);
    }
    
    if (headers) {
        console.log(`%c Response Headers:`, TRACE_STYLES.info, headers);
    }
    
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #27ae60;');
    
    // Clean up timing
    requestTimings.delete(requestKey);
};

/**
 * Log an API error
 */
export const logError = (
    method: string,
    url: string,
    status: number,
    error: any,
    headers?: Record<string, string>
): void => {
    const requestKey = `${method}:${url}`;
    const startTime = requestTimings.get(requestKey);
    const duration = startTime ? Date.now() - startTime : 0;
    const traceId = headers?.['x-trace-id'] || getTraceId();
    const timestamp = new Date().toLocaleTimeString();
    
    console.groupCollapsed(`%c ❌ [${timestamp}] ERROR ← ${status} ${method} ${url}`, TRACE_STYLES.error);
    console.log(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
    console.log(`%c Status: ${status}`, TRACE_STYLES.error);
    console.log(`%c Duration: ${duration}ms`, TRACE_STYLES.timing);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    console.log(`%c Error:`, TRACE_STYLES.error, error);
    
    if (headers) {
        console.log(`%c Response Headers:`, TRACE_STYLES.info, headers);
    }
    
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #e74c3c;');
    
    // Clean up timing
    requestTimings.delete(requestKey);
};

/**
 * Log an outbound WebSocket message
 */
export const logWebSocketSend = (
    messageType: string,
    data: any,
    sessionId?: string,
    playerId?: string
): void => {
    const traceId = getTraceId();
    const timestamp = new Date().toLocaleTimeString();
    
    console.groupCollapsed(`%c 📤 [${timestamp}] WS OUT → ${messageType}`, TRACE_STYLES.wsOut);
    console.log(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    
    if (sessionId) {
        console.log(`%c Session ID: ${sessionId}`, TRACE_STYLES.info);
    }
    if (playerId) {
        console.log(`%c Player ID: ${playerId}`, TRACE_STYLES.info);
    }
    
    console.log(`%c Message Type: ${messageType}`, TRACE_STYLES.info);
    console.log(`%c Payload:`, TRACE_STYLES.data, data);
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #3498db;');
};

/**
 * Log an inbound WebSocket message
 */
export const logWebSocketReceive = (
    messageType: string,
    data: any,
    sessionId?: string,
    playerId?: string
): void => {
    const traceId = getTraceId();
    const timestamp = new Date().toLocaleTimeString();
    
    console.groupCollapsed(`%c 📥 [${timestamp}] WS IN ← ${messageType}`, TRACE_STYLES.wsIn);
    console.log(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    
    if (sessionId) {
        console.log(`%c Session ID: ${sessionId}`, TRACE_STYLES.info);
    }
    if (playerId) {
        console.log(`%c Player ID: ${playerId}`, TRACE_STYLES.info);
    }
    
    console.log(`%c Message Type: ${messageType}`, TRACE_STYLES.info);
    console.log(`%c Payload:`, TRACE_STYLES.data, data);
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #27ae60;');
};

/**
 * Log core engine processing (for backend logs forwarded to frontend)
 */
export const logCoreProcessing = (
    stage: string,
    data: any,
    traceId?: string
): void => {
    const currentTraceId = traceId || getTraceId();
    const timestamp = new Date().toLocaleTimeString();
    
    console.groupCollapsed(`%c ⚙️ [${timestamp}] CORE → ${stage}`, TRACE_STYLES.core);
    console.log(`%c Trace ID: ${currentTraceId}`, TRACE_STYLES.trace);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    console.log(`%c Stage: ${stage}`, TRACE_STYLES.info);
    console.log(`%c Data:`, TRACE_STYLES.data, data);
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #9b59b6;');
};

/**
 * Log game engine event processing
 */
export const logEngineEvent = (
    eventType: string,
    eventData: any,
    traceId?: string
): void => {
    const currentTraceId = traceId || getTraceId();
    const timestamp = new Date().toLocaleTimeString();
    
    console.groupCollapsed(`%c 🎮 [${timestamp}] ENGINE → ${eventType}`, TRACE_STYLES.engine);
    console.log(`%c Trace ID: ${currentTraceId}`, TRACE_STYLES.trace);
    console.log(`%c Timestamp: ${timestamp}`, TRACE_STYLES.info);
    console.log(`%c Event Type: ${eventType}`, TRACE_STYLES.info);
    console.log(`%c Event Data:`, TRACE_STYLES.data, eventData);
    console.groupEnd();
    
    // Visual separator
    console.log('%c─────────────────────────────────────────────────────', 'color: #8e44ad;');
};

/**
 * Log the start of a request journey from frontend
 */
export const logJourneyStart = (
    actionType: string,
    description: string
): string => {
    const traceId = getTraceId();
    const timestamp = new Date().toLocaleTimeString();

    console.log('%c╔═══════════════════════════════════════════════════════════╗', 'color: #16a085;');
    console.log(`%c║ 🚀 JOURNEY START: ${actionType.padEnd(40)} ║`, TRACE_STYLES.journeyStart);
    console.log('%c╠═══════════════════════════════════════════════════════════╣', 'color: #16a085;');
    console.log(`%c║ Trace ID: ${traceId.padEnd(50)} ║`, TRACE_STYLES.info);
    console.log(`%c║ Time: ${timestamp.padEnd(54)} ║`, TRACE_STYLES.info);
    console.log(`%c║ Description: ${description.padEnd(47)} ║`, TRACE_STYLES.info);
    console.log('%c╠═══════════════════════════════════════════════════════════╣', 'color: #16a085;');
    console.log(`%c║ Stage 1/5: Frontend → Backend API                        ║`, TRACE_STYLES.journeyStage);
    console.log('%c╚═══════════════════════════════════════════════════════════╝', 'color: #16a085;');
    console.log('\n');

    return traceId;
};

/**
 * Log a journey stage transition
 */
export const logJourneyStage = (
    stage: number,
    stageName: string,
    description: string,
    data?: any
): void => {
    const traceId = getTraceId();
    const timestamp = new Date().toLocaleTimeString();

    console.log('%c┌───────────────────────────────────────────────────────────┐', 'color: #2ecc71;');
    console.log(`%c│ Stage ${stage}/5: ${stageName.padEnd(36)} │`, TRACE_STYLES.journeyStage);
    console.log('%c├───────────────────────────────────────────────────────────┤', 'color: #2ecc71;');
    console.log(`%c│ ${description.padEnd(59)} │`, TRACE_STYLES.info);
    if (data) {
        const dataStr = JSON.stringify(data).substring(0, 50);
        console.log(`%c│ Data: ${dataStr.padEnd(53)} │`, TRACE_STYLES.data);
    }
    console.log('%c└───────────────────────────────────────────────────────────┘', 'color: #2ecc71;');
    console.log('\n');
};

/**
 * Log journey completion
 */
export const logJourneyComplete = (
    actionType: string,
    totalDuration: number,
    stages?: string[]
): void => {
    const traceId = getTraceId();
    const timestamp = new Date().toLocaleTimeString();

    console.log('%c╔═══════════════════════════════════════════════════════════╗', 'color: #27ae60;');
    console.log(`%c║ ✅ JOURNEY COMPLETE: ${actionType.padEnd(37)} ║`, TRACE_STYLES.journeyComplete);
    console.log('%c╠═══════════════════════════════════════════════════════════╣', 'color: #27ae60;');
    console.log(`%c║ Trace ID: ${traceId.padEnd(50)} ║`, TRACE_STYLES.info);
    console.log(`%c║ Total Duration: ${totalDuration.toString().padEnd(44)}ms ║`, TRACE_STYLES.timing);
    console.log(`%c║ Time: ${timestamp.padEnd(54)} ║`, TRACE_STYLES.info);
    if (stages && stages.length > 0) {
        stages.forEach((stage) => {
            console.log(`%c║ ✓ ${stage.padEnd(56)} ║`, TRACE_STYLES.journeyStage);
        });
    }
    console.log('%c╚═══════════════════════════════════════════════════════════╝', 'color: #27ae60;');
    console.log('\n');
};

/**
 * Log player action flow (complete journey)
 */
export const logPlayerActionFlow = (
    stage: 'sent' | 'received' | 'processing' | 'complete' | 'error',
    action: string,
    characterName: string,
    sessionId: string,
    data?: any
): void => {
    const traceId = getTraceId();
    const timestamp = new Date().toLocaleTimeString();

    let title = '';
    let style = TRACE_STYLES.info;
    let color = '#1abc9c';

    switch (stage) {
        case 'sent':
            title = `📤 PLAYER ACTION SENT → ${characterName}`;
            style = TRACE_STYLES.request;
            color = '#3498db';
            break;
        case 'received':
            title = `📥 ACTION RECEIVED BY SERVER → ${characterName}`;
            style = TRACE_STYLES.response;
            color = '#27ae60';
            break;
        case 'processing':
            title = `⚙️ ACTION PROCESSING → ${characterName}`;
            style = TRACE_STYLES.core;
            color = '#9b59b6';
            break;
        case 'complete':
            title = `✅ ACTION COMPLETE → ${characterName}`;
            style = TRACE_STYLES.response;
            color = '#27ae60';
            break;
        case 'error':
            title = `❌ ACTION FAILED → ${characterName}`;
            style = TRACE_STYLES.error;
            color = '#e74c3c';
            break;
    }

    console.groupCollapsed(`%c [${timestamp}] ${title}`, style);
    console.log(`%c Trace ID: ${traceId}`, TRACE_STYLES.trace);
    console.log(`%c Character: ${characterName}`, TRACE_STYLES.info);
    console.log(`%c Session: ${sessionId}`, TRACE_STYLES.info);
    console.log(`%c Action: ${action}`, TRACE_STYLES.data);

    if (data) {
        console.log(`%c Additional Data:`, TRACE_STYLES.data, data);
    }

    console.groupEnd();

    // Visual separator
    console.log(`%c─────────────────────────────────────────────────────`, `color: ${color};`);
};

// Export for use in services
export default {
    generateTraceId,
    getTraceId,
    setTraceId,
    logRequest,
    logResponse,
    logError,
    logWebSocketSend,
    logWebSocketReceive,
    logCoreProcessing,
    logEngineEvent,
    logPlayerActionFlow,
    logJourneyStart,
    logJourneyStage,
    logJourneyComplete,
    TRACE_STYLES
};

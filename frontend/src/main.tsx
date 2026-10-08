import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthPage } from './pages/AuthPage';
import { LobbyPage } from './pages/LobbyPage';
import { SessionLobbyPage } from './pages/SessionLobbyPage';
import { GamePage } from './pages/GamePage';
import { OAuthCallback } from './components/OAuthCallback';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import './index.css';

const RootRedirect: React.FC = () => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    return <Navigate to={token ? '/lobby' : '/login'} replace />;
};

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ErrorBoundary>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<RootRedirect />} />
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/lobby" element={<LobbyPage />} />
                    <Route path="/session/:sessionId" element={<SessionLobbyPage />} />
                    <Route path="/session/:sessionId/play" element={<GamePage />} />
                    <Route path="/auth/callback" element={<OAuthCallback />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </BrowserRouter>
        </ErrorBoundary>
    </React.StrictMode>,
);

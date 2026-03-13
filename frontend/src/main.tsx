import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import { HomePage } from './components/HomePage'
import { ProfilePage } from './components/ProfilePage'
import { OAuthCallback } from './components/OAuthCallback'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/profile" element={<ProfilePageWrapper />} />
          <Route path="/auth/callback" element={<OAuthCallback />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)

// Wrapper for ProfilePage to get userId from store
function ProfilePageWrapper() {
    const { userId } = useGameStore();
    const navigate = useNavigate();
    
    if (!userId) {
        // Redirect to home if not authenticated
        navigate('/');
        return null;
    }
    
    return <ProfilePage userId={userId} onBack={() => navigate(-1)} onGoHome={() => navigate('/home')} />;
}

// Need to import useGameStore and useNavigate
import { useGameStore } from './store/gameStore'
import { useNavigate } from 'react-router-dom'

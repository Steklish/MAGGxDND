import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import { HomePage } from './components/HomePage'
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
          <Route path="/auth/callback" element={<OAuthCallback />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)

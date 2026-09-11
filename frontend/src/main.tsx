import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { LanguageProvider } from './i18n/LanguageContext';
import { ToastProvider } from './context/ToastContext';
import './styles/index.css';

// Register PWA Service Worker for offline app shell loading
if ('serviceWorker' in navigator && window.location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(
      (reg) => console.log('[PWA] Service Worker registered on scope:', reg.scope),
      (err) => console.log('[PWA] Service Worker registration failed:', err)
    );
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LanguageProvider>
      <ToastProvider>
        <App />
      </ToastProvider>
    </LanguageProvider>
  </React.StrictMode>
);
